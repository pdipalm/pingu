# Pingu API v0.1 draft

## Conventions

- All timestamps are ISO 8601 UTC (RFC 3339), for example `2026-02-20T16:42:00Z`.
- Unless noted, lists are returned in descending time order (`ts desc`).
- `limit` parameters are clamped to a server-defined max.
- `window` is a duration string like `15m`, `1h`, `24h`, `7d`.
- All responses are JSON.
- IDs are UUIDv4 strings.

## Data Model (Conceptual)

### Target

A configured thing to probe (ICMP or HTTP).

### Probe Result
A probe result represents a single execution of a probe against a target at a specific timestamp.

Common fields across all probe types:

- `ts` (timestamp): when the probe was executed
- `success` (boolean): true if the probe met success criteria
- `latency_ms` (integer, nullable): total round-trip time in milliseconds
- `status_code` (integer, nullable): HTTP status code for HTTP probes
- `error` (string, nullable): error message if the probe failed

Success criteria:
- ICMP: success if at least one echo reply is received within timeout
- HTTP: success if request completes and status code < 400

For non-HTTP probes, `status_code` is null.
For successful probes, `error` is null.

## Health
### GET `/health`
Returns basic service status. Poller health is inferred via the most recent stored result timestamp.

Response example:
```json
{
  "ok": true,
  "db": true,
  "enabled_targets": 6,
  "last_result_ts": "2026-02-20T16:42:00Z",
  "seconds_since_last_result": 12
}
```

Notes:
- ```db``` indicates whether the API could successfully query the database.
- ```last_result_ts``` is the max timestamp across stored results.
- ```seconds_since_last_result``` is computed by the API at request time

## Targets
### GET ```/targets```
Lists all targets.

Query params:
- ```status``` (optional, string):
    - Allowed values:
        - ```enabled```
        - ```disabled```
        - ```all```
    - Behavior
        - default: ```enabled```
        - ```status=enabled```: only enabled
        - ```status=disabled```: only disabled
        - ```status=all```: both

Response example:
```json
{
  "items": [
    {
      "id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
      "name": "router",
      "type": "icmp",
      "host": "192.168.1.1",
      "url": null,
      "interval_seconds": 30,
      "timeout_ms": 1000,
      "enabled": true
    }
  ]
}
```

### GET ```/targets/{target_id}```

Get details for a single target.

Response example:
```json
{
  "id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
  "name": "router",
  "type": "icmp",
  "host": "192.168.1.1",
  "url": null,
  "interval_seconds": 30,
  "timeout_ms": 1000,
  "enabled": true
}
```

## Results

Note: Results include denormalized target metadata for convenience.

### GET ```/results/latest-by-target```
Returns the most recent result per enabled target.

Response example:
```json
{
  "items": [
    {
      "target_id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
      "target_name": "router",
      "ts": "2026-02-20T16:42:00Z",
      "success": true,
      "latency_ms": 12,
      "status_code": null,
      "error": null
    }
  ]
}
```

Notes:
- only enabled targets are included

### GET ```/results/latest```
Returns the most recent result records globally across all targets.

Query params:
- limit (optional, integer): default 200, max 1000

Response example:
```json
{
  "items": [
    {
      "target_id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
      "target_name": "router",
      "ts": "2026-02-20T16:42:00Z",
      "success": true,
      "latency_ms": 12,
      "status_code": null,
      "error": null
    }
  ]
}
```

### GET ```/targets/{target_id}/results```
Returns results for a single target within a time range.

Query params:
- ```since``` (optional, string timestamp): default ```now-24h```
- ```until``` (optional, string timestamp): default ```now```
- ```limit``` (optional, integer): default 200, max 1000

Response example:
```json
{
  "target_id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
  "target_name": "router",
  "items": [
    {
      "ts": "2026-02-20T16:42:00Z",
      "success": true,
      "latency_ms": 12,
      "status_code": null,
      "error": null
    }
  ]
}
```

## Summary

### GET ```/summary```
Returns per enabled target uptime percent and average latency for a window.

Query params:
- ```window``` (optional, duration string): default ```1h```

Response example:
```json
{
  "window": "1h",
  "items": [
    {
      "target_id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
      "target_name": "router",
      "uptime_percent": 100.0,
      "avg_latency_ms": 12.4,
      "total_probes": 120
    }
  ]
}
```

### GET ```/summary/{target_id}```
Returns the uptime percent and average latency for a single target over a window.

Query params:
- ```window``` (optional, duration string): default ```1h```

Response example:
```json
{
  "window": "1h",
  "target_id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
  "target_name": "router",
  "uptime_percent": 99.2,
  "avg_latency_ms": 14.1,
  "total_probes": 120
}
```

## Error Responses
- 400: invalid parameters (bad timestamp, bad window format, invalid limit)
- 404: target not found
- 500: unexpected server error

Error example:
```json
{
  "error": "invalid window format, expected like 15m, 1h, 7d"
}
```