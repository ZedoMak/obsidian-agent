# obsidian-agent

A conversational AI agent for your Obsidian vault. Ask it to find notes,
summarize what you wrote last week, fix broken links, tag things, or
edit a note — it figures out which vault operations to run and does it,
chaining multiple steps together when needed.

Built on [MCP](https://modelcontextprotocol.io) (the same protocol Claude
Desktop uses for tool access) and [OpenRouter](https://openrouter.ai) for
the LLM, so you can point it at whichever model you like.

## Requirements

- Python 3.11+
- An [OpenRouter](https://openrouter.ai/keys) API key (free tier available)
- An Obsidian vault on your local filesystem

## Install

```bash
pip install git+https://github.com/ZedoMak/obsidian-agent.git
```

This pulls in `obsidian-mcp` (the vault-access server) automatically —
no separate install step needed.

## First run

```bash
obsidian-agent
```

You'll be asked three things once, and never again:

- your OpenRouter API key
- the absolute path to your vault
- which model to use (defaults to a free-tier model if you're not sure)

This gets saved to `~/.config/obsidian-agent/config.toml`. Change it later
with `obsidian-agent config --reset`, or override any single value with an
environment variable: `OPENROUTER_API_KEY`, `OBSIDIAN_VAULT_PATH`, `AGENT_MODEL`.

## Usage

```bash
obsidian-agent          # start chatting with your vault
obsidian-agent doctor   # troubleshooting: checks obsidian-mcp is installed
                         # and can actually reach your vault
obsidian-agent config   # view current config
```

Inside a chat session:

| Command  | Does                                          |
| -------- | --------------------------------------------- |
| `/help`  | list commands                                 |
| `/tools` | list every vault operation the agent can call |
| `/clear` | wipe conversation history, start fresh        |
| `/exit`  | quit (also: `exit`, `quit`, Ctrl+D)           |

## What it can actually do

Anything the underlying `obsidian-mcp` server exposes — reading, creating,
editing, and deleting notes; searching by text, tag, date, or regex;
managing tags; finding backlinks and broken links; listing orphaned notes.
Run `/tools` inside a session to see the live list for your installed version.

The agent always reads a note before editing it, so it won't blindly
overwrite content — this is a system-level instruction, not something you
need to ask for each time.

## Troubleshooting

**`obsidian-mcp was not found on your PATH`**
Run `obsidian-agent doctor` — it'll tell you exactly what's missing and how
to fix it.

**Something else broke**
This project pins a few dependency versions deliberately
(`fastmcp==2.8.1`, `pydantic<2.12`) because of real breaking changes
upstream. If you're hacking on the source directly rather than using
`pip install`, don't loosen those pins without checking `obsidian-agent doctor`
still passes afterward.

## Contributing

Issues and PRs welcome. This is a young project — expect rough edges.

## License

MIT — see [LICENSE](LICENSE).
