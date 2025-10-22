.PHONY: dev clear-deps

dev:
	@echo "Running all services in local docker environment"
	docker compose -f infra/compose.local.yml up --build -d

clear-deps:
	@echo "Clearing dependencies"
	docker volume rm quizbee-local_app_node_modules quizbee-local_web_node_modules