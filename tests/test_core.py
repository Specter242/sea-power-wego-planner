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
        self.assertIn("NumberOfTaskforce1Vessels=1", output)
        self.assertIn("NumberOfTaskforce2Vessels=1", output)
        self.assertIn("[Taskforce1Vessel1]", output)
        self.assertIn("[Taskforce2Vessel1]", output)


if __name__ == "__main__":
    unittest.main()
