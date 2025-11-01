#!/usr/bin/env python3
"""
Generate production lock files for apps without workspace dependencies.

This script temporarily hides the workspace root and regenerates lock files
for production deployments (e.g., Coolify).

Usage:
    python scripts/python/gen_prod_locks.py
    python scripts/python/gen_prod_locks.py --app api
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Root of the monorepo
ROOT = Path(__file__).parent.parent.parent
WORKSPACE_FILE = ROOT / "pyproject.toml"
WORKSPACE_BACKUP = ROOT / "pyproject.toml.workspace-backup"


def hide_workspace():
    """Temporarily rename workspace root to make apps standalone."""
    if WORKSPACE_FILE.exists():
        shutil.move(WORKSPACE_FILE, WORKSPACE_BACKUP)
        print(f"✓ Hid workspace root: {WORKSPACE_FILE}")


def restore_workspace():
    """Restore workspace root."""
    if WORKSPACE_BACKUP.exists():
        shutil.move(WORKSPACE_BACKUP, WORKSPACE_FILE)
        print(f"✓ Restored workspace root: {WORKSPACE_FILE}")


def generate_lock(app_name: str):
    """Generate production lock file for an app."""
    app_dir = ROOT / "apps" / app_name

    if not app_dir.exists():
        print(f"✗ App not found: {app_dir}")
        return False

    print(f"\n→ Generating production lock for {app_name}...")

    try:
        result = subprocess.run(
            ["uv", "lock"],
            cwd=app_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Generated {app_name}/uv.lock (production)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate lock for {app_name}")
        print(f"  Error: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate production lock files")
    parser.add_argument(
        "--app",
        help="Specific app to generate lock for (default: all Python apps)",
        default=None
    )
    args = parser.parse_args()

    # Find all Python apps
    apps_dir = ROOT / "apps"
    if args.app:
        apps = [args.app]
    else:
        apps = [
            d.name for d in apps_dir.iterdir()
            if d.is_dir() and (d / "pyproject.toml").exists()
        ]

    print(f"Generating production locks for: {', '.join(apps)}")
    print("=" * 60)

    try:
        # Hide workspace
        hide_workspace()

        # Generate locks
        success = all(generate_lock(app) for app in apps)

        if success:
            print("\n" + "=" * 60)
            print("✓ All production locks generated successfully!")
            print("\nNext steps:")
            print("1. Publish workspace packages to PyPI:")
            print("   cd pkgs/python/example-lib && uv build && uv publish")
            print("2. Commit the updated lock files")
            print("3. Deploy via Coolify")
        else:
            print("\n✗ Some locks failed to generate")
            sys.exit(1)

    finally:
        # Always restore workspace
        restore_workspace()


if __name__ == "__main__":
    main()
