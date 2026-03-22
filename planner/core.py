from __future__ import annotations

import copy
import math
import secrets
from datetime import datetime, timezone


BLUE = "Blue"
RED = "Red"
SIDES = (BLUE, RED)


DEFAULT_ENVIRONMENT = {
    "date": "1985,6,26",
    "time": "10,0",
    "convert_time_to_local": False,
    "sea_state": 3,
    "clouds": "Scattered_1",
    "wind_direction": "E",
    "load_background_data": False,
}

DEFAULT_SIDE_METADATA = {
    BLUE: {"faction": "NATO", "starting_funds": 0},
    RED: {"faction": "Warsaw Pact", "starting_funds": 0},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def other_side(side: str) -> str:
    return RED if side == BLUE else BLUE


def normalize_seed(seed: dict) -> dict:
    if not isinstance(seed, dict):
        raise ValueError("Scenario seed must be a JSON object.")
    if not seed.get("scenario_name"):
        raise ValueError("Scenario seed requires 'scenario_name'.")
    if not isinstance(seed.get("turn_duration_minutes"), int) or seed["turn_duration_minutes"] <= 0:
        raise ValueError("'turn_duration_minutes' must be a positive integer.")
    fleets = seed.get("fleets")
    if not isinstance(fleets, list) or not fleets:
        raise ValueError("Scenario seed requires a non-empty 'fleets' list.")
    return seed


def create_session_state(seed: dict) -> dict:
    seed = normalize_seed(seed)
    now = utc_now()
    fleets = [normalize_fleet(entry, idx) for idx, entry in enumerate(seed["fleets"], start=1)]
    map_center = normalize_map_center(seed.get("map_center"), fleets)
    state = {
        "session_id": secrets.token_hex(6),
        "scenario_name": seed["scenario_name"],
        "turn_duration_minutes": seed["turn_duration_minutes"],
        "current_turn": 1,
        "status": "open",
        "created_at": now,
        "updated_at": now,
        "map_center": map_center,
        "environment": normalize_environment(seed.get("environment", {})),
        "side_metadata": normalize_side_metadata(seed.get("side_metadata")),
        "tokens": {
            BLUE: secrets.token_urlsafe(18),
            RED: secrets.token_urlsafe(18),
            "admin": secrets.token_urlsafe(24),
        },
        "fleets": fleets,
        "turns": {},
        "contacts": {
            BLUE: {},
            RED: {},
        },
    }
    get_or_create_turn_record(state, state["current_turn"])
    initialize_contacts(state)
    return state


def normalize_side_metadata(side_metadata: dict | None) -> dict:
    normalized = copy.deepcopy(DEFAULT_SIDE_METADATA)
    source = side_metadata or {}
    for side in SIDES:
        entry = source.get(side, {})
        normalized[side]["faction"] = str(entry.get("faction") or normalized[side]["faction"])
        try:
            normalized[side]["starting_funds"] = int(entry.get("starting_funds", normalized[side]["starting_funds"]))
        except (TypeError, ValueError):
            normalized[side]["starting_funds"] = normalized[side]["starting_funds"]
    return normalized


def normalize_environment(environment: dict) -> dict:
    normalized = dict(DEFAULT_ENVIRONMENT)
    normalized.update(environment or {})
    return normalized


def normalize_map_center(map_center: dict | None, fleets: list[dict]) -> dict:
    if map_center and "lat" in map_center and "lon" in map_center:
        return {"lat": float(map_center["lat"]), "lon": float(map_center["lon"])}

    avg_lat = sum(fleet["lat"] for fleet in fleets) / len(fleets)
    avg_lon = sum(fleet["lon"] for fleet in fleets) / len(fleets)
    return {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4)}


