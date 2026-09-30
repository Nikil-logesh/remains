"""Durable attempt and winner state, using only local SQLite."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AttemptStore:
    def __init__(self, path: str | Path = "signalpost.db") -> None:
        self.path = Path(path)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY, company TEXT NOT NULL, strategy TEXT NOT NULL,
                strategy_version TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS winners (
                company TEXT PRIMARY KEY, attempt_id TEXT NOT NULL, policy TEXT NOT NULL,
                updated_at TEXT NOT NULL)""")

    def record(self, company: str, strategy: str, strategy_version: str,
               payload: dict[str, Any] | None = None, **fields: Any) -> str:
        attempt_id = fields.pop("attempt_id", uuid.uuid4().hex)
        payload = {
            "urls": [], "hashes": [], "candidates": [], "claims": [],
            "accepted_reasons": [], "rejected_reasons": [], "identity_evidence": [],
            "runtime_ms": 0, "requests": 0, "cost_usd": 0, "errors": [],
            "status": "completed", **(payload or {}), **fields,
        }
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?)",
                       (attempt_id, company, strategy, strategy_version,
                        json.dumps(payload, ensure_ascii=False), _now()))
        return attempt_id

    def get(self, attempt_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT id,company,strategy,strategy_version,payload,created_at FROM attempts WHERE id=?",
                             (attempt_id,)).fetchone()
        if not row:
            return None
        return {"attempt_id": row[0], "company": row[1], "strategy": row[2],
                "strategy_version": row[3], **json.loads(row[4]), "created_at": row[5]}

    def attempts(self, company: str | None = None) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT id FROM attempts WHERE company=? ORDER BY created_at",
                              (company,)).fetchall() if company else db.execute(
                              "SELECT id FROM attempts ORDER BY created_at").fetchall()
        return [self.get(row[0]) for row in rows]

    def winner(self, company: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT attempt_id,policy,updated_at FROM winners WHERE company=?",
                             (company,)).fetchone()
        return {"attempt_id": row[0], "policy": json.loads(row[1]), "updated_at": row[2]} if row else None

    def promote(self, company: str, attempt_id: str, policy: dict[str, Any]) -> None:
        if not self.get(attempt_id):
            raise ValueError("attempt does not exist")
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO winners VALUES (?,?,?,?)",
                       (company, attempt_id, json.dumps(policy, sort_keys=True), _now()))

    def promote_if_allowed(self, company: str, attempt_id: str, decision: dict[str, Any]) -> bool:
        """Apply a gate decision atomically; a rejection cannot replace a winner."""
        if not decision.get("promote", False):
            return False
        self.promote(company, attempt_id, dict(decision.get("policy", {})))
        return True
