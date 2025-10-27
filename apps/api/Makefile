.PHONY: stripe

stripe:
	@echo "Running stripe webhook listener"
	stripe listen --forward-to localhost:8000/billing/stripe/webhook

dev:
	uv run python -m uvicorn src.bootstrap:app --reload --host 0.0.0.0

debug:
	uv run python -m uvicorn src.bootstrap:app --reload --host 0.0.0.0 --log-level debug