.PHONY: run test clean help

help:
	@echo "QuizBee Blog Generator Commands:"
	@echo "  make run     - Run CLI interface"
	@echo "  make clean   - Remove generated output files"
	@echo "  make help    - Show this help message"

run:
	cd .. && uv run python -m gen_blog.main

clean:
	rm -rf output/*.json
	@echo "Cleaned output directory"

