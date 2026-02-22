import uuid
from datetime import datetime, timedelta, timezone

from app.repos import results as results_repo
from tests.helpers import insert_target


def test_insert_and_fetch_results(db_session):
    tid = uuid.uuid4()
    insert_target(db_session, tid=tid, name="res-target")

    now = datetime.now(timezone.utc)
    # insert a few results
    results_repo.insert_probe_result(
        s=db_session,
        target_id=tid,
        ts=now - timedelta(seconds=30),
        success=True,
        latency_ms=10,
        status_code=None,
        error=None,
    )
    results_repo.insert_probe_result(
        s=db_session,
        target_id=tid,
        ts=now - timedelta(seconds=10),
        success=False,
        latency_ms=None,
        status_code=500,
        error="fail",
    )
    results_repo.insert_probe_result(
        s=db_session, target_id=tid, ts=now, success=True, latency_ms=5, status_code=200, error=None
    )

    latest = results_repo.fetch_latest_results(s=db_session)
    assert any(r["target_id"] == tid for r in latest)

    per_target = results_repo.fetch_results_for_target(s=db_session, target_id=tid)
    assert len(per_target) >= 3

    latest_by_target = results_repo.fetch_latest_result_by_target(s=db_session)
    # should contain our target name
    assert any(r["target_id"] == tid for r in latest_by_target)
