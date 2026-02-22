SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

COMPOSE ?= docker compose

# Load .env if present (gitignored). Export vars so recipes can use them.
ifneq (,$(wildcard .env))
include .env
export
endif

# Defaults if .env is missing
POSTGRES_DB ?= pingu
POSTGRES_USER ?= postgres
DB_APP_USER ?= pingu_app

.DEFAULT_GOAL := help

.PHONY: help
help:
	@printf "\nTargets:\n"
	@printf "  up           Start services\n"
	@printf "  down         Stop services\n"
	@printf "  rebuild      Rebuild and restart services\n"
	@printf "  full-rebuild Removes volumes, then rebuilds and restarts services\n"
	@printf "  ps           Show containers\n"
	@printf "  logs         Tail logs (all)\n"
	@printf "  api-logs     Tail api logs\n"
	@printf "  poller-logs  Tail poller logs\n"
	@printf "  dbshell      psql into db as postgres\n"
	@printf "  dbshell-app  psql into db as app user\n"
	@printf "  dbwatch      Watch latest probe results\n"
	@printf "  bootstrap    Run bootstrap script once\n"
	@printf "\n"
	@printf "  format       Run isort and black formatting\n"
	@printf "  lint         Run isort, black, and mypy checks\n"
	@printf "  fix          Auto-fix formatting issues\n"
	@printf "  typecheck    Run mypy type checks\n"

.PHONY: up
up:
	$(COMPOSE) up -d

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: rebuild
rebuild:
	$(COMPOSE) up -d --build

.PHONY: full-rebuild
full-rebuild:
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build

.PHONY: format lint fix typecheck
format:
	isort .
	black .

lint:
	isort . --check-only --diff
	black . --check
	mypy .
	@if ! command -v rg >/dev/null; then \
		echo "ripgrep (rg) is not installed. Please install it to run lint checks."; \
		exit 1; \
	fi
	@! rg -n "from app\.db import engine|engine\.connect|SessionLocal\(" app/repos || (echo "Repo must not use engine/SessionLocal directly" && exit 1)

fix:
	isort .
	black .

typecheck:
	mypy .

.PHONY: ps
ps:
	$(COMPOSE) ps

.PHONY: test
test:
	$(COMPOSE) build --no-cache --build-arg INSTALL_DEV=true api --build-arg INCLUDE_TESTS=true
	$(COMPOSE) up -d db
	$(COMPOSE) exec -T db bash -lc "until pg_isready -U $$POSTGRES_USER; do sleep 0.2; done"
	$(COMPOSE) exec -T db psql -U $$POSTGRES_USER -tc "SELECT 1 FROM pg_database WHERE datname='$$TEST_DB_NAME'" | grep -q 1 || \
		$(COMPOSE) exec -T db psql -U $$POSTGRES_USER -c "CREATE DATABASE $$TEST_DB_NAME;"
	$(COMPOSE) run --rm \
		-e TEST_DATABASE_URL=postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASSWORD@db:5432/$$TEST_DB_NAME \
		api bash -lc "pytest -q"
	$(COMPOSE) down

.PHONY: logs
logs:
	$(COMPOSE) logs -f --tail=200

.PHONY: api-logs
api-logs:
	$(COMPOSE) logs -f --tail=200 api

.PHONY: poller-logs
poller-logs:
	$(COMPOSE) logs -f --tail=200 poller

.PHONY: bootstrap
bootstrap:
	$(COMPOSE) run --rm bootstrap

.PHONY: dbshell
dbshell:
	$(COMPOSE) exec db psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"

.PHONY: dbshell-app
dbshell-app:
	$(COMPOSE) exec db psql -U "$(DB_APP_USER)" -d "$(POSTGRES_DB)"

.PHONY: dbwatch
dbwatch:
	watch -n 2 '$(COMPOSE) exec -T db psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)" -c "\
SELECT \
  t.name, \
  r.ts, \
  age(now(), r.ts) AS age, \
  r.success, \
  r.latency_ms, \
  r.error \
FROM probe_results r \
JOIN targets t ON r.target_id = t.id \
ORDER BY r.ts DESC \
LIMIT 30;"'