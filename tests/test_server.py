from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from planner.server import create_server


def request_json(connection: HTTPConnection, method: str, path: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload)
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read().decode("utf-8")
    data = json.loads(raw) if raw else None
    return response.status, data


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "planner.sqlite3"
        self.server = create_server("127.0.0.1", 0, db_path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.connection = HTTPConnection("127.0.0.1", self.port, timeout=10)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp_dir.cleanup()

    def test_session_creation_view_and_submission_flow(self):
        seed = {
            "scenario_name": "HTTP Duel",
            "turn_duration_minutes": 60,
            "fleets": [
                {
                    "id": "blue_1",
                    "sp_id": "BLUE_1",
                    "name": "Blue Fleet",
                    "side": "Blue",
                    "unit_type": "Surface",
                    "lat": 0.0,
                    "lon": 0.0,
                    "heading_deg": 0.0,
                    "speed_kts": 20.0,
                    "detection_radius_nm": 100.0,
                },
                {
                    "id": "red_1",
                    "sp_id": "RED_1",
                    "name": "Red Fleet",
                    "side": "Red",
                    "unit_type": "Surface",
                    "lat": 0.0,
                    "lon": 2.0,
                    "heading_deg": 180.0,
                    "speed_kts": 20.0,
                    "detection_radius_nm": 100.0,
                },
            ],
        }
        status, created = request_json(self.connection, "POST", "/sessions", seed)
        self.assertEqual(status, 201)

        session_id = created["session_id"]
        blue_token = created["blue_token"]
        red_token = created["red_token"]

        status, blue_view = request_json(
            self.connection,
            "GET",
            f"/sessions/{session_id}/view?token={blue_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(blue_view["side"], "Blue")

        status, error = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/turns/Red?token={blue_token}",
            {"turn_number": 1, "orders": []},
        )
        self.assertEqual(status, 403)
        self.assertIn("Token does not match", error["error"])

        status, submit_blue = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/turns/Blue?token={blue_token}",
            {"turn_number": 1, "orders": []},
        )
        self.assertEqual(status, 200)
        self.assertFalse(submit_blue["resolved"])

        status, submit_red = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/turns/Red?token={red_token}",
            {"turn_number": 1, "orders": []},
        )
        self.assertEqual(status, 200)
        self.assertTrue(submit_red["resolved"])


if __name__ == "__main__":
    unittest.main()
