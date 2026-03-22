from __future__ import annotations

import copy
import math
import secrets
from datetime import datetime, timezone

from . import terrain


BLUE = "Blue"
RED = "Red"
SIDES = (BLUE, RED)
DEFAULT_RESOURCE_POINTS = 100
DEFAULT_BUILD_COST = 10


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
    fleets = seed.get("fleets", [])
    if fleets is None:
        seed["fleets"] = []
    elif not isinstance(fleets, list):
        raise ValueError("'fleets' must be a list when provided.")
    return seed


def create_session_state(seed: dict) -> dict:
    seed = normalize_seed(seed)
    now = utc_now()
    fleets = [normalize_fleet(entry, idx) for idx, entry in enumerate(seed.get("fleets", []), start=1)]
    side_state = normalize_side_state(seed.get("sides", {}), fleets)
    map_center = normalize_map_center(seed.get("map_center"), fleets, side_state)
    state = {
        "session_id": secrets.token_hex(6),
        "scenario_name": seed["scenario_name"],
        "turn_duration_minutes": seed["turn_duration_minutes"],
        "current_turn": 1,
        "status": "open",
        "created_at": now,
        "updated_at": now,
        "fleet_counter": len(fleets),
        "map_center": map_center,
        "environment": normalize_environment(seed.get("environment", {})),
        "side_metadata": normalize_side_metadata(seed.get("side_metadata")),
        "tokens": {
            BLUE: secrets.token_urlsafe(18),
            RED: secrets.token_urlsafe(18),
            "admin": secrets.token_urlsafe(24),
        },
        "side_state": side_state,
        "fleets": fleets,
        "turns": {},
        "contacts": {
            BLUE: {},
            RED: {},
        },
    }
    validate_fleets(state["fleets"])
    get_or_create_turn_record(state, state["current_turn"])
    initialize_contacts(state)
    return state


def upgrade_state(state: dict) -> dict:
    fleets = state.get("fleets", [])
    for index, fleet in enumerate(fleets, start=1):
        fleet.setdefault("id", f"fleet_{index:02d}")
        fleet.setdefault("sp_id", str(fleet["id"]).upper())
        fleet.setdefault("name", fleet["id"])
        fleet.setdefault("unit_type", "Surface")
        fleet.setdefault("sea_power_type", "usn_dd_spruance")
        fleet.setdefault("variant_reference", "Variant1")
        fleet.setdefault("station_role", "")
        fleet.setdefault("crew_skill", "Trained")
        fleet.setdefault("telegraph", 2)
        fleet.setdefault("heading_deg", 0.0)
        fleet.setdefault("speed_kts", 0.0)
        fleet.setdefault("detection_radius_nm", 100.0)
        fleet.setdefault("status", "Active")
        fleet.setdefault("resource_cost", DEFAULT_BUILD_COST)
        fleet.setdefault("template_id", "")
        fleet.setdefault("built_turn", 0)
        fleet["composition"] = normalize_composition(
            fleet.get("composition"),
            default_name=str(fleet["name"]),
            default_sea_power_type=str(fleet["sea_power_type"]),
            default_variant_reference=str(fleet["variant_reference"]),
        )

    state["fleet_counter"] = int(state.get("fleet_counter", len(fleets)))
    state["environment"] = normalize_environment(state.get("environment", {}))
    state["side_metadata"] = normalize_side_metadata(state.get("side_metadata"))
    state["side_state"] = normalize_side_state(state.get("side_state", {}), fleets)
    state["map_center"] = normalize_map_center(state.get("map_center"), fleets, state["side_state"])
    state.setdefault("contacts", {BLUE: {}, RED: {}})
    state["contacts"].setdefault(BLUE, {})
    state["contacts"].setdefault(RED, {})
    state.setdefault("turns", {})
    get_or_create_turn_record(state, int(state.get("current_turn", 1)))
    return state


def normalize_side_metadata(side_metadata: dict | None) -> dict:
    normalized = copy.deepcopy(DEFAULT_SIDE_METADATA)
    source = side_metadata or {}
    for side in SIDES:
        entry = source.get(side, {}) if isinstance(source, dict) else {}
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


