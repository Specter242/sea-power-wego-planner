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
            "sides": {
                "Blue": {
                    "resources": 30,
                    "spawn_point": {"lat": 1.0, "lon": 1.5},
                    "build_catalog": [
                        {
                            "id": "blue_patrol",
                            "name": "Blue Patrol",
                            "cost": 12,
                            "unit_type": "Surface",
                            "sea_power_type": "usn_dd_spruance",
                            "variant_reference": "Variant1",
                            "speed_kts": 20,
                            "detection_radius_nm": 100,
                        }
                    ],
                },
                "Red": {"resources": 20},
            },
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
        self.assertEqual(blue_view["economy"]["resources"], 30)

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

        status, built = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/builds/Blue?token={blue_token}",
            {"template_id": "blue_patrol"},
        )
        self.assertEqual(status, 400)

        status, submit_red = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/turns/Red?token={red_token}",
            {"turn_number": 1, "orders": []},
        )
        self.assertEqual(status, 200)
        self.assertTrue(submit_red["resolved"])

    def test_admin_view_and_fleet_edit_flow(self):
        seed = {
            "scenario_name": "Admin Test",
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
        admin_token = created["admin_token"]
        blue_token = created["blue_token"]

        status, admin_view = request_json(
            self.connection,
            "GET",
            f"/sessions/{session_id}/admin/view?admin_token={admin_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(admin_view["role"], "admin")
        self.assertEqual(len(admin_view["fleets"]), 2)
        self.assertIn("Blue", admin_view["side_state"])

        status, error = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/admin/fleets/blue_1?admin_token={blue_token}",
            {"lat": 1.5},
        )
        self.assertEqual(status, 403)
        self.assertIn("Admin token required", error["error"])

        status, update = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/admin/fleets/blue_1?admin_token={admin_token}",
            {"lat": 1.5, "lon": 3.25, "heading_deg": 45, "speed_kts": 25},
        )
        self.assertEqual(status, 200)
        self.assertAlmostEqual(update["fleet"]["lat"], 1.5, places=3)
        self.assertAlmostEqual(update["fleet"]["lon"], 3.25, places=3)
        self.assertEqual(update["fleet"]["heading_deg"], 45.0)
        self.assertEqual(update["fleet"]["speed_kts"], 25.0)

    def test_player_build_flow_spends_resources_and_creates_fleet(self):
        seed = {
            "scenario_name": "Build Test",
            "turn_duration_minutes": 60,
            "sides": {
                "Blue": {
                    "resources": 25,
                    "spawn_point": {"lat": 10.0, "lon": 60.0},
                    "build_catalog": [
                        {
                            "id": "blue_build_1",
                            "name": "Blue Build One",
                            "cost": 15,
                            "unit_type": "Surface",
                            "sea_power_type": "usn_dd_spruance",
                            "variant_reference": "Variant1",
                            "speed_kts": 22,
                            "detection_radius_nm": 90,
                            "composition": [
                                {"name": "USS New One", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                                {"name": "USS New Two", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                            ],
                        }
                    ],
                },
                "Red": {"resources": 10},
            },
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

        status, built = request_json(
            self.connection,
            "POST",
            f"/sessions/{session_id}/builds/Blue?token={blue_token}",
            {"template_id": "blue_build_1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(built["economy"]["resources"], 10)
        self.assertEqual(built["fleet"]["lat"], 10.0)
        self.assertEqual(built["fleet"]["lon"], 60.0)
        self.assertEqual(len(built["fleet"]["composition"]), 2)


if __name__ == "__main__":
    unittest.main()
