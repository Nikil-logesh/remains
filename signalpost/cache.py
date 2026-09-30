"""Minimal SQLite cache foundation; no freshness policy is applied yet."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import CachedOrganization, Organization


class SQLiteCache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS organizations (
                    org_number TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                )"""
            )

    def get(self, org_number: str) -> CachedOrganization | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload, fetched_at FROM organizations WHERE org_number = ?", (org_number,)
            ).fetchone()
        if row is None:
            return None
        return CachedOrganization(
            organization=Organization.model_validate_json(row["payload"]),
            fetched_at=datetime.fromisoformat(row["fetched_at"]),
        )

    def put(self, organization: Organization, fetched_at: datetime | None = None) -> CachedOrganization:
        timestamp = fetched_at or datetime.now(timezone.utc)
        cached = CachedOrganization(organization=organization, fetched_at=timestamp)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO organizations(org_number, payload, fetched_at) VALUES (?, ?, ?)",
                (organization.org_number, organization.model_dump_json(by_alias=True), timestamp.isoformat()),
            )
        return cached
