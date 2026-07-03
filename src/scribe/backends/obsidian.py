"""Obsidian backend: launches obsidian-mcp against a local vault path."""

import os

from mcp import StdioServerParameters

from .base import Backend

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to the user's Obsidian vault. "
    "Always read a note before updating it so you don't overwrite existing "
    "content by accident, unless the user clearly asks you to replace it. "
    "For tasks that touch many notes (reorganizing, restructuring, bulk "
    "tagging), first list and inspect the relevant notes to build a clear "
    "picture of the vault before making any changes, then work through the "
    "changes methodically one note at a time rather than guessing at "
    "structure up front. If a specific note or operation isn't working "
    "after one or two attempts, don't keep retrying it — skip that note, "
    "note it in your final summary as something you couldn't resolve, and "
    "continue with the rest of the task. Trust the result of a successful "
    "tool call — if move_note_tool or rename_note_tool reports success, "
    "the operation happened; do not re-verify it more than once, and never "
    "use create_note_tool to 'recreate' or 'fix' a note that already "
    "exists elsewhere in the vault. Never call any tool with overwrite=True "
    "unless the user explicitly asked to replace that specific note's "
    "content. If you are ever unsure whether an operation succeeded, stop "
    "and report the uncertainty to the user instead of guessing or "
    "reconstructing content from memory."
)


def build_server_params(config: dict) -> StdioServerParameters:
    return StdioServerParameters(
        command="obsidian-mcp",
        args=[],
        env={
            **os.environ,
            "OBSIDIAN_VAULT_PATH": config["obsidian_vault_path"],
            "OBSIDIAN_LOG_LEVEL": "ERROR",
        },
    )


BACKEND = Backend(
    name="obsidian",
    system_prompt=SYSTEM_PROMPT,
    build_server_params=build_server_params,
    required_config_keys=["obsidian_vault_path"],
    setup_prompts={
        "obsidian_vault_path": "Enter the absolute path to your Obsidian vault: ",
    },
)