# tests/conftest.py
import os
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

import app.api as app
from alembic import command
from alembic.config import Config

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/pingu_test",
)


@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL, future=True, pool_pre_ping=True)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> Iterator[None]:
    """
    Apply migrations to the test database once per test session.
    """
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(cfg, "head")
    yield


# from sqlalchemy import text
# import pytest


# @pytest.fixture(scope="session", autouse=True)
# def reset_test_db(engine, apply_migrations) -> Iterator[None]:
#     """
#     Ensure test DB starts empty for each pytest session.
#     """
#     with engine.begin() as conn:
#         db_name = conn.execute(text("select current_database()")).scalar_one()
#         assert "test" in db_name, f"Refusing to wipe non-test database: {db_name}"

#         conn.execute(text("TRUNCATE TABLE probe_results RESTART IDENTITY CASCADE;"))
#         conn.execute(text("TRUNCATE TABLE targets RESTART IDENTITY CASCADE;"))
#     yield


@pytest.fixture()
def db_session(engine, monkeypatch) -> Iterator[Session]:
    """
    Per-test session isolated by outer transaction + SAVEPOINT.

    Any repo calls that use session_scope(existing=None) will still use this
    same connection because we patch app.db.SessionLocal.
    """
    connection = engine.connect()
    outer_txn = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    session = TestingSessionLocal()

    # Guardrail: refuse to run against a non-test database
    db_name = session.execute(text("select current_database()")).scalar_one()
    assert "test" in db_name, f"Refusing to run tests against database: {db_name}"

    # Start SAVEPOINT
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        # If the nested transaction ended, restart it
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    _ = restart_savepoint  # silence unused variable warning

    import app.db as app_db

    monkeypatch.setattr(app_db, "SessionLocal", TestingSessionLocal)

    try:
        yield session
    finally:
        session.close()
        outer_txn.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    with TestClient(app.app) as c:
        yield c
