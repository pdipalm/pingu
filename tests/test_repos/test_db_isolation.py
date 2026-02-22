import uuid

from sqlalchemy import text


def test_transaction_isolation_can_insert(db_session):
    tid = uuid.uuid4()
    db_session.execute(
        text("""
            INSERT INTO targets (id, name, type, host, url, interval_seconds, timeout_ms, enabled, created_at, updated_at)
            VALUES (:id, :name, 'icmp', :host, NULL, 30, 1000, true, NOW(), NOW())
        """),
        {"id": tid, "name": f"iso-{tid}", "host": "8.8.8.8"},
    )
    db_session.commit()

    count = db_session.execute(
        text("SELECT COUNT(*) FROM targets WHERE id = :id"),
        {"id": tid},
    ).scalar_one()
    assert count == 1


def test_transaction_isolation_does_not_leak(db_session):
    # If tests leak state, this will sometimes be > 0 (or you can query by name prefix)
    count = db_session.execute(
        text("SELECT COUNT(*) FROM targets WHERE name LIKE 'iso-%'")
    ).scalar_one()
    assert count == 0
