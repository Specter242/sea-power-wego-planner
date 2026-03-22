from __future__ import annotations

import contextlib
import json
import secrets
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    scenario_name TEXT NOT NULL,
                    seed_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
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

    def list_scenarios(self) -> list[dict]:
        with self.lock, contextlib.closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT scenario_id, scenario_name, created_at, updated_at
                FROM scenarios
                ORDER BY updated_at DESC, scenario_name COLLATE NOCASE ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def create_scenario(self, seed: dict) -> dict:
        normalized_seed = core.normalize_seed(seed)
        now = core.utc_now()
        scenario = {
            "scenario_id": self._generate_scenario_id(),
            "scenario_name": normalized_seed["scenario_name"],
            "seed_json": json.dumps(normalized_seed),
            "created_at": now,
            "updated_at": now,
        }
        with self.lock, contextlib.closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO scenarios (scenario_id, scenario_name, seed_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    scenario["scenario_id"],
                    scenario["scenario_name"],
                    scenario["seed_json"],
                    scenario["created_at"],
                    scenario["updated_at"],
                ),
            )
            connection.commit()
        return self.get_scenario(scenario["scenario_id"])

    def get_scenario(self, scenario_id: str) -> dict | None:
        with self.lock, contextlib.closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT scenario_id, scenario_name, seed_json, created_at, updated_at
                FROM scenarios
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            ).fetchone()
        if row is None:
            return None
        scenario = dict(row)
        scenario["seed"] = json.loads(scenario.pop("seed_json"))
        return scenario

    def update_scenario(self, scenario_id: str, seed: dict) -> dict | None:
        normalized_seed = core.normalize_seed(seed)
        now = core.utc_now()
        with self.lock, contextlib.closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                UPDATE scenarios
                SET scenario_name = ?, seed_json = ?, updated_at = ?
                WHERE scenario_id = ?
                """,
                (
                    normalized_seed["scenario_name"],
                    json.dumps(normalized_seed),
                    now,
                    scenario_id,
                ),
            )
            connection.commit()
        if cursor.rowcount == 0:
            return None
        return self.get_scenario(scenario_id)

    def delete_scenario(self, scenario_id: str) -> bool:
        with self.lock, contextlib.closing(self._connect()) as connection:
            cursor = connection.execute("DELETE FROM scenarios WHERE scenario_id = ?", (scenario_id,))
            connection.commit()
        return cursor.rowcount > 0

    def _generate_scenario_id(self) -> str:
        return secrets.token_hex(6)

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
