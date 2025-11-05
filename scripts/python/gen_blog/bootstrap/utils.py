"""Utility functions for CLI."""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..blogger.models import BlogGenerationOutput

console = Console()


def display_blog_preview(output: BlogGenerationOutput):
    """Display rich preview of generated blog post."""
    # Main info panel
    main_info = f"""[bold]Slug:[/bold] {output.blog.slug}
[bold]Category:[/bold] {output.blog.category.value}
[bold]Tags:[/bold] {', '.join(output.blog.tags) if output.blog.tags else 'None'}
[bold]Authors:[/bold] {', '.join(output.blog.authors)}
[bold]Published:[/bold] {'✓ Yes' if output.blog.published else '✗ No (draft)'}"""

    console.print(Panel(main_info, title="📝 Blog Post", border_style="blue"))

    # Languages table
    table = Table(
        title="🌍 Translations", show_header=True, header_style="bold magenta"
    )
    table.add_column("Language", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Content Length", justify="right", style="green")

    for i18n in output.i18n_entries:
        status_icon = "✓" if i18n.status == "published" else "○"
        table.add_row(
            i18n.locale.upper(),
            i18n.data.title[:50] + ("..." if len(i18n.data.title) > 50 else ""),
            f"{status_icon} {i18n.status}",
            f"{len(i18n.content):,} chars",
        )

    console.print(table)

    # Description preview
    if output.i18n_entries:
        first_entry = output.i18n_entries[0]
        console.print(
            Panel(
                first_entry.data.description,
                title="📄 Description (first language)",
                border_style="green",
            )
        )


def select_file_interactive(files: list[Path], prompt: str) -> Path | None:
    """Interactive file selection with rich table."""
    if not files:
        return None

    console.print(f"\n[bold cyan]{prompt}[/bold cyan]")

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("File Name", style="white")
    table.add_column("Modified", style="dim")

    for i, file in enumerate(files, 1):
        from datetime import datetime

        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        table.add_row(str(i), file.name, mtime.strftime("%Y-%m-%d %H:%M"))

    console.print(table)

    while True:
        try:
            choice = console.input(
                "\n[bold]Enter number (or 'q' to quit):[/bold] "
            ).strip()
            if choice.lower() == "q":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
            console.print("[red]Invalid selection. Try again.[/red]")
        except (ValueError, KeyboardInterrupt):
            return None


def print_success(message: str):
    """Print success message with icon."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print error message with icon."""
    console.print(f"[red]✗[/red] {message}", style="bold red")


def print_info(message: str):
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")
