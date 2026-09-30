"""Async client for the official Brønnøysund registry."""

from datetime import datetime, timezone
from typing import Any

import httpx

from app.models import CompanyIdentity, RegistryRecord
from app.validation.org_number import normalize_org_number, validate_org_number


class BrregError(RuntimeError):
    """A safe, user-facing registry failure."""


class BrregClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client

    async def __aenter__(self) -> "BrregClient":
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def get_company(self, organization_number: str) -> RegistryRecord:
        number = normalize_org_number(organization_number)
        if not validate_org_number(number):
            raise ValueError("invalid Norwegian organization number")
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        source_url = f"{self.base_url}/enheter/{number}"
        try:
            response = await client.get(source_url)
            if response.status_code == 404:
                raise BrregError(f"organization {number} was not found")
            response.raise_for_status()
            payload: Any = response.json()
            if not isinstance(payload, dict):
                raise BrregError("registry returned an unexpected response")
            identity = self._identity_from_payload(payload, source_url)
            return RegistryRecord(identity=identity, raw_response=payload)
        except httpx.HTTPError as exc:
            raise BrregError("could not reach the organization registry") from exc
        except (TypeError, KeyError, ValueError) as exc:
            raise BrregError("registry returned invalid organization data") from exc
        finally:
            if owns_client:
                await client.aclose()

    async def get_organization(self, organization_number: str):
        """Compatibility alias returning the canonical identity."""

        return (await self.get_company(organization_number)).identity

    @staticmethod
    def _identity_from_payload(payload: dict[str, Any], source_url: str) -> CompanyIdentity:
        address = payload.get("forretningsadresse") or {}
        nace = payload.get("naeringskode1") or {}
        postal_code = address.get("postnummer")
        return CompanyIdentity(
            organization_number=str(payload["organisasjonsnummer"]),
            legal_name=str(payload["navn"]),
            organization_form=(payload.get("organisasjonsform") or {}).get("beskrivelse"),
            address=", ".join(address.get("adresse") or []) or None,
            postal_code=str(postal_code) if postal_code is not None else None,
            municipality=address.get("kommune"),
            nace_code=nace.get("kode"),
            employees=payload.get("antallAnsatte"),
            registration_date=payload.get("registrertIEnhetsregisteret"),
            status=payload.get("konkurs") and "bankrupt" or None,
            website=payload.get("hjemmeside"),
            source_url=source_url,
            retrieved_at=datetime.now(timezone.utc),
        )
