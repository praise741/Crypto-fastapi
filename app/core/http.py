from fastapi import Response


def apply_cache_headers(response: Response, ttl_seconds: int) -> None:
    """Attach shared caching headers based on the performance strategy."""

    cache_control = f"public, max-age={ttl_seconds}"
    response.headers.setdefault("Cache-Control", cache_control)
