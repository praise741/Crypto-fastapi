from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

from fastapi.testclient import TestClient


def test_market_prices_parallel_requests(client: TestClient):
    start = perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(client.get, "/api/v1/market/prices") for _ in range(5)
        ]
    responses = [future.result() for future in futures]
    duration = perf_counter() - start

    assert all(response.status_code == 200 for response in responses)
    assert duration < 2.0

    payload = responses[0].json()
    assert payload["success"] is True
    assert "prices" in payload["data"]
