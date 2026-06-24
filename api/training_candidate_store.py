from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from api.sqlite_utils import connect_sqlite


class TrainingCandidateStore:
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
                CREATE TABLE IF NOT EXISTS training_candidates (
                    candidate_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    candidate_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'candidate',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doc_id, candidate_type)
                );
                """
            )

    def promote_from_documents(self, document_store, min_quality: float = 0.35, candidate_type: str = "rag") -> dict:
        promoted = 0
        skipped = 0
        with self.connect() as conn:
            for doc in document_store.list_documents(limit=1000):
                allowed = doc.get("allowed_for_training") if candidate_type != "eval" else doc.get("allowed_for_eval")
                if not allowed or doc.get("quality_score", 0) < min_quality:
                    skipped += 1
                    continue
                try:
                    conn.execute(
                        "INSERT INTO training_candidates (candidate_id, doc_id, source_id, quality_score, candidate_type) VALUES (?, ?, ?, ?, ?)",
                        ("cand_" + uuid4().hex[:12], doc["doc_id"], doc["source_id"], doc["quality_score"], candidate_type),
                    )
                    promoted += 1
                except sqlite3.IntegrityError:
                    skipped += 1
        return {"promoted": promoted, "skipped": skipped, "candidate_type": candidate_type, "min_quality": min_quality}

    def list_candidates(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM training_candidates ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def summary(self) -> dict:
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM training_candidates").fetchone()[0]
            rag = conn.execute("SELECT COUNT(*) FROM training_candidates WHERE candidate_type = 'rag'").fetchone()[0]
            eval_count = conn.execute("SELECT COUNT(*) FROM training_candidates WHERE candidate_type = 'eval'").fetchone()[0]
        return {"candidates": total, "rag": rag, "eval": eval_count}
