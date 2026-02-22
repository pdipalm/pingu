import logging
import time

from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

log = logging.getLogger(__name__)


def timed_execute(
    session: Session, stmt: TextClause, params: dict | None, *, label: str
):
    t0 = time.perf_counter()
    try:
        return session.execute(stmt, params or {})
    finally:
        ms = (time.perf_counter() - t0) * 1000.0
        if ms > 200:
            log.warning("slow db query", extra={"label": label, "ms": round(ms, 1)})
