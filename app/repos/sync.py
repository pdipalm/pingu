import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import session_scope
from app.poller.config import TargetCfg
from app.repos.util import timed_execute


def sync_targets_to_db(cfg_targets: list[TargetCfg], s: Session | None = None) -> None:
    cfg_by_name = {t.name: t for t in cfg_targets}

    with session_scope(existing=s) as session:
        existing = timed_execute(
            session,
            text("SELECT id, name FROM targets"),
            None,
            label="fetch_existing_targets",
        ).all()
        existing_by_name: dict[str, uuid.UUID] = {row.name: row.id for row in existing}

        now = datetime.now(timezone.utc)

        for name, t in cfg_by_name.items():
            existing_id = existing_by_name.get(name)
            if existing_id is None:
                new_id = uuid.uuid4()
                timed_execute(
                    session,
                    text("""
                        INSERT INTO targets (id, name, type, host, url, interval_seconds, timeout_ms, enabled, created_at, updated_at)
                        VALUES (:id, :name, :type, :host, :url, :interval_seconds, :timeout_ms, :enabled, :created_at, :updated_at)
                    """),
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
                    label="insert_target",
                )
            else:
                timed_execute(
                    session,
                    text("""
                        UPDATE targets
                        SET type = :type,
                            host = :host,
                            url = :url,
                            interval_seconds = :interval_seconds,
                            timeout_ms = :timeout_ms,
                            enabled = :enabled,
                            updated_at = :updated_at
                        WHERE id = :id
                    """),
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
                    label="update_target",
                )

        cfg_names = set(cfg_by_name.keys())
        for row in existing:
            if row.name not in cfg_names:
                timed_execute(
                    session,
                    text("""
                        UPDATE targets
                        SET enabled = false, updated_at = :updated_at
                        WHERE id = :id
                    """),
                    {"id": row.id, "updated_at": now},
                    label="disable_target",
                )
