"""Evidence and terminal-output helpers shared by batch integrations."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def content_sha256(value: bytes | str) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def make_evidence(
    field: str,
    status: str,
    source_url: str,
    *,
    value: Any = None,
    source_type: str = "official_financial_dataset",
    retrieved_at: str | None = None,
    content_hash: str | None = None,
    source_row_key: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Create provenance-rich evidence without turning missing values into zero."""
    return {
        "field": field,
        "status": status,
        "availability": status,
        "source_type": source_type,
        "source_class": source_type,
        "source_url": source_url,
        "retrieved_at": retrieved_at or utc_now(),
        "value": value,
        "content_sha256": content_hash,
        "source_row_key": source_row_key,
        "note": note,
    }
