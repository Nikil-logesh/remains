"""JSONL batch input/output with one fail-closed terminal envelope per row."""

from __future__ import annotations

import json
import time
import uuid
import asyncio
from pathlib import Path
from typing import Any, Iterable, TextIO

from app.evidence import content_sha256, make_evidence, utc_now
from app.financial import FinancialDataset, normalize_organisation_number
from app.validation.org_number import validate_org_number


def _input_number(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get(
            "organisation_number",
            value.get("organization_number", value.get("organisasjonsnummer", value.get("org_number"))),
        )
    return normalize_organisation_number(value)


def read_organisation_inputs(path: str | Path) -> list[dict[str, Any]]:
    """Read common starter-kit input forms without changing row order."""
    source = Path(path)
    if source.suffix.lower() == ".json":
        body = json.loads(source.read_text(encoding="utf-8"))
        values = body if isinstance(body, list) else body.get("organisation_numbers", [])
    elif source.suffix.lower() == ".jsonl":
        with source.open(encoding="utf-8") as handle:
            values = [row for _, row, error in iter_input_rows(handle) if error is None]
    else:
        values = [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = []
    for value in values:
        number = _input_number(value)
        if len(number) != 9:
            raise ValueError(f"Invalid Norwegian organisation number: {value!r}")
        result.append({"organisation_number": number})
    return result


def iter_input_rows(handle: Iterable[str]) -> Iterable[tuple[int, Any, str | None]]:
    """Parse JSONL while retaining malformed rows for terminal reporting."""
    for line_number, line in enumerate(handle, 1):
        if not line.strip():
            continue
        try:
            yield line_number, json.loads(line), None
        except json.JSONDecodeError as exc:
            # Retain the original non-empty row so terminal output is lossless.
            yield line_number, line.rstrip("\r\n"), f"invalid JSON on line {line_number}: {exc.msg}"


def terminal_envelope(
    organisation_number: str,
    *,
    run_id: str,
    started_at: str,
    completed_at: str,
    claims: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
    operations: dict[str, Any] | None = None,
    input_row: Any = None,
) -> dict[str, Any]:
    errors = errors or []
    status = "failed" if errors else "completed"
    return {
        "organisation_number": organisation_number or None,
        "organization_number": organisation_number or None,
        "input": input_row,
        "run": {
            "run_id": run_id,
            "started_at": started_at,
            "completed_at": completed_at,
            "terminal_status": status,
        },
        "run_id": run_id,
        "terminal_status": status,
        "claims": claims or [],
        "evidence": evidence or [],
        "changes": [],
        "errors": errors,
        "operations": operations or {"requests": 0, "runtime_ms": 0, "third_party_cost_usd": 0},
    }


def process_jsonl(
    input_handle: TextIO,
    output_handle: TextIO,
    *,
    financial_dataset: str | Path | None = None,
    run_id: str | None = None,
    enrich: bool = False,
    registry_base_url: str = "https://data.brreg.no/enhetsregisteret/api",
    request_timeout_seconds: float = 10.0,
) -> int:
    run_id = run_id or uuid.uuid4().hex
    dataset = FinancialDataset(financial_dataset) if financial_dataset else None
    count = 0
    for line_number, raw, parse_error in iter_input_rows(input_handle):
        count += 1
        started = utc_now()
        started_clock = time.perf_counter()
        number = _input_number(raw) if parse_error is None else ""
        errors: list[dict[str, Any]] = []
        claims: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        if parse_error:
            errors.append({"code": "invalid_input", "message": parse_error, "line": line_number})
            claims.append({"field": "input", "value": None, "availability": "failed", "confidence": 0.0, "evidence_ids": []})
        elif len(number) != 9 or not validate_org_number(number):
            errors.append({"code": "invalid_organisation_number", "message": "expected a valid Norwegian 9-digit organisation number", "line": line_number})
            claims.append({"field": "input", "value": raw, "availability": "failed", "confidence": 0.0, "evidence_ids": []})
        elif dataset:
            if not dataset.path.is_file():
                errors.append({"code": "dataset_unavailable", "message": "financial dataset is not readable"})
                evidence.append(make_evidence("financial_profile", "failed", dataset.source_url, source_row_key=number, note="Snapshot is not readable"))
                claims.append({"field": "financial_profile", "value": None, "availability": "failed", "confidence": 0.0, "evidence_ids": []})
            else:
                record, row = dataset.lookup(number)
                if record is None:
                    evidence.append(make_evidence("financial_profile", "not_available", dataset.source_url, source_row_key=number, note="No matching row in snapshot"))
                    claims.append({"field": "financial_profile", "value": None, "availability": "not_available", "confidence": 1.0, "evidence_ids": []})
                else:
                    row_hash = content_sha256(json.dumps(record, ensure_ascii=False, sort_keys=True))
                    item = make_evidence("financial_profile", "available", dataset.source_url, value=record, content_hash=row_hash, source_row_key=f"{number}:line-{row}")
                    item["id"] = f"financial-{number}"
                    evidence.append(item)
                    for field, value in record.items():
                        if field not in {"organisation_number", "organisasjonsnummer"} and value is not None and value != "":
                            claims.append({"field": field, "value": value, "availability": "available", "confidence": 1.0, "evidence_ids": [f"financial-{number}"]})
        elif len(number) == 9 and validate_org_number(number):
            # A source not configured is an explicit abstention, not an empty success.
            claims.append({"field": "financial_profile", "value": None, "availability": "not_applicable", "confidence": 1.0, "evidence_ids": []})
        if enrich and len(number) == 9 and validate_org_number(number) and not parse_error:
            from app.clients.brreg import BrregClient
            from app.pipeline import build_profile
            async def _enrich():
                async with BrregClient(registry_base_url, request_timeout_seconds) as registry:
                    return await build_profile(number, registry)
            result = asyncio.run(_enrich())
            claims = [c.model_dump(mode="json") for c in result.claims]
            evidence = [e.model_dump(mode="json") for e in result.evidence]
            errors.extend(result.errors)
        elapsed = round((time.perf_counter() - started_clock) * 1000, 3)
        envelope = terminal_envelope(number, run_id=run_id, started_at=started, completed_at=utc_now(), claims=claims, evidence=evidence, errors=errors, operations={"requests": 0, "runtime_ms": elapsed, "third_party_cost_usd": 0}, input_row=raw)
        envelope["input_line"] = line_number
        output_handle.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    return count
