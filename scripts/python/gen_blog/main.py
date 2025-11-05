"""CLI tool for AI-powered blog post generation."""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pocketbase import PocketBase

from .models import RawBlogInput, BlogGenerationOutput
from .agent import generate_blog_post
from .storage import save_blog_output, load_blog_output, list_output_files
from .uploader import BlogUploader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment
loaded = load_dotenv(dotenv_path="../../envs/.env")
assert loaded, "Failed to load .env file"

PB_URL = os.getenv("PUBLIC_PB_URL", "")
PB_EMAIL = os.getenv("PB_EMAIL", "")
PB_PASSWORD = os.getenv("PB_PASSWORD", "")

# Paths
RAW_DIR = Path(__file__).parent / "raw"
OUTPUT_DIR = Path(__file__).parent / "output"


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_success(text: str):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text: str):
    """Print error message."""
    print(f"✗ {text}", file=sys.stderr)


def list_raw_files() -> list[Path]:
    """List all raw input files."""
    if not RAW_DIR.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        return []

    return sorted(RAW_DIR.glob("*.json"))


def select_file(files: list[Path], prompt: str) -> Path | None:
    """Interactive file selection."""
    if not files:
        return None

    print(prompt)
    for i, file in enumerate(files, 1):
        print(f"  {i}. {file.name}")

    while True:
        try:
            choice = input("\nEnter number (or 'q' to quit): ").strip()
            if choice.lower() == "q":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
            print("Invalid selection. Try again.")
        except (ValueError, KeyboardInterrupt):
            return None


