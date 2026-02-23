
# Poller

This document describes the poller component: how it is configured, how it runs, and probe implementation details for ICMP and HTTP checks.

## Overview

- The poller loads target definitions from a YAML file (default `targets.yaml`), synchronizes them into the database, and starts an asyncio task per enabled target.
- There are two probe types: `icmp` and `http`. Each enabled target runs a long-lived loop that performs a probe, stores the result to the DB, then sleeps for the target's `interval_seconds`.

## How to run

- From the repository you can run the poller module directly:

```bash
python -m app.poller
```

- The poller reads the path to the targets file from `app.config.settings.targets_path` (default: `targets.yaml`). The application `Settings` may be populated from an `.env` file.

## Configuration (targets YAML)

- The poller expects a YAML file with a top-level `targets` sequence. Each target contains the fields shown below.

Example `targets.yaml`:

```yaml
targets:
	- name: router
		type: icmp
		host: 192.168.1.1
		interval_seconds: 30
		timeout_ms: 1000
		enabled: true

	- name: website
		type: http
		url: https://example.com/
		interval_seconds: 60
		timeout_ms: 2000
		enabled: true
```

Field summary:
- `name` (string): unique human-friendly target name. Used to sync DB entries.
- `type` (string): `icmp` or `http`.
- `host` (string, icmp): required for `icmp` targets.
- `url` (string, http): required for `http` targets.
- `interval_seconds` (int): how often to run the probe.
- `timeout_ms` (int): probe timeout in milliseconds.
- `enabled` (bool): whether the poller should probe this target.

## Syncing to database

- On startup the poller calls `load_targets()` to parse the YAML and then `sync_targets_to_db()` which:
	- inserts new targets (generates UUIDs),
	- updates existing targets by name (type, host/url, interval, timeout, enabled, updated_at), and
	- marks DB targets that are not present in the YAML as `enabled = false`.

## Runtime behavior

- After syncing, the poller queries the DB for enabled ICMP and HTTP targets and starts an asyncio task for each target.
- Each task runs forever in a loop:
	1. record a UTC timestamp for the probe
	2. run the probe (ICMP or HTTP)
	3. log success/failure and any slow-response warnings
	4. call `insert_probe_result(...)` to persist the probe result
	5. sleep for `interval_seconds`
- If there are no enabled targets the poller sleeps forever (60s intervals) and logs that there are no targets.

## Probe implementation details

### HTTP (`app.poller.http.http_probe_once`)
- Uses `httpx.AsyncClient` with `follow_redirects=True`.
- Timeout: computed from `timeout_ms / 1000.0` seconds and passed to the client.
- Latency: measured with `time.perf_counter()` and returned as integer milliseconds.
- Return value: `(success, latency_ms, status_code, error)` where
	- `success` is `True` when an HTTP response was received (transport succeeded), `False` on timeout/connect/HTTP transport errors.
	- `status_code` is the HTTP response code when available.
	- `error` is a short string like `timeout`, `connect_error`, or an `http_error: ExceptionName` description.

Notes: the poller treats `success` as transport-level success. Consumers may also look at `status_code` (for example, to treat 4xx/5xx as application-level failures).

### ICMP (`app.poller.icmp.icmp_ping_once`)
- Uses the system `ping` command via `asyncio.create_subprocess_exec`. The container must provide `iputils-ping` (or equivalent) and the process needs permission to send ICMP (e.g. `CAP_NET_RAW`).
- Command: `ping -n -c 1 -W <seconds> <host>` where `-W` timeout is computed as `max(1, ceil(timeout_ms/1000))` seconds.
- Parses output with the regex `time[=<]([\d.]+)\s*ms` to extract round-trip time when available; otherwise falls back to measured wall-clock elapsed time.
- Return value: `(success, latency_ms, error)` where
	- `success` is `True` when `ping` returns exit code 0, `False` otherwise,
	- `latency_ms` is integer milliseconds when available,
	- `error` is a short string describing the failure (permission issue, unknown host, timeout, or `ping` stderr).

## Storage

- Probe results are persisted via `insert_probe_result` into the `probe_results` table with the fields: `target_id`, `ts`, `success`, `latency_ms`, `status_code`, `error`.

## Logging

- The poller configures `logging.basicConfig(level=INFO)` and writes `INFO`/`WARNING`/`DEBUG` messages for starts, slow responses (>80% of timeout), and failures. Unexpected exceptions are logged with a stack trace.

## Requirements & Notes

- Python dependencies: `httpx`, `PyYAML` (used by `app.poller.http` and `app.poller.config`). Ensure these are installed in your environment.
- ICMP probes require the `ping` binary and appropriate privileges (e.g. `CAP_NET_RAW` in containers) or running as root.
- Timeouts: `timeout_ms` is applied differently between HTTP and ICMP probes because HTTP client accepts fractional seconds while ICMP uses whole-second `ping` semantics (rounded up, minimum 1s).

## Debugging

- To test a single HTTP probe from a Python REPL, import and run `await app.poller.http.http_probe_once(url, timeout_ms)`.
- To test a single ICMP probe, import and run `await app.poller.icmp.icmp_ping_once(host, timeout_ms)` (requires `ping` + permissions).

## Future Work

- The poller is intentionally simple: it creates one asyncio Task per enabled target and relies on cooperative sleeping. It does not provide advanced scheduling, jitter, or concurrency limits beyond what asyncio provides.

