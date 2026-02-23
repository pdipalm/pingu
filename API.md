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
- `id` (integer): internal database id for the probe result record (present on stored result objects)
- `target_id` (UUID): identifier of the target the probe ran against (often included in list responses)

Success criteria:
- ICMP: success if at least one echo reply is received within timeout
- HTTP: success if request completes and status code < 400

For non-HTTP probes, `status_code` is null.
For successful probes, `error` is null.

## Health

### GET `/health`

Returns basic service status. Poller health is inferred from the most recent stored result timestamp.

#### Response Example

```json
{
  "generated_at": "2026-02-22T03:10:58.123456Z",
  "ok": true,
  "db": true,
  "thresholds": {
    "stale_after_seconds": 180
  },
  "stats": {
    "enabled_targets": 6,
    "last_result_ts": "2026-02-22T03:10:41.872795Z",
    "seconds_since_last_result": 17
  }
}
```

#### Fields

- `ok` (boolean)  
  Overall service health indicator.  
  - `true` if:
    - The database is reachable, and
    - The most recent result is within `stale_after_seconds`
  - `false` otherwise.

- `db` (boolean)  
  Indicates whether the API was able to successfully query the database.

- `thresholds.stale_after_seconds` (integer)  
  Maximum allowed age in seconds of the most recent result before the service is considered stale.
- `generated_at` (string)  
  ISO 8601 UTC timestamp with `Z` suffix indicating when the response was produced.

- `stats.enabled_targets` (integer)  
  Count of currently enabled targets.

- `stats.last_result_ts` (string | null)  
  ISO 8601 UTC timestamp (with `Z` suffix) of the most recent stored result across all targets.  
  `null` if no results exist.

- `stats.seconds_since_last_result` (integer | null)  
  Number of seconds between the current request time (UTC) and `last_result_ts`.  
  `null` if no results exist.

#### Health Evaluation Logic

- `last_result_ts` is computed as `MAX(ts)` across all stored results.
- `seconds_since_last_result` is computed by the API at request time.
- The poller is considered healthy if:
  - A recent result exists, and
  - `seconds_since_last_result <= stale_after_seconds`.

Notes on computation:
- `stale_after_seconds` is computed by the service as the greater of 30 seconds and `ceil(max_interval_seconds * 1.5)` when there are enabled targets; otherwise it is 0. `max_interval_seconds` is derived from the `interval_seconds` of enabled targets.

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
  "generated_at": "2026-02-22T03:11:00.000000Z",
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

- `since` (optional, string timestamp): inclusive lower bound for `ts` (RFC3339). If omitted no lower bound is applied.
- `until` (optional, string timestamp): exclusive upper bound for `ts` (RFC3339). If omitted no upper bound is applied.

Note: the implementation supports `since` and `until` datetime query parameters in addition to `limit`.

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
Note: the running API accepts `since` and `until` as optional datetime query parameters but does not apply a server-side default of `now-24h`/`now`; if omitted the query is unbounded on that side (results are limited only by `limit`).
Response example:
```json
{
  "target_id": "b5c59b0e-7e88-4e9f-8f3d-3c2c9d8c1b0b",
  "target_name": "router",
  "generated_at": "2026-02-22T03:11:05.000000Z",
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

## Summary (TODO)

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