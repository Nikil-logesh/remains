"""Pydantic models for the registry foundation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CompanyIdentity(BaseModel):
    """Canonical identity returned by Brønnøysundregistrene."""

    model_config = ConfigDict(extra="ignore")

    organization_number: str
    legal_name: str
    organization_form: str | None = None
    address: str | None = None
    postal_code: str | None = None
    municipality: str | None = None
    nace_code: str | None = None
    employees: int | None = None
    registration_date: str | None = None
    status: str | None = None
    website: str | None = None
    source_url: str
    retrieved_at: datetime


class RegistryRecord(BaseModel):
    """Identity plus the raw response retained for diagnostics."""

    identity: CompanyIdentity
    raw_response: dict


class Evidence(BaseModel):
    """Auditable support for a claim; unsupported claims are never emitted."""

    id: str
    field: str
    status: Literal[
        "available", "not_available", "blocked", "not_applicable", "ambiguous", "failed"
    ]
    source_type: str
    source_url: str
    retrieved_at: datetime | str
    value: Any = None
    content_sha256: str | None = None
    note: str | None = None
    availability: Literal[
        "available", "not_available", "blocked", "not_applicable", "ambiguous", "failed"
    ] | None = None


class Claim(BaseModel):
    field: str
    value: Any = None
    availability: Literal[
        "available", "not_available", "blocked", "not_applicable", "ambiguous", "failed"
    ] = "available"
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    """Normalized profile assembled from official sources and verified evidence."""

    model_config = ConfigDict(extra="ignore")
    organization_number: str
    legal_name: str | None = None
    organization_form: str | None = None
    website: str | None = None
    address: str | None = None
    postal_code: str | None = None
    municipality: str | None = None
    employees: int | None = None
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    retrieved_at: datetime | str | None = None


class ProfileChange(BaseModel):
    field: str
    before: Any = None
    after: Any = None
    kind: Literal["added", "removed", "changed"]


class OutputEnvelope(BaseModel):
    organization_number: str | None = None
    profile: CompanyProfile | None = None
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    changes: list[ProfileChange] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    operations: dict[str, Any] = Field(default_factory=dict)


class Organization(BaseModel):
    """Backward-compatible registry response model."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    organization_number: str = Field(alias="organisasjonsnummer")
    legal_name: str = Field(alias="navn")
    organization_form: str | None = Field(default=None, alias="organisasjonsform")
    address: str | None = None
    postal_code: str | None = None
    municipality: str | None = None
    website: str | None = None