def normalize_map_center(map_center: dict | None, fleets: list[dict], side_state: dict | None = None) -> dict:
    if map_center and "lat" in map_center and "lon" in map_center:
        return {"lat": float(map_center["lat"]), "lon": float(map_center["lon"])}

    if fleets:
        avg_lat = sum(fleet["lat"] for fleet in fleets) / len(fleets)
        avg_lon = sum(fleet["lon"] for fleet in fleets) / len(fleets)
        return {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4)}

    if isinstance(side_state, dict):
        spawn_points = [
            entry.get("spawn_point")
            for entry in side_state.values()
            if isinstance(entry, dict) and isinstance(entry.get("spawn_point"), dict)
        ]
        if spawn_points:
            avg_lat = sum(float(point["lat"]) for point in spawn_points) / len(spawn_points)
            avg_lon = sum(float(point["lon"]) for point in spawn_points) / len(spawn_points)
            return {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4)}

    return {"lat": 0.0, "lon": 0.0}


def normalize_side_state(side_seed: dict, fleets: list[dict]) -> dict:
    normalized = {}
    for side in SIDES:
        defaults = derive_side_defaults(side, fleets)
        source = side_seed.get(side, {}) if isinstance(side_seed, dict) else {}
        spawn_seed = source.get("spawn_point") or defaults["spawn_point"]
        build_catalog_seed = source.get("build_catalog") or defaults["build_catalog"]
        normalized[side] = {
            "resources": int(source.get("resources", DEFAULT_RESOURCE_POINTS)),
            "total_spent": int(source.get("total_spent", 0)),
            "income_per_turn": int(source.get("income_per_turn", 0)),
            "spawn_point": {"lat": float(spawn_seed["lat"]), "lon": float(spawn_seed["lon"])},
            "build_catalog": [
                normalize_catalog_entry(side, entry, idx)
                for idx, entry in enumerate(build_catalog_seed, start=1)
            ],
        }
    return normalized


def derive_side_defaults(side: str, fleets: list[dict]) -> dict:
    side_fleets = [fleet for fleet in fleets if fleet["side"] == side]
    if side_fleets:
        avg_lat = sum(fleet["lat"] for fleet in side_fleets) / len(side_fleets)
        avg_lon = sum(fleet["lon"] for fleet in side_fleets) / len(side_fleets)
        spawn_point = {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4)}
    else:
        spawn_point = {"lat": 0.0, "lon": 0.0}

    catalog = []
    seen = set()
    for fleet in side_fleets:
        key = (fleet["sea_power_type"], fleet["variant_reference"], fleet["name"])
        if key in seen:
            continue
        seen.add(key)
        catalog.append(
            {
                "id": f"{side.lower()}_{len(catalog) + 1}",
                "name": fleet["name"],
                "cost": int(fleet.get("resource_cost", DEFAULT_BUILD_COST)),
                "unit_type": fleet["unit_type"],
                "sea_power_type": fleet["sea_power_type"],
                "variant_reference": fleet["variant_reference"],
                "station_role": fleet["station_role"],
                "crew_skill": fleet["crew_skill"],
                "telegraph": fleet["telegraph"],
                "speed_kts": fleet["speed_kts"],
                "detection_radius_nm": fleet["detection_radius_nm"],
                "composition": copy.deepcopy(fleet["composition"]),
            }
        )
    if not catalog:
        catalog.append(
            {
                "id": f"{side.lower()}_surface_group",
                "name": f"{side} Surface Group",
                "cost": DEFAULT_BUILD_COST,
                "unit_type": "Surface",
                "sea_power_type": "usn_dd_spruance" if side == BLUE else "ir_pt_kaivan",
                "variant_reference": "Variant1",
                "station_role": "",
                "crew_skill": "Trained",
                "telegraph": 2,
                "speed_kts": 18.0,
                "detection_radius_nm": 80.0,
                "composition": [],
            }
        )
    return {"spawn_point": spawn_point, "build_catalog": catalog}


