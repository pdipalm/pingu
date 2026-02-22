import uuid
from datetime import datetime, timedelta, timezone

from tests.db_helpers import insert_result, insert_target


def test_health_no_targets(client, db_session):

    r = client.get("/health")
    assert r.status_code == 200
    payload = r.json()
    assert payload["db"] is True
    assert payload["ok"] is True
    assert payload["stats"]["enabled_targets"] == 0
    assert payload["stats"]["last_result_ts"] is None


def test_health_with_recent_result_not_stale(client, db_session):

    tid = uuid.uuid4()
    insert_target(db_session, tid=tid, name="t-recent", interval_seconds=30)
    now = datetime.now(timezone.utc)
    insert_result(db_session, target_id=tid, ts=now)

    r = client.get("/health")
    assert r.status_code == 200
    payload = r.json()
    assert payload["stats"]["enabled_targets"] == 1
    assert payload["ok"] is True
    assert payload["stats"]["last_result_ts"] is not None


def test_health_with_stale_result(client, db_session):

    tid = uuid.uuid4()
    # small interval still respects MIN_STALE_SECONDS -> 30s
    insert_target(db_session, tid=tid, name="t-stale", interval_seconds=1)
    # insert an old result to be stale
    old = datetime.now(timezone.utc) - timedelta(seconds=120)
    insert_result(db_session, target_id=tid, ts=old)

    r = client.get("/health")
    assert r.status_code == 200
    payload = r.json()
    assert payload["stats"]["enabled_targets"] == 1
    assert payload["ok"] is False
