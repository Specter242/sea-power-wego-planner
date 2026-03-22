from __future__ import annotations

import json
import sqlite3
import tempfile
import textwrap
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

from planner import catalogs as catalog_module
from planner import core
from planner.server import create_server


def request_json(connection: HTTPConnection, method: str, path: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload)
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read().decode("utf-8")
    data = json.loads(raw) if raw else None
    return response.status, data


def write_catalog_files(temp_dir: str) -> dict:
    ammo_path = Path(temp_dir) / catalog_module.DEFAULT_AMMO_DATABASE_NAME
    ammo_path.write_text(
        '{"ships":{"usn_dd_spruance":{"usn_rim-7m":4},"ir_pt_kaivan":{"wp_grad":32}}}',
        encoding="utf-8",
    )
    html_path = Path(temp_dir) / catalog_module.DEFAULT_COST_MATRIX_NAME
    html_path.write_text(
        textwrap.dedent(
            """
            <html><body>
            <tr class='ship-row' data-search='usn_dd_spruance spruance destroyer' data-role='Destroyer' data-name='Spruance' data-base='1000' data-weapons='300' data-total='1300'>
              <td><b>Spruance</b><div class='small'>usn_dd_spruance</div></td>
              <td><span class='badge'>Destroyer</span></td>
              <td>AN/SPS-40</td>
              <td class='num'>1000</td>
              <td class='num'>300</td>
              <td class='num'><b>1300</b></td>
              <td><div class='small'>Fleet escort.</div><details><summary>Show loadout pricing</summary><table class='loadout-table'>
                <tr><th>Weapon</th><th>ID</th><th class='num'>Qty</th><th>Basis</th><th class='num'>Unit Price</th><th class='num'>Extended</th></tr>
                <tr><td>RIM-7M</td><td class='small'>usn_rim-7m</td><td class='num'>4</td><td>each</td><td class='num'>100</td><td class='num'>400</td></tr>
              </table></details></td>
            </tr>
            <tr class='ship-row' data-search='ir_pt_kaivan kaivan patrol' data-role='Patrol' data-name='Kaivan' data-base='200' data-weapons='100' data-total='300'>
              <td><b>Kaivan</b><div class='small'>ir_pt_kaivan</div></td>
              <td><span class='badge'>Patrol</span></td>
              <td>Surface search radar</td>
              <td class='num'>200</td>
              <td class='num'>100</td>
              <td class='num'><b>300</b></td>
              <td><div class='small'>Small patrol craft.</div></td>
            </tr>
            <tr class='weapon-row'><td>RIM-7M</td><td class='small'>usn_rim-7m</td><td>each</td><td class='num'>100</td></tr>
            <tr class='weapon-row'><td>Grad</td><td class='small'>wp_grad</td><td>per 10</td><td class='num'>12</td></tr>
            </body></html>
            """
        ).strip(),
        encoding="utf-8",
    )
    save_path = Path(temp_dir) / "catalog_reference.sav"
    save_path.write_text(save_text(), encoding="utf-8")
    return {"ammo_database": str(ammo_path), "cost_matrix_html": str(html_path), "sav_files": [str(save_path)]}


def save_text() -> str:
    return textwrap.dedent(
        """
        [Mission]
        Taskforce1_Formation1=Taskforce1Vessel1|Blue Group|Loose|1.5
        [Taskforce1Vessel1]
        Type=usn_dd_spruance
        VariantReference=Variant1
        Name=USS Alpha
        GeoPosition=10,20,0
        VelocityInKnots=20
        Heading=90
        Telegraph=2
        [Taskforce2Vessel1]
        Type=ir_pt_kaivan
        VariantReference=Variant1
        Name=IRIS One
        GeoPosition=11,21,0
        VelocityInKnots=15
        Heading=270
        Telegraph=2
        """
    ).strip()