def normalize_catalog_entry(side: str, entry: dict, index: int) -> dict:
    if not isinstance(entry, dict):
        raise ValueError("Build catalog entries must be JSON objects.")
    catalog_id = str(entry.get("id") or f"{side.lower()}_{index}")
    name = str(entry.get("name") or f"{side} Build {index}")
    sea_power_type = str(entry.get("sea_power_type") or "usn_dd_spruance")
    variant_reference = str(entry.get("variant_reference") or "Variant1")
    return {
        "id": catalog_id,
        "name": name,
        "cost": int(entry.get("cost", DEFAULT_BUILD_COST)),
        "unit_type": str(entry.get("unit_type", "Surface")),
        "sea_power_type": sea_power_type,
        "variant_reference": variant_reference,
        "station_role": str(entry.get("station_role", "")),
        "crew_skill": str(entry.get("crew_skill", "Trained")),
        "telegraph": int(entry.get("telegraph", 2)),
        "speed_kts": float(entry.get("speed_kts", 18.0)),
        "detection_radius_nm": float(entry.get("detection_radius_nm", 100.0)),
        "composition": normalize_composition(
            entry.get("composition"),
            default_name=name,
            default_sea_power_type=sea_power_type,
            default_variant_reference=variant_reference,
        ),
    }


def normalize_fleet(entry: dict, index: int) -> dict:
    if entry.get("side") not in SIDES:
        raise ValueError(f"Fleet {index} has invalid side '{entry.get('side')}'.")
    if "lat" not in entry or "lon" not in entry:
        raise ValueError(f"Fleet {index} requires 'lat' and 'lon'.")
    if "speed_kts" not in entry:
        raise ValueError(f"Fleet {index} requires 'speed_kts'.")
    fleet_id = str(entry.get("id") or f"fleet_{index:02d}")
    sea_power_type = str(entry.get("sea_power_type", "usn_dd_spruance"))
    variant_reference = str(entry.get("variant_reference", "Variant1"))
    name = str(entry.get("name") or fleet_id)
    return {
        "id": fleet_id,
        "sp_id": str(entry.get("sp_id") or fleet_id.upper()),
        "name": name,
        "side": entry["side"],
        "unit_type": str(entry.get("unit_type", "Surface")),
        "sea_power_type": sea_power_type,
        "variant_reference": variant_reference,
        "station_role": str(entry.get("station_role", "")),
        "crew_skill": str(entry.get("crew_skill", "Trained")),
        "telegraph": int(entry.get("telegraph", 2)),
        "lat": float(entry["lat"]),
        "lon": float(entry["lon"]),
        "heading_deg": float(entry.get("heading_deg", 0.0)),
        "speed_kts": float(entry["speed_kts"]),
        "detection_radius_nm": float(entry.get("detection_radius_nm", 100.0)),
        "status": str(entry.get("status", "Active")),
        "resource_cost": int(entry.get("resource_cost", DEFAULT_BUILD_COST)),
        "template_id": str(entry.get("template_id", "")),
        "built_turn": int(entry.get("built_turn", 0)),
        "composition": normalize_composition(
            entry.get("composition"),
            default_name=name,
            default_sea_power_type=sea_power_type,
            default_variant_reference=variant_reference,
        ),
    }


def validate_fleets(fleets: list[dict]) -> None:
    for fleet in fleets:
        terrain.validate_unit_position(fleet["unit_type"], fleet["lat"], fleet["lon"])


def normalize_composition(
    composition: list[dict] | None,
    default_name: str,
    default_sea_power_type: str,
    default_variant_reference: str,
) -> list[dict]:
    if not composition:
        return [
            {
                "name": default_name,
                "sea_power_type": default_sea_power_type,
                "variant_reference": default_variant_reference,
                "count": 1,
            }
        ]

    normalized = []
    for index, item in enumerate(composition, start=1):
        if not isinstance(item, dict):
            raise ValueError("Fleet composition entries must be JSON objects.")
        normalized.append(
            {
                "name": str(item.get("name") or f"{default_name} Unit {index}"),
                "sea_power_type": str(item.get("sea_power_type") or default_sea_power_type),
                "variant_reference": str(item.get("variant_reference") or default_variant_reference),
                "count": max(1, int(item.get("count", 1))),
            }
        )
    return normalized


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


