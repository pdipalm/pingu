import uuid

from sqlalchemy import text

from app.models import HttpTarget, IcmpTarget
from app.repos import targets as targets_repo


def insert_target(
    db_session, *, tid, name, type_, host, url, interval=30, timeout=1000, enabled=True
):
    db_session.execute(
        text("""
			INSERT INTO targets (id, name, type, host, url, interval_seconds, timeout_ms, enabled, created_at, updated_at)
			VALUES (:id, :name, :type, :host, :url, :interval_seconds, :timeout_ms, :enabled, NOW(), NOW())
			"""),
        {
            "id": tid,
            "name": name,
            "type": type_,
            "host": host,
            "url": url,
            "interval_seconds": interval,
            "timeout_ms": timeout,
            "enabled": enabled,
        },
    )


def test_fetch_all_and_by_id_and_enabled_filters(db_session):
    tid1 = uuid.uuid4()
    tid2 = uuid.uuid4()
    tid3 = uuid.uuid4()

    insert_target(db_session, tid=tid1, name="a-icmp", type_="icmp", host="1.1.1.1", url=None)
    insert_target(
        db_session, tid=tid2, name="b-http", type_="http", host=None, url="https://example.local"
    )
    insert_target(
        db_session,
        tid=tid3,
        name="c-disabled",
        type_="icmp",
        host="8.8.8.8",
        url=None,
        enabled=False,
    )

    # fetch_all default (enabled)
    all_enabled = targets_repo.fetch_all_targets(s=db_session)
    names = [t["name"] for t in all_enabled]
    assert "a-icmp" in names and "b-http" in names and "c-disabled" not in names

    # fetch_all disabled
    disabled = targets_repo.fetch_all_targets(s=db_session, status="disabled")
    assert any(t["name"] == "c-disabled" for t in disabled)

    # fetch_all all
    all_ = targets_repo.fetch_all_targets(s=db_session, status="all")
    assert len(all_) >= 3

    # fetch_target_by_id
    row = targets_repo.fetch_target_by_id(s=db_session, target_id=tid1)
    assert row is not None and row["name"] == "a-icmp"

    # fetch enabled icmp targets -> dataclass list
    icmps = targets_repo.fetch_enabled_icmp_targets(s=db_session)
    assert any(isinstance(t, IcmpTarget) for t in icmps)
    assert any(t.host == "1.1.1.1" for t in icmps)

    # fetch enabled http targets -> dataclass list
    https = targets_repo.fetch_enabled_http_targets(s=db_session)
    assert any(isinstance(t, HttpTarget) for t in https)
    assert any(t.url == "https://example.local" for t in https)
