.PHONY: dev up down stop tail logs clean pr status

dev:
	docker compose -f infra/compose.local.yml --env-file envs/.env up -d

build:
	docker compose -f infra/compose.local.yml --env-file envs/.env build

infra:
	docker compose -f infra/compose.local.yml up pb meilisearch dragonfly -d

back:
	docker compose -f infra/compose.local.yml up api -d

front:
	docker compose -f infra/compose.local.yml up web app -d

test-prod-build:
	docker compose -f infra/compose.prod.yml --env-file envs/.env build

test-prod-up:
	docker compose -f infra/compose.prod.yml --env-file envs/.env up -d

test-prod-build-infra:
	docker compose -f infra/compose.prod.yml --env-file envs/.env build pb meili dragonfly

test-prod-up-infra:
	docker compose -f infra/compose.prod.yml --env-file envs/.env up pb meili dragonfly -d