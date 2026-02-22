import uuid
from datetime import datetime, timedelta, timezone

from tests.db_helpers import insert_result, insert_target


def test_results_latest_and_limit(client, db_session):

    t1 = uuid.uuid4()
    t2 = uuid.uuid4()
    insert_target(db_session, tid=t1, name="r-a")
    insert_target(db_session, tid=t2, name="r-b")

    now = datetime.now(timezone.utc)
    insert_result(db_session, target_id=t1, ts=now - timedelta(seconds=5))
    insert_result(db_session, target_id=t2, ts=now - timedelta(seconds=4))
    insert_result(db_session, target_id=t1, ts=now - timedelta(seconds=1))

    # limit results to 2
    r = client.get("/results/latest?limit=2")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 2
    # newest should be the most recent ts
    assert items[0]["ts"] >= items[1]["ts"]


def test_results_latest_by_target(client, db_session):

    t1 = uuid.uuid4()
    t2 = uuid.uuid4()
    insert_target(db_session, tid=t1, name="by-a")
    insert_target(db_session, tid=t2, name="by-b")

    now = datetime.now(timezone.utc)
    insert_result(db_session, target_id=t1, ts=now - timedelta(seconds=20))
    insert_result(db_session, target_id=t2, ts=now - timedelta(seconds=10))

    r = client.get("/results/latest-by-target")
    assert r.status_code == 200
    items = r.json()["items"]
    # should include both target names
    names = {it["target_name"] for it in items}
    assert "by-a" in names and "by-b" in names
