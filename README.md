# Pingu

Lightweight probe collector and API for ICMP/HTTP targets.

## Quick summary
- Poller loads YAML targets, syncs to DB, runs probes, and persists results.
- HTTP API exposes health, targets, and results.

## Getting started

Prereqs: Python 3.12, PostgreSQL, Docker (optional).

Run locally:
```bash
# create virtualenv, install
pip install -e .
# configure DB via .env or env vars (see app.config)
export DATABASE_URL=postgresql+psycopg://...
python -m app.poller    # runs poller (sync + probe loops)
uvicorn app.api:app --reload  # run API
```

Docker:
- See [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml).
- Makefile tasks: `make up`, `make test`, `make api-logs`. See [Makefile](Makefile).

## Project layout
- API: [app/api/api.py](app/api/api.py) exposes FastAPI app [`app.api.api.app`](app/api/api.py)
  - Routes:
    - Targets: [app/api/routes/targets.py](app/api/routes/targets.py)
    - Results: [app/api/routes/results.py](app/api/routes/results.py)
    - Target-specific results: [app/api/routes/target_results.py](app/api/routes/target_results.py)
    - Health: [app/api/routes/health.py](app/api/routes/health.py)
- Poller: [app/poller/__main__.py](app/poller/__main__.py) (entrypoint: [`app.poller.__main__.main`](app/poller/__main__.py))
  - Loads YAML via [`app.poller.config.load_targets`](app/poller/config.py)
  - Syncs via [`app.repos.sync.sync_targets_to_db`](app/repos/sync.py)
  - Probes use [`app.repos.results.insert_probe_result`](app/repos/results.py)
- Repos / DB helpers:
  - Targets: [app/repos/targets.py](app/repos/targets.py) (`app.repos.targets.fetch_all_targets`)
  - Results: [app/repos/results.py](app/repos/results.py) (`app.repos.results.fetch_results_for_target`)
  - DB session helper: [`app.db.session_scope`](app/db.py)
- Config / models:
  - Settings: [`app.config.settings`](app/config.py)
  - Target dataclasses: [app/models.py](app/models.py) (`app.models.IcmpTarget`, `app.models.HttpTarget`)
- Migrations: [alembic/](alembic/) (initial: [alembic/versions/0001_init.py](alembic/versions/0001_init.py))
- Tests: [tests/](tests/) (fixtures in [tests/conftest.py](tests/conftest.py), helpers in [tests/db_helpers.py](tests/db_helpers.py))

## Configuration
- Targets YAML: [targets.yaml](targets.yaml). Format parsed by [`app.poller.config.load_targets`](app/poller/config.py).
- App settings: [app/config.py](app/config.py) (`DATABASE_URL`, `targets_path`, `log_level`) read from `.env`.

## API overview
- GET /health — health check (see [app/api/routes/health.py](app/api/routes/health.py))
- GET /targets — list targets (see [app/api/routes/targets.py](app/api/routes/targets.py))
- GET /targets/{target_id} — target details
- GET /results/latest — recent results (see [app/api/routes/results.py](app/api/routes/results.py))
- GET /results/latest-by-target — latest per-target
- GET /targets/{target_id}/results — results for a specific target (see [app/api/routes/target_results.py](app/api/routes/target_results.py))

API shapes are defined in [app/api/schemas.py](app/api/schemas.py).

## Database & migrations
- DB session helper: [`app.db.session_scope`](app/db.py)
- Migrations: Alembic config [alembic.ini](alembic.ini) and versions in [alembic/versions/](alembic/versions/). Initial schema at [alembic/versions/0001_init.py](alembic/versions/0001_init.py).

## Testing
- Tests live in [tests/](tests/). Use pytest:
```bash
pytest -q
```
- CI and test container orchestration available via `Makefile` (see [Makefile](Makefile)).

## Development notes
- Poller stores probe rows via [`app.repos.results.insert_probe_result`](app/repos/results.py).
- Query helpers for results/health are in [app/repos/results.py](app/repos/results.py) and [app/repos/health.py](app/repos/health.py).
- Use [`app.repos.sync.sync_targets_to_db`](app/repos/sync.py) to keep DB in sync with YAML.

## Contributing
- Follow formatting/lint rules in `Makefile` (`make fmt`, `make lint`, `make typecheck`).
- Tests must pass (`make test`).

## Useful links
- App entry: [app/api/api.py](app/api/api.py)
- Poller entry: [app/poller/__main__.py](app/poller/__main__.py)
- Config: [app/config.py](app/config.py)
- DB helpers: [app/db.py](app/db.py)
- Repos: [app/repos/results.py](app/repos/results.py), [app/repos/targets.py](app/repos/targets.py), [app/repos/sync.py](app/repos/sync.py)
- Tests: [tests/](tests/)

