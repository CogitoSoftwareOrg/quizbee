SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: dev up down stop tail logs clean pr status

LOG_DIR := logs
PID_DIR := .pids
TS := $(shell date +%Y%m%d-%H%M%S)

# stdbuf может отсутствовать: аккуратно даунгрейдимся к пустой строке
BUF := $(shell command -v stdbuf >/dev/null 2>&1 && echo "stdbuf -oL -eL" || echo "")

# Универсальный фоновой запуск с логами и PID
define run_bg
	mkdir -p $(LOG_DIR) $(PID_DIR)
	log_out="$(LOG_DIR)/$(1).$(TS).log"; \
	log_err="$(LOG_DIR)/$(1).$(TS).err"; \
	( cd $(2) && $(BUF) $(3) ) \
		> >(tee -a $$log_out) \
		2> >(tee -a $$log_err >&2) & \
	echo $$! > $(PID_DIR)/$(1).pid; \
	ln -sf $$(basename $$log_out) $(LOG_DIR)/$(1).latest.log; \
	ln -sf $$(basename $$log_err) $(LOG_DIR)/$(1).latest.err; \
	echo "• $(1) started (pid $$(cat $(PID_DIR)/$(1).pid)) → logs: $$log_out"
endef

# ---- infra (docker compose) ----
up:
	@echo "Running infra via Docker Compose"
	@mkdir -p $(LOG_DIR)
	docker compose -f infra/compose.local.yml up --build -d \
		> >(tee -a $(LOG_DIR)/compose.$(TS).out) \
		2> >(tee -a $(LOG_DIR)/compose.$(TS).err >&2)
	@ln -sf compose.$(TS).out $(LOG_DIR)/compose.latest.out
	@ln -sf compose.$(TS).err $(LOG_DIR)/compose.latest.err

down:
	@echo "Stopping Docker Compose infra"
	-docker compose -f infra/compose.local.yml down

status:
	@echo "=== Docker ==="
	@docker compose -f infra/compose.local.yml ps || true
	@echo "=== PIDs ==="
	@ls -1 $(PID_DIR)/*.pid 2>/dev/null || echo "no local dev pids"

# ---- dev processes ----
dev: up
	@echo "Starting local dev processes (logs → ./$(LOG_DIR))"
	# api
	@PYTHONUNBUFFERED=1 $(call run_bg,api,apps/api,uv run python -m uvicorn src.bootstrap:app --reload --host 0.0.0.0)
	# web (astro)
	@$(call run_bg,web,apps/web,pnpm astro dev --host 0.0.0.0 --port 4321)
	# app (vite/svelte)
	@$(call run_bg,app,apps/app,pnpm dev --host 0.0.0.0 --port 5173)
	@echo
	@echo "Tips:"
	@echo "  • make tail LOG=api|web|app|compose"
	@echo "  • make logs           # tail всех логов"
	@echo "  • make stop           # убить локальные дев-процессы"
	@echo "  • make down           # остановить docker-инфру"
	@echo "  • make status         # состояние контейнеров и локальных PID"

stop:
	@echo "Stopping local dev processes"
	@if ls $(PID_DIR)/*.pid >/dev/null 2>&1; then \
		for f in $(PID_DIR)/*.pid; do \
			name=$$(basename $$f .pid); pid=$$(cat $$f || true); \
			if [ -n "$$pid" ] && kill -0 $$pid 2>/dev/null; then \
				echo "• killing $$name (pid $$pid)"; kill $$pid || true; \
			else \
				echo "• $$name already stopped"; \
			fi; \
			rm -f $$f; \
		done; \
	else echo "No PIDs found"; fi

# ---- logs ----
# Пример: make tail LOG=api
tail:
	@if [ -z "$(LOG)" ]; then \
		echo "Usage: make tail LOG=api|web|app|compose"; exit 1; \
	fi
	@last=$$(ls -1t $(LOG_DIR)/$(LOG).* 2>/dev/null | head -n 1); \
	if [ -z "$$last" ]; then echo "No logs for '$(LOG)'"; exit 1; fi; \
	echo "Tailing $$last"; \
	tail -n +1 -F "$$last"

logs:
	@echo "Tailing all logs in ./$(LOG_DIR) (Ctrl+C to exit)"
	@touch $(LOG_DIR)/.keep
	@tail -n 50 -F $(LOG_DIR)/*

clean:
	@echo "Cleaning logs and PIDs"
	-rm -rf $(LOG_DIR) $(PID_DIR)

# PR
pr:
	gh pr create --base main --draft --fill
