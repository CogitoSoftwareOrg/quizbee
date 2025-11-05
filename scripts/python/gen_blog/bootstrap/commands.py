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
    select_files_interactive,
    print_success,
    print_error,
    print_info,
    print_warning,
    console,
)

logger = logging.getLogger(__name__)

# Load environment
loaded = load_dotenv(dotenv_path="../../envs/.env.production")
if not loaded:
    print_error("Failed to load .env file from envs/.env")

PB_URL = os.getenv("PUBLIC_PB_URL", "http://localhost:8090")
PB_EMAIL = os.getenv("PB_EMAIL", "")
PB_PASSWORD = os.getenv("PB_PASSWORD", "")

# Paths
RAW_DIR = Path(__file__).parent.parent / "raw"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


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


async def _generate_single_blog(
    raw_file: Path, progress_task=None
) -> tuple[Path, BlogGenerationOutput | None, str | None]:
    """Generate a single blog post. Returns (raw_file, output, error_message)."""
    try:
        # Load input
        raw_input = load_raw_input(raw_file)

        # Generate blog post
        output = await generate_blog_post(raw_input)

        # Save to local storage
        output_path = save_blog_output(output, raw_file.name)

        return (raw_file, output, None)
    except Exception as e:
        logger.exception(f"Generation error for {raw_file.name}")
        return (raw_file, None, str(e))


async def cmd_generate():
    """Generate new blog post(s) from raw input(s)."""
    console.print("\n[bold blue]═══ Generate Blog Post(s) ═══[/bold blue]\n")

    # Select raw input file(s)
    raw_files = list_raw_files()
    if not raw_files:
        print_error(f"No raw input files found in {RAW_DIR}")
        print_info(f"Please create a JSON file in {RAW_DIR}")
        return

    selected_files = select_files_interactive(raw_files, "Select raw input file(s):")
    if not selected_files:
        print_warning("Cancelled.")
        return

    console.print(
        f"\n[bold]Processing {len(selected_files)} file(s) in parallel...[/bold]\n"
    )

    try:
        # Generate all blog posts in parallel with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description=f"Generating {len(selected_files)} blog post(s) with AI (30-60 seconds each)...",
                total=None,
            )
            results = await asyncio.gather(
                *[_generate_single_blog(f) for f in selected_files],
                return_exceptions=False,
            )

        # Process results
        successful = []
        failed = []

        for raw_file, output, error in results:
            if error:
                failed.append((raw_file, error))
            else:
                successful.append((raw_file, output))

        # Display results
        console.print()
        if successful:
            print_success(f"Successfully generated {len(successful)} blog post(s)!")
            for raw_file, output in successful:
                console.print(f"\n[bold cyan]═══ {raw_file.name} ═══[/bold cyan]")
                display_blog_preview(output)
                output_path = OUTPUT_DIR / f"{raw_file.stem}.json"
                console.print(f"  [dim]Saved to: {output_path.name}[/dim]")

        if failed:
            console.print()
            print_error(f"Failed to generate {len(failed)} blog post(s):")
            for raw_file, error in failed:
                console.print(f"  [red]✗[/red] {raw_file.name}: {error}")

    except Exception as e:
        print_error(f"Batch generation failed: {e}")
        logger.exception("Batch generation error")


async def _upload_single_blog(
    output_file: Path, pb: PocketBase
) -> tuple[Path, dict | None, str | None]:
    """Upload a single blog post. Returns (output_file, result, error_message)."""
    try:
        # Load output
        output = load_blog_output(output_file)

        # Upload
        uploader = BlogUploader(pb)
        result = await uploader.upload_blog_post(output)

        return (output_file, result, None)
    except Exception as e:
        logger.exception(f"Upload error for {output_file.name}")
        return (output_file, None, str(e))


