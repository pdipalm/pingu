import asyncio

import pytest

from app.poller.icmp import icmp_ping_once


class FakeProc:
    def __init__(self, returncode: int, out: bytes, err: bytes):
        self.returncode = returncode
        self._out = out
        self._err = err

    async def communicate(self):
        return self._out, self._err


@pytest.mark.anyio
async def test_icmp_ping_once_parses_latency(monkeypatch):
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        out = b"64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=23.4 ms\n"
        return FakeProc(0, out, b"")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    success, latency_ms, error = await icmp_ping_once("1.1.1.1", 1000)
    assert success is True
    assert latency_ms == 23
    assert error is None


@pytest.mark.anyio
async def test_icmp_ping_once_failure_returns_detail(monkeypatch):
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        return FakeProc(1, b"", b"ping: unknown host no-such-host\n")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    success, latency_ms, error = await icmp_ping_once("no-such-host", 1000)
    assert success is False
    assert latency_ms is None
    assert error is not None
    assert "unknown host" in error
