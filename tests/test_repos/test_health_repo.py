import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.repos import health as health_repo
from app.repos import results as results_repo


def insert_target(db_session, *, tid, name, interval=30, enabled=True):
    db_session.execute(
        text("""
			INSERT INTO targets (id, name, type, host, url, interval_seconds, timeout_ms, enabled, created_at, updated_at)
			VALUES (:id, :name, 'icmp', '127.0.0.1', NULL, :interval_seconds, 1000, :enabled, NOW(), NOW())
			"""),
        {"id": tid, "name": name, "interval_seconds": interval, "enabled": enabled},
    )


def test_fetch_health_db_stats(db_session):
    tid = uuid.uuid4()
    insert_target(db_session, tid=tid, name="health1", interval=45, enabled=True)

    # insert a result so last_result_ts is set
    now = datetime.now(timezone.utc)
    results_repo.insert_probe_result(
        target_id=tid, ts=now, success=True, latency_ms=1, status_code=200, error=None, s=db_session
    )

    stats = health_repo.fetch_health_db_stats(s=db_session)
    assert stats.enabled_targets >= 1
    assert stats.max_interval_seconds >= 45
    assert stats.last_result_ts is not None
