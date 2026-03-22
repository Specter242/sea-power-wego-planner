from __future__ import annotations

import contextlib
import json
import sqlite3
import threading
from pathlib import Path

from . import core


class SQLiteSessionStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.lock = threading.RLock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self.lock, contextlib.closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def create_session(self, seed: dict) -> dict:
        state = core.create_session_state(seed)
        self.save_state(state)
        return state

    def save_state(self, state: dict) -> None:
        with self.lock, contextlib.closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO sessions (session_id, state_json, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id)
                DO UPDATE SET state_json = excluded.state_json
                """,
                (state["session_id"], json.dumps(state), state["created_at"]),
            )
            connection.commit()

    def get_state(self, session_id: str) -> dict | None:
        with self.lock, contextlib.closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT state_json FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["state_json"])

    def session_role_for_token(self, state: dict, token: str) -> str | None:
        if not token:
            return None
        for role, known_token in state["tokens"].items():
            if token == known_token:
                return role
        return None
