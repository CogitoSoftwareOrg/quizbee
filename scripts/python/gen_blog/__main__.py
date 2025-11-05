"""Allow running the package as a module: python -m gen_blog."""

from .bootstrap.cli import main

if __name__ == "__main__":
    main()
