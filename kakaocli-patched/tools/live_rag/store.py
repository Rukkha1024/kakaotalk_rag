"""SQLite store for Kakao Live RAG ingestion and retrieval.

Keeps canonical messages, FTS search data, and restart
checkpoint state in one local database.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS messages (
    log_id INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,
    chat_id INTEGER NOT NULL,
    chat_name TEXT,
    sender_id INTEGER NOT NULL,
    sender TEXT,
    text TEXT,
    message_type INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    is_from_me INTEGER NOT NULL,
    raw_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_timestamp
    ON messages (chat_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_messages_sender_timestamp
    ON messages (sender, timestamp);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text,
    sender,
    chat_name,
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS ingest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    batch_size INTEGER NOT NULL,
    inserted_count INTEGER NOT NULL,
    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS live_rag_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


class LiveRAGStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            self._ensure_fts_table(connection)
            self._ensure_checkpoint_state(connection)

    def _ensure_fts_table(self, connection: sqlite3.Connection) -> None:
        row = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'messages_fts'
            """
        ).fetchone()
        sql = row["sql"] if row is not None else None
        if sql and "content=''" not in sql:
            return

        connection.execute("DROP TABLE IF EXISTS messages_fts")
        connection.execute(
            """
            CREATE VIRTUAL TABLE messages_fts USING fts5(
                text,
                sender,
                chat_name,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO messages_fts (rowid, text, sender, chat_name)
            SELECT
                log_id,
                COALESCE(text, ''),
                COALESCE(sender, ''),
                COALESCE(chat_name, '')
            FROM messages
            """
        )
        connection.commit()

    def ingest_messages(self, messages: list[dict[str, Any]], source: str = "webhook") -> dict[str, int]:
        normalized = [self._normalize_message(message) for message in messages]
        if not normalized:
            return {"accepted": 0, "inserted": 0}

        log_ids = [message["log_id"] for message in normalized]
        with self._connect() as connection:
            current_checkpoint = self._get_int_state(connection, "last_ingested_log_id")
            existing = {
                row["log_id"]
                for row in connection.execute(
                    f"SELECT log_id FROM messages WHERE log_id IN ({','.join('?' for _ in log_ids)})",
                    log_ids,
                )
            }
            for message in normalized:
                connection.execute(
                    """
                    INSERT INTO messages (
                        log_id,
                        event_type,
                        chat_id,
                        chat_name,
                        sender_id,
                        sender,
                        text,
                        message_type,
                        timestamp,
                        is_from_me,
                        raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(log_id) DO UPDATE SET
                        event_type = excluded.event_type,
                        chat_id = excluded.chat_id,
                        chat_name = excluded.chat_name,
                        sender_id = excluded.sender_id,
                        sender = excluded.sender,
                        text = excluded.text,
                        message_type = excluded.message_type,
                        timestamp = excluded.timestamp,
                        is_from_me = excluded.is_from_me,
                        raw_json = excluded.raw_json
                    """,
                    (
                        message["log_id"],
                        message["type"],
                        message["chat_id"],
                        message.get("chat_name"),
                        message["sender_id"],
                        message.get("sender"),
                        message.get("text"),
                        message["message_type"],
                        message["timestamp"],
                        int(message["is_from_me"]),
                        json.dumps(message, ensure_ascii=False, sort_keys=True),
                    ),
                )
                connection.execute("DELETE FROM messages_fts WHERE rowid = ?", (message["log_id"],))
                connection.execute(
                    """
                    INSERT INTO messages_fts (rowid, text, sender, chat_name)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        message["log_id"],
                        message.get("text") or "",
                        message.get("sender") or "",
                        message.get("chat_name") or "",
                    ),
                )

            inserted = len([log_id for log_id in log_ids if log_id not in existing])
            connection.execute(
                """
                INSERT INTO ingest_runs (source, batch_size, inserted_count)
                VALUES (?, ?, ?)
                """,
                (source, len(normalized), inserted),
            )
            next_checkpoint = max(log_ids) if current_checkpoint is None else max(current_checkpoint, max(log_ids))
            self._set_state(connection, "last_ingested_log_id", str(next_checkpoint))
            self._set_state(connection, "last_ingest_source", source)
            connection.commit()

        return {"accepted": len(normalized), "inserted": inserted}

    def stats(self) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS message_count,
                    COUNT(DISTINCT chat_id) AS chat_count,
                    MIN(timestamp) AS oldest_timestamp,
                    MAX(timestamp) AS newest_timestamp
                FROM messages
                """
            ).fetchone()
            stats = dict(row) if row is not None else {}
            stats["last_ingested_log_id"] = self._get_int_state(connection, "last_ingested_log_id")
            stats["last_ingest_source"] = self._get_state(connection, "last_ingest_source")
            return stats

    def list_messages(
        self,
        *,
        limit: int = 50,
        chat_id: int | None = None,
        speaker: str | None = None,
        since_days: float | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if chat_id is not None:
            clauses.append("chat_id = ?")
            params.append(chat_id)
        if speaker:
            clauses.append("sender = ?")
            params.append(speaker)
        if since_days is not None:
            cutoff = self._utc_now() - timedelta(days=since_days)
            clauses.append("timestamp >= ?")
            params.append(self._isoformat(cutoff))

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    event_type AS type,
                    log_id,
                    chat_id,
                    chat_name,
                    sender_id,
                    sender,
                    text,
                    message_type,
                    timestamp,
                    is_from_me
                FROM messages
                {where_clause}
                ORDER BY timestamp DESC, log_id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            return [
                {
                    "type": row["type"],
                    "log_id": row["log_id"],
                    "chat_id": row["chat_id"],
                    "chat_name": row["chat_name"],
                    "sender_id": row["sender_id"],
                    "sender": row["sender"],
                    "text": row["text"],
                    "message_type": row["message_type"],
                    "timestamp": row["timestamp"],
                    "is_from_me": bool(row["is_from_me"]),
                }
                for row in rows
            ]

    def retrieve(
        self,
        *,
        query: str,
        limit: int = 8,
        chat_id: int | None = None,
        speaker: str | None = None,
        context_before: int = 2,
        context_after: int = 2,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        try:
            hits = self._fts_hits(
                query=query,
                limit=limit,
                chat_id=chat_id,
                speaker=speaker,
                context_before=context_before,
                context_after=context_after,
            )
        except sqlite3.OperationalError:
            hits = self._like_hits(
                query=query,
                limit=limit,
                chat_id=chat_id,
                speaker=speaker,
                context_before=context_before,
                context_after=context_after,
            )

        return [
            {
                "score": hit["score"],
                "message": self._serialize_row(hit["message"]),
                "context_before": [self._serialize_row(row) for row in hit["context_before"]],
                "context_after": [self._serialize_row(row) for row in hit["context_after"]],
            }
            for hit in hits
        ]

    def _fts_hits(
        self,
        *,
        query: str,
        limit: int,
        chat_id: int | None,
        speaker: str | None,
        context_before: int,
        context_after: int,
    ) -> list[dict[str, Any]]:
        clauses = ["messages_fts MATCH ?"]
        params: list[Any] = [query]

        if chat_id is not None:
            clauses.append("m.chat_id = ?")
            params.append(chat_id)
        if speaker:
            clauses.append("m.sender = ?")
            params.append(speaker)
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    m.*,
                    bm25(messages_fts) AS score
                FROM messages_fts
                JOIN messages AS m ON m.log_id = messages_fts.rowid
                WHERE {' AND '.join(clauses)}
                ORDER BY score, m.timestamp DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            return [
                self._expand_hit(
                    connection,
                    row,
                    context_before=context_before,
                    context_after=context_after,
                )
                for row in rows
            ]

    def _like_hits(
        self,
        *,
        query: str,
        limit: int,
        chat_id: int | None,
        speaker: str | None,
        context_before: int,
        context_after: int,
    ) -> list[dict[str, Any]]:
        clauses = ["COALESCE(text, '') LIKE ?"]
        params: list[Any] = [f"%{query}%"]

        if chat_id is not None:
            clauses.append("chat_id = ?")
            params.append(chat_id)
        if speaker:
            clauses.append("sender = ?")
            params.append(speaker)
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *, 0.0 AS score
                FROM messages
                WHERE {' AND '.join(clauses)}
                ORDER BY timestamp DESC, log_id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            return [
                self._expand_hit(
                    connection,
                    row,
                    context_before=context_before,
                    context_after=context_after,
                )
                for row in rows
            ]

    def _expand_hit(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        *,
        context_before: int,
        context_after: int,
    ) -> dict[str, Any]:
        current_log_id = row["log_id"]
        chat_id = row["chat_id"]
        before_rows = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE chat_id = ? AND log_id < ?
            ORDER BY log_id DESC
            LIMIT ?
            """,
            (chat_id, current_log_id, context_before),
        ).fetchall()
        after_rows = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE chat_id = ? AND log_id > ?
            ORDER BY log_id ASC
            LIMIT ?
            """,
            (chat_id, current_log_id, context_after),
        ).fetchall()

        return {
            "score": float(row["score"]),
            "message": row,
            "context_before": list(reversed(before_rows)),
            "context_after": list(after_rows),
        }

    def _normalize_message(self, message: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": str(message.get("type", "message")),
            "log_id": int(message["log_id"]),
            "chat_id": int(message["chat_id"]),
            "chat_name": message.get("chat_name"),
            "sender_id": int(message.get("sender_id", 0)),
            "sender": message.get("sender"),
            "text": message.get("text"),
            "message_type": int(message.get("message_type", -1)),
            "timestamp": str(message["timestamp"]),
            "is_from_me": bool(message.get("is_from_me", False)),
        }

    def _serialize_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "type": row["event_type"],
            "log_id": row["log_id"],
            "chat_id": row["chat_id"],
            "chat_name": row["chat_name"],
            "sender_id": row["sender_id"],
            "sender": row["sender"],
            "text": row["text"],
            "message_type": row["message_type"],
            "timestamp": row["timestamp"],
            "is_from_me": bool(row["is_from_me"]),
        }

    def last_ingested_log_id(self) -> int | None:
        with self._connect() as connection:
            return self._get_int_state(connection, "last_ingested_log_id")

    def _ensure_checkpoint_state(self, connection: sqlite3.Connection) -> None:
        if self._get_int_state(connection, "last_ingested_log_id") is not None:
            return
        max_log_id = self._max_log_id(connection)
        if max_log_id is not None:
            self._set_state(connection, "last_ingested_log_id", str(max_log_id))

    def _max_log_id(self, connection: sqlite3.Connection) -> int | None:
        row = connection.execute("SELECT MAX(log_id) AS max_log_id FROM messages").fetchone()
        if row is None or row["max_log_id"] is None:
            return None
        return int(row["max_log_id"])

    def _get_state(self, connection: sqlite3.Connection, key: str) -> str | None:
        row = connection.execute(
            "SELECT value FROM live_rag_state WHERE key = ?",
            (key,),
        ).fetchone()
        return None if row is None else str(row["value"])

    def _get_int_state(self, connection: sqlite3.Connection, key: str) -> int | None:
        value = self._get_state(connection, key)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _set_state(self, connection: sqlite3.Connection, key: str, value: str) -> None:
        connection.execute(
            """
            INSERT INTO live_rag_state (key, value, updated_at)
            VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value),
        )

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _isoformat(value: datetime) -> str:
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
