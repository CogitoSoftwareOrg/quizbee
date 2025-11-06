"""Local storage utilities for generated blog posts."""

import json
import logging
from pathlib import Path
from datetime import datetime

from .models import BlogGenerationOutput

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def save_blog_output(output: BlogGenerationOutput, input_file: str) -> Path:
    """
    Save generated blog output to local JSON file.

    Args:
        output: Generated blog data
        input_file: Name of the input file (for naming output)

    Returns:
        Path to saved output file
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Create filename from slug and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_stem = Path(input_file).stem
    output_file = OUTPUT_DIR / f"{output.blog.slug}_{timestamp}.json"

    # Convert to dict for JSON serialization
    data = output.model_dump(mode="json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Blog output saved to: {output_file}")
    return output_file


def load_blog_output(file_path: Path) -> BlogGenerationOutput:
    """
    Load blog output from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        BlogGenerationOutput object
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return BlogGenerationOutput.model_validate(data)


def list_output_files() -> list[Path]:
    """List all generated blog output files."""
    if not OUTPUT_DIR.exists():
        return []

    return sorted(OUTPUT_DIR.glob("*.json"), reverse=True)


def get_latest_output() -> Path | None:
    """Get the most recently generated output file."""
    files = list_output_files()
    return files[0] if files else None
