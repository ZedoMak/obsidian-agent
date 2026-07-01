"""The agentic chat loop: keeps calling tools until the model responds
with plain text instead of another tool call, instead of stopping after
one round."""

import json
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from .core import (
    SYSTEM_PROMPT,
    build_llm_client,
    build_server_params,
    convert_mcp_tool_to_openai,
    execute_tool_call,
)

MAX_STEPS = 8
EXTRA_HEADERS = {
    "HTTP-Referer": "http://localhost:8080",
    "X-Title": "Obsidian Agent",
}


async def run_turn(client_llm, model, messages, tools, session, max_steps=MAX_STEPS):
    """Keep calling tools, feeding results back to the model, until it
    responds with plain text instead of another tool call, or the step
    budget runs out."""
    for _ in range(max_steps):
        response = client_llm.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            extra_headers=EXTRA_HEADERS,
        )
        msg = response.choices[0].message
        messages.append(msg.to_dict())

        if not msg.tool_calls:
            return msg.content

        print("Agent is using tools...")
        for tool_call in msg.tool_calls:
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                result_text = "Error: malformed tool arguments"
            else:
                result_text = await execute_tool_call(
                    tool_call.function.name, args, session
                )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text,
                }
            )

    return "Stopped after too many steps — the task may be more complex than expected."


async def main_loop(config: dict):
    vault_path = config["vault_path"]
    model = config["model"]
    api_key = config["openrouter_api_key"]

    client_llm = build_llm_client(api_key)
    server_params = build_server_params(vault_path)

    print(f"Starting Obsidian MCP server for vault: {vault_path}")

    # AsyncExitStack keeps the stdio subprocess and MCP session alive for
    # the whole chat loop. Returning a session from inside a narrower
    # "async with" block would close the connection the moment that
    # function returns — every tool call after that would silently fail.
    async with AsyncExitStack() as stack:
        read_stream, write_stream = await stack.enter_async_context(
            stdio_client(server_params)
        )
        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await session.initialize()
        tools_result = await session.list_tools()
        if not tools_result.tools:
            print("No tools available. Exiting.")
            return

        openai_tools = [convert_mcp_tool_to_openai(t) for t in tools_result.tools]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        print(f"Agent ready (using {model}). Type 'exit' to quit.\n")
        while True:
            try:
                user_input = input("You: ")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})

            try:
                reply = await run_turn(client_llm, model, messages, openai_tools, session)
                messages.append({"role": "assistant", "content": reply})
                print(f"Agent: {reply}\n")
            except Exception as e:
                print(f"Error: {e}\n")