def admin_fleet_snapshot(fleet: dict) -> dict:
    snapshot = fleet_view_snapshot(fleet)
    snapshot.update(
        {
            "detection_radius_nm": fleet["detection_radius_nm"],
            "sea_power_type": fleet["sea_power_type"],
            "variant_reference": fleet["variant_reference"],
            "station_role": fleet["station_role"],
            "crew_skill": fleet["crew_skill"],
            "telegraph": fleet["telegraph"],
        }
    )
    return snapshot


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
        fleet = fleet_by_id(state, fleet_id)
        previous_lat = fleet["lat"]
        previous_lon = fleet["lon"]
        cleaned_waypoints = []
        for waypoint in waypoints:
            if "lat" not in waypoint or "lon" not in waypoint:
                raise ValueError(f"Fleet '{fleet_id}' waypoint requires 'lat' and 'lon'.")
            lat = float(waypoint["lat"])
            lon = float(waypoint["lon"])
            terrain.validate_movement_segment(fleet["unit_type"], previous_lat, previous_lon, lat, lon)
            cleaned_waypoints.append({"lat": lat, "lon": lon})
            previous_lat = lat
            previous_lon = lon
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
    award_income(state)
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


def award_income(state: dict) -> None:
    for side in SIDES:
        income = int(state["side_state"][side].get("income_per_turn", 0))
        if income:
            state["side_state"][side]["resources"] += income


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


def refresh_contacts_for_current_state(state: dict) -> None:
    visible = compute_visibility(state["fleets"])
    turn_marker = max(0, state["current_turn"] - 1)
    for side in SIDES:
        previous_contacts = state["contacts"].get(side, {})
        updated_contacts = {}
        for fleet in state["fleets"]:
            if fleet["side"] == side:
                continue
            if fleet["id"] in visible[side]:
                updated_contacts[fleet["id"]] = visible_contact_snapshot(fleet, last_seen_turn=turn_marker)
            elif fleet["id"] in previous_contacts:
                snapshot = dict(previous_contacts[fleet["id"]])
                snapshot["state"] = "last_known"
                updated_contacts[fleet["id"]] = snapshot
        state["contacts"][side] = updated_contacts


def fleet_by_id(state: dict, fleet_id: str) -> dict:
    for fleet in state["fleets"]:
        if fleet["id"] == fleet_id:
            return fleet
    raise ValueError(f"Unknown fleet '{fleet_id}'.")


def admin_update_fleet(state: dict, fleet_id: str, updates: dict) -> dict:
    if not isinstance(updates, dict):
        raise ValueError("Fleet updates must be a JSON object.")

    fleet = fleet_by_id(state, fleet_id)
    candidate = dict(fleet)
    allowed_fields = {
        "name",
        "side",
        "unit_type",
        "lat",
        "lon",
        "heading_deg",
        "speed_kts",
        "detection_radius_nm",
        "status",
    }
    for key in updates:
        if key not in allowed_fields:
            raise ValueError(f"Field '{key}' cannot be edited from the admin panel.")

    if "name" in updates:
        name = str(updates["name"]).strip()
        if not name:
            raise ValueError("Fleet name cannot be empty.")
        candidate["name"] = name
    if "side" in updates:
        side = str(updates["side"])
        if side not in SIDES:
            raise ValueError("Fleet side must be Blue or Red.")
        candidate["side"] = side
    if "unit_type" in updates:
        candidate["unit_type"] = str(updates["unit_type"]).strip() or candidate["unit_type"]
    if "lat" in updates:
        lat = float(updates["lat"])
        if lat < -90.0 or lat > 90.0:
            raise ValueError("Latitude must be between -90 and 90.")
        candidate["lat"] = lat
    if "lon" in updates:
        lon = float(updates["lon"])
        if lon < -180.0 or lon > 180.0:
            raise ValueError("Longitude must be between -180 and 180.")
        candidate["lon"] = lon
    if "heading_deg" in updates:
        candidate["heading_deg"] = float(updates["heading_deg"]) % 360.0
    if "speed_kts" in updates:
        speed = float(updates["speed_kts"])
        if speed < 0.0:
            raise ValueError("Speed cannot be negative.")
        candidate["speed_kts"] = speed
    if "detection_radius_nm" in updates:
        radius = float(updates["detection_radius_nm"])
        if radius < 0.0:
            raise ValueError("Detection radius cannot be negative.")
        candidate["detection_radius_nm"] = radius
    if "status" in updates:
        candidate["status"] = str(updates["status"]).strip() or candidate["status"]

    terrain.validate_unit_position(candidate["unit_type"], candidate["lat"], candidate["lon"])
    fleet.update(candidate)

    refresh_contacts_for_current_state(state)
    state["updated_at"] = utc_now()
    return admin_fleet_snapshot(fleet)


