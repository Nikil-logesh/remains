from __future__ import annotations
import asyncio
import random
import httpx

class RequestBudget:
    def __init__(self, maximum: int = 20):
        self.maximum, self.used = maximum, 0
    def consume(self) -> None:
        if self.used >= self.maximum:
            raise RuntimeError("request budget exhausted")
        self.used += 1

async def request_with_retry(client: httpx.AsyncClient, method: str, url: str, *,
                             budget: RequestBudget | None = None, retries: int = 2, **kwargs) -> httpx.Response:
    last = None
    for attempt in range(retries + 1):
        if budget:
            budget.consume()
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code not in {429, 500, 502, 503, 504}:
                return response
            last = RuntimeError(f"transient HTTP {response.status_code}")
        except httpx.HTTPError as exc:
            last = exc
        if attempt < retries:
            await asyncio.sleep(min(2 ** attempt, 4) + random.random() * .1)
    raise RuntimeError("request failed after retries") from last
