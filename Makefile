.PHONY: dev up down stop tail logs clean pr status

dev:
	docker compose -f infra/compose.local.yml up -d

build:
	docker compose -f infra/compose.local.yml build --no-cache

infra:
	docker compose -f infra/compose.local.yml up pb meilisearch dragonfly -d

back:
	docker compose -f infra/compose.local.yml up api -d

front:
	docker compose -f infra/compose.local.yml up web app -d

test-prod-build:
	docker compose -f infra/compose.prod.yml build --no-cache

test-prod-up:
	docker compose -f infra/compose.prod.yml up -d