License: see repository root (not specified).// filepath: README.md
# Pingu

Lightweight probe collector and API for ICMP/HTTP targets.

## Quick summary
- Poller loads YAML targets, syncs to DB, runs probes, and persists results.
- HTTP API exposes health, targets, and results.

## Getting started

Prereqs: Python 3.12, PostgreSQL, Docker (optional).

Run locally:
```bash
# create virtualenv, install
pip install -e .
# configure DB via .env or env vars (see app.config)
export DATABASE_URL=postgresql+psycopg://...
python -m app.poller    # runs poller (sync + probe loops)
uvicorn app.api:app --reload  # run API
```

Docker:
- See [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml).
- Makefile tasks: `make up`, `make test`, `make api-logs`. See [Makefile](Makefile).

## Project layout
- API: [app/api/api.py](app/api/api.py) exposes FastAPI app [`app.api.api.app`](app/api/api.py)
  - Routes:
    - Targets: [app/api/routes/targets.py](app/api/routes/targets.py)
    - Results: [app/api/routes/results.py](app/api/routes/results.py)
    - Target-specific results: [app/api/routes/target_results.py](app/api/routes/target_results.py)
    - Health: [app/api/routes/health.py](app/api/routes/health.py)
- Poller: [app/poller/__main__.py](app/poller/__main__.py) (entrypoint: [`app.poller.__main__.main`](app/poller/__main__.py))
  - Loads YAML via [`app.poller.config.load_targets`](app/poller/config.py)
  - Syncs via [`app.repos.sync.sync_targets_to_db`](app/repos/sync.py)
  - Probes use [`app.repos.results.insert_probe_result`](app/repos/results.py)
- Repos / DB helpers:
  - Targets: [app/repos/targets.py](app/repos/targets.py) (`app.repos.targets.fetch_all_targets`)
  - Results: [app/repos/results.py](app/repos/results.py) (`app.repos.results.fetch_results_for_target`)
  - DB session helper: [`app.db.session_scope`](app/db.py)
- Config / models:
  - Settings: [`app.config.settings`](app/config.py)
  - Target dataclasses: [app/models.py](app/models.py) (`app.models.IcmpTarget`, `app.models.HttpTarget`)
- Migrations: [alembic/](alembic/) (initial: [alembic/versions/0001_init.py](alembic/versions/0001_init.py))
- Tests: [tests/](tests/) (fixtures in [tests/conftest.py](tests/conftest.py), helpers in [tests/db_helpers.py](tests/db_helpers.py))

## Configuration
- Targets YAML: [targets.yaml](targets.yaml). Format parsed by [`app.poller.config.load_targets`](app/poller/config.py).
- App settings: [app/config.py](app/config.py) (`DATABASE_URL`, `targets_path`, `log_level`) read from `.env`.

## API overview
- GET /health — health check (see [app/api/routes/health.py](app/api/routes/health.py))
- GET /targets — list targets (see [app/api/routes/targets.py](app/api/routes/targets.py))
- GET /targets/{target_id} — target details
- GET /results/latest — recent results (see [app/api/routes/results.py](app/api/routes/results.py))
- GET /results/latest-by-target — latest per-target
- GET /targets/{target_id}/results — results for a specific target (see [app/api/routes/target_results.py](app/api/routes/target_results.py))

API shapes are defined in [app/api/schemas.py](app/api/schemas.py).

## Database & migrations
- DB session helper: [`app.db.session_scope`](app/db.py)
- Migrations: Alembic config [alembic.ini](alembic.ini) and versions in [alembic/versions/](alembic/versions/). Initial schema at [alembic/versions/0001_init.py](alembic/versions/0001_init.py).

## Testing
- Tests live in [tests/](tests/). Use pytest:
```bash
pytest -q
```
- CI and test container orchestration available via `Makefile` (see [Makefile](Makefile)).

## Development notes
- Poller stores probe rows via [`app.repos.results.insert_probe_result`](app/repos/results.py).
- Query helpers for results/health are in [app/repos/results.py](app/repos/results.py) and [app/repos/health.py](app/repos/health.py).
- Use [`app.repos.sync.sync_targets_to_db`](app/repos/sync.py) to keep DB in sync with YAML.

## Contributing
- Follow formatting/lint rules in `Makefile` (`make fmt`, `make lint`, `make typecheck`).
- Tests must pass (`make test`).

## Useful links
- App entry: [app/api/api.py](app/api/api.py)
- Poller entry: [app/poller/__main__.py](app/poller/__main__.py)
- Config: [app/config.py](app/config.py)
- DB helpers: [app/db.py](app/db.py)
- Repos: [app/repos/results.py](app/repos/results.py), [app/repos/targets.py](app/repos/targets.py), [app/repos/sync.py](app/repos/sync.py)
- Tests: [tests/](tests/)

License: see repository root (not specified).