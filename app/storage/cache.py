"""SQLite registry-response cache."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.models import RegistryRecord
from app.storage.database import initialize_database


class RegistryCache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        initialize_database(self.path)

    def get(self, organization_number: str) -> RegistryRecord | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT payload FROM registry_cache WHERE organization_number = ?",
                (organization_number,),
            ).fetchone()
        return RegistryRecord.model_validate_json(row[0]) if row else None

    def put(self, record: RegistryRecord) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """INSERT OR REPLACE INTO registry_cache
                (organization_number, payload, retrieved_at) VALUES (?, ?, ?)""",
                (
                    record.identity.organization_number,
                    json.dumps(record.model_dump(mode="json"), ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
