"""Read-only asynchronous Brønnøysund Enhetsregisteret client."""

from typing import Any

import httpx

from .models import Organization
from .validators import validate_org_number


class RegistryError(RuntimeError):
    """A safe, user-facing registry failure."""


class BrregClient:
    def __init__(self, base_url: str, timeout: float = 10.0, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client

    async def get_organization(self, org_number: str) -> Organization:
        number = validate_org_number(org_number)
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.get(f"{self.base_url}/enheter/{number}")
            if response.status_code == 404:
                raise RegistryError(f"organization {number} was not found")
            response.raise_for_status()
            payload: Any = response.json()
            if not isinstance(payload, dict):
                raise RegistryError("registry returned an unexpected response")
            return Organization.model_validate(payload)
        except httpx.HTTPError as exc:
            raise RegistryError("could not reach the organization registry") from exc
        except ValueError as exc:
            raise RegistryError("registry returned invalid organization data") from exc
        finally:
            if owns_client:
                await client.aclose()
