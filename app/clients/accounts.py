"""Official structured account discovery (optional and read-only)."""
from __future__ import annotations
import httpx
from app.clients.http import RequestBudget, request_with_retry

class AccountsClient:
    def __init__(self, base_url: str = "https://data.brreg.no/enhetsregisteret/api", client=None, budget=None):
        self.base_url, self.client, self.budget = base_url.rstrip("/"), client, budget or RequestBudget()
    async def get_accounts(self, number: str) -> dict:
        own = self.client is None
        client = self.client or httpx.AsyncClient(timeout=10)
        try:
            response = await request_with_retry(client, "GET", f"{self.base_url}/enheter/{number}",
                                                budget=self.budget)
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {}
        finally:
            if own: await client.aclose()

    async def get_company_accounts(self, number: str) -> dict:
        return await self.get_accounts(number)
