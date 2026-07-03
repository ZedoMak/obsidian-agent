# scribe

A conversational AI agent for your notes. Ask it to find things, summarize
what you wrote, restructure a mess of files, fix broken links, tag things,
or edit content directly — it figures out which operations to run and
does it, chaining multiple steps together when the task needs it.

Built on [MCP](https://modelcontextprotocol.io) for tool access and
[OpenRouter](https://openrouter.ai) for the LLM, so you can point it at
whichever model you like. Currently supports **Obsidian**, with more
backends (Notion and others) planned — see [Roadmap](#roadmap).

## Requirements

- Python 3.11+
- An [OpenRouter](https://openrouter.ai/keys) API key (free tier available)
- For Obsidian: a vault on your local filesystem

## Install

```bash
pip install git+https://github.com/ZedoMak/scribe.git
```

This pulls in everything needed for the Obsidian backend automatically —
no separate install step.

## First run

```bash
scribe obsidian chat
```

You'll be asked for your OpenRouter API key and the absolute path to your
vault, once. This is saved to `~/.config/scribe/config.toml`. Redo setup
any time with `scribe obsidian config --reset`, or override a single value
with an environment variable: `OPENROUTER_API_KEY`, `OBSIDIAN_VAULT_PATH`,
`AGENT_MODEL`.

## Usage

Every backend follows the same command shape: `scribe <backend> <command>`.

```bash
scribe obsidian chat                                  # interactive session
scribe obsidian task "reorganize my Projects folder"   # one-off task, then exit
scribe obsidian search --query "authentication roadmap"
scribe obsidian summarize --file "Weekly Notes"
scribe obsidian tags --min-usage 5
scribe obsidian doctor                                 # troubleshooting
scribe obsidian config                                 # view current config
```

### Interactive chat

```bash
scribe obsidian chat
```

Talk to your vault like you would to a person. Inside a session:

| Command  | Does                                    |
| -------- | --------------------------------------- |
| `/help`  | list commands                           |
| `/tools` | list every operation the agent can call |
| `/clear` | wipe conversation history, start fresh  |
| `/exit`  | quit (also: `exit`, `quit`, Ctrl+D)     |

### One-off tasks

```bash
scribe obsidian task "merge my two Machine Learning folders and tag everything by topic"
```

Runs a single instruction to completion, then exits — useful for scripting
or quick jobs where you don't want a full chat session.

For anything that changes files, `task` shows you a plan before doing
anything:

╭─ proposed plan ──────────────────────────────────╮
│ 1. Move Model.md and DataSets.md into │
│ Machine Learning/Fundamentals/ │
│ 2. Create Machine Learning/Linear Regression/ │
│ and move the 3 related notes there │
│ 3. Tag all moved notes with #ml │
╰────────────────────────────────────────────────────╯
Proceed with this plan? [y/N]

Nothing is touched until you approve. Skip the prompt with `--yes`/`-y` if
you trust it and want it to just run (careful with this on anything
destructive).

`summarize`, `search`, and `tags` are read-only shortcuts for common
lookups — they skip the plan step since there's nothing to confirm.

## What it can actually do

Anything the underlying Obsidian MCP server exposes: reading, creating,
editing, and deleting notes; searching by text, tag, date, or regex;
managing tags; finding backlinks and broken links; listing orphaned notes;
moving and renaming notes and folders. Run `/tools` inside a chat session
to see the live list.

The agent is instructed to survey your vault before restructuring it,
trust successful operations instead of re-verifying obsessively, and skip
(rather than force) anything that doesn't go as expected — these are
lessons from real failures during development, not defaults you need to
configure.

## Troubleshooting

**`obsidian-mcp was not found on your PATH`**
Run `scribe obsidian doctor` — it checks what's missing and how to fix it.

**A task times out or seems stuck**
Individual tool calls are capped at 30 seconds; a stuck call will report a
timeout instead of hanging forever. If a task genuinely needs to touch a
lot of notes, it's normal for it to take a while — you'll see each tool
call as it happens.

**Something else broke**
This project pins a few dependency versions deliberately
(`fastmcp==2.8.1`, `pydantic<2.12`) because of real breaking changes
upstream in those libraries. If you're hacking on the source directly,
don't loosen those pins without confirming `scribe obsidian doctor` still
passes afterward.

## Roadmap

- [ ] Notion backend
- [ ] Conversation history persistence across sessions
- [ ] More granular per-backend safety controls

## Contributing

Issues and PRs welcome. This is a young project — expect rough edges.

## License

MIT — see [LICENSE](LICENSE).