def normalize_fleet(entry: dict, index: int) -> dict:
    if entry.get("side") not in SIDES:
        raise ValueError(f"Fleet {index} has invalid side '{entry.get('side')}'.")
    if "lat" not in entry or "lon" not in entry:
        raise ValueError(f"Fleet {index} requires 'lat' and 'lon'.")
    if "speed_kts" not in entry:
        raise ValueError(f"Fleet {index} requires 'speed_kts'.")
    fleet_id = entry.get("id") or f"fleet_{index:02d}"
    return {
        "id": fleet_id,
        "sp_id": entry.get("sp_id") or fleet_id.upper(),
        "name": entry.get("name") or fleet_id,
        "side": entry["side"],
        "unit_type": entry.get("unit_type", "Surface"),
        "sea_power_type": entry.get("sea_power_type", "usn_dd_spruance"),
        "variant_reference": entry.get("variant_reference", "Variant1"),
        "station_role": entry.get("station_role", ""),
        "crew_skill": entry.get("crew_skill", "Trained"),
        "telegraph": int(entry.get("telegraph", 2)),
        "lat": float(entry["lat"]),
        "lon": float(entry["lon"]),
        "heading_deg": float(entry.get("heading_deg", 0.0)),
        "speed_kts": float(entry["speed_kts"]),
        "detection_radius_nm": float(entry.get("detection_radius_nm", 100.0)),
        "status": entry.get("status", "Active"),
    }


def get_or_create_turn_record(state: dict, turn_number: int) -> dict:
    turn_key = str(turn_number)
    if turn_key not in state["turns"]:
        state["turns"][turn_key] = {
            "turn_number": turn_number,
            "status": "open",
            "submissions": {},
            "resolution_summary": None,
        }
    return state["turns"][turn_key]


def initialize_contacts(state: dict) -> None:
    visible = compute_visibility(state["fleets"])
    for side in SIDES:
        enemy_side = other_side(side)
        contacts = {}
        for fleet in state["fleets"]:
            if fleet["side"] != enemy_side:
                continue
            if fleet["id"] in visible[side]:
                contacts[fleet["id"]] = visible_contact_snapshot(fleet, last_seen_turn=0)
        state["contacts"][side] = contacts


def visible_contact_snapshot(fleet: dict, last_seen_turn: int) -> dict:
    return {
        "fleet_id": fleet["id"],
        "sp_id": fleet["sp_id"],
        "name": fleet["name"],
        "unit_type": fleet["unit_type"],
        "state": "visible",
        "lat": fleet["lat"],
        "lon": fleet["lon"],
        "heading_deg": fleet["heading_deg"],
        "last_seen_turn": last_seen_turn,
    }


def compute_visibility(fleets: list[dict]) -> dict[str, set[str]]:
    visible = {BLUE: set(), RED: set()}
    for observer in fleets:
        for target in fleets:
            if observer["side"] == target["side"]:
                continue
            if nautical_miles_between(observer, target) <= observer["detection_radius_nm"]:
                visible[observer["side"]].add(target["id"])
    return visible


