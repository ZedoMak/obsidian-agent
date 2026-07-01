"""Command-line entry point for obsidian-agent."""

import argparse
import asyncio

from .config import CONFIG_FILE, load_config
from .doctor import run_doctor
from .loop import main_loop


def main():
    parser = argparse.ArgumentParser(
        prog="obsidian-agent",
        description="Chat with your Obsidian vault via an MCP-connected AI agent.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("chat", help="Start an interactive chat session (default).")
    subparsers.add_parser("doctor", help="Check that obsidian-mcp is installed and reachable.")
    config_parser = subparsers.add_parser("config", help="View or reset your configuration.")
    config_parser.add_argument("--reset", action="store_true", help="Re-run first-time setup.")

    args = parser.parse_args()
    command = args.command or "chat"

    if command == "config":
        if args.reset:
            load_config(force_setup=True)
        else:
            print(f"Config file: {CONFIG_FILE}")
            if CONFIG_FILE.exists():
                print(CONFIG_FILE.read_text())
            else:
                print("No config yet — run 'obsidian-agent config --reset' to create one.")
        return

    config = load_config()

    if command == "doctor":
        run_doctor(config)
    else:
        asyncio.run(main_loop(config))


if __name__ == "__main__":
    main()