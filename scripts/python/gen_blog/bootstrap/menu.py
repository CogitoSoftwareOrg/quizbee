"""Interactive menu for CLI."""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import commands

console = Console()


async def show_interactive_menu():
    """Display interactive menu and handle user input."""
    while True:
        console.clear()

        # Header
        console.print(
            Panel.fit(
                "[bold cyan]🐝 QuizBee Blog Generator[/bold cyan]\n"
                "[dim]AI-powered blog post generation[/dim]",
                border_style="cyan",
            )
        )

        # Menu table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold yellow", justify="right")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        table.add_row("1", "generate", "Generate new blog post from raw input")
        table.add_row("2", "upload", "Upload generated blog post to PocketBase")
        table.add_row("3", "update", "Update existing blog post in PocketBase")
        table.add_row("4", "full", "Generate and upload in one go")
        table.add_row("5", "list", "List generated blog posts")
        table.add_row("6", "clean", "Remove all generated output files")
        table.add_row("q", "quit", "Exit")

        console.print(table)
        console.print()

        # Get user input
        choice = (
            console.input("[bold]Select command (1-6 or q):[/bold] ").strip().lower()
        )

        try:
            if choice in ["1", "generate", "gen", "g"]:
                await commands.cmd_generate()
            elif choice in ["2", "upload", "up", "u"]:
                await commands.cmd_upload()
            elif choice in ["3", "update", "upd"]:
                await commands.cmd_update()
            elif choice in ["4", "full", "f"]:
                await commands.cmd_full()
            elif choice in ["5", "list", "ls", "l"]:
                commands.cmd_list()
            elif choice in ["6", "clean", "c"]:
                from . import cli

                cli.clean(force=False)
            elif choice in ["q", "quit", "exit"]:
                console.print("\n[dim]Goodbye![/dim]")
                break
            else:
                console.print("[red]Invalid command. Try again.[/red]")
                await asyncio.sleep(1)
                continue

            # Pause after command execution
            console.print()
            console.input("[dim]Press Enter to continue...[/dim]")

        except KeyboardInterrupt:
            console.print("\n\n[dim]Interrupted. Returning to menu...[/dim]")
            await asyncio.sleep(1)
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            console.input("[dim]Press Enter to continue...[/dim]")


def run_interactive():
    """Run interactive menu."""
    try:
        asyncio.run(show_interactive_menu())
    except KeyboardInterrupt:
        console.print("\n\n[dim]Goodbye![/dim]")
