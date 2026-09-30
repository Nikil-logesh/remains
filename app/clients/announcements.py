"""Best-effort announcements client; unavailable data is returned as empty."""
from __future__ import annotations
import httpx
from app.clients.http import RequestBudget, request_with_retry

class AnnouncementsClient:
    def __init__(self, base_url: str, client=None, budget=None):
        self.base_url, self.client, self.budget = base_url.rstrip("/"), client, budget or RequestBudget()
    async def list(self, number: str) -> list[dict]:
        own = self.client is None
        client = self.client or httpx.AsyncClient(timeout=10)
        try:
            response = await request_with_retry(client, "GET", f"{self.base_url}/{number}", budget=self.budget)
            if response.status_code == 404: return []
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else data.get("_embedded", {}).get("announcements", [])
        finally:
            if own: await client.aclose()
