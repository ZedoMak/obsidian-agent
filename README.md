# obsidian-agent

A conversational AI agent that reads, searches, and edits your Obsidian
vault, using [MCP](https://modelcontextprotocol.io) to talk to the
`obsidian-mcp` server and OpenRouter for the LLM.

## Install

```bash
pip install -e .
```

You also need `obsidian-mcp` installed and on your PATH — check with:

```bash
obsidian-agent doctor
```

## Usage

```bash
obsidian-agent        # starts a chat session (runs first-time setup if needed)
obsidian-agent doctor # checks obsidian-mcp is installed and can reach your vault
obsidian-agent config --reset  # redo setup (change API key, vault path, model)
```

On first run you'll be asked for your OpenRouter API key, your vault's
absolute path, and which model to use. This is saved to
`~/.config/obsidian-agent/config.toml`.

You can override any of these with environment variables instead:
`OPENROUTER_API_KEY`, `OBSIDIAN_VAULT_PATH`, `AGENT_MODEL`.
