"""Streaming access to the supplied financial-filer JSONL snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote


def normalize_organisation_number(value: Any) -> str:
    return "".join(ch for ch in str(value or "").strip() if ch.isdigit())


def iter_financial_records(path: str | Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (line number, record) without loading the dataset into memory."""
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield line_number, record


def lookup_financial_record(
    path: str | Path, organisation_number: str
) -> tuple[dict[str, Any] | None, int | None]:
    """Find one organisation with a bounded-memory sequential scan."""
    wanted = normalize_organisation_number(organisation_number)
    for line_number, record in iter_financial_records(path):
        candidate = normalize_organisation_number(
            record.get(
                "organisation_number",
                record.get("organization_number", record.get("organisasjonsnummer", record.get("org_number"))),
            )
        )
        if candidate == wanted:
            return record, line_number
    return None, None


class FinancialDataset:
    """Configurable streaming dataset facade used by batch processing."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def lookup(self, organisation_number: str) -> tuple[dict[str, Any] | None, int | None]:
        return lookup_financial_record(self.path, organisation_number)

    @property
    def source_url(self) -> str:
        return self.path.resolve().as_uri()
