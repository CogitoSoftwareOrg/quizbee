.PHONY: dev

dev:
	@echo "Running all services in local docker environment"
	docker compose -f infra/compose.local.yml up --build -d