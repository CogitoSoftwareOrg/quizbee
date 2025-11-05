"""CLI interface using Typer."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from . import commands

# Setup logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

app = typer.Typer(
    name="gen_blog",
    help="🐝 QuizBee Blog Generator - AI-powered blog post generation",
)

console = Console()


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """
    QuizBee Blog Generator - AI-powered blog post generation.

    Run without arguments for interactive menu, or use specific commands.
    """
    if ctx.invoked_subcommand is None:
        # No command provided, show interactive menu
        from .menu import run_interactive

        run_interactive()


@app.command("generate", help="Generate new blog post from raw input")
def generate():
    """Generate a blog post from raw input file."""
    asyncio.run(commands.cmd_generate())


@app.command("upload", help="Upload generated blog post to PocketBase")
def upload():
    """Upload a generated blog post to PocketBase."""
    asyncio.run(commands.cmd_upload())


@app.command("update", help="Update existing blog post in PocketBase")
def update(
    blog_id: Optional[str] = typer.Argument(
        None, help="Blog post ID to update (will prompt if not provided)"
    )
):
    """Update an existing blog post in PocketBase."""
    asyncio.run(commands.cmd_update(blog_id))


@app.command("full", help="Generate and upload in one go")
def full():
    """Generate a blog post and upload it in one workflow."""
    asyncio.run(commands.cmd_full())


@app.command("list", help="List generated blog posts")
def list_posts():
    """List all generated blog posts in the output directory."""
    commands.cmd_list()


@app.command("clean", help="Remove all generated output files")
def clean(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Remove all generated output files."""
    from .utils import print_success, print_warning, print_info

    output_dir = Path(__file__).parent / "output"

    if not output_dir.exists():
        print_warning("Output directory doesn't exist.")
        return

    files = list(output_dir.glob("*.json"))

    if not files:
        print_info("No files to clean.")
        return

    if not force:
        confirm = typer.confirm(
            f"Delete {len(files)} generated file(s)?", default=False
        )
        if not confirm:
            print_warning("Cancelled.")
            return

    for file in files:
        file.unlink()

    print_success(f"Removed {len(files)} file(s)")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
