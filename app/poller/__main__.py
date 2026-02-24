import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional
from uuid import UUID

import anyio
from anyio import to_thread as anyto_thread

from app.config import settings
from app.constants import MAX_BACKOFF_MULTIPLIER
from app.models import HttpTarget, IcmpTarget
from app.poller.config import load_targets
from app.poller.http import http_probe_once
from app.poller.icmp import icmp_ping_once
from app.repos.results import insert_probe_result
from app.repos.sync import sync_targets_to_db
from app.repos.targets import fetch_enabled_http_targets, fetch_enabled_icmp_targets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@dataclass(frozen=True)
class ProbeResult:
    success: bool
    latency_ms: Optional[int]
    status_code: Optional[int]
    error: Optional[str]


ProbeFn = Callable[[], Awaitable[ProbeResult]]


def compute_sleep_time(interval_seconds: int, backoff_multiplier: int) -> float:
    base_sleep = interval_seconds * backoff_multiplier
    jitter = random.uniform(-0.1 * base_sleep, 0.1 * base_sleep)
    return max(0.1, base_sleep + jitter)


async def _write_result_async(
    *,
    target_id: UUID,
    ts: datetime,
    result: ProbeResult,
) -> None:
    try:
        await anyto_thread.run_sync(
            lambda: insert_probe_result(
                target_id=target_id,
                ts=ts,
                success=result.success,
                latency_ms=result.latency_ms,
                status_code=result.status_code,
                error=result.error,
            )
        )
    except Exception:
        logging.exception("failed to write probe result")


def _log_result(
    *,
    kind: str,
    target_name: str,
    timeout_ms: int,
    result: ProbeResult,
) -> None:
    if result.success:
        logging.debug(
            f"{kind} success",
            extra={
                "target": target_name,
                "latency_ms": result.latency_ms,
                "status_code": result.status_code,
            },
        )
        if result.latency_ms is not None and result.latency_ms > timeout_ms * 0.8:
            logging.info(
                f"{kind} slow response",
                extra={
                    "target": target_name,
                    "latency_ms": result.latency_ms,
                    "status_code": result.status_code,
                },
            )
    else:
        logging.warning(
            f"{kind} failure",
            extra={
                "target": target_name,
                "error": result.error,
                "status_code": result.status_code,
            },
        )


async def poll_forever(
    *,
    kind: str,
    target_id: UUID,
    target_name: str,
    interval_seconds: int,
    timeout_ms: int,
    probe: ProbeFn,
) -> None:
    logging.info(f"[poller] starting {kind} poll loop for {target_name} every {interval_seconds}s")

    backoff = 1

    while True:
        try:
            ts = datetime.now(timezone.utc)

            result = await probe()
            _log_result(
                kind=kind,
                target_name=target_name,
                timeout_ms=timeout_ms,
                result=result,
            )

            if result.success:
                backoff = 1
            else:
                backoff = min(backoff * 2, MAX_BACKOFF_MULTIPLIER)

            await _write_result_async(target_id=target_id, ts=ts, result=result)

        except Exception as e:
            logging.exception(f"unexpected error during {kind} poll for target {target_name}: {e}")

        sleep_time = compute_sleep_time(interval_seconds, backoff)
        await anyio.sleep(sleep_time)


async def poll_icmp_forever(t: IcmpTarget) -> None:
    async def probe() -> ProbeResult:
        success, latency_ms, error = await icmp_ping_once(t.host, t.timeout_ms)
        return ProbeResult(
            success=success,
            latency_ms=latency_ms,
            status_code=None,
            error=error,
        )

    await poll_forever(
        kind="icmp",
        target_id=t.id,
        target_name=f"{t.name} ({t.host})",
        interval_seconds=t.interval_seconds,
        timeout_ms=t.timeout_ms,
        probe=probe,
    )


async def poll_http_forever(t: HttpTarget) -> None:
    async def probe() -> ProbeResult:
        success, latency_ms, status_code, error = await http_probe_once(t.url, t.timeout_ms)
        return ProbeResult(
            success=success,
            latency_ms=latency_ms,
            status_code=status_code,
            error=error,
        )

    await poll_forever(
        kind="http",
        target_id=t.id,
        target_name=f"{t.name} ({t.url})",
        interval_seconds=t.interval_seconds,
        timeout_ms=t.timeout_ms,
        probe=probe,
    )


async def main_async() -> None:
    logging.info(f"[poller] loading targets from {settings.targets_path}")
    targets = load_targets(settings.targets_path)
    sync_targets_to_db(targets)
    logging.info(f"[poller] synced {len(targets)} targets into db")

    icmp_targets = fetch_enabled_icmp_targets()
    http_targets = fetch_enabled_http_targets()

    logging.info(
        "starting poll loops",
        extra={"icmp": len(icmp_targets), "http": len(http_targets)},
    )

    if not icmp_targets and not http_targets:
        logging.info("[poller] no enabled targets; sleeping forever")
        while True:
            await anyio.sleep(60)

    async with anyio.create_task_group() as tg:
        for it in icmp_targets:
            tg.start_soon(poll_icmp_forever, it)
        for ht in http_targets:
            tg.start_soon(poll_http_forever, ht)


def main() -> None:
    anyio.run(main_async)


if __name__ == "__main__":
    main()
