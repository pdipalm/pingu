# Pingu

Lightweight probe/polling service (ICMP + HTTP) with an HTTP API and Postgres storage.

## Quick links
- App entry points: `app.poller.__main__.main`, `app.api.api.app`
- Config & DB helpers: `app.config.Settings`, `app.db.session_scope`
- Poller config loader: `app.poller.config.TargetCfg`
- ICMP probe implementation: `app.poller.icmp.icmp_ping_once`
- Migrations: `alembic/` (initial schema in `alembic/versions/0001_init.py`)
- Dev infra: `Dockerfile`, `docker-compose.yml`, `Makefile`
- Tests: `tests/` (fixtures in `tests/conftest.py`)
- Docs: `API.md`, `poller.md`

## Overview
Pingu loads targets from a YAML file, syncs them to the DB, and runs per-target probes (ICMP/HTTP) in asyncio tasks. Probe results are stored in Postgres and exposed via the API.

## Important note — docker only
Running the services directly on the host (API/poller + local DB) is currently unreliable in a local-only setup. For reliable runs and tests, use the provided Docker configuration. See "Running (recommended)" below.

## Requirements
- Python 3.11+ (for development)
- Postgres (handled in the Docker image)
- For ICMP probes: system `ping` (iputils-ping) and appropriate privileges (handled in the Docker image)

## Configuration
- Environment: `.env`. See `example.env`
- Targets file: `targets.yaml`.
- DB URL: set `DATABASE_URL` (used by app) and `TEST_DATABASE_URL` for tests.

## Running (Docker)
Build and start API + DB (and any other services) using Docker Compose:

```sh
docker compose up -d --build
```

Run everything (API + poller + DB) in Docker (example Makefile targets exist):

```sh
make up
```

To stop and remove containers:

```sh
docker compose down
```

## Basic API examples
Assumes API reachable at `http://localhost:8000` (container mapping in Docker Compose). See `API.md` for full API docs and examples.

### Health
```json
> curl -s http:/localhost:8000/health | jq
{
  "generated_at": "2026-02-23T01:53:52.223350Z",
  "ok": true,
  "db": true,
  "thresholds": {
    "stale_after_seconds": 180
  },
  "stats": {
    "enabled_targets": 19,
    "last_result_ts": "2026-02-23T01:53:27.153555Z",
    "seconds_since_last_result": 25
  }
}
```

### Targets
#### All Targets
```json
> curl -s http:/localhost:8000/targets | jq
{
  "generated_at": "2026-02-23T01:55:56.632985Z",
  "items": [
    {
      "id": "fb4c6d37-c55d-44fa-9415-89528fa8290b",
      "name": "bbc-uk",
      "type": "http",
      "enabled": true,
      "interval_seconds": 60,
      "timeout_ms": 3000,
      "host": null,
      "url": "https://www.bbc.co.uk"
    },
    {
      "id": "fa82f468-1108-466b-9172-d6a356d8e08a",
      "name": "cat-camera",
      "type": "icmp",
      "enabled": true,
      "interval_seconds": 30,
      "timeout_ms": 1000,
      "host": "192.168.1.229",
      "url": null
    },
    {
      "id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
      "name": "cat-feeder",
      "type": "icmp",
      "enabled": true,
      "interval_seconds": 30,
      "timeout_ms": 1000,
      "host": "192.168.1.177",
      "url": null
    },
    {
      "id": "f5478070-d954-48db-941e-a53e167ee120",
      "name": "cloudflare-dns",
      "type": "icmp",
      "enabled": true,
      "interval_seconds": 60,
      "timeout_ms": 1000,
      "host": "1.1.1.1",
      "url": null
    }
  ]
}
```

#### Single Target
```json
> curl -s http:/localhost:8000/targets/9e09f8ee-8faf-4989-9a9f-4637dbeff832 | jq
{
  "id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
  "name": "cat-feeder",
  "type": "icmp",
  "enabled": true,
  "interval_seconds": 30,
  "timeout_ms": 1000,
  "host": "192.168.1.177",
  "url": null
}
```

