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
	@printf "  bootstrap    Run bootstrap once\n"
	@printf "\n"

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

.PHONY: ps
ps:
	$(COMPOSE) ps

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