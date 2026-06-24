from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite


class WebDocumentStore:
    def __init__(self, path: str | Path = "runtime_data/corpus.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    tags_json TEXT NOT NULL,
                    allowed_for_search INTEGER NOT NULL,
                    allowed_for_training INTEGER NOT NULL,
                    allowed_for_finetune INTEGER NOT NULL,
                    allowed_for_eval INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(content_hash)
                );
                """
            )

    def add_document(self, source: dict[str, Any], processed: dict[str, Any]) -> dict:
        doc_id = "doc_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO documents (
                    doc_id, source_id, url, title, text, content_hash, quality_score, tags_json,
                    allowed_for_search, allowed_for_training, allowed_for_finetune, allowed_for_eval
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    source["source_id"],
                    processed["url"],
                    processed["title"],
                    processed["text"],
                    processed["content_hash"],
                    processed["quality_score"],
                    json.dumps(processed.get("tags", []), ensure_ascii=False),
                    1 if source.get("allowed_for_search") else 0,
                    1 if source.get("allowed_for_training") else 0,
                    1 if source.get("allowed_for_finetune") else 0,
                    1 if source.get("allowed_for_eval") else 0,
                ),
            )
        return self.get_by_hash(processed["content_hash"]) or {}

    def get_by_hash(self, content_hash: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM documents WHERE content_hash = ?", (content_hash,)).fetchone()
        return self._row(dict(row)) if row else None

    def list_documents(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    def summary(self) -> dict:
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            trainable = conn.execute("SELECT COUNT(*) FROM documents WHERE allowed_for_training = 1").fetchone()[0]
            searchable = conn.execute("SELECT COUNT(*) FROM documents WHERE allowed_for_search = 1").fetchone()[0]
            avg_quality = conn.execute("SELECT COALESCE(AVG(quality_score), 0) FROM documents").fetchone()[0]
        return {"documents": total, "searchable": searchable, "trainable": trainable, "average_quality": round(avg_quality, 3)}

    @staticmethod
    def _row(item: dict) -> dict:
        item["tags"] = json.loads(item.pop("tags_json") or "[]")
        for key in ["allowed_for_search", "allowed_for_training", "allowed_for_finetune", "allowed_for_eval"]:
            item[key] = bool(item[key])
        return item
