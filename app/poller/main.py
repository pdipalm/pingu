import asyncio
from datetime import datetime, timezone
from app.config import settings
from app.models import IcmpTarget, HttpTarget
from app.repos.results import insert_probe_result
from app.repos.targets import fetch_enabled_icmp_targets, fetch_enabled_http_targets
from app.poller.config import load_targets
from app.poller.sync import sync_targets_to_db
from app.poller.icmp import icmp_ping_once
from app.poller.http import http_probe_once

async def poll_icmp_forever(t: IcmpTarget) -> None:
    print(f"[poller] starting ICMP poll loop for {t.name} ({t.host}) every {t.interval_seconds}s")

    while True:
        ts = datetime.now(timezone.utc)
        success, latency_ms, error = await icmp_ping_once(t.host, t.timeout_ms)
        insert_probe_result(
            target_id=t.id,
            ts=ts,
            success=success,
            latency_ms=latency_ms,
            status_code=None,
            error=error,
        )
        await asyncio.sleep(t.interval_seconds)

async def poll_http_forever(t: HttpTarget) -> None:
    print(f"[poller] starting HTTP poll loop for {t.name} ({t.url}) every {t.interval_seconds}s")

    while True:
        ts = datetime.now(timezone.utc)

        success, latency_ms, status_code, error = await http_probe_once(
            t.url,
            t.timeout_ms,
        )

        insert_probe_result(
            target_id=t.id,
            ts=ts,
            success=success,
            latency_ms=latency_ms,
            status_code=status_code,
            error=error,
        )

        await asyncio.sleep(t.interval_seconds)


async def main_async() -> None:
    print(f"[poller] loading targets from {settings.targets_path}")
    targets = load_targets(settings.targets_path)
    sync_targets_to_db(targets)
    print(f"[poller] synced {len(targets)} targets into db")

    icmp_targets = fetch_enabled_icmp_targets()
    http_targets = fetch_enabled_http_targets()

    tasks = []

    for t in icmp_targets:
        tasks.append(asyncio.create_task(poll_icmp_forever(t)))

    for t in http_targets:
        tasks.append(asyncio.create_task(poll_http_forever(t)))

    if not tasks:
        print("[poller] no enabled targets; sleeping forever")
        while True:
            await asyncio.sleep(60)

    await asyncio.gather(*tasks)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()