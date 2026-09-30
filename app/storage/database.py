"""SQLite database initialization."""

import sqlite3
from pathlib import Path


def initialize_database(path: str | Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS registry_cache (
                organization_number TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                retrieved_at TEXT NOT NULL
            )"""
        )
