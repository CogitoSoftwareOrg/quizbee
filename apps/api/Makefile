.PHONY: stripe

stripe:
	@echo "Running stripe webhook listener"
	stripe listen --forward-to localhost:8000/billing/stripe/webhook