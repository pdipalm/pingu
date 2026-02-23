import asyncio
from uuid import uuid4

import pytest

from app.models import IcmpTarget


@pytest.mark.anyio
async def test_poll_icmp_forever_inserts_one_result(monkeypatch):
    import app.poller.__main__ as poller_main

    tid = uuid4()
    t = IcmpTarget(
        id=tid,
        name="t1",
        host="1.1.1.1",
        interval_seconds=30,
        timeout_ms=1000,
    )

    calls = []

    async def fake_ping(host: str, timeout_ms: int):
        assert host == "1.1.1.1"
        assert timeout_ms == 1000
        return True, 42, None

    def fake_insert_probe_result(**kwargs):
        calls.append(kwargs)

    async def fake_sleep(_seconds: float):
        raise asyncio.CancelledError()

    monkeypatch.setattr(poller_main, "icmp_ping_once", fake_ping)
    monkeypatch.setattr(poller_main, "insert_probe_result", fake_insert_probe_result)
    monkeypatch.setattr(poller_main.anyio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await poller_main.poll_icmp_forever(t)

    assert len(calls) == 1
    row = calls[0]
    assert row["target_id"] == tid
    assert row["success"] is True
    assert row["latency_ms"] == 42
    assert row["status_code"] is None
    assert row["error"] is None
    assert row["ts"].tzinfo is not None


@pytest.mark.anyio
async def test_poll_icmp_forever_handles_probe_exception(monkeypatch):
    import app.poller.__main__ as poller_main

    t = IcmpTarget(
        id=uuid4(),
        name="bad",
        host="1.1.1.1",
        interval_seconds=1,
        timeout_ms=1000,
    )

    inserted = []
    ping_calls = 0

    async def boom(*_args, **_kwargs):
        nonlocal ping_calls
        ping_calls += 1
        raise RuntimeError("probe failed")

    def fake_insert_probe_result(**kwargs):
        inserted.append(kwargs)

    async def fake_sleep(_seconds: float):
        raise asyncio.CancelledError()

    monkeypatch.setattr(poller_main, "icmp_ping_once", boom)
    monkeypatch.setattr(poller_main, "insert_probe_result", fake_insert_probe_result)
    monkeypatch.setattr(poller_main.anyio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await poller_main.poll_icmp_forever(t)

    assert ping_calls == 1
    assert inserted == []
