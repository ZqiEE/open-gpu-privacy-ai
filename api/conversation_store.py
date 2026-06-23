from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Literal

Role = Literal["system", "user", "assistant"]


class ConversationStore:
    def __init__(self, path: str | Path = "runtime_data/conversations.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                );
                """
            )

    def create_conversation(self, user_id: str = "local", title: str = "New chat") -> dict:
        now = time.time()
        conversation_id = f"conv_{uuid.uuid4().hex[:16]}"
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, title, user_id, now, now),
            )
        return self.get_conversation(conversation_id) or {}

    def get_or_create(self, conversation_id: str | None, user_id: str, title: str = "New chat") -> dict:
        if conversation_id:
            existing = self.get_conversation(conversation_id)
            if existing:
                return existing
        return self.create_conversation(user_id=user_id, title=title)

    def get_conversation(self, conversation_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        return dict(row) if row else None

    def list_conversations(self, user_id: str = "local", limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_message(self, conversation_id: str, role: Role, content: str, source: str = "local", model_id: str = "ailovanta-local") -> dict:
        now = time.time()
        message_id = f"msg_{uuid.uuid4().hex[:16]}"
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO conversation_messages (id, conversation_id, role, content, source, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (message_id, conversation_id, role, content, source, model_id, now),
            )
            conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        return self.get_message(message_id) or {}

    def get_message(self, message_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM conversation_messages WHERE id = ?", (message_id,)).fetchone()
        return dict(row) if row else None

    def list_messages(self, conversation_id: str, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM conversation_messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
                (conversation_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_conversation(self, conversation_id: str) -> bool:
        with self.connect() as conn:
            found = conn.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
            if not found:
                return False
            conn.execute("DELETE FROM conversation_messages WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        return True

    def status(self) -> dict:
        with self.connect() as conn:
            conversations = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            messages = conn.execute("SELECT COUNT(*) FROM conversation_messages").fetchone()[0]
        return {"conversations": conversations, "messages": messages, "store": "sqlite", "path": str(self.path)}
