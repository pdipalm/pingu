import asyncio
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import yaml
from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal


@dataclass(frozen=True)
class TargetCfg:
    name: str
    type: str  # "icmp" or "http"
    host: str | None
    url: str | None
    interval_seconds: int
    timeout_ms: int
    enabled: bool


@dataclass(frozen=True)
class IcmpTarget:
    id: uuid.UUID
    name: str
    host: str
    interval_seconds: int
    timeout_ms: int


PING_TIME_RE = re.compile(r"time[=<]([\d.]+)\s*ms")


def load_targets(path: str) -> list[TargetCfg]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    items = raw.get("targets", [])
    out: list[TargetCfg] = []
    for it in items:
        out.append(
            TargetCfg(
                name=str(it["name"]),
                type=str(it["type"]),
                host=it.get("host"),
                url=it.get("url"),
                interval_seconds=int(it["interval_seconds"]),
                timeout_ms=int(it["timeout_ms"]),
                enabled=bool(it.get("enabled", True)),
            )
        )
    return out


def sync_targets_to_db(cfg_targets: list[TargetCfg]) -> None:
    cfg_by_name = {t.name: t for t in cfg_targets}

    with SessionLocal() as s:
        existing = s.execute(text("SELECT id, name FROM targets")).all()
        existing_by_name: dict[str, uuid.UUID] = {row.name: row.id for row in existing}

        for name, t in cfg_by_name.items():
            existing_id = existing_by_name.get(name)
            now = datetime.now(timezone.utc)
            if existing_id is None:
                new_id = uuid.uuid4()
                s.execute(
                    text(
                        """
                        INSERT INTO targets (id, name, type, host, url, interval_seconds, timeout_ms, enabled, created_at, updated_at)
                        VALUES (:id, :name, :type, :host, :url, :interval_seconds, :timeout_ms, :enabled, :created_at, :updated_at)
                        """
                    ),
                    {
                        "id": new_id,
                        "name": t.name,
                        "type": t.type,
                        "host": t.host,
                        "url": t.url,
                        "interval_seconds": t.interval_seconds,
                        "timeout_ms": t.timeout_ms,
                        "enabled": t.enabled,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            else:
                s.execute(
                    text(
                        """
                        UPDATE targets
                        SET type = :type,
                            host = :host,
                            url = :url,
                            interval_seconds = :interval_seconds,
                            timeout_ms = :timeout_ms,
                            enabled = :enabled,
                            updated_at = :updated_at
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": existing_id,
                        "type": t.type,
                        "host": t.host,
                        "url": t.url,
                        "interval_seconds": t.interval_seconds,
                        "timeout_ms": t.timeout_ms,
                        "enabled": t.enabled,
                        "updated_at": now,
                    },
                )

        cfg_names = set(cfg_by_name.keys())
        for row in existing:
            if row.name not in cfg_names:
                s.execute(
                    text("UPDATE targets SET enabled = false, updated_at = :updated_at WHERE id = :id"),
                    {"id": row.id, "updated_at": datetime.now(timezone.utc)},
                )

        s.commit()


def fetch_enabled_icmp_targets() -> list[IcmpTarget]:
    with SessionLocal() as s:
        rows = s.execute(
            text(
                """
                SELECT id, name, host, interval_seconds, timeout_ms
                FROM targets
                WHERE enabled = true AND type = 'icmp'
                """
            )
        ).mappings().all()

    out: list[IcmpTarget] = []
    for r in rows:
        host = r["host"]
        if host is None:
            # Shouldn't happen due to DB CHECK constraint, but keeps type checkers happy
            continue
        out.append(
            IcmpTarget(
                id=r["id"],
                name=r["name"],
                host=host,
                interval_seconds=int(r["interval_seconds"]),
                timeout_ms=int(r["timeout_ms"]),
            )
        )
    return out


def insert_probe_result(
    *,
    target_id: uuid.UUID,
    ts: datetime,
    success: bool,
    latency_ms: int | None,
    status_code: int | None,
    error: str | None,
) -> None:
    with SessionLocal() as s:
        s.execute(
            text(
                """
                INSERT INTO probe_results (target_id, ts, success, latency_ms, status_code, error)
                VALUES (:target_id, :ts, :success, :latency_ms, :status_code, :error)
                """
            ),
            {
                "target_id": target_id,
                "ts": ts,
                "success": success,
                "latency_ms": latency_ms,
                "status_code": status_code,
                "error": error,
            },
        )
        s.commit()


async def icmp_ping_once(host: str, timeout_ms: int) -> tuple[bool, int | None, str | None]:
    """
    Returns (success, latency_ms, error).
    Uses system ping. Requires iputils-ping + CAP_NET_RAW in container.
    """
    # Linux iputils: -c 1 (one packet), -W <seconds> (timeout per reply)
    timeout_s = max(1, int((timeout_ms + 999) / 1000))
    cmd = ["ping", "-n", "-c", "1", "-W", str(timeout_s), host]

    start = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_b, err_b = await proc.communicate()
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    out = (out_b or b"").decode("utf-8", errors="replace")
    err = (err_b or b"").decode("utf-8", errors="replace")

    if proc.returncode == 0:
        m = PING_TIME_RE.search(out)
        if m:
            try:
                return True, int(float(m.group(1))), None
            except Exception:
                return True, elapsed_ms, None
        return True, elapsed_ms, None

    # Common failures: permission, unknown host, timeout
    detail = (err.strip() or out.strip() or f"ping failed rc={proc.returncode}")[:500]
    return False, None, detail


async def poll_target_forever(t: IcmpTarget) -> None:
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


async def main_async() -> None:
    print(f"[poller] loading targets from {settings.targets_path}")
    targets = load_targets(settings.targets_path)
    sync_targets_to_db(targets)
    print(f"[poller] synced {len(targets)} targets into db")

    icmp_targets = fetch_enabled_icmp_targets()
    if not icmp_targets:
        print("[poller] no enabled icmp targets found; sleeping")
        while True:
            await asyncio.sleep(60)

    tasks = [asyncio.create_task(poll_target_forever(t)) for t in icmp_targets]
    await asyncio.gather(*tasks)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()