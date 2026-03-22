from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from planner import catalogs as catalog_module
from planner import core


def write_catalog_files(temp_dir: str) -> dict:
    ammo_path = Path(temp_dir) / catalog_module.DEFAULT_AMMO_DATABASE_NAME
    ammo_path.write_text(
        textwrap.dedent(
            """
            {
              "ships": {
                "usn_dd_spruance": {
                  "usn_rim-7m": 4,
                  "usn_cal_127mm": 200
                },
                "ir_pt_kaivan": {
                  "wp_grad": 32
                }
              }
            }
            """
        ).strip(),
        encoding="utf-8",
    )

    html_path = Path(temp_dir) / catalog_module.DEFAULT_COST_MATRIX_NAME
    html_path.write_text(
        textwrap.dedent(
            """
            <html><body>
            <table>
              <tr class='ship-row' data-search='usn_dd_spruance spruance destroyer aegis escort' data-role='Destroyer' data-name='Spruance' data-base='1000' data-weapons='300' data-total='1300'>
                <td><b>Spruance</b><div class='small'>usn_dd_spruance</div></td>
                <td><span class='badge'>Destroyer</span></td>
                <td>AN/SPS-40, AN/SQS-53</td>
                <td class='num'>1000</td>
                <td class='num'>300</td>
                <td class='num'><b>1300</b></td>
                <td><div class='small'>Flagship escort destroyer.</div><details><summary>Show loadout pricing</summary><table class='loadout-table'>
                  <tr><th>Weapon</th><th>ID</th><th class='num'>Qty</th><th>Basis</th><th class='num'>Unit Price</th><th class='num'>Extended</th></tr>
                  <tr><td>RIM-7M</td><td class='small'>usn_rim-7m</td><td class='num'>4</td><td>each</td><td class='num'>100</td><td class='num'>400</td></tr>
                  <tr><td>127mm ammo</td><td class='small'>usn_cal_127mm</td><td class='num'>200</td><td>per 100</td><td class='num'>50</td><td class='num'>100</td></tr>
                </table></details></td>
              </tr>
              <tr class='ship-row' data-search='ir_pt_kaivan patrol craft' data-role='Patrol' data-name='Kaivan' data-base='200' data-weapons='100' data-total='300'>
                <td><b>Kaivan</b><div class='small'>ir_pt_kaivan</div></td>
                <td><span class='badge'>Patrol</span></td>
                <td>Surface search radar</td>
                <td class='num'>200</td>
                <td class='num'>100</td>
                <td class='num'><b>300</b></td>
                <td><div class='small'>Small patrol craft.</div></td>
              </tr>
            </table>
            <table class='weapon-table'>
              <tr class='weapon-row'><td>RIM-7M</td><td class='small'>usn_rim-7m</td><td>each</td><td class='num'>100</td></tr>
              <tr class='weapon-row'><td>127mm ammo</td><td class='small'>usn_cal_127mm</td><td>per 100</td><td class='num'>50</td></tr>
              <tr class='weapon-row'><td>Grad</td><td class='small'>wp_grad</td><td>per 10</td><td class='num'>12</td></tr>
            </table>
            </body></html>
            """
        ).strip(),
        encoding="utf-8",
    )
    save_path = Path(temp_dir) / "catalog_reference.sav"
    save_path.write_text(imported_save_text(), encoding="utf-8")
    return {
        "ammo_database": str(ammo_path),
        "cost_matrix_html": str(html_path),
        "sav_files": [str(save_path)],
    }


