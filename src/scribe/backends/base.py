"""Shared shape every backend must implement."""

from dataclasses import dataclass
from typing import Callable

from mcp import StdioServerParameters


@dataclass
class Backend:
    name: str
    system_prompt: str
    build_server_params: Callable[[dict], StdioServerParameters]
    required_config_keys: list[str]      # keys this backend needs from config
    setup_prompts: dict[str, str]        # config_key -> prompt text for first-run setup