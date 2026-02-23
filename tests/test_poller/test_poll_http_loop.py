import asyncio
from uuid import uuid4

import pytest

from app.models import HttpTarget


@pytest.mark.anyio
async def test_poll_http_forever_inserts_one_result(monkeypatch):
    import app.poller.__main__ as poller_main

    tid = uuid4()
    t = HttpTarget(
        id=tid,
        name="site",
        url="https://example.com",
        interval_seconds=10,
        timeout_ms=500,
    )

    calls = []

    async def fake_probe(url: str, timeout_ms: int):
        assert url == "https://example.com"
        assert timeout_ms == 500
        return False, None, 503, "upstream error"

    def fake_insert_probe_result(**kwargs):
        calls.append(kwargs)

    async def fake_sleep(_seconds: float):
        raise asyncio.CancelledError()

    monkeypatch.setattr(poller_main, "http_probe_once", fake_probe)
    monkeypatch.setattr(poller_main, "insert_probe_result", fake_insert_probe_result)
    monkeypatch.setattr(poller_main.anyio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await poller_main.poll_http_forever(t)

    assert len(calls) == 1
    row = calls[0]

    assert row["target_id"] == tid
    assert row["success"] is False
    assert row["latency_ms"] is None
    assert row["status_code"] == 503
    assert row["error"] == "upstream error"
    assert row["ts"].tzinfo is not None