def build_fleet_for_side(state: dict, side: str, template_id: str) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side.")
    turn = get_or_create_turn_record(state, state["current_turn"])
    if side in turn["submissions"]:
        raise ValueError(f"{side} has already submitted turn {state['current_turn']}.")

    side_info = state["side_state"][side]
    template = catalog_entry_by_id(side_info["build_catalog"], template_id)
    cost = int(template["cost"])
    if side_info["resources"] < cost:
        raise ValueError(f"{side} does not have enough resources to build '{template['name']}'.")

    fleet = create_built_fleet(state, side, template)
    side_info["resources"] -= cost
    side_info["total_spent"] += cost
    state["fleets"].append(fleet)
    refresh_contacts_for_current_state(state)
    state["updated_at"] = utc_now()
    return fleet_view_snapshot(fleet)


def catalog_entry_by_id(catalog: list[dict], template_id: str) -> dict:
    for entry in catalog:
        if entry["id"] == template_id:
            return entry
    raise ValueError(f"Unknown build template '{template_id}'.")


def create_built_fleet(state: dict, side: str, template: dict) -> dict:
    state["fleet_counter"] = int(state.get("fleet_counter", len(state["fleets"]))) + 1
    counter = state["fleet_counter"]
    fleet_id = f"{side.lower()}_built_{counter}"
    spawn = state["side_state"][side]["spawn_point"]
    fleet = {
        "id": fleet_id,
        "sp_id": f"{side.upper()}_BUILT_{counter}",
        "name": f"{template['name']} {counter}",
        "side": side,
        "unit_type": template["unit_type"],
        "sea_power_type": template["sea_power_type"],
        "variant_reference": template["variant_reference"],
        "station_role": template["station_role"],
        "crew_skill": template["crew_skill"],
        "telegraph": template["telegraph"],
        "lat": float(spawn["lat"]),
        "lon": float(spawn["lon"]),
        "heading_deg": 0.0,
        "speed_kts": float(template["speed_kts"]),
        "detection_radius_nm": float(template["detection_radius_nm"]),
        "status": f"Built Turn {state['current_turn']}",
        "resource_cost": int(template["cost"]),
        "template_id": template["id"],
        "built_turn": state["current_turn"],
        "composition": copy.deepcopy(template["composition"]),
    }
    terrain.validate_unit_position(fleet["unit_type"], fleet["lat"], fleet["lon"])
    return fleet


def build_player_view(state: dict, side: str) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side for player view.")
    enemy_side = other_side(side)
    turn = get_or_create_turn_record(state, state["current_turn"])
    own_fleets = [fleet_view_snapshot(fleet) for fleet in state["fleets"] if fleet["side"] == side]
    contacts = sorted(state["contacts"].get(side, {}).values(), key=lambda item: item["sp_id"])
    own_submission = turn["submissions"].get(side)
    side_info = state["side_state"][side]
    return {
        "session_id": state["session_id"],
        "scenario_name": state["scenario_name"],
        "role": "player",
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
        "economy": player_side_state_snapshot(state, side),
        "can_build": own_submission is None,
    }


