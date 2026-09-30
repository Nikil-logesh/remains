"""Profile validation, persistence, and deterministic change detection."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.models import CompanyProfile, Evidence, ProfileChange


def validate_evidence(profile: CompanyProfile) -> CompanyProfile:
    ids = {item.id for item in profile.evidence}
    for claim in profile.claims:
        if claim.availability == "available" and (not claim.evidence_ids or not set(claim.evidence_ids) <= ids):
            raise ValueError(f"claim {claim.field!r} has no valid evidence")
    return profile


def validate_claims(profile: CompanyProfile) -> CompanyProfile:
    """Compatibility alias for callers that validate the claim graph."""
    return validate_evidence(profile)


def diff_profiles(previous: CompanyProfile | None, current: CompanyProfile) -> list[ProfileChange]:
    if previous is None:
        return []
    fields = ("legal_name", "organization_form", "website", "address", "postal_code",
              "municipality", "employees")
    changes = []
    for field in fields:
        before, after = getattr(previous, field), getattr(current, field)
        if before != after:
            changes.append(ProfileChange(field=field, before=before, after=after,
                kind="added" if before is None else "removed" if after is None else "changed"))
    return changes


class ProfileStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS profiles (organization_number TEXT PRIMARY KEY, payload TEXT NOT NULL)")

    def get(self, number: str) -> CompanyProfile | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM profiles WHERE organization_number=?", (number,)).fetchone()
        return CompanyProfile.model_validate_json(row[0]) if row else None

    def put(self, profile: CompanyProfile) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO profiles VALUES (?,?)",
                       (profile.organization_number, profile.model_dump_json()))
