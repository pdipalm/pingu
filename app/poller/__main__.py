import asyncio
import logging
from datetime import datetime, timezone

from app.config import settings
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


async def poll_icmp_forever(t: IcmpTarget) -> None:
    logging.info(
        f"[poller] starting ICMP poll loop for {t.name} ({t.host}) every {t.interval_seconds}s"
    )

    while True:
        try:
            ts = datetime.now(timezone.utc)
            success, latency_ms, error = await icmp_ping_once(t.host, t.timeout_ms)
            if success:
                logging.debug(
                    "icmp success",
                    extra={
                        "target": t.name,
                        "latency_ms": latency_ms,
                    },
                )
                if latency_ms is not None and latency_ms > t.timeout_ms * 0.8:
                    logging.info(
                        "icmp slow response",
                        extra={
                            "target": t.name,
                            "latency_ms": latency_ms,
                        },
                    )
            else:
                logging.warning(
                    "icmp failure",
                    extra={
                        "target": t.name,
                        "error": error,
                    },
                )
            insert_probe_result(
                target_id=t.id,
                ts=ts,
                success=success,
                latency_ms=latency_ms,
                status_code=None,
                error=error,
            )
        except Exception as e:
            logging.exception(
                f"unexpected error during ICMP poll for target {t.name}: {e}"
            )
        await asyncio.sleep(t.interval_seconds)


async def poll_http_forever(t: HttpTarget) -> None:
    logging.info(
        f"[poller] starting HTTP poll loop for {t.name} ({t.url}) every {t.interval_seconds}s"
    )

    while True:
        try:
            ts = datetime.now(timezone.utc)

            success, latency_ms, status_code, error = await http_probe_once(
                t.url,
                t.timeout_ms,
            )

            if success:
                logging.debug(
                    "http success",
                    extra={
                        "target": t.name,
                        "latency_ms": latency_ms,
                        "status_code": status_code,
                    },
                )
                if latency_ms is not None and latency_ms > t.timeout_ms * 0.8:
                    logging.info(
                        "http slow response",
                        extra={
                            "target": t.name,
                            "latency_ms": latency_ms,
                            "status_code": status_code,
                        },
                    )
            else:
                logging.warning(
                    "http failure",
                    extra={
                        "target": t.name,
                        "error": error,
                    },
                )

            insert_probe_result(
                target_id=t.id,
                ts=ts,
                success=success,
                latency_ms=latency_ms,
                status_code=status_code,
                error=error,
            )
        except Exception as e:
            logging.exception(
                f"unexpected error during HTTP poll for target {t.name}: {e}"
            )
        await asyncio.sleep(t.interval_seconds)


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

    tasks = []

    for it in icmp_targets:
        tasks.append(asyncio.create_task(poll_icmp_forever(it)))

    for ht in http_targets:
        tasks.append(asyncio.create_task(poll_http_forever(ht)))

    if not tasks:
        logging.info("[poller] no enabled targets; sleeping forever")
        while True:
            await asyncio.sleep(60)

    await asyncio.gather(*tasks)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
