import asyncio
import re
import time

PING_TIME_RE = re.compile(r"time[=<]([\d.]+)\s*ms")


async def icmp_ping_once(host: str, timeout_ms: int) -> tuple[bool, int | None, str | None]:
    """
    Returns (success, latency_ms, error).
    Uses system ping. Requires iputils-ping + CAP_NET_RAW in container.
    """
    # Linux iputils: -c 1 (one packet), -W <seconds> (timeout per reply)
    timeout_s = max(1, int((timeout_ms + 999) / 1000))
    cmd = ["ping", "-n", "-c", "1", "-W", str(timeout_s), host]

    start = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_b, err_b = await proc.communicate()
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    out = (out_b or b"").decode("utf-8", errors="replace")
    err = (err_b or b"").decode("utf-8", errors="replace")

    if proc.returncode == 0:
        m = PING_TIME_RE.search(out)
        if m:
            try:
                return True, int(float(m.group(1))), None
            except Exception:
                return True, elapsed_ms, None
        return True, elapsed_ms, None

    # Common failures: permission, unknown host, timeout
    detail = (err.strip() or out.strip() or f"ping failed rc={proc.returncode}")[:500]
    return False, None, detail
