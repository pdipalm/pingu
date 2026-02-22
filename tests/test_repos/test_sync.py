import uuid

from sqlalchemy import text

from app.poller.config import TargetCfg
from app.repos import sync as sync_repo


def test_sync_targets_to_db_add_update_disable(db_session):
    # Start with one existing DB-only target which should be disabled
    existing_id = uuid.uuid4()
    db_session.execute(
        text("""
			INSERT INTO targets (id, name, type, host, url, interval_seconds, timeout_ms, enabled, created_at, updated_at)
			VALUES (:id, :name, 'icmp', '1.2.3.4', NULL, 10, 1000, true, NOW(), NOW())
			"""),
        {"id": existing_id, "name": "db-only"},
    )

    # Config contains one new and one that updates
    cfg = [
        TargetCfg(
            name="cfg-new",
            type="icmp",
            host="9.9.9.9",
            url=None,
            interval_seconds=15,
            timeout_ms=500,
            enabled=True,
        ),
        TargetCfg(
            name="db-only",
            type="icmp",
            host="5.5.5.5",
            url=None,
            interval_seconds=20,
            timeout_ms=600,
            enabled=True,
        ),
    ]

    sync_repo.sync_targets_to_db(cfg, s=db_session)

    # after sync, db-only should still exist but with updated host
    row = (
        db_session.execute(
            text("SELECT host, enabled FROM targets WHERE name = :name"), {"name": "db-only"}
        )
        .mappings()
        .one()
    )
    assert row["host"] == "5.5.5.5"
    assert row["enabled"] is True

    # cfg-new should be present
    new_row = db_session.execute(
        text("SELECT id FROM targets WHERE name = :name"), {"name": "cfg-new"}
    ).scalar_one_or_none()
    assert new_row is not None

    # Now sync with only cfg-new to ensure db-only becomes disabled
    sync_repo.sync_targets_to_db(
        [
            TargetCfg(
                name="cfg-new",
                type="icmp",
                host="9.9.9.9",
                url=None,
                interval_seconds=15,
                timeout_ms=500,
                enabled=True,
            )
        ],
        s=db_session,
    )
    disabled = db_session.execute(
        text("SELECT enabled FROM targets WHERE name = :name"), {"name": "db-only"}
    ).scalar_one()
    assert disabled is False
