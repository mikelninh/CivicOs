from __future__ import annotations
import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from civicos.core.models import EvidenceFact, EvidenceReceipt


@dataclass(frozen=True)
class StoredSnapshot:
    source_id: str
    sha256: str
    fetched_at: str
    facts: list[dict[str, Any]]
    metadata: dict[str, Any]


class SnapshotStore:
    """Small durable store for public-source Watchtower state.

    Production deployments can replace this adapter with a managed database. The
    default path is outside committed source files and can be overridden with
    CIVICOS_STATE_DB.
    """

    def __init__(self, path: str | Path | None = None):
        raw = path or os.getenv("CIVICOS_STATE_DB") or ".civicos/state.sqlite3"
        self.path = Path(raw)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        with self._connect() as con:
            con.execute(
                """CREATE TABLE IF NOT EXISTS source_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    facts_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )"""
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_source ON source_snapshots(source_id, id DESC)")

    def save(self, receipt: EvidenceReceipt, facts: list[EvidenceFact], metadata: dict[str, Any] | None = None) -> StoredSnapshot:
        facts_json = [fact.model_dump(mode="json") for fact in facts]
        meta = metadata or {}
        with self._connect() as con:
            con.execute(
                "INSERT INTO source_snapshots(source_id, sha256, fetched_at, facts_json, metadata_json) VALUES (?, ?, ?, ?, ?)",
                (receipt.source_id, receipt.sha256, receipt.fetched_at.isoformat(), json.dumps(facts_json), json.dumps(meta)),
            )
        return StoredSnapshot(receipt.source_id, receipt.sha256, receipt.fetched_at.isoformat(), facts_json, meta)

    def latest(self, source_id: str) -> StoredSnapshot | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT source_id, sha256, fetched_at, facts_json, metadata_json FROM source_snapshots WHERE source_id=? ORDER BY id DESC LIMIT 1",
                (source_id,),
            ).fetchone()
        if not row:
            return None
        return StoredSnapshot(row[0], row[1], row[2], json.loads(row[3]), json.loads(row[4]))

    def count(self, source_id: str | None = None) -> int:
        with self._connect() as con:
            if source_id:
                row = con.execute("SELECT COUNT(*) FROM source_snapshots WHERE source_id=?", (source_id,)).fetchone()
            else:
                row = con.execute("SELECT COUNT(*) FROM source_snapshots").fetchone()
        return int(row[0])