def nautical_miles_between(a: dict, b: dict) -> float:
    lat1 = math.radians(a["lat"])
    lon1 = math.radians(a["lon"])
    lat2 = math.radians(b["lat"])
    lon2 = math.radians(b["lon"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 3440.065 * 2.0 * math.atan2(math.sqrt(h), math.sqrt(1.0 - h))


def bearing_degrees(start: dict | tuple[float, float], end: dict | tuple[float, float]) -> float:
    start_lat, start_lon = extract_lat_lon(start)
    end_lat, end_lon = extract_lat_lon(end)
    lat1 = math.radians(start_lat)
    lon1 = math.radians(start_lon)
    lat2 = math.radians(end_lat)
    lon2 = math.radians(end_lon)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def extract_lat_lon(value: dict | tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, dict):
        return float(value["lat"]), float(value["lon"])
    return float(value[0]), float(value[1])


def submit_turn(state: dict, side: str, turn_number: int, orders: list[dict]) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side.")
    if turn_number != state["current_turn"]:
        raise ValueError("Turn number does not match the current turn.")

    turn = get_or_create_turn_record(state, turn_number)
    if side in turn["submissions"]:
        raise ValueError(f"{side} has already submitted turn {turn_number}.")

    normalized_orders = normalize_orders(state, side, orders)
    turn["submissions"][side] = {
        "submitted_at": utc_now(),
        "orders": normalized_orders,
    }
    state["updated_at"] = utc_now()

    resolved = False
    summary = None
    if all(team in turn["submissions"] for team in SIDES):
        summary = resolve_current_turn(state)
        resolved = True

    return {
        "resolved": resolved,
        "resolution_summary": summary,
        "current_turn": state["current_turn"],
    }


def normalize_orders(state: dict, side: str, orders: list[dict]) -> list[dict]:
    if not isinstance(orders, list):
        raise ValueError("Orders payload must be a list.")
    owned_fleet_ids = {fleet["id"] for fleet in state["fleets"] if fleet["side"] == side}
    normalized = []
    seen_fleets = set()
    for order in orders:
        fleet_id = order.get("fleet_id")
        if fleet_id not in owned_fleet_ids:
            raise ValueError(f"Fleet '{fleet_id}' does not belong to {side}.")
        if fleet_id in seen_fleets:
            raise ValueError(f"Fleet '{fleet_id}' has duplicate orders.")
        seen_fleets.add(fleet_id)
        waypoints = order.get("waypoints")
        if not isinstance(waypoints, list):
            raise ValueError(f"Fleet '{fleet_id}' requires a waypoint list.")
        cleaned_waypoints = []
        for waypoint in waypoints:
            if "lat" not in waypoint or "lon" not in waypoint:
                raise ValueError(f"Fleet '{fleet_id}' waypoint requires 'lat' and 'lon'.")
            cleaned_waypoints.append({"lat": float(waypoint["lat"]), "lon": float(waypoint["lon"])})
        normalized.append({"fleet_id": fleet_id, "waypoints": cleaned_waypoints})
    return normalized


def resolve_current_turn(state: dict) -> dict:
    turn_number = state["current_turn"]
    turn = get_or_create_turn_record(state, turn_number)
    if not all(side in turn["submissions"] for side in SIDES):
        raise ValueError("Cannot resolve a turn until both sides submit.")

    simulation_fleets = copy.deepcopy(state["fleets"])
    order_lookup = {
        order["fleet_id"]: [dict(waypoint) for waypoint in order["waypoints"]]
        for side in SIDES
        for order in turn["submissions"][side]["orders"]
    }

    path_context = {}
    for fleet in simulation_fleets:
        path_context[fleet["id"]] = {
            "remaining_waypoints": order_lookup.get(fleet["id"], []),
        }

    step_minutes = max(1, min(10, state["turn_duration_minutes"]))
    steps = max(1, math.ceil(state["turn_duration_minutes"] / step_minutes))
    step_hours = state["turn_duration_minutes"] / 60.0 / steps

    seen_contacts = {BLUE: {}, RED: {}}
    final_visible = {BLUE: set(), RED: set()}
    for step_index in range(steps):
        for fleet in simulation_fleets:
            move_budget_nm = fleet["speed_kts"] * step_hours
            advance_fleet_along_waypoints(fleet, path_context[fleet["id"]], move_budget_nm)

        final_visible = compute_visibility(simulation_fleets)
        for observer_side in SIDES:
            for fleet in simulation_fleets:
                if fleet["side"] == observer_side:
                    continue
                if fleet["id"] in final_visible[observer_side]:
                    seen_contacts[observer_side][fleet["id"]] = {
                        "fleet_id": fleet["id"],
                        "sp_id": fleet["sp_id"],
                        "name": fleet["name"],
                        "unit_type": fleet["unit_type"],
                        "state": "visible",
                        "lat": fleet["lat"],
                        "lon": fleet["lon"],
                        "heading_deg": fleet["heading_deg"],
                        "last_seen_turn": turn_number,
                        "last_seen_step": step_index + 1,
                    }

    state["fleets"] = simulation_fleets
    update_contacts_from_resolution(state, seen_contacts, final_visible, turn_number)

    summary = {
        "turn_number": turn_number,
        "resolved_at": utc_now(),
        "blue_submitted": True,
        "red_submitted": True,
        "fleet_positions": {
            fleet["id"]: {"lat": fleet["lat"], "lon": fleet["lon"], "heading_deg": fleet["heading_deg"]}
            for fleet in simulation_fleets
        },
    }
    turn["status"] = "resolved"
    turn["resolution_summary"] = summary
    state["current_turn"] += 1
    get_or_create_turn_record(state, state["current_turn"])
    state["updated_at"] = utc_now()
    return summary


def advance_fleet_along_waypoints(fleet: dict, path_context: dict, move_budget_nm: float) -> None:
    while move_budget_nm > 0.0001 and path_context["remaining_waypoints"]:
        next_waypoint = path_context["remaining_waypoints"][0]
        distance_to_waypoint = nautical_miles_between(fleet, next_waypoint)
        if distance_to_waypoint <= move_budget_nm + 0.0001:
            fleet["heading_deg"] = bearing_degrees(fleet, next_waypoint)
            fleet["lat"] = next_waypoint["lat"]
            fleet["lon"] = next_waypoint["lon"]
            move_budget_nm -= distance_to_waypoint
            path_context["remaining_waypoints"].pop(0)
        else:
            fraction = move_budget_nm / distance_to_waypoint if distance_to_waypoint else 0.0
            fleet["heading_deg"] = bearing_degrees(fleet, next_waypoint)
            fleet["lat"] += (next_waypoint["lat"] - fleet["lat"]) * fraction
            fleet["lon"] += (next_waypoint["lon"] - fleet["lon"]) * fraction
            move_budget_nm = 0.0


def update_contacts_from_resolution(state: dict, seen_contacts: dict, final_visible: dict, turn_number: int) -> None:
    enemy_fleet_lookup = {fleet["id"]: fleet for fleet in state["fleets"]}
    for side in SIDES:
        updated_contacts = {}
        previous_contacts = state["contacts"].get(side, {})
        for enemy_id, previous in previous_contacts.items():
            updated_contacts[enemy_id] = dict(previous)

        for enemy_id, contact in seen_contacts[side].items():
            updated_contacts[enemy_id] = contact

        for enemy_id, fleet in enemy_fleet_lookup.items():
            if fleet["side"] == side:
                continue
            if enemy_id in final_visible[side]:
                updated_contacts[enemy_id] = visible_contact_snapshot(fleet, last_seen_turn=turn_number)
            elif enemy_id in updated_contacts:
                updated_contacts[enemy_id]["state"] = "last_known"

        state["contacts"][side] = updated_contacts


def build_player_view(state: dict, side: str) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side for player view.")
    enemy_side = other_side(side)
    turn = get_or_create_turn_record(state, state["current_turn"])
    own_fleets = [fleet_view_snapshot(fleet) for fleet in state["fleets"] if fleet["side"] == side]
    contacts = sorted(state["contacts"].get(side, {}).values(), key=lambda item: item["sp_id"])
    own_submission = turn["submissions"].get(side)
    return {
        "session_id": state["session_id"],
        "scenario_name": state["scenario_name"],
        "side": side,
        "current_turn": state["current_turn"],
        "turn_duration_minutes": state["turn_duration_minutes"],
        "map_center": state["map_center"],
        "environment": state["environment"],
        "side_metadata": state["side_metadata"],
        "status": turn["status"],
        "own_submitted": own_submission is not None,
        "opponent_ready": other_side(side) in turn["submissions"],
        "fleets": own_fleets,
        "contacts": contacts,
        "orders": own_submission["orders"] if own_submission else [],
        "can_submit": own_submission is None,
        "enemy_side": enemy_side,
    }


def build_admin_view(state: dict) -> dict:
    return {
        "session_id": state["session_id"],
        "scenario_name": state["scenario_name"],
        "current_turn": state["current_turn"],
        "turn_duration_minutes": state["turn_duration_minutes"],
        "map_center": state["map_center"],
        "environment": state["environment"],
        "side_metadata": state["side_metadata"],
        "fleets": [fleet_view_snapshot(fleet) for fleet in state["fleets"]],
        "turns": state["turns"],
        "contacts": state["contacts"],
    }


def fleet_view_snapshot(fleet: dict) -> dict:
    return {
        "id": fleet["id"],
        "sp_id": fleet["sp_id"],
        "name": fleet["name"],
        "side": fleet["side"],
        "unit_type": fleet["unit_type"],
        "lat": fleet["lat"],
        "lon": fleet["lon"],
        "heading_deg": fleet["heading_deg"],
        "speed_kts": fleet["speed_kts"],
        "status": fleet["status"],
    }


def export_scenario_ini(state: dict) -> str:
    center = state["map_center"]
    env = state["environment"]
    blue_fleets = [fleet for fleet in state["fleets"] if fleet["side"] == BLUE]
    red_fleets = [fleet for fleet in state["fleets"] if fleet["side"] == RED]

    lines = []
    lines.extend(
        [
            "[Debug]",
            "DisableEnemyAIPlayer=True",
            "[Language_en]",
            f"Name={state['scenario_name']}",
            "[Language_cn]",
            f"Name={state['scenario_name']}",
            "[Language_ru]",
            f"Name={state['scenario_name']}",
            "[Language_de]",
            f"Name={state['scenario_name']}",
            "[Language_es]",
            f"Name={state['scenario_name']}",
            "[Language_fr]",
            f"Name={state['scenario_name']}",
            "[Language_ko]",
            f"Name={state['scenario_name']}",
            "[Language_ja]",
            f"Name={state['scenario_name']}",
            "[Language_vn]",
            f"Name={state['scenario_name']}",
            "[Environment]",
            f"Date={env['date']}",
            f"Time={env['time']}",
            f"ConvertTimeToLocal={str(bool(env['convert_time_to_local']))}",
            f"SeaState={env['sea_state']}",
            f"Clouds={env['clouds']}",
            f"WindDirection={env['wind_direction']}",
            f"MapCenterLatitude={center['lat']}",
            f"MapCenterLongitude={center['lon']}",
            f"LoadBackgroundData={str(bool(env['load_background_data']))}",
            "[Mission]",
            "Difficulty=0",
            "PlayerTaskforce=Taskforce1",
            "EnemyTaskforce=Taskforce2",
            f"NumberOfTaskforce1Vessels={len(blue_fleets)}",
        ]
    )
    if red_fleets:
        lines.append(f"NumberOfTaskforce2Vessels={len(red_fleets)}")

    append_taskforce(lines, center, "Taskforce1", blue_fleets)
    append_taskforce(lines, center, "Taskforce2", red_fleets)
    return "\n".join(lines) + "\n"


def append_taskforce(lines: list[str], center: dict, section_prefix: str, fleets: list[dict]) -> None:
    for index, fleet in enumerate(fleets, start=1):
        east_nm, north_nm = relative_position_nm(center, fleet)
        lines.extend(
            [
                f"[{section_prefix}Vessel{index}]",
                f"Type={fleet['sea_power_type']}",
                f"VariantReference={fleet['variant_reference']}",
            ]
        )
        if fleet["station_role"]:
            lines.append(f"StationRole={fleet['station_role']}")
        lines.extend(
            [
                f"CrewSkill={fleet['crew_skill']}",
                f"RelativePositionInNM={east_nm:.2f},0,{north_nm:.2f}",
                f"Telegraph={fleet['telegraph']}",
                f"Heading={int(round(fleet['heading_deg'])) % 360}",
            ]
        )


def relative_position_nm(center: dict, fleet: dict) -> tuple[float, float]:
    lat_factor = 60.0
    north_nm = (fleet["lat"] - center["lat"]) * lat_factor
    avg_lat = math.radians((fleet["lat"] + center["lat"]) / 2.0)
    east_nm = (fleet["lon"] - center["lon"]) * lat_factor * math.cos(avg_lat)
    return east_nm, north_nm