def build_admin_view(state: dict) -> dict:
    turn = get_or_create_turn_record(state, state["current_turn"])
    return {
        "session_id": state["session_id"],
        "scenario_name": state["scenario_name"],
        "role": "admin",
        "current_turn": state["current_turn"],
        "turn_duration_minutes": state["turn_duration_minutes"],
        "map_center": state["map_center"],
        "environment": state["environment"],
        "side_metadata": state["side_metadata"],
        "fleets": [admin_fleet_snapshot(fleet) for fleet in state["fleets"]],
        "turns": state["turns"],
        "current_turn_record": turn,
        "contacts": state["contacts"],
        "side_state": {side: player_side_state_snapshot(state, side) for side in SIDES},
    }


def player_side_state_snapshot(state: dict, side: str) -> dict:
    side_info = state["side_state"][side]
    return {
        "side": side,
        "resources": int(side_info["resources"]),
        "total_spent": int(side_info["total_spent"]),
        "income_per_turn": int(side_info.get("income_per_turn", 0)),
        "spawn_point": copy.deepcopy(side_info["spawn_point"]),
        "fleet_count": sum(1 for fleet in state["fleets"] if fleet["side"] == side),
        "build_catalog": [catalog_snapshot(entry) for entry in side_info["build_catalog"]],
    }


def catalog_snapshot(entry: dict) -> dict:
    return {
        "id": entry["id"],
        "name": entry["name"],
        "cost": entry["cost"],
        "unit_type": entry["unit_type"],
        "speed_kts": entry["speed_kts"],
        "detection_radius_nm": entry["detection_radius_nm"],
        "composition": copy.deepcopy(entry["composition"]),
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
        "resource_cost": fleet["resource_cost"],
        "composition": copy.deepcopy(fleet["composition"]),
    }


def export_scenario_ini(state: dict) -> str:
    center = state["map_center"]
    env = state["environment"]
    blue_fleets = [fleet for fleet in state["fleets"] if fleet["side"] == BLUE]
    red_fleets = [fleet for fleet in state["fleets"] if fleet["side"] == RED]
    blue_vessel_count = count_export_vessels(blue_fleets)
    red_vessel_count = count_export_vessels(red_fleets)

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
            f"NumberOfTaskforce1Vessels={blue_vessel_count}",
        ]
    )
    if red_vessel_count:
        lines.append(f"NumberOfTaskforce2Vessels={red_vessel_count}")

    append_taskforce(lines, center, "Taskforce1", blue_fleets)
    append_taskforce(lines, center, "Taskforce2", red_fleets)
    return "\n".join(lines) + "\n"


def count_export_vessels(fleets: list[dict]) -> int:
    total = 0
    for fleet in fleets:
        for item in fleet.get("composition", []):
            total += int(item.get("count", 1))
    return total


def append_taskforce(lines: list[str], center: dict, section_prefix: str, fleets: list[dict]) -> None:
    vessel_index = 1
    for fleet in fleets:
        east_nm, north_nm = relative_position_nm(center, fleet)
        for item in fleet.get("composition", []):
            repeat_count = int(item.get("count", 1))
            for copy_index in range(repeat_count):
                lines.extend(
                    [
                        f"[{section_prefix}Vessel{vessel_index}]",
                        f"Type={item['sea_power_type']}",
                        f"VariantReference={item['variant_reference']}",
                    ]
                )
                if fleet["station_role"]:
                    lines.append(f"StationRole={fleet['station_role']}")
                if item["name"]:
                    lines.append(f"Name={item['name']}" if repeat_count == 1 else f"Name={item['name']} {copy_index + 1}")
                lines.extend(
                    [
                        f"CrewSkill={fleet['crew_skill']}",
                        f"RelativePositionInNM={east_nm:.2f},0,{north_nm:.2f}",
                        f"Telegraph={fleet['telegraph']}",
                        f"Heading={int(round(fleet['heading_deg'])) % 360}",
                    ]
                )
                vessel_index += 1


def relative_position_nm(center: dict, fleet: dict) -> tuple[float, float]:
    lat_factor = 60.0
    north_nm = (fleet["lat"] - center["lat"]) * lat_factor
    avg_lat = math.radians((fleet["lat"] + center["lat"]) / 2.0)
    east_nm = (fleet["lon"] - center["lon"]) * lat_factor * math.cos(avg_lat)
    return east_nm, north_nm
