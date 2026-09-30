"""Pydantic models used by Signalpost."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .validators import OrgNumber


class Organization(BaseModel):
    """The stable, useful subset of a Brønnøysund organization."""

    model_config = ConfigDict(extra="ignore")

    org_number: OrgNumber = Field(alias="organisasjonsnummer")
    name: str = Field(alias="navn")
    organization_form: str | None = Field(default=None, alias="organisasjonsform")
    municipality: Any = Field(default=None, alias="forretningsadresse")
    registered: bool | None = Field(default=None, alias="registrertIMvaregisteret")

    @property
    def display_address(self) -> str | None:
        """Return a safe, human-readable address when the API supplied one."""
        if not isinstance(self.municipality, dict):
            return self.municipality
        parts = [
            *(self.municipality.get("adresse") or []),
            self.municipality.get("postnummer"),
            self.municipality.get("poststed"),
        ]
        return ", ".join(str(part) for part in parts if part)


class CachedOrganization(BaseModel):
    """A cached registry response and its retrieval time."""

    organization: Organization
    fetched_at: datetime
