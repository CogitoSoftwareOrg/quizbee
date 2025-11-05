.PHONY: run install clean help

help:
	@echo "QuizBee Blog Generator Commands:"
	@echo "  make run       - Run CLI interface"
	@echo "  make install   - Install/sync dependencies"
	@echo "  make clean     - Remove generated output files"
	@echo "  make help      - Show this help message"

install:
	cd .. && uv sync

run:
	cd .. && uv run python -m gen_blog

clean:
	cd .. && uv run python -m gen_blog clean --force

