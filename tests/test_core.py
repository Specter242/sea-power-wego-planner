from __future__ import annotations

import unittest

from planner import core


def example_seed():
    return {
        "scenario_name": "Test Duel",
        "turn_duration_minutes": 60,
        "map_center": {"lat": 0.0, "lon": 0.0},
        "side_metadata": {
            "Blue": {"faction": "NATO", "starting_funds": 1200},
            "Red": {"faction": "Iran", "starting_funds": 900},
        },
        "sides": {
            "Blue": {
                "resources": 50,
                "income_per_turn": 5,
                "spawn_point": {"lat": 1.0, "lon": 1.0},
                "build_catalog": [
                    {
                        "id": "blue_dd_pair",
                        "name": "Destroyer Pair",
                        "cost": 20,
                        "unit_type": "Surface",
                        "sea_power_type": "usn_dd_spruance",
                        "variant_reference": "Variant1",
                        "speed_kts": 24,
                        "detection_radius_nm": 110,
                        "composition": [
                            {"name": "USS Alpha", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                            {"name": "USS Bravo", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                        ],
                    }
                ],
            },
            "Red": {
                "resources": 40,
                "income_per_turn": 3,
                "spawn_point": {"lat": 0.0, "lon": 2.0},
            },
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
                "heading_deg": 90.0,
                "speed_kts": 60.0,
                "detection_radius_nm": 120.0,
                "resource_cost": 18,
                "composition": [
                    {"name": "USS Blue One", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                    {"name": "USS Blue Two", "sea_power_type": "usn_dd_spruance", "variant_reference": "Variant1"},
                ],
            },
            {
                "id": "red_1",
                "sp_id": "RED_1",
                "name": "Red Fleet",
                "side": "Red",
                "unit_type": "Surface",
                "lat": 0.0,
                "lon": 1.0,
                "heading_deg": 270.0,
                "speed_kts": 20.0,
                "detection_radius_nm": 60.0,
                "composition": [
                    {"name": "IRIS Red One", "sea_power_type": "ir_pt_kaivan", "variant_reference": "Variant1"}
                ],
            },
        ],
    }


class CoreTests(unittest.TestCase):
    def test_side_metadata_is_preserved_in_state_and_player_view(self):
        state = core.create_session_state(example_seed())
        self.assertEqual(state["side_metadata"]["Blue"]["faction"], "NATO")
        self.assertEqual(state["side_metadata"]["Red"]["starting_funds"], 900)

        blue_view = core.build_player_view(state, "Blue")
        self.assertEqual(blue_view["side_metadata"]["Blue"]["starting_funds"], 1200)
        self.assertEqual(blue_view["side_metadata"]["Red"]["faction"], "Iran")

    def test_multileg_movement_truncates_mid_path(self):
        state = core.create_session_state(example_seed())
        result = core.submit_turn(
            state,
            "Blue",
            1,
            [{"fleet_id": "blue_1", "waypoints": [{"lat": 0.0, "lon": 0.5}, {"lat": 0.0, "lon": 1.5}]}],
        )
        self.assertFalse(result["resolved"])
        result = core.submit_turn(state, "Red", 1, [])
        self.assertTrue(result["resolved"])

        blue_fleet = next(fleet for fleet in state["fleets"] if fleet["id"] == "blue_1")
        self.assertAlmostEqual(blue_fleet["lat"], 0.0, places=3)
        self.assertAlmostEqual(blue_fleet["lon"], 1.0, places=2)

    def test_last_known_contacts_persist_after_visibility_is_lost(self):
        seed = example_seed()
        seed["fleets"][0]["detection_radius_nm"] = 80.0
        seed["fleets"][1]["speed_kts"] = 120.0
        state = core.create_session_state(seed)

        core.submit_turn(state, "Blue", 1, [])
        core.submit_turn(
            state,
            "Red",
            1,
            [{"fleet_id": "red_1", "waypoints": [{"lat": 0.0, "lon": 0.5}]}],
        )

        blue_view = core.build_player_view(state, "Blue")
        self.assertEqual(blue_view["contacts"][0]["state"], "visible")

        core.submit_turn(state, "Blue", 2, [])
        core.submit_turn(
            state,
            "Red",
            2,
            [{"fleet_id": "red_1", "waypoints": [{"lat": 0.0, "lon": 2.0}]}],
        )

        blue_view = core.build_player_view(state, "Blue")
        self.assertEqual(blue_view["contacts"][0]["state"], "last_known")
        self.assertEqual(blue_view["contacts"][0]["last_seen_turn"], 2)

    def test_export_contains_expected_sections(self):
        state = core.create_session_state(example_seed())
        output = core.export_scenario_ini(state)
        self.assertIn("[Environment]", output)
        self.assertIn("[Mission]", output)
        self.assertIn("NumberOfTaskforce1Vessels=2", output)
        self.assertIn("NumberOfTaskforce2Vessels=1", output)
        self.assertIn("[Taskforce1Vessel1]", output)
        self.assertIn("[Taskforce2Vessel1]", output)
        self.assertIn("Name=USS Blue One", output)

    def test_build_fleet_spends_resources_and_uses_spawn_point(self):
        state = core.create_session_state(example_seed())
        built = core.build_fleet_for_side(state, "Blue", "blue_dd_pair")
        self.assertEqual(built["lat"], 1.0)
        self.assertEqual(built["lon"], 1.0)
        self.assertEqual(len(built["composition"]), 2)
        self.assertEqual(state["side_state"]["Blue"]["resources"], 30)

    def test_income_is_awarded_after_turn_resolution(self):
        state = core.create_session_state(example_seed())
        core.submit_turn(state, "Blue", 1, [])
        core.submit_turn(state, "Red", 1, [])
        self.assertEqual(state["side_state"]["Blue"]["resources"], 55)
        self.assertEqual(state["side_state"]["Red"]["resources"], 43)

    def test_surface_fleet_cannot_start_on_land(self):
        seed = example_seed()
        seed["fleets"][0]["lat"] = 39.0
        seed["fleets"][0]["lon"] = -98.0
        with self.assertRaisesRegex(ValueError, "stay on water"):
            core.create_session_state(seed)

    def test_surface_orders_cannot_cross_land(self):
        state = core.create_session_state(example_seed())
        with self.assertRaisesRegex(ValueError, "stay on water"):
            core.submit_turn(
                state,
                "Blue",
                1,
                [{"fleet_id": "blue_1", "waypoints": [{"lat": 39.0, "lon": -98.0}]}],
            )


if __name__ == "__main__":
    unittest.main()
