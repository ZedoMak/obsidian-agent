"""Sanity checks: is the backend's MCP server installed, and can we
actually reach it with the configured settings."""

import asyncio
import json
import os
import shutil

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from . import ui


def run_doctor(config: dict, backend):
    ui.console.rule(f"[bold cyan]scribe doctor — {backend.name}")

    server_params = backend.build_server_params(config)
    found = shutil.which(server_params.command) is not None
    if not found:
        ui.console.print(f"[bold red]✗[/] {server_params.command} was not found on your PATH.")
        raise SystemExit(1)
    ui.console.print(f"[bold green]✓[/] {server_params.command} found on PATH.")

    try:
        asyncio.run(_check_connection(config, backend))
    except Exception as e:
        ui.print_error(f"Could not connect: {e}")
        raise SystemExit(1)

    ui.console.print("\n[bold green]All checks passed.[/]")


async def _check_connection(config: dict, backend):
    server_params = backend.build_server_params(config)

    with open(os.devnull, "w") as devnull:
        async with stdio_client(server_params, errlog=devnull) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                ui.console.print(
                    f"[bold green]✓[/] Connected. {len(tools_result.tools)} tools available:"
                )
                for tool in tools_result.tools:
                    desc = (tool.description or "").strip().splitlines()
                    desc = desc[0] if desc else ""
                    ui.console.print(f"  [cyan]{tool.name}[/]  [dim]{desc}[/]")

                # Obsidian-specific smoke test; generalize this once a
                # second backend needs its own probe.
                if backend.name == "obsidian":
                    ui.console.print("\n[dim]Listing notes in vault root...[/]")
                    result = await session.call_tool(
                        "list_notes_tool", arguments={"recursive": True}
                    )
                    content = result.content[0].text if result.content else "No data"
                    try:
                        data = json.loads(content)
                        items = data.get("items", [])
                        ui.console.print(
                            f"[bold green]✓[/] Found {data.get('total', len(items))} notes. First 10:"
                        )
                        for note in items[:10]:
                            ui.console.print(f"  [dim]-[/] {note.get('path')}")
                    except json.JSONDecodeError:
                        ui.console.print("[yellow]Raw response:[/]", content)