"""CLI commands for blog generation."""

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pocketbase import PocketBase
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..blogger.models import RawBlogInput, BlogGenerationOutput
from ..blogger.agent import generate_blog_post
from ..blogger.storage import save_blog_output, load_blog_output, list_output_files
from ..blogger.uploader import BlogUploader
from .utils import (
    display_blog_preview,
    select_file_interactive,
    print_success,
    print_error,
    print_info,
    print_warning,
    console,
)

logger = logging.getLogger(__name__)

# Load environment
loaded = load_dotenv(dotenv_path="../../envs/.env")
if not loaded:
    print_error("Failed to load .env file from envs/.env")

PB_URL = os.getenv("PUBLIC_PB_URL", "http://localhost:8090")
PB_EMAIL = os.getenv("PB_EMAIL", "")
PB_PASSWORD = os.getenv("PB_PASSWORD", "")

# Paths
RAW_DIR = Path(__file__).parent / "raw"
OUTPUT_DIR = Path(__file__).parent / "output"


def list_raw_files() -> list[Path]:
    """List all raw input files."""
    if not RAW_DIR.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        return []
    return sorted(RAW_DIR.glob("*.json"))


def load_raw_input(file_path: Path) -> RawBlogInput:
    """Load and validate raw input file."""
    logger.info(f"Loading raw input from: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RawBlogInput.model_validate(data)


async def cmd_generate():
    """Generate new blog post from raw input."""
    console.print("\n[bold blue]═══ Generate Blog Post ═══[/bold blue]\n")

    # Select raw input file
    raw_files = list_raw_files()
    if not raw_files:
        print_error(f"No raw input files found in {RAW_DIR}")
        print_info(f"Please create a JSON file in {RAW_DIR}")
        return

    selected = select_file_interactive(raw_files, "Select raw input file:")
    if not selected:
        print_warning("Cancelled.")
        return

    try:
        # Load input
        raw_input = load_raw_input(selected)
        print_success(f"Loaded input: {selected.name}")

        # Generate blog post with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description="Generating blog post with AI (30-60 seconds)...",
                total=None,
            )
            output = await generate_blog_post(raw_input)

        print_success("Blog post generated successfully!")

        # Display preview
        display_blog_preview(output)

        # Save to local storage
        output_path = save_blog_output(output, selected.name)
        print_success(f"Saved to: {output_path.name}")

    except Exception as e:
        print_error(f"Generation failed: {e}")
        logger.exception("Generation error")


