"""Command-line entry point for obsidian-agent, built on Typer for
clean --help output and a lower-boilerplate command structure."""

import asyncio

import typer

from .config import CONFIG_FILE, load_config
from .doctor import run_doctor
from .loop import main_loop

app = typer.Typer(
    name="obsidian-agent",
    help="Chat with your Obsidian vault via an MCP-connected AI agent.",
    add_completion=True,
    no_args_is_help=False,
)


@app.command()
def chat():
    """Start an interactive chat session (default command)."""
    config = load_config()
    asyncio.run(main_loop(config))


@app.command()
def doctor():
    """Check that obsidian-mcp is installed and can reach your vault."""
    config = load_config()
    run_doctor(config)


@app.command()
def config(reset: bool = typer.Option(False, "--reset", help="Re-run first-time setup.")):
    """View or reset your configuration."""
    if reset:
        load_config(force_setup=True)
        return
    typer.echo(f"Config file: {CONFIG_FILE}")
    if CONFIG_FILE.exists():
        typer.echo(CONFIG_FILE.read_text())
    else:
        typer.echo("No config yet — run 'obsidian-agent config --reset' to create one.")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        chat()


if __name__ == "__main__":
    app()