def example_seed(catalog_paths: dict) -> dict:
    return {
        "scenario_name": "HTTP Campaign",
        "turn_duration_minutes": 60,
        "catalog_paths": catalog_paths,
        "sides": {
            "Blue": {"resources": 100, "spawn_point": {"lat": 0.0, "lon": 0.0}},
            "Red": {"resources": 100, "spawn_point": {"lat": 0.5, "lon": 0.5}},
        },
        "fleets": [
            {
                "id": "blue_1",
                "name": "Blue Fleet",
                "side": "Blue",
                "lat": 0.0,
                "lon": 0.0,
                "speed_kts": 20.0,
                "composition": [{"name": "USS Alpha", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"}],
            },
            {
                "id": "red_1",
                "name": "Red Fleet",
                "side": "Red",
                "lat": 0.5,
                "lon": 0.5,
                "speed_kts": 15.0,
                "composition": [{"name": "IRIS One", "sea_power_type": "ir_pt_kaivan", "variant_reference": "Variant1"}],
            },
        ],
    }


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_catalog_dir = catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR
        catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = Path(self.temp_dir.name)
        self.catalog_paths = write_catalog_files(self.temp_dir.name)
        self.campaign_path = Path(self.temp_dir.name) / "current_campaign.json"
        self.legacy_db_path = Path(self.temp_dir.name) / "planner.sqlite3"
        self.server = None
        self.connection = None
        self.thread = None
        self.start_server()

    def tearDown(self):
        self.stop_server()
        catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = self.original_catalog_dir
        self.temp_dir.cleanup()

    def start_server(self):
        self.server = create_server("127.0.0.1", 0, self.campaign_path, legacy_db_path=self.legacy_db_path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.connection = HTTPConnection("127.0.0.1", self.port, timeout=10)

    def stop_server(self):
        if self.connection is not None:
            self.connection.close()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)

    def restart_server(self):
        self.stop_server()
        self.server = None
        self.connection = None
        self.thread = None
        self.start_server()

    def seed_campaign(self, seed: dict):
        self.server.store.save_state(core.create_session_state(seed))

    def test_blank_campaign_bootstrap_view(self):
        status, view = request_json(self.connection, "GET", "/api/campaign/view?role=Admin")

        self.assertEqual(status, 200)
        self.assertEqual(view["scenario_name"], "New Campaign")
        self.assertEqual(len(view["ports"]), 2)
        self.assertEqual(len(view["ships"]), 0)
        self.assertEqual(len(view["fleets"]), 0)
        self.assertIn("ship_options", view["catalogs"])
        self.assertTrue(view["catalogs"]["status"]["available"])
        self.assertGreater(len(view["catalogs"]["ship_options"]), 0)

        status, blue_view = request_json(self.connection, "GET", "/api/campaign/view?role=Blue")
        self.assertEqual(status, 200)
        self.assertEqual(len(blue_view["ports"]), 1)
        self.assertEqual(blue_view["ports"][0]["side"], "Blue")
        self.assertIn("ship_options", blue_view["catalogs"])
        saved_state = json.loads(self.campaign_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_state["catalog_paths"]["ammo_database"], self.catalog_paths["ammo_database"])

    def test_legacy_sqlite_bootstrap_and_json_precedence(self):
        self.stop_server()
        if self.campaign_path.exists():
            self.campaign_path.unlink()
        state = core.create_session_state(example_seed(self.catalog_paths))
        state["scenario_name"] = "Legacy Campaign"
        connection = sqlite3.connect(self.legacy_db_path)
        try:
            connection.execute("CREATE TABLE sessions (session_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, created_at TEXT NOT NULL)")
            connection.execute(
                "INSERT INTO sessions (session_id, state_json, created_at) VALUES (?, ?, ?)",
                ("legacy", json.dumps(state), state["created_at"]),
            )
            connection.commit()
        finally:
            connection.close()

        self.start_server()
        status, view = request_json(self.connection, "GET", "/api/campaign/view?role=Admin")
        self.assertEqual(status, 200)
        self.assertEqual(view["scenario_name"], "Legacy Campaign")

        self.stop_server()
        json_state = core.create_blank_campaign_state({"scenario_name": "Json Campaign", "catalog_paths": self.catalog_paths})
        self.campaign_path.write_text(json.dumps(json_state), encoding="utf-8")
        self.start_server()
        status, view = request_json(self.connection, "GET", "/api/campaign/view?role=Admin")
        self.assertEqual(status, 200)
        self.assertEqual(view["scenario_name"], "Json Campaign")

    def test_import_save_endpoint_and_admin_view(self):
        save_path = Path(self.temp_dir.name) / "import.sav"
        save_path.write_text(save_text(), encoding="utf-8")
        status, preview = request_json(
            self.connection,
            "POST",
            "/api/campaign/import-save/preview?role=Admin",
            {
                "save_path": str(save_path),
                "scenario_name": "Imported HTTP",
                "turn_duration_minutes": 60,
                "catalog_paths": self.catalog_paths,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(preview["preview"]["scenario_name"], "Imported HTTP")
        blue_fleet = next(group for group in preview["preview"]["sides"] if group["side"] == "Blue")["fleets"][0]
        selected_ship_id = blue_fleet["ships"][0]["candidate_id"]

        status, created = request_json(
            self.connection,
            "POST",
            "/api/campaign/import-save?role=Admin",
            {
                "save_path": str(save_path),
                "scenario_name": "Imported HTTP",
                "turn_duration_minutes": 60,
                "catalog_paths": self.catalog_paths,
                "selected_ship_ids": [selected_ship_id],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(created["imported"]["ship_count"], 1)
        self.assertEqual(created["campaign"]["scenario_name"], "New Campaign")

        status, blue_view = request_json(self.connection, "GET", "/api/campaign/view?role=Blue")
        self.assertEqual(status, 200)
        self.assertEqual(len(blue_view["fleets"]), 1)
        self.assertEqual(len(blue_view["ships"]), 1)
        self.assertIn("nation_label", blue_view["catalogs"]["ship_options"][0])
        self.assertIn("weapon_entries", blue_view["fleets"][0]["ships"][0])
        self.assertIn("class_display_name", blue_view["fleets"][0]["ships"][0])
        self.assertIn("class_summary_note", blue_view["fleets"][0]["ships"][0])
        self.assertIn("class_group", blue_view["catalogs"]["ship_options"][0])

    def test_role_permissions_and_primary_logistics_flow(self):
        status, _ = request_json(
            self.connection,
            "POST",
            "/api/campaign/reset?role=Admin",
            {"catalog_paths": self.catalog_paths},
        )
        self.assertEqual(status, 200)

        status, error = request_json(
            self.connection,
            "POST",
            "/api/ships?role=Red",
            {"side": "Blue", "name": "Intrusion", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        self.assertEqual(status, 403)
        self.assertIn("Role does not match", error["error"])

        status, created_ship = request_json(
            self.connection,
            "POST",
            "/api/ships?role=Blue",
            {"side": "Blue", "name": "USS Alpha", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        self.assertEqual(status, 200)
        first_ship_id = created_ship["ship"]["id"]

        status, created_ship = request_json(
            self.connection,
            "POST",
            "/api/ships?role=Blue",
            {"side": "Blue", "name": "USS Bravo", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        self.assertEqual(status, 200)
        second_ship_id = created_ship["ship"]["id"]

        status, fleet_one = request_json(
            self.connection,
            "POST",
            "/api/fleets?role=Blue",
            {"side": "Blue", "name": "Blue One", "port_id": "blue_port_1", "ship_ids": [first_ship_id]},
        )
        self.assertEqual(status, 200)
        fleet_one_id = fleet_one["fleet"]["id"]

        status, fleet_two = request_json(
            self.connection,
            "POST",
            "/api/fleets?role=Blue",
            {"side": "Blue", "name": "Blue Two", "port_id": "blue_port_1", "ship_ids": [second_ship_id]},
        )
        self.assertEqual(status, 200)
        fleet_two_id = fleet_two["fleet"]["id"]

        status, merged = request_json(
            self.connection,
            "POST",
            f"/api/fleets/{fleet_two_id}/merge?role=Blue",
            {"target_fleet_id": fleet_one_id},
        )
        self.assertEqual(status, 200)
        self.assertEqual(merged["fleet"]["id"], fleet_one_id)

        status, detached = request_json(
            self.connection,
            "POST",
            f"/api/ships/{second_ship_id}/transfer?role=Blue",
            {"new_fleet_name": "Detached Bravo"},
        )
        self.assertEqual(status, 200)
        detached_fleet_id = detached["ship"]["fleet_id"]

        status, reserved = request_json(
            self.connection,
            "POST",
            f"/api/ships/{second_ship_id}/transfer?role=Blue",
            {"to_reserve": True},
        )
        self.assertEqual(status, 200)
        self.assertIsNone(reserved["ship"]["fleet_id"])

        state = self.server.store.get_state()
        first_ship = core.ship_by_id(state, first_ship_id)
        first_ship["loadout"] = {"usn_rim-7m": 1}
        first_ship["subsystems"] = [
            {
                "id": "radar",
                "name": "Radar",
                "category": "sensor",
                "current_integrity": 5,
                "nominal_integrity": 10,
                "repairable": True,
                "state": "damaged",
            }
        ]
        first_ship["class_costs"] = {"base_hull": 1000}
        state["side_state"]["Blue"]["resources"] = 2000
        self.server.store.save_state(state)

        status, rearm = request_json(
            self.connection,
            "POST",
            f"/api/ships/{first_ship_id}/rearm?role=Blue",
            {"mode": "full"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(rearm["job"]["ship_id"], first_ship_id)

        status, repair = request_json(
            self.connection,
            "POST",
            f"/api/ships/{first_ship_id}/repair?role=Blue",
            {"subsystem_id": "radar"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(repair["job"]["ship_id"], first_ship_id)

        status, undocked = request_json(
            self.connection,
            "POST",
            f"/api/fleets/{fleet_one_id}/dock?role=Blue",
            {"action": "undock"},
        )
        self.assertEqual(status, 200)
        self.assertIsNone(undocked["fleet"]["docked_port_id"])

        status, submission = request_json(
            self.connection,
            "POST",
            "/api/turns/Blue?role=Blue",
            {"turn_number": 1, "orders": [{"fleet_id": fleet_one_id, "waypoints": [{"lat": 0.2, "lon": 0.2}]}]},
        )
        self.assertEqual(status, 200)
        self.assertFalse(submission["resolved"])
        self.assertFalse(submission["both_ready"])

        status, submission = request_json(
            self.connection,
            "POST",
            "/api/turns/Red?role=Red",
            {"turn_number": 1, "orders": []},
        )
        self.assertEqual(status, 200)
        self.assertTrue(submission["both_ready"])

        status, resolved = request_json(self.connection, "POST", "/api/campaign/resolve?role=Admin", {})
        self.assertEqual(status, 200)
        self.assertTrue(resolved["resolved"])
        self.assertEqual(resolved["next_turn"], 2)

        status, blue_view = request_json(self.connection, "GET", "/api/campaign/view?role=Blue")
        self.assertEqual(status, 200)
        self.assertTrue(all(port["side"] == "Blue" for port in blue_view["ports"]))

    def test_bulk_ship_create_returns_multiple_records(self):
        status, _ = request_json(
            self.connection,
            "POST",
            "/api/campaign/reset?role=Admin",
            {"catalog_paths": self.catalog_paths},
        )
        self.assertEqual(status, 200)

        status, created = request_json(
            self.connection,
            "POST",
            "/api/ships?role=Blue",
            {"side": "Blue", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1", "quantity": 3},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(created["ships"]), 3)
        self.assertEqual([ship["name"] for ship in created["ships"]], ["Spruance 1", "Spruance 2", "Spruance 3"])

    def test_view_exposes_ship_action_options_and_fleet_movement_flags(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})
        first = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        second = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        core.create_fleet_for_side(state, "Blue", {"name": "Screen", "port_id": "blue_port_1", "ship_ids": [first["id"]]})
        self.server.store.save_state(state)

        status, blue_view = request_json(self.connection, "GET", "/api/campaign/view?role=Blue")
        self.assertEqual(status, 200)
        reserve_ship = next(ship for ship in blue_view["ships"] if ship["id"] == second["id"])
        self.assertTrue(reserve_ship["can_transfer"])
        self.assertIn("eligible_transfer_fleets", reserve_ship)
        self.assertIn("can_dock", reserve_ship)
        self.assertIn("movement_disabled_reason", blue_view["fleets"][0])
        self.assertFalse(blue_view["fleets"][0]["can_draft_movement"])
        self.assertIn("Docked fleets", blue_view["fleets"][0]["movement_disabled_reason"])

        status, admin_view = request_json(self.connection, "GET", "/api/campaign/view?role=Admin")
        self.assertEqual(status, 200)
        self.assertFalse(admin_view["fleets"][0]["can_draft_movement"])

    def test_ship_dock_transfer_splits_ship_into_singleton_fleet(self):
        state = core.create_blank_campaign_state(
            {
                "catalog_paths": self.catalog_paths,
                "ports": [
                    {"id": "blue_port_1", "side": "Blue", "name": "Blue Base", "lat": 0.0, "lon": 0.0, "radius_nm": 5.0},
                    {"id": "blue_port_2", "side": "Blue", "name": "Forward Base", "lat": 0.0, "lon": 0.03, "radius_nm": 5.0},
                    {"id": "red_port_1", "side": "Red", "name": "Red Base", "lat": 0.0, "lon": 0.5, "radius_nm": 5.0},
                ],
            }
        )
        first = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        second = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        fleet = core.create_fleet_for_side(state, "Blue", {"name": "Screen", "port_id": "blue_port_1", "ship_ids": [first["id"], second["id"]]})
        core.dock_fleet(state, fleet["id"], {"action": "undock"})
        self.server.store.save_state(state)

        status, docked = request_json(
            self.connection,
            "POST",
            f"/api/ships/{second['id']}/transfer?role=Blue",
            {"dock_port_id": "blue_port_2", "new_fleet_name": "Detached Dock"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(docked["ship"]["port_id"], "blue_port_2")
        self.assertNotEqual(docked["ship"]["fleet_id"], fleet["id"])

        saved = self.server.store.get_state()
        self.assertEqual(core.fleet_by_id(saved, fleet["id"])["ship_ids"], [first["id"]])
        self.assertEqual(core.fleet_by_id(saved, docked["ship"]["fleet_id"])["docked_port_id"], "blue_port_2")

    def test_port_preview_endpoint_returns_snapped_placement(self):
        with patch("planner.server.core.preview_port_placement", return_value={"side": "Blue", "requested_lat": 1.0, "requested_lon": 2.0, "lat": 1.1, "lon": 2.2, "distance_nm": 0.8, "coastal": True}):
            status, preview = request_json(
                self.connection,
                "POST",
                "/api/ports/preview?role=Blue",
                {"side": "Blue", "lat": 1.0, "lon": 2.0},
            )

        self.assertEqual(status, 200)
        self.assertTrue(preview["placement"]["coastal"])
        self.assertEqual(preview["placement"]["lat"], 1.1)

    def test_import_save_rejects_empty_selection(self):
        save_path = Path(self.temp_dir.name) / "empty-selection.sav"
        save_path.write_text(save_text(), encoding="utf-8")

        status, error = request_json(
            self.connection,
            "POST",
            "/api/campaign/import-save?role=Admin",
            {
                "save_path": str(save_path),
                "catalog_paths": self.catalog_paths,
                "selected_ship_ids": [],
                "selected_fleet_ids": [],
            },
        )

        self.assertEqual(status, 400)
        self.assertIn("Select at least one ship", error["error"])

    def test_create_ship_bumps_duplicate_names_per_side(self):
        status, _ = request_json(
            self.connection,
            "POST",
            "/api/campaign/reset?role=Admin",
            {"catalog_paths": self.catalog_paths},
        )
        self.assertEqual(status, 200)

        status, first = request_json(
            self.connection,
            "POST",
            "/api/ships?role=Blue",
            {"side": "Blue", "name": "Spruance 1", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(first["ship"]["name"], "Spruance 1")

        status, second = request_json(
            self.connection,
            "POST",
            "/api/ships?role=Blue",
            {"side": "Blue", "name": "Spruance 1", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(second["ship"]["name"], "Spruance 2")

        status, red = request_json(
            self.connection,
            "POST",
            "/api/ships?role=Red",
            {"side": "Red", "name": "Spruance 1", "sea_power_type": "usn_dd_spruance", "port_id": "red_port_1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(red["ship"]["name"], "Spruance 1")

    def test_admin_can_update_side_economy_endpoint(self):
        status, response = request_json(
            self.connection,
            "POST",
            "/api/sides/Blue?role=Admin",
            {"resources": 240, "income_per_turn": 11},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["side"]["resources"], 240)
        self.assertEqual(response["side"]["income_per_turn"], 11)

        status, error = request_json(
            self.connection,
            "POST",
            "/api/sides/Blue?role=Blue",
            {"resources": 999},
        )
        self.assertEqual(status, 403)
        self.assertIn("Admin role required", error["error"])

    def test_missing_default_catalog_reports_unavailable_and_blocks_creation(self):
        self.stop_server()
        if self.campaign_path.exists():
            self.campaign_path.unlink()
        empty_dir = tempfile.TemporaryDirectory()
        catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = Path(empty_dir.name)
        self.start_server()
        try:
            status, view = request_json(self.connection, "GET", "/api/campaign/view?role=Admin")
            self.assertEqual(status, 200)
            self.assertFalse(view["catalogs"]["status"]["available"])

            status, error = request_json(
                self.connection,
                "POST",
                "/api/ships?role=Blue",
                {"side": "Blue", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
            )
            self.assertEqual(status, 400)
            self.assertIn("Ship catalog is unavailable", error["error"])
        finally:
            self.stop_server()
            empty_dir.cleanup()
            catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = self.original_catalog_dir
            self.start_server()


if __name__ == "__main__":
    unittest.main()
