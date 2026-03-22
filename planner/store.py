from __future__ import annotations

import contextlib
import json
import sqlite3
import threading
from pathlib import Path

from . import core


class LegacySQLiteStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def latest_state(self) -> dict | None:
        if not self.db_path.exists():
            return None
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sessions'"
            ).fetchall()
            if not tables:
                return None
            rows = connection.execute("SELECT state_json, created_at FROM sessions").fetchall()
        finally:
            connection.close()

        newest_state = None
        newest_stamp = ""
        for row in rows:
            try:
                payload = json.loads(row["state_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            updated_at = str(payload.get("updated_at") or row["created_at"] or "")
            if updated_at >= newest_stamp:
                newest_stamp = updated_at
                newest_state = payload
        if newest_state is None:
            return None
        return core.upgrade_state(newest_state)


class JSONCampaignStore:
    def __init__(self, campaign_path: str | Path, legacy_db_path: str | Path | None = None):
        self.campaign_path = Path(campaign_path)
        self.legacy_db_path = Path(legacy_db_path) if legacy_db_path else None
        self.lock = threading.RLock()
        self.campaign_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with self.lock:
            if self.campaign_path.exists():
                state, changed = self._read_campaign()
                if changed:
                    self._write_campaign(state)
            else:
                state = self._bootstrap_state()
                self._write_campaign(state)
            self._state = state

    def _bootstrap_state(self) -> dict:
        if self.legacy_db_path is not None:
            migrated = LegacySQLiteStore(self.legacy_db_path).latest_state()
            if migrated is not None:
                return migrated
        return core.create_blank_campaign_state()

    def _read_campaign(self) -> tuple[dict, bool]:
        raw_text = self.campaign_path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
        original = json.dumps(payload, sort_keys=True)
        upgraded = core.upgrade_state(payload)
        changed = json.dumps(upgraded, sort_keys=True) != original
        return upgraded, changed

    def _write_campaign(self, state: dict) -> None:
        self.campaign_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def get_state(self) -> dict:
        with self.lock:
            self._state, changed = self._read_campaign()
            if changed:
                self._write_campaign(self._state)
            return self._state

    def save_state(self, state: dict) -> None:
        with self.lock:
            state["updated_at"] = core.utc_now()
            self._write_campaign(state)
            self._state = state

    def import_save(self, payload: dict) -> dict:
        with self.lock:
            state = self.get_state()
            result = core.apply_imported_save_selection(state, payload)
            self.save_state(state)
            return result

    def preview_import_save(self, payload: dict) -> dict:
        with self.lock:
            state = self.get_state()
            return core.preview_imported_save(state, payload)

    def reset_campaign(self, payload: dict | None = None) -> dict:
        with self.lock:
            state = core.create_blank_campaign_state(payload or {})
            self.save_state(state)
            return state