def imported_save_text() -> str:
    return textwrap.dedent(
        """
        [Environment]
        Date=1985,6,26
        Time=10,0
        SeaState=3
        Clouds=Scattered_1
        WindDirection=E
        [Mission]
        Taskforce1_Formation1=Taskforce1Vessel1,Taskforce1Vessel2|Blue Group|Loose|1.5
        [Taskforce1Vessel1]
        Type=usn_dd_spruance
        VariantReference=Variant1
        Name=USS Alpha
        GeoPosition=10,20,0
        VelocityInKnots=20
        Heading=90
        Telegraph=2
        [Taskforce1Vessel1WeaponMagazineSystem1]
        CurrentIntegrity=10
        Ammunition1_Count=2
        [Taskforce1Vessel1WeaponSystemLauncher2]
        CurrentIntegrity=10
        LoadedAmmunitions=usn_rim-7m,1
        [Taskforce1Vessel1SensorSystemRadar3]
        CurrentIntegrity=8
        [Taskforce1Vessel2]
        Type=usn_dd_spruance
        VariantReference=Variant1
        Name=USS Bravo
        GeoPosition=10.1,20.1,0
        VelocityInKnots=20
        Heading=90
        Telegraph=2
        [Taskforce1Vessel2WeaponMagazineSystem1]
        CurrentIntegrity=10
        Ammunition1_Count=4
        [Taskforce1Vessel2WeaponSystemGun2]
        CurrentIntegrity=10
        LoadedAmmunitions=usn_cal_127mm,20
        [Taskforce2Vessel1]
        Type=ir_pt_kaivan
        VariantReference=Variant1
        Name=IRIS One
        GeoPosition=11,21,0
        VelocityInKnots=15
        Heading=270
        Telegraph=2
        [Taskforce2Vessel1WeaponMagazineSystem1]
        CurrentIntegrity=10
        Ammunition1_Count=10
        [Taskforce2Vessel1WeaponSystemLauncher2]
        CurrentIntegrity=10
        LoadedAmmunitions=wp_grad,2
        """
    ).strip()