def load_raw_input(file_path: Path) -> RawBlogInput:
    """Load and validate raw input file."""
    logger.info(f"Loading raw input from: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RawBlogInput.model_validate(data)


def display_blog_preview(output: BlogGenerationOutput):
    """Display preview of generated blog post."""
    print("\n" + "─" * 60)
    print(f"Slug: {output.blog.slug}")
    print(f"Category: {output.blog.category}")
    print(f"Tags: {', '.join(output.blog.tags)}")
    print(f"Authors: {', '.join(output.blog.authors)}")
    print(f"Published: {output.blog.published}")
    print("\nLanguages:")
    for i18n in output.i18n_entries:
        print(f"  - {i18n.locale}: {i18n.data.title}")
        print(f"    Status: {i18n.status}")
        print(f"    Description: {i18n.data.description[:80]}...")
        content_preview = i18n.content[:200].replace("\n", " ")
        print(f"    Content: {content_preview}...")
    print("─" * 60)


async def action_generate():
    """Generate new blog post from raw input."""
    print_header("Generate Blog Post")

    # Select raw input file
    raw_files = list_raw_files()
    if not raw_files:
        print_error(f"No raw input files found in {RAW_DIR}")
        print(f"Please create a JSON file in {RAW_DIR}")
        return

    selected = select_file(raw_files, "Select raw input file:")
    if not selected:
        print("Cancelled.")
        return

    try:
        # Load input
        raw_input = load_raw_input(selected)
        print_success(f"Loaded input: {selected.name}")

        # Generate blog post
        print("\nGenerating blog post with AI... (this may take 30-60 seconds)")
        output = await generate_blog_post(raw_input)
        print_success("Blog post generated successfully!")

        # Display preview
        display_blog_preview(output)

        # Save to local storage
        output_path = save_blog_output(output, selected.name)
        print_success(f"Saved to: {output_path}")

    except Exception as e:
        print_error(f"Generation failed: {e}")
        logger.exception("Generation error")


async def action_upload():
    """Upload generated blog post to PocketBase."""
    print_header("Upload Blog Post")

    # Select output file
    output_files = list_output_files()
    if not output_files:
        print_error(f"No generated blog posts found in {OUTPUT_DIR}")
        print("Please generate a blog post first.")
        return

    selected = select_file(output_files, "Select blog post to upload:")
    if not selected:
        print("Cancelled.")
        return

    try:
        # Load output
        output = load_blog_output(selected)
        print_success(f"Loaded: {selected.name}")

        # Display preview
        display_blog_preview(output)

        # Confirm upload
        confirm = input("\nUpload to PocketBase? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

        # Connect to PocketBase
        pb = PocketBase(PB_URL)
        await pb.collection("_superusers").auth.with_password(PB_EMAIL, PB_PASSWORD)
        print_success("Connected to PocketBase")

        # Upload
        uploader = BlogUploader(pb)
        result = await uploader.upload_blog_post(output)

        print_success(f"Uploaded successfully!")
        print(f"  Blog ID: {result['blog_id']}")
        print(f"  I18n IDs: {', '.join(result['i18n_ids'])}")

    except Exception as e:
        print_error(f"Upload failed: {e}")
        logger.exception("Upload error")


async def action_update():
    """Update existing blog post in PocketBase."""
    print_header("Update Blog Post")

    # Get blog ID
    blog_id = input("Enter blog post ID to update: ").strip()
    if not blog_id:
        print("Cancelled.")
        return

    # Select output file
    output_files = list_output_files()
    if not output_files:
        print_error(f"No generated blog posts found in {OUTPUT_DIR}")
        return

    selected = select_file(output_files, "Select blog post data:")
    if not selected:
        print("Cancelled.")
        return

    try:
        # Load output
        output = load_blog_output(selected)
        print_success(f"Loaded: {selected.name}")
        display_blog_preview(output)

        # Confirm update
        confirm = input(f"\nUpdate blog post {blog_id}? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

        # Connect to PocketBase
        pb = PocketBase(PB_URL)
        await pb.collection("_superusers").auth.with_password(PB_EMAIL, PB_PASSWORD)
        print_success("Connected to PocketBase")

        # Update
        uploader = BlogUploader(pb)
        result = await uploader.update_blog_post(blog_id, output)

        print_success(f"Updated successfully!")
        print(f"  Blog ID: {result['blog_id']}")
        print(f"  I18n IDs: {', '.join(result['i18n_ids'])}")

    except Exception as e:
        print_error(f"Update failed: {e}")
        logger.exception("Update error")


async def action_full_workflow():
    """Generate and upload in one go."""
    print_header("Generate & Upload Blog Post")

    # Select raw input file
    raw_files = list_raw_files()
    if not raw_files:
        print_error(f"No raw input files found in {RAW_DIR}")
        return

    selected = select_file(raw_files, "Select raw input file:")
    if not selected:
        print("Cancelled.")
        return

    try:
        # Load and generate
        raw_input = load_raw_input(selected)
        print_success(f"Loaded input: {selected.name}")

        print("\nGenerating blog post with AI... (this may take 30-60 seconds)")
        output = await generate_blog_post(raw_input)
        print_success("Blog post generated successfully!")

        # Display and save
        display_blog_preview(output)
        output_path = save_blog_output(output, selected.name)
        print_success(f"Saved to: {output_path}")

        # Confirm upload
        confirm = input("\nUpload to PocketBase? (y/n): ").strip().lower()
        if confirm != "y":
            print("Skipped upload. Use 'upload' command to upload later.")
            return

        # Connect and upload
        pb = PocketBase(PB_URL)
        await pb.collection("_superusers").auth.with_password(PB_EMAIL, PB_PASSWORD)
        print_success("Connected to PocketBase")

        uploader = BlogUploader(pb)
        result = await uploader.upload_blog_post(output)

        print_success(f"Uploaded successfully!")
        print(f"  Blog ID: {result['blog_id']}")
        print(f"  I18n IDs: {', '.join(result['i18n_ids'])}")

    except Exception as e:
        print_error(f"Failed: {e}")
        logger.exception("Workflow error")


def show_menu():
    """Display main menu."""
    print_header("QuizBee Blog Generator")
    print("Commands:")
    print("  1. generate - Generate blog post from raw input")
    print("  2. upload   - Upload generated blog post to PocketBase")
    print("  3. update   - Update existing blog post in PocketBase")
    print("  4. full     - Generate and upload in one go")
    print("  5. list     - List generated blog posts")
    print("  6. quit     - Exit")
    print()


async def main():
    """Main CLI loop."""
    while True:
        show_menu()
        choice = input("Enter command: ").strip().lower()

        if choice in ["1", "generate", "gen"]:
            await action_generate()
        elif choice in ["2", "upload", "up"]:
            await action_upload()
        elif choice in ["3", "update", "upd"]:
            await action_update()
        elif choice in ["4", "full", "f"]:
            await action_full_workflow()
        elif choice in ["5", "list", "ls"]:
            output_files = list_output_files()
            if output_files:
                print("\nGenerated blog posts:")
                for file in output_files:
                    print(f"  - {file.name}")
            else:
                print("\nNo generated blog posts found.")
        elif choice in ["6", "quit", "exit", "q"]:
            print("\nGoodbye!")
            break
        else:
            print("Invalid command. Try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