async def cmd_upload():
    """Upload generated blog post to PocketBase."""
    console.print("\n[bold blue]═══ Upload Blog Post ═══[/bold blue]\n")

    # Select output file
    output_files = list_output_files()
    if not output_files:
        print_error(f"No generated blog posts found in {OUTPUT_DIR}")
        print_info("Please generate a blog post first using 'generate' command.")
        return

    selected = select_file_interactive(output_files, "Select blog post to upload:")
    if not selected:
        print_warning("Cancelled.")
        return

    try:
        # Load output
        output = load_blog_output(selected)
        print_success(f"Loaded: {selected.name}")

        # Display preview
        display_blog_preview(output)

        # Confirm upload
        confirm = (
            console.input("\n[bold yellow]Upload to PocketBase? (y/n):[/bold yellow] ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print_warning("Cancelled.")
            return

        # Connect to PocketBase
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Connecting to PocketBase...", total=None)
            pb = PocketBase(PB_URL)
            await pb.collection("_superusers").auth.with_password(PB_EMAIL, PB_PASSWORD)

        print_success("Connected to PocketBase")

        # Upload
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Uploading blog post...", total=None)
            uploader = BlogUploader(pb)
            result = await uploader.upload_blog_post(output)

        print_success("Uploaded successfully!")
        console.print(f"  [cyan]Blog ID:[/cyan] {result['blog_id']}")
        console.print(f"  [cyan]I18n IDs:[/cyan] {result['i18n_ids']}")

    except Exception as e:
        print_error(f"Upload failed: {e}")
        logger.exception("Upload error")


async def cmd_update(blog_id: str | None = None):
    """Update existing blog post in PocketBase."""
    console.print("\n[bold blue]═══ Update Blog Post ═══[/bold blue]\n")

    # Get blog ID
    if not blog_id:
        blog_id = console.input("[bold]Enter blog post ID to update:[/bold] ").strip()
    if not blog_id:
        print_warning("Cancelled.")
        return

    # Select output file
    output_files = list_output_files()
    if not output_files:
        print_error(f"No generated blog posts found in {OUTPUT_DIR}")
        return

    selected = select_file_interactive(output_files, "Select blog post data:")
    if not selected:
        print_warning("Cancelled.")
        return

    try:
        # Load output
        output = load_blog_output(selected)
        print_success(f"Loaded: {selected.name}")
        display_blog_preview(output)

        # Confirm update
        confirm = (
            console.input(
                f"\n[bold yellow]Update blog post {blog_id}? (y/n):[/bold yellow] "
            )
            .strip()
            .lower()
        )
        if confirm != "y":
            print_warning("Cancelled.")
            return

        # Connect to PocketBase
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Connecting to PocketBase...", total=None)
            pb = PocketBase(PB_URL)
            await pb.collection("_superusers").auth.with_password(PB_EMAIL, PB_PASSWORD)

        print_success("Connected to PocketBase")

        # Update
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Updating blog post...", total=None)
            uploader = BlogUploader(pb)
            result = await uploader.update_blog_post(blog_id, output)

        print_success("Updated successfully!")
        console.print(f"  [cyan]Blog ID:[/cyan] {result['blog_id']}")
        console.print(f"  [cyan]I18n IDs:[/cyan] {result['i18n_ids']}")

    except Exception as e:
        print_error(f"Update failed: {e}")
        logger.exception("Update error")


async def cmd_full():
    """Generate and upload in one go."""
    console.print("\n[bold blue]═══ Generate & Upload Blog Post ═══[/bold blue]\n")

    # Select raw input file
    raw_files = list_raw_files()
    if not raw_files:
        print_error(f"No raw input files found in {RAW_DIR}")
        return

    selected = select_file_interactive(raw_files, "Select raw input file:")
    if not selected:
        print_warning("Cancelled.")
        return

    try:
        # Load and generate
        raw_input = load_raw_input(selected)
        print_success(f"Loaded input: {selected.name}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description="Generating blog post with AI (30-60 seconds)...",
                total=None,
            )
            output = await generate_blog_post(raw_input)

        print_success("Blog post generated successfully!")

        # Display and save
        display_blog_preview(output)
        output_path = save_blog_output(output, selected.name)
        print_success(f"Saved to: {output_path.name}")

        # Confirm upload
        confirm = (
            console.input("\n[bold yellow]Upload to PocketBase? (y/n):[/bold yellow] ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print_info("Skipped upload. Use 'upload' command to upload later.")
            return

        # Connect and upload
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Connecting to PocketBase...", total=None)
            pb = PocketBase(PB_URL)
            await pb.collection("_superusers").auth.with_password(PB_EMAIL, PB_PASSWORD)

        print_success("Connected to PocketBase")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Uploading blog post...", total=None)
            uploader = BlogUploader(pb)
            result = await uploader.upload_blog_post(output)

        print_success("Uploaded successfully!")
        console.print(f"  [cyan]Blog ID:[/cyan] {result['blog_id']}")
        console.print(f"  [cyan]I18n IDs:[/cyan] {result['i18n_ids']}")

    except Exception as e:
        print_error(f"Failed: {e}")
        logger.exception("Workflow error")


def cmd_list():
    """List generated blog posts."""
    console.print("\n[bold blue]═══ Generated Blog Posts ═══[/bold blue]\n")

    output_files = list_output_files()
    if not output_files:
        print_info("No generated blog posts found.")
        return

    from rich.table import Table

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File Name", style="cyan")
    table.add_column("Modified", style="white")
    table.add_column("Size", justify="right", style="green")

    from datetime import datetime

    for file in output_files:
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        size = file.stat().st_size
        size_kb = size / 1024
        table.add_row(
            file.name,
            mtime.strftime("%Y-%m-%d %H:%M:%S"),
            f"{size_kb:.1f} KB",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(output_files)} file(s)[/dim]")