def example_seed(catalog_paths: dict) -> dict:
    return {
        "scenario_name": "Campaign Test",
        "turn_duration_minutes": 60,
        "catalog_paths": catalog_paths,
        "sides": {
            "Blue": {"resources": 1000, "income_per_turn": 5, "spawn_point": {"lat": 0.0, "lon": 0.0}},
            "Red": {"resources": 1000, "income_per_turn": 5, "spawn_point": {"lat": 0.5, "lon": 0.5}},
        },
        "fleets": [
            {
                "id": "blue_1",
                "name": "Blue Fleet",
                "side": "Blue",
                "lat": 0.0,
                "lon": 0.0,
                "heading_deg": 90.0,
                "speed_kts": 20.0,
                "detection_radius_nm": 100.0,
                "composition": [
                    {"name": "USS Alpha", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                    {"name": "USS Bravo", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                ],
            },
            {
                "id": "red_1",
                "name": "Red Fleet",
                "side": "Red",
                "lat": 0.5,
                "lon": 0.5,
                "heading_deg": 270.0,
                "speed_kts": 15.0,
                "detection_radius_nm": 90.0,
                "composition": [
                    {"name": "IRIS One", "sea_power_type": "ir_pt_kaivan", "variant_reference": "Variant1"}
                ],
            },
        ],
    }


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_catalog_dir = catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR
        catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = Path(self.temp_dir.name)
        self.catalog_paths = write_catalog_files(self.temp_dir.name)

    def tearDown(self):
        catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = self.original_catalog_dir
        self.temp_dir.cleanup()

    def test_blank_campaign_defaults(self):
        state = core.create_blank_campaign_state({})

        self.assertEqual(state["scenario_name"], "New Campaign")
        self.assertEqual(state["current_turn"], 1)
        self.assertEqual(len(state["ports"]), 2)
        self.assertEqual(len(state["ships"]), 0)
        self.assertEqual(len(state["fleets"]), 0)
        self.assertEqual(state["catalogs"]["ship_index"], ["ir_pt_kaivan", "usn_dd_spruance"])
        self.assertEqual(state["catalogs"]["ship_options"][0]["nation_label"], "Iran")
        self.assertEqual(state["catalog_paths"]["ammo_database"], self.catalog_paths["ammo_database"])
        self.assertTrue(state["catalogs"]["status"]["available"])

    def test_catalog_ship_options_include_name_role_and_nation(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})
        options = {option["ship_id"]: option for option in state["catalogs"]["ship_options"]}

        self.assertEqual(options["usn_dd_spruance"]["name"], "Spruance")
        self.assertEqual(options["usn_dd_spruance"]["role"], "Destroyer")
        self.assertEqual(options["usn_dd_spruance"]["nation_code"], "usn")
        self.assertEqual(options["usn_dd_spruance"]["nation_label"], "United States")
        self.assertEqual(options["ir_pt_kaivan"]["role"], "Patrol")
        self.assertEqual(options["usn_dd_spruance"]["sensors"], "AN/SPS-40, AN/SQS-53")
        self.assertEqual(options["usn_dd_spruance"]["summary_note"], "Flagship escort destroyer.")
        self.assertEqual(options["usn_dd_spruance"]["loadout_reference"], "ammo_database")
        self.assertEqual(options["usn_dd_spruance"]["class_group"], "Destroyer")
        self.assertEqual(options["ir_pt_kaivan"]["class_group"], "Patrol")

    def test_catalog_ship_options_fallback_when_html_metadata_missing(self):
        ammo_only = Path(self.temp_dir.name) / "ammo_only.json"
        ammo_only.write_text('{"ships":{"rn_type_42":{"sea_dart":22}}}', encoding="utf-8")
        state = core.create_blank_campaign_state({"catalog_paths": {"ammo_database": str(ammo_only)}})
        options = {option["ship_id"]: option for option in state["catalogs"]["ship_options"]}
        option = options["rn_type_42"]

        self.assertEqual(option["ship_id"], "rn_type_42")
        self.assertEqual(option["name"], "Type 42")
        self.assertEqual(option["role"], "Unknown")
        self.assertEqual(option["nation_label"], "Royal Navy")

    def test_catalog_class_group_collapses_hull_code_variants(self):
        ammo_only = Path(self.temp_dir.name) / "class_groups.json"
        ammo_only.write_text('{"ships":{"usn_ddg_kidd":{"sm_1":40},"usn_dd_spruance":{"usn_rim-7m":4},"usn_cg_ticonderoga":{"sm_2":80}}}', encoding="utf-8")
        state = core.create_blank_campaign_state({"catalog_paths": {"ammo_database": str(ammo_only)}})
        options = {option["ship_id"]: option for option in state["catalogs"]["ship_options"]}

        self.assertEqual(options["usn_dd_spruance"]["class_group"], "Destroyer")
        self.assertEqual(options["usn_ddg_kidd"]["class_group"], "Destroyer")
        self.assertEqual(options["usn_cg_ticonderoga"]["class_group"], "Cruiser")

    def test_save_inference_supplies_loadout_when_other_sources_missing(self):
        save_only = Path(self.temp_dir.name) / "save_only.sav"
        save_only.write_text(imported_save_text(), encoding="utf-8")
        empty_dir = tempfile.TemporaryDirectory()
        original = catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR
        catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = Path(empty_dir.name)
        try:
            state = core.create_blank_campaign_state({"catalog_paths": {"sav_files": [str(save_only)]}})
            ship = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        finally:
            catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = original
            empty_dir.cleanup()

        self.assertEqual(ship["loadout_source"], "save_inference")
        self.assertEqual(ship["max_loadout"]["usn_rim-7m"], 3)
        self.assertEqual(ship["max_loadout"]["usn_cal_127mm"], 24)

    def test_catalog_status_reports_missing_sources(self):
        empty_dir = tempfile.TemporaryDirectory()
        original = catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR
        catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = Path(empty_dir.name)
        try:
            state = core.create_blank_campaign_state({})
        finally:
            catalog_module.DEFAULT_EXTERNAL_CATALOG_DIR = original
            empty_dir.cleanup()

        self.assertFalse(state["catalogs"]["status"]["available"])
        self.assertEqual(state["catalogs"]["ship_options"], [])

    def test_import_save_creates_formation_fleet_and_loadouts(self):
        save_path = Path(self.temp_dir.name) / "sample.sav"
        save_path.write_text(imported_save_text(), encoding="utf-8")
        state = core.create_imported_session_state(
            {
                "save_path": str(save_path),
                "scenario_name": "Imported",
                "turn_duration_minutes": 60,
                "catalog_paths": self.catalog_paths,
            }
        )

        self.assertEqual(state["scenario_name"], "Imported")
        self.assertEqual(len(state["fleets"]), 2)
        blue_fleet = next(fleet for fleet in state["fleets"] if fleet["side"] == "Blue")
        self.assertEqual(blue_fleet["name"], "Blue Group")
        self.assertEqual(len(blue_fleet["ship_ids"]), 2)
        alpha = next(ship for ship in state["ships"] if ship["name"] == "USS Alpha")
        self.assertEqual(alpha["loadout"]["usn_rim-7m"], 3)
        self.assertTrue(alpha["subsystems"])

    def test_preview_imported_save_groups_candidates_by_side_and_fleet(self):
        save_path = Path(self.temp_dir.name) / "preview.sav"
        save_path.write_text(imported_save_text(), encoding="utf-8")
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})

        preview = core.preview_imported_save(
            state,
            {
                "save_path": str(save_path),
                "scenario_name": "Preview",
                "turn_duration_minutes": 60,
                "catalog_paths": self.catalog_paths,
            },
        )

        blue_group = next(group for group in preview["sides"] if group["side"] == "Blue")
        red_group = next(group for group in preview["sides"] if group["side"] == "Red")
        self.assertEqual(blue_group["fleet_count"], 1)
        self.assertEqual(blue_group["fleets"][0]["ship_count"], 2)
        self.assertEqual(red_group["fleet_count"], 1)
        self.assertEqual(red_group["fleets"][0]["ships"][0]["class_display_name"], "Kaivan")

    def test_apply_imported_save_selection_merges_selected_subset(self):
        save_path = Path(self.temp_dir.name) / "merge.sav"
        save_path.write_text(imported_save_text(), encoding="utf-8")
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})
        existing = core.create_ship_for_side(state, "Blue", {"name": "USS Alpha", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})

        preview = core.preview_imported_save(
            state,
            {
                "save_path": str(save_path),
                "catalog_paths": self.catalog_paths,
            },
        )
        blue_fleet = next(group for group in preview["sides"] if group["side"] == "Blue")["fleets"][0]
        selected_ship = blue_fleet["ships"][0]
        result = core.apply_imported_save_selection(
            state,
            {
                "save_path": str(save_path),
                "catalog_paths": self.catalog_paths,
                "selected_ship_ids": [selected_ship["candidate_id"]],
            },
        )

        self.assertEqual(result["fleet_count"], 1)
        self.assertEqual(result["ship_count"], 1)
        self.assertEqual(len(state["fleets"]), 1)
        self.assertEqual(len(state["ships"]), 2)
        imported_ship = next(ship for ship in state["ships"] if ship["id"] in result["ship_ids"])
        self.assertNotEqual(imported_ship["id"], existing["id"])
        self.assertNotEqual(imported_ship["name"], "USS Alpha")

    def test_detach_ship_creates_single_ship_fleet(self):
        state = core.create_session_state(example_seed(self.catalog_paths))
        ship = next(ship for ship in state["ships"] if ship["name"] == "USS Alpha")
        original_fleet_count = len(state["fleets"])

        detached = core.transfer_ship(state, ship["id"], {"new_fleet_name": "Alpha Solo"})

        self.assertEqual(detached["fleet_id"], "blue_fleet_2")
        self.assertEqual(len(state["fleets"]), original_fleet_count + 1)
        self.assertEqual(len(core.fleet_by_id(state, "blue_1")["ship_ids"]), 1)

    def test_update_helpers_follow_new_edit_rules(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})
        with patch("planner.core.terrain.point_is_coastal_land", return_value=True):
            port = core.update_port(state, "blue_port_1", {"name": "Blue Anchorage", "lat": 1.0, "lon": -1.0, "radius_nm": 9})
        ship = core.create_ship_for_side(
            state,
            "Blue",
            {"name": "USS Test", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        ship = core.update_ship(state, ship["id"], {"name": "USS Renamed"})
        fleet = core.create_fleet_for_side(
            state,
            "Blue",
            {"name": "Screen", "port_id": "blue_port_1", "ship_ids": [ship["id"]]},
        )
        fleet = core.update_fleet(state, fleet["id"], {"name": "Blue Screen"})

        self.assertEqual(port["name"], "Blue Anchorage")
        self.assertEqual(ship["name"], "USS Renamed")
        self.assertEqual(fleet["name"], "Blue Screen")
        with self.assertRaisesRegex(ValueError, "cannot be edited"):
            core.update_fleet(state, fleet["id"], {"lat": 2.0})

    def test_create_ship_requires_port_and_known_class(self):
        state = core.create_session_state(example_seed(self.catalog_paths))
        with self.assertRaisesRegex(ValueError, "friendly port"):
            core.create_ship_for_side(state, "Blue", {"name": "USS Bad", "sea_power_type": "usn_dd_spruance"})
        blue_port = core.first_port_for_side(state, "Blue")
        with self.assertRaisesRegex(ValueError, "available database options"):
            core.create_ship_for_side(state, "Blue", {"name": "USS Bad", "sea_power_type": "unknown_hull", "port_id": blue_port["id"]})

    def test_bulk_ship_create_uses_readable_auto_numbering(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})

        created = core.create_ships_for_side(
            state,
            "Blue",
            {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1", "quantity": 3},
        )

        self.assertEqual(len(created), 3)
        self.assertEqual([ship["name"] for ship in created], ["Spruance 1", "Spruance 2", "Spruance 3"])
        self.assertTrue(all(ship["port_id"] == "blue_port_1" for ship in created))

    def test_ship_names_remain_unique_per_side(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})

        first = core.create_ship_for_side(
            state,
            "Blue",
            {"name": "Spruance 1", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        second = core.create_ship_for_side(
            state,
            "Blue",
            {"name": "Spruance 1", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )
        red = core.create_ship_for_side(
            state,
            "Red",
            {"name": "Spruance 1", "sea_power_type": "usn_dd_spruance", "port_id": "red_port_1"},
        )

        self.assertEqual(first["name"], "Spruance 1")
        self.assertEqual(second["name"], "Spruance 2")
        self.assertEqual(red["name"], "Spruance 1")

    def test_rename_rejects_duplicate_ship_name_on_same_side(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})
        first = core.create_ship_for_side(state, "Blue", {"name": "Alpha", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        second = core.create_ship_for_side(state, "Blue", {"name": "Bravo", "sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})

        with self.assertRaisesRegex(ValueError, "already in use"):
            core.update_ship(state, second["id"], {"name": first["name"]})

    def test_admin_can_update_side_economy(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})

        updated = core.update_side_economy(state, "Blue", {"resources": 250, "income_per_turn": 12})

        self.assertEqual(updated["resources"], 250)
        self.assertEqual(updated["income_per_turn"], 12)

    def test_ship_snapshot_includes_readable_metadata_and_weapon_entries(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})

        ship = core.create_ship_for_side(
            state,
            "Blue",
            {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"},
        )

        self.assertEqual(ship["class_display_name"], "Spruance")
        self.assertEqual(ship["class_role"], "Destroyer")
        self.assertEqual(ship["nation_label"], "United States")
        self.assertEqual(ship["class_sensors"], "AN/SPS-40, AN/SQS-53")
        self.assertEqual(ship["class_summary_note"], "Flagship escort destroyer.")
        self.assertTrue(ship["weapon_entries"])
        self.assertEqual(ship["weapon_entries"][0]["name"], "127mm ammo")

    def test_ship_snapshot_includes_action_options_and_reasons(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})
        reserve_one = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        reserve_two = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        fleet = core.create_fleet_for_side(state, "Blue", {"name": "Screen", "port_id": "blue_port_1", "ship_ids": [reserve_one["id"]]})

        reserve_snapshot = core.ship_view_snapshot(state, core.ship_by_id(state, reserve_two["id"]), state["catalogs"])
        fleet_snapshot = core.ship_view_snapshot(state, core.ship_by_id(state, reserve_one["id"]), state["catalogs"])

        self.assertTrue(reserve_snapshot["can_transfer"])
        self.assertEqual(reserve_snapshot["eligible_transfer_fleets"][0]["id"], fleet["id"])
        self.assertFalse(reserve_snapshot["can_dock"])
        self.assertIn("Reserve ships", reserve_snapshot["dock_reason"])
        self.assertFalse(reserve_snapshot["can_detach"])

        self.assertTrue(fleet_snapshot["can_move_to_reserve"])
        self.assertEqual(fleet_snapshot["move_to_reserve_reason"], "")

    def test_ship_docking_splits_to_singleton_fleet(self):
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
        one = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        two = core.create_ship_for_side(state, "Blue", {"sea_power_type": "usn_dd_spruance", "port_id": "blue_port_1"})
        fleet = core.create_fleet_for_side(state, "Blue", {"name": "Screen", "port_id": "blue_port_1", "ship_ids": [one["id"], two["id"]]})

        core.dock_fleet(state, fleet["id"], {"action": "undock"})
        docked = core.transfer_ship(state, two["id"], {"dock_port_id": "blue_port_2", "new_fleet_name": "Detached Dock"})

        self.assertEqual(docked["port_id"], "blue_port_2")
        self.assertNotEqual(docked["fleet_id"], fleet["id"])
        self.assertEqual(core.fleet_by_id(state, fleet["id"])["ship_ids"], [one["id"]])
        self.assertEqual(core.fleet_by_id(state, docked["fleet_id"])["docked_port_id"], "blue_port_2")

    def test_fleet_movement_affordance_varies_by_role_and_dock_state(self):
        state = core.create_session_state(example_seed(self.catalog_paths))

        blue_view = core.build_player_view(state, "Blue")
        admin_view = core.build_admin_view(state)
        self.assertTrue(blue_view["fleets"][0]["can_draft_movement"])
        self.assertFalse(admin_view["fleets"][0]["can_draft_movement"])

        blue_port = core.first_port_for_side(state, "Blue")
        core.dock_fleet(state, "blue_1", {"port_id": blue_port["id"]})
        blue_view = core.build_player_view(state, "Blue")
        self.assertFalse(blue_view["fleets"][0]["can_draft_movement"])
        self.assertIn("Docked fleets", blue_view["fleets"][0]["movement_disabled_reason"])

    def test_preview_port_placement_uses_terrain_snap(self):
        state = core.create_blank_campaign_state({"catalog_paths": self.catalog_paths})

        with patch("planner.core.terrain.snap_port_to_coast", return_value={"lat": 12.5, "lon": 42.25, "distance_nm": 1.75}):
            preview = core.preview_port_placement(state, "Blue", {"lat": 12.4, "lon": 42.3})

        self.assertTrue(preview["coastal"])
        self.assertEqual(preview["lat"], 12.5)
        self.assertEqual(preview["lon"], 42.25)
        self.assertEqual(preview["distance_nm"], 1.75)

    def test_rearm_cost_and_turns(self):
        state = core.create_session_state(example_seed(self.catalog_paths))
        blue_port = core.first_port_for_side(state, "Blue")
        core.dock_fleet(state, "blue_1", {"port_id": blue_port["id"]})
        ship = next(ship for ship in state["ships"] if ship["name"] == "USS Alpha")
        ship["loadout"] = {"usn_rim-7m": 2}

        job = core.queue_ship_rearm(state, ship["id"], {"mode": "full"})

        self.assertEqual(job["cost"], 300.0)
        self.assertEqual(job["ready_turn"], 2)

    def test_repair_queue_and_completion_requires_explicit_resolve(self):
        state = core.create_session_state(example_seed(self.catalog_paths))
        blue_port = core.first_port_for_side(state, "Blue")
        core.dock_fleet(state, "blue_1", {"port_id": blue_port["id"]})
        ship = next(ship for ship in state["ships"] if ship["name"] == "USS Alpha")
        ship["subsystems"] = [
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
        ship["class_costs"] = {"base_hull": 1000}

        job = core.queue_ship_repair(state, ship["id"], {"subsystem_id": "radar"})

        self.assertEqual(job["cost"], 375.0)
        self.assertEqual(job["ready_turn"], 3)

        core.submit_turn(state, "Blue", 1, [])
        core.submit_turn(state, "Red", 1, [])
        core.resolve_current_turn(state)
        core.submit_turn(state, "Blue", 2, [])
        core.submit_turn(state, "Red", 2, [])
        core.resolve_current_turn(state)

        self.assertEqual(ship["subsystems"][0]["current_integrity"], 10)
        self.assertEqual(state["repair_queue"][0]["state"], "completed")

    def test_export_reflects_ship_membership(self):
        state = core.create_session_state(example_seed(self.catalog_paths))
        output = core.export_scenario_ini(state)
        self.assertIn("NumberOfTaskforce1Vessels=2", output)
        self.assertIn("Name=USS Alpha", output)
        self.assertIn("Name=USS Bravo", output)


if __name__ == "__main__":
    unittest.main()
