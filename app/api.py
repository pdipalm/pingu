from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import text

from app.db import SessionLocal, db_ok

app = FastAPI(title="Pingu", version="0.1.0")


@app.get("/health")
def health():
    ok = True
    db = db_ok()

    last_ts = None
    seconds_since = None
    enabled_targets = 0

    if db:
        with SessionLocal() as s:
            enabled_targets = s.execute(text("SELECT COUNT(*) FROM targets WHERE enabled = true")).scalar_one()
            last_ts = s.execute(text("SELECT MAX(ts) FROM probe_results")).scalar_one()

        if last_ts is not None:
            now = datetime.now(timezone.utc)
            seconds_since = int((now - last_ts).total_seconds())

    return {
        "ok": ok,
        "db": db,
        "enabled_targets": enabled_targets,
        "last_result_ts": last_ts,
        "seconds_since_last_result": seconds_since,
    }