async def cmd_upload():
    """Upload generated blog post(s) to PocketBase."""
    console.print("\n[bold blue]═══ Upload Blog Post(s) ═══[/bold blue]\n")

    # Select output file(s)
    output_files = list_output_files()
    if not output_files:
        print_error(f"No generated blog posts found in {OUTPUT_DIR}")
        print_info("Please generate a blog post first using 'generate' command.")
        return

    selected_files = select_files_interactive(
        output_files, "Select blog post(s) to upload:"
    )
    if not selected_files:
        print_warning("Cancelled.")
        return

    try:
        # Display previews
        for selected in selected_files:
            output = load_blog_output(selected)
            console.print(f"\n[bold cyan]═══ {selected.name} ═══[/bold cyan]")
            display_blog_preview(output)

        # Confirm upload
        confirm = (
            console.input(
                f"\n[bold yellow]Upload {len(selected_files)} blog post(s) to PocketBase? (y/n):[/bold yellow] "
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

        # Upload all posts in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description=f"Uploading {len(selected_files)} blog post(s)...",
                total=None,
            )
            results = await asyncio.gather(
                *[_upload_single_blog(f, pb) for f in selected_files],
                return_exceptions=False,
            )

        # Process results
        successful = []
        failed = []

        for output_file, result, error in results:
            if error:
                failed.append((output_file, error))
            else:
                successful.append((output_file, result))

        # Display results
        console.print()
        if successful:
            print_success(f"Successfully uploaded {len(successful)} blog post(s)!")
            for output_file, result in successful:
                console.print(f"\n[bold cyan]═══ {output_file.name} ═══[/bold cyan]")
                console.print(f"  [cyan]Blog ID:[/cyan] {result['blog_id']}")
                console.print(f"  [cyan]I18n IDs:[/cyan] {result['i18n_ids']}")

        if failed:
            console.print()
            print_error(f"Failed to upload {len(failed)} blog post(s):")
            for output_file, error in failed:
                console.print(f"  [red]✗[/red] {output_file.name}: {error}")

    except Exception as e:
        print_error(f"Batch upload failed: {e}")
        logger.exception("Batch upload error")


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
    console.print("\n[bold blue]═══ Generate & Upload Blog Post(s) ═══[/bold blue]\n")

    # Select raw input file(s)
    raw_files = list_raw_files()
    if not raw_files:
        print_error(f"No raw input files found in {RAW_DIR}")
        return

    selected_files = select_files_interactive(raw_files, "Select raw input file(s):")
    if not selected_files:
        print_warning("Cancelled.")
        return

    console.print(
        f"\n[bold]Processing {len(selected_files)} file(s) in parallel...[/bold]\n"
    )

    try:
        # Generate all blog posts in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description=f"Generating {len(selected_files)} blog post(s) with AI (30-60 seconds each)...",
                total=None,
            )
            gen_results = await asyncio.gather(
                *[_generate_single_blog(f) for f in selected_files],
                return_exceptions=False,
            )

        # Process generation results
        successful_gen = []
        failed_gen = []

        for raw_file, output, error in gen_results:
            if error:
                failed_gen.append((raw_file, error))
            else:
                successful_gen.append((raw_file, output))

        # Display generation results
        console.print()
        if successful_gen:
            print_success(f"Successfully generated {len(successful_gen)} blog post(s)!")
            for raw_file, output in successful_gen:
                console.print(f"\n[bold cyan]═══ {raw_file.name} ═══[/bold cyan]")
                display_blog_preview(output)
                output_path = OUTPUT_DIR / f"{raw_file.stem}.json"
                console.print(f"  [dim]Saved to: {output_path.name}[/dim]")

        if failed_gen:
            console.print()
            print_error(f"Failed to generate {len(failed_gen)} blog post(s):")
            for raw_file, error in failed_gen:
                console.print(f"  [red]✗[/red] {raw_file.name}: {error}")

        if not successful_gen:
            print_warning("No blog posts to upload.")
            return

        # Confirm upload
        confirm = (
            console.input(
                f"\n[bold yellow]Upload {len(successful_gen)} blog post(s) to PocketBase? (y/n):[/bold yellow] "
            )
            .strip()
            .lower()
        )
        if confirm != "y":
            print_info("Skipped upload. Use 'upload' command to upload later.")
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

        # Upload all successfully generated posts in parallel
        output_files_to_upload = [
            OUTPUT_DIR / f"{raw_file.stem}.json" for raw_file, _ in successful_gen
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description=f"Uploading {len(output_files_to_upload)} blog post(s)...",
                total=None,
            )
            upload_results = await asyncio.gather(
                *[_upload_single_blog(f, pb) for f in output_files_to_upload],
                return_exceptions=False,
            )

        # Process upload results
        successful_upload = []
        failed_upload = []

        for output_file, result, error in upload_results:
            if error:
                failed_upload.append((output_file, error))
            else:
                successful_upload.append((output_file, result))

        # Display upload results
        console.print()
        if successful_upload:
            print_success(
                f"Successfully uploaded {len(successful_upload)} blog post(s)!"
            )
            for output_file, result in successful_upload:
                console.print(f"\n[bold cyan]═══ {output_file.name} ═══[/bold cyan]")
                console.print(f"  [cyan]Blog ID:[/cyan] {result['blog_id']}")
                console.print(f"  [cyan]I18n IDs:[/cyan] {result['i18n_ids']}")

        if failed_upload:
            console.print()
            print_error(f"Failed to upload {len(failed_upload)} blog post(s):")
            for output_file, error in failed_upload:
                console.print(f"  [red]✗[/red] {output_file.name}: {error}")

    except Exception as e:
        print_error(f"Workflow failed: {e}")
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
