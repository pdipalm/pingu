import time

import httpx


async def http_probe_once(
    url: str, timeout_ms: int
) -> tuple[bool, int | None, int | None, str | None]:
    """
    Returns (success, latency_ms, status_code, error)
    success = transport success (HTTP response received)
    """
    timeout_s = timeout_ms / 1000.0

    try:
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            start = time.perf_counter()
            resp = await client.get(url)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

        return True, elapsed_ms, resp.status_code, None

    except httpx.TimeoutException:
        return False, None, None, "timeout"
    except httpx.ConnectError:
        return False, None, None, "connect_error"
    except httpx.HTTPError as e:
        return False, None, None, f"http_error: {type(e).__name__}"
    except Exception as e:
        return False, None, None, str(e)[:500]
