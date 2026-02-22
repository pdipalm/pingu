import time

import httpx


async def http_probe_once(
    url: str, timeout_ms: int
) -> tuple[bool, int | None, int | None, str | None]:
    """
    Returns (success, latency_ms, status_code, error)
    """
    timeout_s = timeout_ms / 1000.0

    try:
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            start = time.perf_counter()
            resp = await client.get(url)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

        success = 200 <= resp.status_code < 400

        return success, elapsed_ms, resp.status_code, None

    except Exception as e:
        return False, None, None, str(e)[:500]
