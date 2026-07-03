"""The agentic chat loop and one-shot task runner. Backend-agnostic:
works against whichever Backend (obsidian, notion, ...) is passed in."""

import json
from contextlib import AsyncExitStack

from . import ui
from .core import build_llm_client, connect_session, execute_tool_call, split_tools

MAX_STEPS_CHAT = 10
MAX_STEPS_PLAN = 15
MAX_STEPS_EXECUTE = 40

EXTRA_HEADERS = {
    "HTTP-Referer": "http://localhost:8080",
    "X-Title": "Scribe",
}

PLAN_INSTRUCTION = (
    "\n\nFirst, investigate using the read-only tools available to you to "
    "understand the current state of the relevant items. Do NOT make any "
    "changes yet — you don't have write tools available in this phase. "
    "Once you understand what needs to happen, respond with a clear, "
    "numbered, human-readable plan describing exactly what you will "
    "create, move, rename, or edit, and how. Do not call any more tools "
    "once you're ready to write the plan."
)

EXECUTE_INSTRUCTION = (
    "The user approved the plan above. Execute it now, exactly as "
    "described, using the tools available to you. Work through it "
    "methodically. If something doesn't match what you expected, don't "
    "improvise a workaround — skip that step, note it, and continue "
    "with the rest of the plan."
)


async def run_turn(client_llm, model, messages, tools, session, max_steps):
    seen_calls = {}

    for step in range(max_steps):
        with ui.thinking_spinner():
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

        for tool_call in msg.tool_calls:
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                result_text = "Error: malformed tool arguments"
            else:
                signature = (tool_call.function.name, json.dumps(args, sort_keys=True))
                if signature in seen_calls:
                    result_text = (
                        "You already called this exact tool with these exact "
                        "arguments earlier. Don't retry it — use the earlier "
                        "result, try something different, or skip this and "
                        "move on."
                    )
                else:
                    ui.print_tool_call(tool_call.function.name, args)
                    result_text = await execute_tool_call(
                        tool_call.function.name, args, session
                    )
                    seen_calls[signature] = result_text
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": result_text}
            )

    return (
        f"Stopped after {max_steps} steps — this task may need breaking "
        "into smaller pieces, or run it again to continue from here."
    )


def handle_slash_command(command: str, messages: list, tools: list, system_prompt: str) -> bool:
    if command == "/help":
        ui.print_help()
        return True
    if command == "/tools":
        ui.print_tools(tools)
        return True
    if command == "/clear":
        messages.clear()
        messages.append({"role": "system", "content": system_prompt})
        ui.console.print("[dim]Conversation cleared.[/]\n")
        return True
    return False


async def main_loop(config: dict, backend):
    model = config["model"]
    client_llm = build_llm_client(config["openrouter_api_key"])

    async with AsyncExitStack() as stack:
        with ui.console.status(f"[dim]starting {backend.name}...[/]"):
            session, openai_tools = await connect_session(stack, backend, config)

        messages = [{"role": "system", "content": backend.system_prompt}]
        ui.print_banner(backend.name, model)

        while True:
            try:
                ui.print_turn_separator()
                user_input = ui.prompt_user()
            except (EOFError, KeyboardInterrupt):
                ui.console.print("\n[dim]Goodbye.[/]")
                break

            stripped = user_input.strip()
            if not stripped:
                continue
            if stripped.lower() in ("exit", "quit", "/exit", "/quit"):
                ui.console.print("[dim]Goodbye.[/]")
                break
            if stripped.startswith("/"):
                if handle_slash_command(stripped, messages, openai_tools, backend.system_prompt):
                    continue

            messages.append({"role": "user", "content": user_input})

            try:
                reply = await run_turn(
                    client_llm, model, messages, openai_tools, session, MAX_STEPS_CHAT
                )
                messages.append({"role": "assistant", "content": reply})
                ui.print_agent_reply(reply)
            except Exception as e:
                ui.print_error(str(e))


async def run_once(config: dict, backend, task_prompt: str, skip_confirm: bool = False):
    model = config["model"]
    client_llm = build_llm_client(config["openrouter_api_key"])

    async with AsyncExitStack() as stack:
        with ui.console.status(f"[dim]connecting to {backend.name}...[/]"):
            session, all_tools = await connect_session(stack, backend, config)

        read_only_tools, write_tools = split_tools(all_tools)

        if not write_tools:
            messages = [
                {"role": "system", "content": backend.system_prompt},
                {"role": "user", "content": task_prompt},
            ]
            try:
                reply = await run_turn(
                    client_llm, model, messages, all_tools, session, MAX_STEPS_EXECUTE
                )
                ui.print_agent_reply(reply)
            except Exception as e:
                ui.print_error(str(e))
            return

        messages = [
            {"role": "system", "content": backend.system_prompt},
            {"role": "user", "content": task_prompt + PLAN_INSTRUCTION},
        ]
        try:
            plan = await run_turn(
                client_llm, model, messages, read_only_tools, session, MAX_STEPS_PLAN
            )
        except Exception as e:
            ui.print_error(str(e))
            return

        ui.print_plan(plan or "(the agent didn't produce a plan)")

        if not skip_confirm:
            if not ui.confirm_plan():
                ui.console.print("[dim]Cancelled. No changes were made.[/]")
                return

        messages.append({"role": "assistant", "content": plan})
        messages.append({"role": "user", "content": EXECUTE_INSTRUCTION})
        try:
            result = await run_turn(
                client_llm, model, messages, all_tools, session, MAX_STEPS_EXECUTE
            )
            ui.print_agent_reply(result)
        except Exception as e:
            ui.print_error(str(e))