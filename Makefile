.PHONY: dev clear-deps pr

dev:
	@echo "Running all services in local docker environment"
	docker compose -f infra/compose.local.yml up --build -d
	cd apps/api && uv run python -m uvicorn src.bootstrap:app --reload --host 0.0.0.0
	cd apps/web && pnpm astro dev --host 0.0.0.0 --port 4321
	cd apps/app && pnpm dev --host 0.0.0.0 --port 5173

pr:
	gh pr create --base main --draft --fill