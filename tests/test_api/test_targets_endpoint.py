import uuid
from datetime import datetime, timedelta, timezone

from tests.db_helpers import insert_result, insert_target


def test_list_targets_filters_and_get_by_id(client, db_session):

    t1 = uuid.uuid4()
    t2 = uuid.uuid4()
    t3 = uuid.uuid4()
    insert_target(db_session, tid=t1, name="ta", enabled=True)
    insert_target(db_session, tid=t2, name="tb", enabled=True)
    insert_target(db_session, tid=t3, name="tc", enabled=False)

    # default (enabled)
    r = client.get("/targets")
    assert r.status_code == 200
    items = r.json()["items"]
    names = {i["name"] for i in items}
    assert "ta" in names and "tb" in names and "tc" not in names

    # disabled
    r = client.get("/targets?status=disabled")
    items = r.json()["items"]
    assert any(i["name"] == "tc" for i in items)

    # all
    r = client.get("/targets?status=all")
    items = r.json()["items"]
    assert any(i["name"] == "tc" for i in items)

    # get by id
    r = client.get(f"/targets/{t1}")
    assert r.status_code == 200
    assert r.json()["name"] == "ta"

    # 404 for missing
    missing = uuid.uuid4()
    r = client.get(f"/targets/{missing}")
    assert r.status_code == 404


def test_target_results_range_and_bad_range(client, db_session):

    tid = uuid.uuid4()
    insert_target(db_session, tid=tid, name="t-results", enabled=True)

    now = datetime.now(timezone.utc)
    insert_result(db_session, target_id=tid, ts=now - timedelta(seconds=30))
    insert_result(db_session, target_id=tid, ts=now - timedelta(seconds=10))

    # valid since/until
    since = (now - timedelta(seconds=40)).isoformat()
    until = (now - timedelta(seconds=5)).isoformat()
    r = client.get(
        f"/targets/{tid}/results",
        params={"since": since, "until": until},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 2

    # bad range (since > until)
    r = client.get(
        f"/targets/{tid}/results",
        params={"since": until, "until": since},
    )
    assert r.status_code == 400
