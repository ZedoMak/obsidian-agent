"""Backend registry. Each backend module exposes a BACKEND object
describing how to launch its MCP server and what system prompt to use.
"""

from . import obsidian

BACKENDS = {
    "obsidian": obsidian.BACKEND,
}


def get_backend(name: str):
    if name not in BACKENDS:
        available = ", ".join(BACKENDS)
        raise ValueError(f"Unknown backend '{name}'. Available: {available}")
    return BACKENDS[name]