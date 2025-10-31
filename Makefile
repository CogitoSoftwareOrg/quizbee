.PHONY: dev up down stop tail logs clean pr status

dev:
	docker compose -f infra/compose.local.yml up -d

build:
	docker compose -f infra/compose.local.yml up -d --build

infra:
	docker compose -f infra/compose.local.yml up pb meilisearch dragonfly -d

back:
	docker compose -f infra/compose.local.yml up api -d

front:
	docker compose -f infra/compose.local.yml up web app -d