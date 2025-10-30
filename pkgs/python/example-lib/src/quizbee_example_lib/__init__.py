"""Example shared library for QuizBee."""

__version__ = "0.1.0"


def greet(name: str) -> str:
    """Example function to demonstrate hot-reload."""
    return f"Hello, {name} from quizbee-example-lib!"


__all__ = ["greet", "__version__"]