### Target Results
```json
> curl -s http:/localhost:8000/targets/9e09f8ee-8faf-4989-9a9f-4637db
eff832/results?limit=3 | jq
{
  "target_id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
  "target_name": "cat-feeder",
  "generated_at": "2026-02-23T01:57:50.218217Z",
  "items": [
    {
      "id": 897,
      "target_id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
      "ts": "2026-02-23T01:57:47.509801Z",
      "success": true,
      "latency_ms": 13,
      "status_code": null,
      "error": null
    },
    {
      "id": 890,
      "target_id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
      "ts": "2026-02-23T01:57:14.765047Z",
      "success": true,
      "latency_ms": 7,
      "status_code": null,
      "error": null
    },
    {
      "id": 879,
      "target_id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
      "ts": "2026-02-23T01:56:42.018678Z",
      "success": true,
      "latency_ms": 5,
      "status_code": null,
      "error": null
    }
  ]
}
```

### Results
#### Latest
```json
> curl -s http:/localhost:8000/results/latest?limit=3 | jq
{
  "generated_at": "2026-02-23T02:00:32.381915Z",
  "items": [
    {
      "target_id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
      "target_name": "cat-feeder",
      "ts": "2026-02-23T02:00:25.094013Z",
      "success": true,
      "latency_ms": 9,
      "status_code": null,
      "error": null
    },
    {
      "target_id": "fa82f468-1108-466b-9172-d6a356d8e08a",
      "target_name": "cat-camera",
      "ts": "2026-02-23T02:00:25.093217Z",
      "success": true,
      "latency_ms": 5,
      "status_code": null,
      "error": null
    },
    {
      "target_id": "35849f4e-d04b-480d-8822-a4b888fdef45",
      "target_name": "tokyo-university",
      "ts": "2026-02-23T02:00:06.916011Z",
      "success": true,
      "latency_ms": 2218,
      "status_code": 200,
      "error": null
    }
  ]
}
```

#### Latest by Target
```json
> curl -s http:/localhost:8000/results/latest-by-target | jq
{
  "generated_at": "2026-02-23T02:03:10.764962Z",
  "items": [
    {
      "target_id": "fb4c6d37-c55d-44fa-9415-89528fa8290b",
      "target_name": "bbc-uk",
      "ts": "2026-02-23T02:03:09.957787Z",
      "success": true,
      "latency_ms": 251,
      "status_code": 200,
      "error": null
    },
    {
      "target_id": "fa82f468-1108-466b-9172-d6a356d8e08a",
      "target_name": "cat-camera",
      "ts": "2026-02-23T02:03:08.799660Z",
      "success": true,
      "latency_ms": 3,
      "status_code": null,
      "error": null
    },
    {
      "target_id": "9e09f8ee-8faf-4989-9a9f-4637dbeff832",
      "target_name": "cat-feeder",
      "ts": "2026-02-23T02:03:08.807612Z",
      "success": true,
      "latency_ms": 3,
      "status_code": null,
      "error": null
    },
    {
      "target_id": "f5478070-d954-48db-941e-a53e167ee120",
      "target_name": "cloudflare-dns",
      "ts": "2026-02-23T02:03:08.792135Z",
      "success": true,
      "latency_ms": 22,
      "status_code": null,
      "error": null
    }
  ]
}
```


## Development & tests
- Useful Makefile targets: `make test`, `make lint`, `make fmt`, `make typecheck`.

## Notes for maintainers
- DB session helper: `app.db.session_scope` ensures transactional isolation for repo functions.
- Default pagination limits: `app.constants.DEFAULT_LIMIT`, `app.constants.MAX_LIMIT`.

## Where to look in the code
- Poller main loop: `app.poller.__main__.main_async`
- API routes: `app/api/api.py` and `app/api/routes/`
- Repos: `app.repos` (DB access helpers and syncing)

## Future Work:
- Poller: concurrency limits & scheduler/queue, batch writes, ipv6 support
- API: /summary endpoint, true pagination
- DB: retention policy
