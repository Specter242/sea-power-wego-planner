from __future__ import annotations

import copy
import math
import re
from datetime import datetime, timezone

from . import terrain
from .catalogs import (
    build_ship_options,
    catalog_is_available,
    catalog_path_snapshot,
    class_profile,
    load_catalogs,
    rearm_cost_and_work,
    ship_option_for_id,
)
from .importer import parse_save_candidates, parse_save_file


BLUE = "Blue"
RED = "Red"
SIDES = (BLUE, RED)
ADMIN = "Admin"
DEFAULT_RESOURCE_POINTS = 100
DEFAULT_BUILD_COST = 10
STATE_VERSION = 2


DEFAULT_ENVIRONMENT = {
    "date": "1985,6,26",
    "time": "10,0",
    "convert_time_to_local": False,
    "sea_state": 3,
    "clouds": "Scattered_1",
    "wind_direction": "E",
    "load_background_data": False,
}

REPAIR_CATEGORY_MULTIPLIER = {
    "sensor": 0.75,
    "control": 0.75,
    "decoy": 0.75,
    "chaff": 0.75,
    "weapon": 1.0,
    "magazine": 1.0,
    "flightdeck": 1.0,
    "cargo": 1.0,
    "propulsion": 1.25,
    "power": 1.25,
    "rudder": 1.25,
    "sonar": 1.25,
    "towed": 1.25,
}

REPAIR_CATEGORY_TURNS = {
    "sensor": 0.25,
    "control": 0.25,
    "decoy": 0.25,
    "chaff": 0.25,
    "weapon": 0.5,
    "magazine": 0.5,
    "flightdeck": 0.5,
    "cargo": 0.5,
    "propulsion": 0.75,
    "power": 0.75,
    "rudder": 0.75,
    "sonar": 0.75,
    "towed": 0.75,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def other_side(side: str) -> str:
    return RED if side == BLUE else BLUE


def normalize_role_name(raw: str) -> str:
    value = str(raw or "").strip().lower()
    if value == "blue":
        return BLUE
    if value == "red":
        return RED
    if value == "admin":
        return ADMIN
    raise ValueError("Role must be Blue, Red, or Admin.")


def normalize_seed(seed: dict) -> dict:
    if not isinstance(seed, dict):
        raise ValueError("Scenario seed must be a JSON object.")
    if not seed.get("scenario_name"):
        raise ValueError("Scenario seed requires 'scenario_name'.")
    duration = seed.get("turn_duration_minutes")
    if not isinstance(duration, int) or duration <= 0:
        raise ValueError("'turn_duration_minutes' must be a positive integer.")
    return seed


def create_session_state(seed: dict) -> dict:
    seed = normalize_seed(seed)
    now = utc_now()
    return build_session_state(
        seed,
        created_at=now,
        updated_at=now,
        current_turn=1,
        turns=None,
        contacts=None,
    )


def create_blank_campaign_state(overrides: dict | None = None) -> dict:
    payload = overrides or {}
    catalogs = existing_or_loaded_catalogs(payload)
    seed = {
        "scenario_name": str(payload.get("scenario_name") or "New Campaign"),
        "turn_duration_minutes": int(payload.get("turn_duration_minutes", 60)),
        "map_center": payload.get("map_center") or {"lat": 0.0, "lon": 0.0},
        "environment": normalize_environment(payload.get("environment", {})),
        "ports": payload.get("ports")
        or [
            {"id": "blue_port_1", "side": BLUE, "name": "Blue Base", "lat": 0.0, "lon": -0.5, "radius_nm": 5.0},
            {"id": "red_port_1", "side": RED, "name": "Red Base", "lat": 0.0, "lon": 0.5, "radius_nm": 5.0},
        ],
        "sides": payload.get("sides")
        or {
            BLUE: {"resources": DEFAULT_RESOURCE_POINTS, "income_per_turn": 0},
            RED: {"resources": DEFAULT_RESOURCE_POINTS, "income_per_turn": 0},
        },
        "fleets": payload.get("fleets") or [],
        "ships": payload.get("ships") or [],
        "catalogs": catalogs,
        "catalog_paths": catalog_path_snapshot(catalogs),
        "terrain_enforced": bool(payload.get("terrain_enforced", False)),
    }
    return create_session_state(seed)


def create_imported_session_state(payload: dict) -> dict:
    catalogs = load_catalogs(payload.get("catalog_paths"))
    imported_seed = parse_save_file(
        payload.get("save_path", ""),
        catalogs,
        scenario_name=str(payload.get("scenario_name") or "") or None,
        turn_duration_minutes=int(payload.get("turn_duration_minutes", 60)),
    )
    imported_seed["catalog_paths"] = catalog_path_snapshot(catalogs)
    return create_session_state(imported_seed)


def import_catalogs_for_payload(state: dict, payload: dict) -> dict:
    if payload.get("catalog_paths"):
        return load_catalogs(payload.get("catalog_paths"))
    return existing_or_loaded_catalogs(state)


def preview_imported_save(state: dict, payload: dict) -> dict:
    catalogs = import_catalogs_for_payload(state, payload)
    preview = parse_save_candidates(
        payload.get("save_path", ""),
        catalogs,
        scenario_name=str(payload.get("scenario_name") or "") or None,
        turn_duration_minutes=int(payload.get("turn_duration_minutes", state.get("turn_duration_minutes", 60))),
    )
    preview["catalog_paths"] = catalog_path_snapshot(catalogs)
    return preview


def apply_imported_save_selection(state: dict, payload: dict) -> dict:
    catalogs = import_catalogs_for_payload(state, payload)
    preview = preview_imported_save(state, payload)
    selected_ship_ids = resolve_import_selection(preview, payload)
    if not selected_ship_ids:
        raise ValueError("Select at least one ship to import.")

    state["catalogs"] = catalogs
    state["catalog_paths"] = catalog_path_snapshot(catalogs)
    initialize_counters(state)

    imported_fleet_ids = []
    imported_ship_ids = []
    for candidate_fleet in preview.get("fleet_candidates", []):
        selected_ships = [ship for ship in candidate_fleet.get("ships", []) if ship.get("candidate_id") in selected_ship_ids]
        if not selected_ships:
            continue
        side = normalize_side_name(candidate_fleet["side"])
        fleet_name = ensure_unique_fleet_name(state, side, candidate_fleet["name"])
        state["fleet_counter"] = int(state.get("fleet_counter", 0)) + 1
        fleet_id = f"{side.lower()}_fleet_{state['fleet_counter']}"
        fleet = normalize_fleet_record(
            {
                "id": fleet_id,
                "sp_id": fleet_id.upper(),
                "name": fleet_name,
                "side": side,
                "unit_type": candidate_fleet.get("unit_type", "Surface"),
                "lat": candidate_fleet.get("lat", 0.0),
                "lon": candidate_fleet.get("lon", 0.0),
                "heading_deg": candidate_fleet.get("heading_deg", 0.0),
                "speed_kts": candidate_fleet.get("speed_kts", 0.0),
                "telegraph": candidate_fleet.get("telegraph", 2),
                "detection_radius_nm": candidate_fleet.get("detection_radius_nm", 100.0),
                "status": "Active",
                "docked_port_id": None,
                "station_role": candidate_fleet.get("station_role", ""),
            },
            state["fleet_counter"],
        )
        state["fleets"].append(fleet)
        imported_fleet_ids.append(fleet["id"])

        for candidate_ship in selected_ships:
            state["ship_counter"] = int(state.get("ship_counter", 0)) + 1
            ship_id = f"{side.lower()}_ship_{state['ship_counter']}"
            ship_name = ensure_unique_ship_name(state, side, candidate_ship["name"])
            ship = normalize_ship_record(
                {
                    **candidate_ship,
                    "id": ship_id,
                    "side": side,
                    "name": ship_name,
                    "fleet_id": fleet["id"],
                    "port_id": None,
                    "status": "Active",
                    "history": list(candidate_ship.get("history", [])) + [f"Imported from {preview['save_path']}"],
                    "lat": fleet["lat"],
                    "lon": fleet["lon"],
                    "heading_deg": fleet["heading_deg"],
                    "speed_kts": fleet["speed_kts"],
                    "telegraph": fleet["telegraph"],
                    "station_role": fleet["station_role"],
                    "unit_type": fleet["unit_type"],
                    "detection_radius_nm": fleet["detection_radius_nm"],
                },
                state["catalogs"],
                state["ship_counter"],
            )
            state["ships"].append(ship)
            fleet["ship_ids"].append(ship["id"])
            imported_ship_ids.append(ship["id"])

    if not imported_ship_ids:
        raise ValueError("Selection did not include any importable ships.")

    refresh_all_fleets(state)
    refresh_contacts_for_current_state(state)
    state["updated_at"] = utc_now()
    return {
        "fleet_count": len(imported_fleet_ids),
        "ship_count": len(imported_ship_ids),
        "fleet_ids": imported_fleet_ids,
        "ship_ids": imported_ship_ids,
        "campaign": build_admin_view(state),
    }


def resolve_import_selection(preview: dict, payload: dict) -> set[str]:
    has_ship_selection = "selected_ship_ids" in payload
    has_fleet_selection = "selected_fleet_ids" in payload
    explicit_ship_ids = {str(item) for item in (payload.get("selected_ship_ids") or []) if str(item).strip()}
    explicit_fleet_ids = {str(item) for item in (payload.get("selected_fleet_ids") or []) if str(item).strip()}
    fleet_lookup = {fleet["candidate_id"]: fleet for fleet in preview.get("fleet_candidates", [])}
    selected_ship_ids = set(explicit_ship_ids)
    for fleet_id in explicit_fleet_ids:
        fleet = fleet_lookup.get(fleet_id)
        if fleet is None:
            raise ValueError(f"Unknown import fleet selection '{fleet_id}'.")
        selected_ship_ids.update(ship["candidate_id"] for ship in fleet.get("ships", []))
    if has_ship_selection or has_fleet_selection:
        valid_ship_ids = {ship["candidate_id"] for fleet in preview.get("fleet_candidates", []) for ship in fleet.get("ships", [])}
        unknown_ship_ids = selected_ship_ids - valid_ship_ids
        if unknown_ship_ids:
            raise ValueError(f"Unknown import ship selection '{sorted(unknown_ship_ids)[0]}'.")
        return selected_ship_ids
    return {ship["candidate_id"] for fleet in preview.get("fleet_candidates", []) for ship in fleet.get("ships", [])}


def build_session_state(
    seed: dict,
    *,
    created_at: str,
    updated_at: str,
    current_turn: int,
    turns: dict | None,
    contacts: dict | None,
) -> dict:
    catalogs = existing_or_loaded_catalogs(seed)
    fleet_seed = seed.get("fleets", [])
    top_level_ships = seed.get("ships", [])

    fleets: list[dict] = []
    ships: list[dict] = []

    if top_level_ships:
        ships = [normalize_ship_record(entry, catalogs, index + 1) for index, entry in enumerate(top_level_ships)]
        fleets = [normalize_fleet_record(entry, index + 1) for index, entry in enumerate(fleet_seed, start=1)]
        link_existing_ships_to_fleets(fleets, ships)
    else:
        fleets, ships = expand_seed_fleets(fleet_seed, catalogs)

    side_source = seed.get("side_state") or seed.get("sides") or {}
    side_state = normalize_side_state(side_source)
    ports = normalize_ports(seed.get("ports"), fleets, side_source)

    state = {
        "version": STATE_VERSION,
        "scenario_name": seed["scenario_name"],
        "turn_duration_minutes": int(seed["turn_duration_minutes"]),
        "current_turn": int(current_turn),
        "status": "open",
        "created_at": created_at,
        "updated_at": updated_at,
        "terrain_enforced": bool(seed.get("terrain_enforced", False)),
        "environment": normalize_environment(seed.get("environment", {})),
        "map_center": normalize_map_center(seed.get("map_center"), fleets, ports),
        "side_state": side_state,
        "ports": ports,
        "fleets": fleets,
        "ships": ships,
        "repair_queue": copy.deepcopy(seed.get("repair_queue", [])),
        "rearm_queue": copy.deepcopy(seed.get("rearm_queue", [])),
        "catalogs": catalogs,
        "catalog_paths": catalog_path_snapshot(catalogs),
        "turns": copy.deepcopy(turns or {}),
        "contacts": copy.deepcopy(contacts or {BLUE: {}, RED: {}}),
    }

    assign_docked_ship_ports(state)
    refresh_all_fleets(state)
    validate_state(state)
    get_or_create_turn_record(state, state["current_turn"])
    refresh_contacts_for_current_state(state)
    initialize_counters(state)
    return state


def upgrade_state(state: dict) -> dict:
    if not isinstance(state, dict):
        raise ValueError("Session state must be a JSON object.")
    if state.get("version") == STATE_VERSION and state.get("ships") is not None:
        state.setdefault("repair_queue", [])
        state.setdefault("rearm_queue", [])
        state["catalogs"] = existing_or_loaded_catalogs(state)
        state["catalog_paths"] = catalog_path_snapshot(state["catalogs"])
        state.setdefault("ports", [])
        state.setdefault("contacts", {BLUE: {}, RED: {}})
        state["contacts"].setdefault(BLUE, {})
        state["contacts"].setdefault(RED, {})
        state.setdefault("turns", {})
        state.setdefault("terrain_enforced", False)
        get_or_create_turn_record(state, int(state.get("current_turn", 1)))
        initialize_counters(state)
        refresh_all_fleets(state)
        assign_docked_ship_ports(state)
        state.pop("tokens", None)
        state.pop("session_id", None)
        return state

    legacy_seed = {
        "scenario_name": state.get("scenario_name", "Sea Power Campaign"),
        "turn_duration_minutes": int(state.get("turn_duration_minutes", 60)),
        "map_center": state.get("map_center"),
        "environment": state.get("environment", {}),
        "sides": state.get("side_state", {}),
        "fleets": state.get("fleets", []),
        "terrain_enforced": bool(state.get("terrain_enforced", False)),
        "catalogs": existing_or_loaded_catalogs(state),
        "catalog_paths": state.get("catalog_paths") or {},
    }
    return build_session_state(
        legacy_seed,
        created_at=str(state.get("created_at") or utc_now()),
        updated_at=str(state.get("updated_at") or utc_now()),
        current_turn=int(state.get("current_turn", 1)),
        turns=state.get("turns", {}),
        contacts=state.get("contacts", {BLUE: {}, RED: {}}),
    )


def normalize_environment(environment: dict) -> dict:
    normalized = dict(DEFAULT_ENVIRONMENT)
    normalized.update(environment or {})
    return normalized


def normalize_side_state(source: dict) -> dict:
    normalized = {}
    for side in SIDES:
        side_source = source.get(side, {}) if isinstance(source, dict) else {}
        normalized[side] = {
            "display_name": str(side_source.get("display_name") or side),
            "resources": int(side_source.get("resources", DEFAULT_RESOURCE_POINTS)),
            "total_spent": int(side_source.get("total_spent", 0)),
            "income_per_turn": int(side_source.get("income_per_turn", 0)),
            "build_catalog": copy.deepcopy(side_source.get("build_catalog", [])),
        }
    return normalized


def normalize_ports(port_seed: list | None, fleets: list[dict], side_source: dict) -> list[dict]:
    ports = []
    if isinstance(port_seed, list) and port_seed:
        for index, port in enumerate(port_seed, start=1):
            ports.append(
                {
                    "id": str(port.get("id") or f"port_{index}"),
                    "side": normalize_side_name(str(port.get("side") or BLUE)),
                    "name": str(port.get("name") or f"Port {index}"),
                    "lat": float(port.get("lat", 0.0)),
                    "lon": float(port.get("lon", 0.0)),
                    "radius_nm": float(port.get("radius_nm", 5.0)),
                    "kind": str(port.get("kind") or "naval_base"),
                }
            )
        return ports

    for side in SIDES:
        spawn_point = {}
        if isinstance(side_source, dict):
            spawn_point = (side_source.get(side, {}) or {}).get("spawn_point", {}) or {}
        if "lat" in spawn_point and "lon" in spawn_point:
            lat = float(spawn_point["lat"])
            lon = float(spawn_point["lon"])
        else:
            side_fleets = [fleet for fleet in fleets if fleet["side"] == side]
            if side_fleets:
                lat = sum(fleet["lat"] for fleet in side_fleets) / len(side_fleets)
                lon = sum(fleet["lon"] for fleet in side_fleets) / len(side_fleets)
            else:
                lat = 0.0
                lon = 0.0
        ports.append(
            {
                "id": f"{side.lower()}_port_1",
                "side": side,
                "name": f"{side} Base",
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "radius_nm": 5.0,
                "kind": "naval_base",
            }
        )
    return ports


def normalize_map_center(map_center: dict | None, fleets: list[dict], ports: list[dict]) -> dict:
    if map_center and "lat" in map_center and "lon" in map_center:
        return {"lat": float(map_center["lat"]), "lon": float(map_center["lon"])}

    anchors = fleets or ports
    if not anchors:
        return {"lat": 0.0, "lon": 0.0}
    avg_lat = sum(item["lat"] for item in anchors) / len(anchors)
    avg_lon = sum(item["lon"] for item in anchors) / len(anchors)
    return {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4)}


def existing_or_loaded_catalogs(source: dict) -> dict:
    catalogs = source.get("catalogs")
    if isinstance(catalogs, dict) and catalog_is_available(catalogs):
        loaded = copy.deepcopy(catalogs)
        loaded.setdefault("work_units_per_turn", 8.0)
        loaded.setdefault("ammo_database", {})
        loaded.setdefault("ship_costs", {})
        loaded.setdefault("weapon_prices", {})
        loaded.setdefault("html_loadouts", {})
        loaded.setdefault("save_inference", {})
        loaded.setdefault("repair_nominal_overrides", {})
        loaded.setdefault(
            "paths",
            {
                "ammo_database": "",
                "cost_matrix_html": "",
                "sav_files": [],
            },
        )
        loaded.setdefault("status", {})
        loaded.setdefault("ship_index", sorted(set(loaded["ammo_database"]) | set(loaded["ship_costs"]) | set(loaded["save_inference"])))
        loaded.setdefault(
            "ship_options",
            build_ship_options(
                loaded["ship_index"],
                loaded["ship_costs"],
                loaded["ammo_database"],
                loaded["html_loadouts"],
                loaded["save_inference"],
            ),
        )
        return loaded
    return load_catalogs(source.get("catalog_paths"))


def expand_seed_fleets(fleet_seed: list, catalogs: dict) -> tuple[list[dict], list[dict]]:
    fleets = []
    ships = []
    ship_counter = 0
    for index, entry in enumerate(fleet_seed or [], start=1):
        fleet = normalize_fleet_record(entry, index)
        child_entries = []
        if entry.get("ships"):
            child_entries = entry.get("ships", [])
        elif entry.get("composition"):
            child_entries = composition_to_ship_entries(entry.get("composition", []), entry)
        else:
            child_entries = [default_ship_entry_from_fleet(entry, fleet["name"])]

        ship_ids = []
        for child in child_entries:
            ship_counter += 1
            ship = normalize_ship_record(child, catalogs, ship_counter)
            ship["side"] = fleet["side"]
            ship["fleet_id"] = fleet["id"]
            ship["port_id"] = fleet.get("docked_port_id")
            ship["lat"] = fleet["lat"]
            ship["lon"] = fleet["lon"]
            ship["heading_deg"] = fleet["heading_deg"]
            ship["speed_kts"] = fleet["speed_kts"]
            ship["telegraph"] = fleet["telegraph"]
            ship["station_role"] = fleet["station_role"]
            ship["unit_type"] = fleet["unit_type"]
            ship["detection_radius_nm"] = fleet["detection_radius_nm"]
            ship_ids.append(ship["id"])
            ships.append(ship)
        fleet["ship_ids"] = ship_ids
        fleets.append(fleet)
    return fleets, ships


def normalize_fleet_record(entry: dict, index: int) -> dict:
    side = normalize_side_name(str(entry.get("side") or BLUE))
    fleet_id = str(entry.get("id") or f"fleet_{index:02d}")
    return {
        "id": fleet_id,
        "sp_id": str(entry.get("sp_id") or fleet_id.upper()),
        "name": str(entry.get("name") or fleet_id),
        "side": side,
        "unit_type": str(entry.get("unit_type", "Surface")),
        "lat": float(entry.get("lat", 0.0)),
        "lon": float(entry.get("lon", 0.0)),
        "heading_deg": float(entry.get("heading_deg", 0.0)) % 360.0,
        "speed_kts": float(entry.get("speed_kts", 0.0)),
        "telegraph": int(entry.get("telegraph", 2)),
        "detection_radius_nm": float(entry.get("detection_radius_nm", 100.0)),
        "status": str(entry.get("status") or "Active"),
        "ship_ids": [str(ship_id) for ship_id in entry.get("ship_ids", [])],
        "docked_port_id": entry.get("docked_port_id"),
        "station_role": str(entry.get("station_role", "")),
    }


def normalize_ship_record(entry: dict, catalogs: dict, index: int) -> dict:
    sea_power_type = str(entry.get("sea_power_type") or entry.get("Type") or "usn_dd_spruance")
    profile = class_profile(catalogs, sea_power_type)
    ship_id = str(entry.get("id") or f"ship_{index:03d}")
    max_loadout = copy.deepcopy(profile["max_loadout"])
    loadout = {str(key): int(value) for key, value in (entry.get("loadout") or {}).items()}
    if not loadout and max_loadout:
        loadout = copy.deepcopy(max_loadout)
    subsystems = []
    for subsystem in entry.get("subsystems", []) or []:
        subsystems.append(
            {
                "id": str(subsystem.get("id") or f"{ship_id}_subsystem_{len(subsystems) + 1}"),
                "name": str(subsystem.get("name") or subsystem.get("id") or "Subsystem"),
                "category": str(subsystem.get("category") or "control"),
                "current_integrity": float(subsystem.get("current_integrity", subsystem.get("nominal_integrity", 1))),
                "nominal_integrity": int(subsystem.get("nominal_integrity", 1)),
                "repairable": bool(subsystem.get("repairable", True)),
                "state": str(subsystem.get("state") or "operational"),
            }
        )

    return {
        "id": ship_id,
        "side": normalize_side_name(str(entry.get("side") or BLUE)),
        "name": str(entry.get("name") or ship_id),
        "sea_power_type": sea_power_type,
        "variant_reference": str(entry.get("variant_reference") or "Variant1"),
        "fleet_id": entry.get("fleet_id"),
        "port_id": entry.get("port_id"),
        "status": str(entry.get("status") or "Active"),
        "class_costs": dict(entry.get("class_costs") or profile["costs"]),
        "max_loadout": max_loadout,
        "loadout": loadout,
        "subsystems": subsystems,
        "history": [str(item) for item in (entry.get("history") or [])],
        "lat": float(entry.get("lat", 0.0)),
        "lon": float(entry.get("lon", 0.0)),
        "heading_deg": float(entry.get("heading_deg", 0.0)) % 360.0,
        "speed_kts": float(entry.get("speed_kts", 0.0)),
        "telegraph": int(entry.get("telegraph", 2)),
        "station_role": str(entry.get("station_role", "")),
        "unit_type": str(entry.get("unit_type", "Surface")),
        "detection_radius_nm": float(entry.get("detection_radius_nm", 100.0)),
    }


def link_existing_ships_to_fleets(fleets: list[dict], ships: list[dict]) -> None:
    fleet_lookup = {fleet["id"]: fleet for fleet in fleets}
    for ship in ships:
        fleet_id = ship.get("fleet_id")
        if fleet_id and fleet_id in fleet_lookup:
            fleet_lookup[fleet_id]["ship_ids"].append(ship["id"])
            fleet_lookup[fleet_id]["side"] = ship["side"]
    for fleet in fleets:
        if not fleet["ship_ids"]:
            fleet["ship_ids"] = [ship["id"] for ship in ships if ship.get("fleet_id") == fleet["id"]]


def composition_to_ship_entries(composition: list[dict], fleet_entry: dict) -> list[dict]:
    entries = []
    for item in composition:
        count = int(item.get("count", 1))
        for copy_index in range(count):
            base_name = str(item.get("name") or fleet_entry.get("name") or "Ship")
            name = base_name if count == 1 else f"{base_name} {copy_index + 1}"
            entries.append(
                {
                    "name": name,
                    "sea_power_type": str(item.get("sea_power_type") or fleet_entry.get("sea_power_type") or "usn_dd_spruance"),
                    "variant_reference": str(item.get("variant_reference") or fleet_entry.get("variant_reference") or "Variant1"),
                }
            )
    return entries


def default_ship_entry_from_fleet(entry: dict, fallback_name: str) -> dict:
    return {
        "name": str(entry.get("name") or fallback_name),
        "sea_power_type": str(entry.get("sea_power_type") or "usn_dd_spruance"),
        "variant_reference": str(entry.get("variant_reference") or "Variant1"),
    }


def initialize_counters(state: dict) -> None:
    state["fleet_counter"] = max([0] + [extract_trailing_number(fleet["id"]) for fleet in state["fleets"]])
    state["ship_counter"] = max([0] + [extract_trailing_number(ship["id"]) for ship in state["ships"]])
    state["port_counter"] = max([0] + [extract_trailing_number(port["id"]) for port in state["ports"]])


def extract_trailing_number(value: str) -> int:
    digits = ""
    for character in reversed(str(value)):
        if not character.isdigit():
            break
        digits = character + digits
    return int(digits) if digits else 0


def validate_state(state: dict) -> None:
    for port in state["ports"]:
        validate_lat_lon(port["lat"], port["lon"])
    for fleet in state["fleets"]:
        validate_lat_lon(fleet["lat"], fleet["lon"])
        validate_state_position(state, fleet["unit_type"], fleet["lat"], fleet["lon"])


def validate_lat_lon(lat: float, lon: float) -> None:
    if lat < -90.0 or lat > 90.0:
        raise ValueError("Latitude must be between -90 and 90.")
    if lon < -180.0 or lon > 180.0:
        raise ValueError("Longitude must be between -180 and 180.")


def validate_state_position(state: dict, unit_type: str, lat: float, lon: float) -> None:
    if state.get("terrain_enforced"):
        terrain.validate_unit_position(unit_type, lat, lon)


def validate_state_movement(state: dict, unit_type: str, start_point: dict, end_point: dict) -> None:
    if state.get("terrain_enforced"):
        terrain.validate_movement_segment(unit_type, start_point["lat"], start_point["lon"], end_point["lat"], end_point["lon"])


def get_or_create_turn_record(state: dict, turn_number: int) -> dict:
    key = str(int(turn_number))
    turn = state["turns"].get(key)
    if turn is None:
        turn = {"turn_number": int(turn_number), "status": "open", "submissions": {}}
        state["turns"][key] = turn
    return turn


def compute_visibility(fleets: list[dict]) -> dict[str, set[str]]:
    visibility = {BLUE: set(), RED: set()}
    for observer in fleets:
        if observer["docked_port_id"]:
            continue
        for target in fleets:
            if observer["side"] == target["side"]:
                continue
            if nautical_miles_between(observer, target) <= float(observer.get("detection_radius_nm", 100.0)):
                visibility[observer["side"]].add(target["id"])
    return visibility


def visible_contact_snapshot(fleet: dict, last_seen_turn: int) -> dict:
    return {
        "fleet_id": fleet["id"],
        "sp_id": fleet["sp_id"],
        "name": fleet["name"],
        "unit_type": fleet["unit_type"],
        "lat": fleet["lat"],
        "lon": fleet["lon"],
        "heading_deg": fleet["heading_deg"],
        "ship_count": len(fleet["ship_ids"]),
        "last_seen_turn": last_seen_turn,
        "state": "visible",
    }


def refresh_contacts_for_current_state(state: dict) -> None:
    visible = compute_visibility(state["fleets"])
    current_turn = int(state.get("current_turn", 1))
    for side in SIDES:
        previous_contacts = state["contacts"].get(side, {})
        updated_contacts = {}
        for fleet in state["fleets"]:
            if fleet["side"] == side:
                continue
            if fleet["id"] in visible[side]:
                updated_contacts[fleet["id"]] = visible_contact_snapshot(fleet, last_seen_turn=current_turn)
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


def ship_by_id(state: dict, ship_id: str) -> dict:
    for ship in state["ships"]:
        if ship["id"] == ship_id:
            return ship
    raise ValueError(f"Unknown ship '{ship_id}'.")


def port_by_id(state: dict, port_id: str) -> dict:
    for port in state["ports"]:
        if port["id"] == port_id:
            return port
    raise ValueError(f"Unknown port '{port_id}'.")


def player_side_state_snapshot(state: dict, side: str) -> dict:
    side_info = state["side_state"][side]
    return {
        "side": side,
        "display_name": side_info["display_name"],
        "resources": int(side_info["resources"]),
        "total_spent": int(side_info["total_spent"]),
        "income_per_turn": int(side_info["income_per_turn"]),
        "fleet_count": sum(1 for fleet in state["fleets"] if fleet["side"] == side),
        "ship_count": sum(1 for ship in state["ships"] if ship["side"] == side),
        "port_count": sum(1 for port in state["ports"] if port["side"] == side),
    }


def build_player_view(state: dict, side: str) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side for player view.")
    turn = get_or_create_turn_record(state, state["current_turn"])
    own_submission = turn["submissions"].get(side)
    return {
        "scenario_name": state["scenario_name"],
        "role": "player",
        "side": side,
        "current_turn": state["current_turn"],
        "turn_duration_minutes": state["turn_duration_minutes"],
        "map_center": state["map_center"],
        "environment": state["environment"],
        "status": turn["status"],
        "own_submitted": own_submission is not None,
        "opponent_ready": other_side(side) in turn["submissions"],
        "can_submit": own_submission is None,
        "orders": copy.deepcopy((own_submission or {}).get("orders", [])),
        "ports": [port_view_snapshot(port) for port in state["ports"] if port["side"] == side],
        "fleets": [fleet_view_snapshot(state, fleet, role=side) for fleet in state["fleets"] if fleet["side"] == side],
        "ships": [ship_view_snapshot(state, ship, state["catalogs"]) for ship in state["ships"] if ship["side"] == side],
        "contacts": sorted(state["contacts"].get(side, {}).values(), key=lambda item: item["sp_id"]),
        "repair_queue": [copy.deepcopy(job) for job in state["repair_queue"] if job["side"] == side],
        "rearm_queue": [copy.deepcopy(job) for job in state["rearm_queue"] if job["side"] == side],
        "economy": player_side_state_snapshot(state, side),
        "side_state": {side_name: player_side_state_snapshot(state, side_name) for side_name in SIDES},
        "catalogs": view_catalog_snapshot(state["catalogs"]),
    }


def build_admin_view(state: dict) -> dict:
    turn = get_or_create_turn_record(state, state["current_turn"])
    return {
        "scenario_name": state["scenario_name"],
        "role": ADMIN,
        "current_turn": state["current_turn"],
        "turn_duration_minutes": state["turn_duration_minutes"],
        "map_center": state["map_center"],
        "environment": state["environment"],
        "status": turn["status"],
        "ports": [port_view_snapshot(port) for port in state["ports"]],
        "fleets": [fleet_view_snapshot(state, fleet, role=ADMIN) for fleet in state["fleets"]],
        "ships": [ship_view_snapshot(state, ship, state["catalogs"]) for ship in state["ships"]],
        "repair_queue": copy.deepcopy(state["repair_queue"]),
        "rearm_queue": copy.deepcopy(state["rearm_queue"]),
        "turns": copy.deepcopy(state["turns"]),
        "current_turn_record": copy.deepcopy(turn),
        "contacts": copy.deepcopy(state["contacts"]),
        "side_state": {side: player_side_state_snapshot(state, side) for side in SIDES},
        "catalogs": view_catalog_snapshot(state["catalogs"]),
    }


def build_role_view(state: dict, role: str) -> dict:
    normalized = normalize_role_name(role)
    if normalized == ADMIN:
        return build_admin_view(state)
    return build_player_view(state, normalized)


def view_catalog_snapshot(catalogs: dict) -> dict:
    return {
        "ship_index": list(catalogs.get("ship_index", [])),
        "ship_options": copy.deepcopy(catalogs.get("ship_options", [])),
        "paths": copy.deepcopy(catalogs.get("paths", {})),
        "status": copy.deepcopy(catalogs.get("status", {})),
        "work_units_per_turn": float(catalogs.get("work_units_per_turn", 8.0)),
        "weapon_price_count": len(catalogs.get("weapon_prices", {})),
        "ship_cost_count": len(catalogs.get("ship_costs", {})),
        "save_inference_count": len(catalogs.get("save_inference", {})),
    }


def fleet_view_snapshot(state: dict, fleet: dict, *, role: str | None = None) -> dict:
    can_draft_movement, movement_disabled_reason = fleet_movement_affordance(fleet, role)
    ships = [ship_view_snapshot(state, ship, state["catalogs"]) for ship in ships_for_fleet(state, fleet["id"])]
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
        "telegraph": fleet["telegraph"],
        "detection_radius_nm": fleet["detection_radius_nm"],
        "status": fleet["status"],
        "ship_ids": list(fleet["ship_ids"]),
        "ship_count": len(fleet["ship_ids"]),
        "docked_port_id": fleet.get("docked_port_id"),
        "station_role": fleet.get("station_role", ""),
        "can_draft_movement": can_draft_movement,
        "movement_disabled_reason": movement_disabled_reason,
        "ships": ships,
    }


def ship_view_snapshot(state: dict, ship: dict, catalogs: dict | None = None) -> dict:
    catalogs = catalogs or {}
    ship_option = ship_option_for_id(catalogs, ship["sea_power_type"])
    class_costs = copy.deepcopy(ship.get("class_costs", {}))
    transfer_options = eligible_transfer_fleet_options(state, ship)
    dock_options = eligible_ship_dock_port_options(state, ship)
    can_move_to_reserve, move_to_reserve_reason = ship_can_move_to_reserve(state, ship)
    can_detach = bool(ship.get("fleet_id"))
    return {
        "id": ship["id"],
        "side": ship["side"],
        "name": ship["name"],
        "sea_power_type": ship["sea_power_type"],
        "class_display_name": ship_option["name"],
        "class_role": ship_option["role"],
        "class_group": ship_option.get("class_group", "Other"),
        "nation_code": ship_option["nation_code"],
        "nation_label": ship_option["nation_label"],
        "class_display_label": ship_option["display_label"],
        "class_search_text": ship_option.get("search_text", ""),
        "class_sensors": ship_option.get("sensors", ""),
        "class_summary_note": ship_option.get("summary_note", ""),
        "loadout_source": ship_option.get("loadout_reference", ""),
        "variant_reference": ship["variant_reference"],
        "fleet_id": ship.get("fleet_id"),
        "port_id": ship.get("port_id"),
        "status": ship["status"],
        "class_costs": class_costs,
        "class_base_hull": float(class_costs.get("base_hull", 0.0) or 0.0),
        "class_weapons_value": float(class_costs.get("weapons_value", 0.0) or 0.0),
        "class_total_value": float(class_costs.get("total_value", 0.0) or 0.0),
        "max_loadout": copy.deepcopy(ship.get("max_loadout", {})),
        "loadout": copy.deepcopy(ship.get("loadout", {})),
        "weapon_entries": ship_weapon_entries(ship, catalogs),
        "subsystems": copy.deepcopy(ship.get("subsystems", [])),
        "history": copy.deepcopy(ship.get("history", [])),
        "lat": ship["lat"],
        "lon": ship["lon"],
        "heading_deg": ship["heading_deg"],
        "speed_kts": ship["speed_kts"],
        "unit_type": ship["unit_type"],
        "eligible_transfer_fleets": transfer_options,
        "eligible_dock_ports": dock_options,
        "can_transfer": bool(transfer_options),
        "transfer_reason": "" if transfer_options else transfer_unavailable_reason(ship),
        "can_move_to_reserve": can_move_to_reserve,
        "move_to_reserve_reason": move_to_reserve_reason,
        "can_detach": can_detach,
        "detach_reason": "" if can_detach else "Reserve ships are already detached from any fleet.",
        "can_dock": bool(dock_options),
        "dock_reason": "" if dock_options else dock_unavailable_reason(ship),
    }


def ship_weapon_entries(ship: dict, catalogs: dict) -> list[dict]:
    weapon_prices = catalogs.get("weapon_prices", {}) if isinstance(catalogs, dict) else {}
    loadout = ship.get("loadout", {}) or {}
    max_loadout = ship.get("max_loadout", {}) or {}
    weapon_ids = sorted(set(loadout) | set(max_loadout))
    entries = []
    for weapon_id in weapon_ids:
        pricing = weapon_prices.get(weapon_id, {})
        entries.append(
            {
                "weapon_id": weapon_id,
                "name": str(pricing.get("name") or weapon_id),
                "current": int(loadout.get(weapon_id, 0)),
                "max": int(max_loadout.get(weapon_id, 0)),
                "basis": str(pricing.get("basis") or ""),
                "unit_price": float(pricing.get("unit_price", 0.0) or 0.0),
            }
        )
    return entries


def port_view_snapshot(port: dict) -> dict:
    return {
        "id": port["id"],
        "side": port["side"],
        "name": port["name"],
        "lat": port["lat"],
        "lon": port["lon"],
        "radius_nm": port["radius_nm"],
        "kind": port["kind"],
    }


def fleet_movement_affordance(fleet: dict, role: str | None) -> tuple[bool, str]:
    if role == ADMIN:
        return False, "ADMIN view cannot draft movement."
    if role in SIDES and fleet["side"] != role:
        return False, "Only friendly fleets can draft movement."
    if not fleet.get("ship_ids"):
        return False, "Fleets without ships cannot move."
    if fleet.get("docked_port_id"):
        return False, "Docked fleets cannot draft movement."
    return True, ""


def fleet_option_snapshot(state: dict, fleet: dict, *, distance_nm: float | None = None) -> dict:
    snapshot = {
        "id": fleet["id"],
        "name": fleet["name"],
        "ship_count": len(fleet.get("ship_ids", [])),
        "docked_port_id": fleet.get("docked_port_id"),
        "port_name": port_name_by_id(state, fleet.get("docked_port_id")),
        "status": fleet.get("status", ""),
    }
    if distance_nm is not None:
        snapshot["distance_nm"] = round(float(distance_nm), 3)
    return snapshot


def port_option_snapshot(port: dict, *, distance_nm: float | None = None) -> dict:
    snapshot = {
        "id": port["id"],
        "name": port["name"],
        "side": port["side"],
        "radius_nm": float(port.get("radius_nm", 5.0)),
        "kind": port.get("kind", "naval_base"),
    }
    if distance_nm is not None:
        snapshot["distance_nm"] = round(float(distance_nm), 3)
    return snapshot


def port_name_by_id(state: dict, port_id: str | None) -> str:
    if not port_id:
        return ""
    try:
        return port_by_id(state, port_id)["name"]
    except ValueError:
        return ""


def eligible_transfer_fleet_options(state: dict, ship: dict) -> list[dict]:
    fleets = [fleet for fleet in state["fleets"] if fleet["side"] == ship["side"] and fleet["id"] != ship.get("fleet_id")]
    if not fleets:
        return []
    if not ship.get("fleet_id"):
        port_id = str(ship.get("port_id") or "")
        return [fleet_option_snapshot(state, fleet) for fleet in fleets if fleet.get("docked_port_id") == port_id]
    source_fleet = fleet_by_id(state, ship["fleet_id"])
    options = []
    for fleet in fleets:
        if not fleets_can_transfer(source_fleet, fleet):
            continue
        distance_nm = None if source_fleet.get("docked_port_id") == fleet.get("docked_port_id") and source_fleet.get("docked_port_id") else nautical_miles_between(source_fleet, fleet)
        options.append(fleet_option_snapshot(state, fleet, distance_nm=distance_nm))
    return options


def eligible_ship_dock_port_options(state: dict, ship: dict) -> list[dict]:
    if not ship.get("fleet_id"):
        return []
    source_fleet = fleet_by_id(state, ship["fleet_id"])
    options = []
    for port in state["ports"]:
        if port["side"] != ship["side"]:
            continue
        if port["id"] == source_fleet.get("docked_port_id"):
            continue
        distance_nm = nautical_miles_between(source_fleet, port)
        if distance_nm <= float(port.get("radius_nm", 5.0)):
            options.append(port_option_snapshot(port, distance_nm=distance_nm))
    options.sort(key=lambda item: (item.get("distance_nm", 999999.0), item["name"]))
    return options


def ship_can_move_to_reserve(state: dict, ship: dict) -> tuple[bool, str]:
    if not ship.get("fleet_id"):
        return False, "Ship is already in reserve."
    source_fleet = fleet_by_id(state, ship["fleet_id"])
    port_id = ship.get("port_id") or source_fleet.get("docked_port_id")
    if not port_id:
        return False, "Ship must be docked at a friendly port to enter reserve."
    port = port_by_id(state, port_id)
    if port["side"] != ship["side"]:
        return False, "Ship must be docked at a friendly port to enter reserve."
    return True, ""


def transfer_unavailable_reason(ship: dict) -> str:
    if ship.get("fleet_id"):
        return "No nearby friendly fleets are available for transfer."
    return "Reserve ships can only join fleets docked at the same port."


def dock_unavailable_reason(ship: dict) -> str:
    if not ship.get("fleet_id"):
        if ship.get("port_id"):
            return "Reserve ships must join a fleet before moving to another port."
        return "Only ships in fleets can dock at nearby ports."
    return "No nearby friendly ports are available for docking."


def submit_turn(state: dict, side: str, turn_number: int, orders: list[dict]) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side.")
    turn = get_or_create_turn_record(state, state["current_turn"])
    if int(turn_number) != int(state["current_turn"]):
        raise ValueError(f"Turn {turn_number} is not the current turn.")
    if side in turn["submissions"]:
        raise ValueError(f"{side} has already submitted turn {state['current_turn']}.")

    normalized_orders = normalize_orders(state, side, orders)
    turn["submissions"][side] = {"submitted_at": utc_now(), "orders": normalized_orders}
    state["updated_at"] = utc_now()
    return {
        "resolved": False,
        "turn_number": state["current_turn"],
        "orders": normalized_orders,
        "both_ready": len(turn["submissions"]) == len(SIDES),
    }


def normalize_orders(state: dict, side: str, orders: list[dict]) -> list[dict]:
    if not isinstance(orders, list):
        raise ValueError("Orders must be a list.")
    owned_fleet_ids = {fleet["id"] for fleet in state["fleets"] if fleet["side"] == side}
    cleaned_orders = []
    seen = set()
    for order in orders:
        fleet_id = str(order.get("fleet_id") or "")
        if fleet_id not in owned_fleet_ids:
            raise ValueError(f"Fleet '{fleet_id}' does not belong to {side}.")
        if fleet_id in seen:
            raise ValueError(f"Fleet '{fleet_id}' has duplicate orders.")
        fleet = fleet_by_id(state, fleet_id)
        if fleet.get("docked_port_id"):
            raise ValueError(f"Fleet '{fleet_id}' is docked and cannot move.")
        waypoints = order.get("waypoints", [])
        if not isinstance(waypoints, list):
            raise ValueError(f"Fleet '{fleet_id}' requires a waypoint list.")
        previous = {"lat": fleet["lat"], "lon": fleet["lon"]}
        normalized_waypoints = []
        for waypoint in waypoints:
            if "lat" not in waypoint or "lon" not in waypoint:
                raise ValueError(f"Fleet '{fleet_id}' waypoint requires 'lat' and 'lon'.")
            next_point = {"lat": float(waypoint["lat"]), "lon": float(waypoint["lon"])}
            validate_lat_lon(next_point["lat"], next_point["lon"])
            validate_state_movement(state, fleet["unit_type"], previous, next_point)
            normalized_waypoints.append(next_point)
            previous = next_point
        cleaned_orders.append({"fleet_id": fleet_id, "waypoints": normalized_waypoints})
        seen.add(fleet_id)
    return cleaned_orders


def resolve_current_turn(state: dict) -> dict:
    turn = get_or_create_turn_record(state, state["current_turn"])
    if len(turn["submissions"]) < len(SIDES):
        raise ValueError("Both sides must submit before resolution.")

    step_hours = state["turn_duration_minutes"] / 60.0
    order_lookup = {
        order["fleet_id"]: [dict(waypoint) for waypoint in submission["orders"]]
        for submission in turn["submissions"].values()
        for order in submission["orders"]
    }

    for fleet in state["fleets"]:
        if fleet.get("docked_port_id"):
            continue
        move_budget_nm = fleet["speed_kts"] * step_hours
        advance_fleet_along_waypoints(state, fleet, order_lookup.get(fleet["id"], []), move_budget_nm)
        synchronize_ships_with_fleet(state, fleet)

    refresh_all_fleets(state)
    refresh_contacts_for_current_state(state)
    turn["status"] = "resolved"
    turn["resolved_at"] = utc_now()
    award_income(state)
    state["current_turn"] = int(state["current_turn"]) + 1
    get_or_create_turn_record(state, state["current_turn"])
    complete_due_jobs(state)
    state["updated_at"] = utc_now()

    return {
        "resolved": True,
        "turn_number": int(state["current_turn"]) - 1,
        "next_turn": state["current_turn"],
        "fleet_positions": {
            fleet["id"]: {"lat": fleet["lat"], "lon": fleet["lon"], "heading_deg": fleet["heading_deg"]}
            for fleet in state["fleets"]
        },
    }


def advance_fleet_along_waypoints(state: dict, fleet: dict, waypoints: list[dict], move_budget_nm: float) -> None:
    previous_point = {"lat": fleet["lat"], "lon": fleet["lon"]}
    while move_budget_nm > 0 and waypoints:
        next_waypoint = waypoints[0]
        distance = nautical_miles_between(previous_point, next_waypoint)
        if distance <= move_budget_nm:
            fleet["heading_deg"] = bearing_degrees(previous_point, next_waypoint)
            fleet["lat"] = next_waypoint["lat"]
            fleet["lon"] = next_waypoint["lon"]
            previous_point = {"lat": fleet["lat"], "lon": fleet["lon"]}
            waypoints.pop(0)
            move_budget_nm -= distance
        else:
            fraction = move_budget_nm / distance if distance else 0.0
            next_point = {
                "lat": fleet["lat"] + (next_waypoint["lat"] - fleet["lat"]) * fraction,
                "lon": fleet["lon"] + (next_waypoint["lon"] - fleet["lon"]) * fraction,
            }
            validate_state_movement(state, fleet["unit_type"], previous_point, next_point)
            fleet["heading_deg"] = bearing_degrees(previous_point, next_waypoint)
            fleet["lat"] = next_point["lat"]
            fleet["lon"] = next_point["lon"]
            move_budget_nm = 0


def award_income(state: dict) -> None:
    for side in SIDES:
        income = int(state["side_state"][side].get("income_per_turn", 0))
        state["side_state"][side]["resources"] += income


def complete_due_jobs(state: dict) -> None:
    current_turn = int(state["current_turn"])
    for job in state["repair_queue"]:
        if job["state"] != "queued" or int(job["ready_turn"]) > current_turn:
            continue
        ship = ship_by_id(state, job["ship_id"])
        subsystem = subsystem_by_id(ship, job["subsystem_id"])
        subsystem["current_integrity"] = subsystem["nominal_integrity"]
        subsystem["state"] = "operational"
        job["state"] = "completed"
        ship["history"].append(f"Completed repair of {subsystem['name']} on turn {current_turn}")
    for job in state["rearm_queue"]:
        if job["state"] != "queued" or int(job["ready_turn"]) > current_turn:
            continue
        ship = ship_by_id(state, job["ship_id"])
        ship["loadout"] = copy.deepcopy(job["desired_loadout"])
        job["state"] = "completed"
        ship["history"].append(f"Completed rearm on turn {current_turn}")


def build_fleet_for_side(state: dict, side: str, template_id: str) -> dict:
    side_info = state["side_state"][side]
    templates = side_info.get("build_catalog", [])
    template = next((entry for entry in templates if entry.get("id") == template_id), None)
    if template is None:
        raise ValueError(f"Unknown build template '{template_id}'.")
    cost = int(template.get("cost", DEFAULT_BUILD_COST))
    if state["side_state"][side]["resources"] < cost:
        raise ValueError(f"{side} does not have enough resources to build '{template['name']}'.")
    fleet_payload = {
        "name": str(template.get("name") or template_id),
        "side": side,
        "port_id": first_port_for_side(state, side)["id"],
        "_allow_empty": True,
        "speed_kts": float(template.get("speed_kts", 18.0)),
        "unit_type": str(template.get("unit_type", "Surface")),
        "detection_radius_nm": float(template.get("detection_radius_nm", 100.0)),
        "telegraph": int(template.get("telegraph", 2)),
        "station_role": str(template.get("station_role", "")),
    }
    fleet = create_fleet_for_side(state, side, fleet_payload)
    for ship_entry in composition_to_ship_entries(template.get("composition", []), template):
        create_ship_for_side(
            state,
            side,
            {
                "name": ship_entry["name"],
                "sea_power_type": ship_entry["sea_power_type"],
                "variant_reference": ship_entry["variant_reference"],
                "fleet_id": fleet["id"],
                "_allow_fleet_assignment": True,
            },
        )
    state["side_state"][side]["resources"] -= cost
    state["side_state"][side]["total_spent"] += cost
    refresh_all_fleets(state)
    state["updated_at"] = utc_now()
    return fleet_view_snapshot(state, fleet_by_id(state, fleet["id"]))


def preview_port_placement(state: dict, side: str, payload: dict) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side.")
    lat = float(payload.get("lat"))
    lon = float(payload.get("lon"))
    validate_lat_lon(lat, lon)
    snapped = terrain.snap_port_to_coast(lat, lon)
    return {
        "side": side,
        "requested_lat": lat,
        "requested_lon": lon,
        "lat": snapped["lat"],
        "lon": snapped["lon"],
        "distance_nm": snapped["distance_nm"],
        "coastal": True,
    }


def create_port_for_side(state: dict, side: str, payload: dict) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side.")
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("Port name is required.")
    lat = float(payload.get("lat"))
    lon = float(payload.get("lon"))
    validate_lat_lon(lat, lon)
    if not terrain.point_is_coastal_land(lat, lon):
        raise ValueError("Ports must be placed on a coastal land point.")
    port_id = str(payload.get("id") or next_port_id(state, side))
    port = {
        "id": port_id,
        "side": side,
        "name": name,
        "lat": lat,
        "lon": lon,
        "radius_nm": float(payload.get("radius_nm", 5.0)),
        "kind": str(payload.get("kind") or "naval_base"),
    }
    state["ports"].append(port)
    initialize_counters(state)
    state["updated_at"] = utc_now()
    state["map_center"] = normalize_map_center(None, state["fleets"], state["ports"])
    return port_view_snapshot(port)


def create_fleet_for_side(state: dict, side: str, payload: dict) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side.")
    allow_empty = bool(payload.get("_allow_empty", False))
    ship_ids = [str(ship_id) for ship_id in payload.get("ship_ids", []) if str(ship_id).strip()]
    if not allow_empty and not ship_ids:
        raise ValueError("Creating a fleet requires one or more existing reserve ships.")
    ships_to_assign = []
    state["fleet_counter"] = int(state.get("fleet_counter", 0)) + 1
    fleet_id = str(payload.get("id") or f"{side.lower()}_fleet_{state['fleet_counter']}")
    port_id = payload.get("port_id")
    docked_port_id = None
    if port_id:
        port = port_by_id(state, str(port_id))
        if port["side"] != side:
            raise ValueError("Fleet can only start at a friendly port.")
        lat = port["lat"]
        lon = port["lon"]
        docked_port_id = port["id"]
        status = "Docked"
    else:
        if not allow_empty:
            raise ValueError("Creating a fleet requires choosing the port where the ships already are.")
        lat = float(payload.get("lat"))
        lon = float(payload.get("lon"))
        validate_lat_lon(lat, lon)
        status = str(payload.get("status") or "Active")
    if ship_ids:
        for ship_id in ship_ids:
            ship = ship_by_id(state, ship_id)
            if ship["side"] != side:
                raise ValueError("Fleets can only include friendly ships.")
            if ship.get("fleet_id"):
                raise ValueError("Creating a fleet requires ships that are not already assigned to another fleet.")
            if str(ship.get("port_id") or "") != str(docked_port_id or ""):
                raise ValueError("All ships in a newly created fleet must already be at the selected port.")
            ships_to_assign.append(ship)
    fleet = {
        "id": fleet_id,
        "sp_id": str(payload.get("sp_id") or fleet_id.upper()),
        "name": str(payload.get("name") or fleet_id),
        "side": side,
        "unit_type": str(payload.get("unit_type") or "Surface"),
        "lat": lat,
        "lon": lon,
        "heading_deg": float(payload.get("heading_deg", 0.0)) % 360.0,
        "speed_kts": float(payload.get("speed_kts", 0.0)),
        "telegraph": int(payload.get("telegraph", 2)),
        "detection_radius_nm": float(payload.get("detection_radius_nm", 100.0)),
        "status": status,
        "ship_ids": [],
        "docked_port_id": docked_port_id,
        "station_role": str(payload.get("station_role", "")),
    }
    validate_state_position(state, fleet["unit_type"], fleet["lat"], fleet["lon"])
    state["fleets"].append(fleet)
    if ships_to_assign:
        for ship in ships_to_assign:
            fleet["ship_ids"].append(ship["id"])
            ship["fleet_id"] = fleet["id"]
            ship["status"] = "Docked"
            synchronize_ship_with_fleet(ship, fleet)
        refresh_all_fleets(state)
    state["updated_at"] = utc_now()
    return fleet_view_snapshot(state, fleet_by_id(state, fleet["id"]))


def ensure_unique_ship_name(state: dict, side: str, requested_name: str, *, exclude_ship_id: str | None = None) -> str:
    raw_name = str(requested_name or "").strip()
    if not raw_name:
        raise ValueError("Ship name is required.")
    existing_names = {
        normalize_name_key(ship["name"]): ship["name"]
        for ship in state["ships"]
        if ship["side"] == side and ship["id"] != exclude_ship_id
    }
    if normalize_name_key(raw_name) not in existing_names:
        return raw_name
    base_name, start_number = split_name_suffix(raw_name)
    next_number = max(start_number, next_ship_name_suffix(state, side, base_name, exclude_ship_id=exclude_ship_id))
    while True:
        candidate = f"{base_name} {next_number}".strip()
        if normalize_name_key(candidate) not in existing_names:
            return candidate
        next_number += 1


def next_ship_name_suffix(state: dict, side: str, base_name: str, *, exclude_ship_id: str | None = None) -> int:
    normalized_base = normalize_name_key(base_name)
    highest = 0
    for ship in state["ships"]:
        if ship["side"] != side or ship["id"] == exclude_ship_id:
            continue
        existing_base, suffix = split_name_suffix(ship["name"])
        if normalize_name_key(existing_base) != normalized_base:
            continue
        highest = max(highest, suffix if suffix > 0 else 1)
    return highest + 1 if highest else 1


def split_name_suffix(name: str) -> tuple[str, int]:
    value = str(name or "").strip()
    match = re.match(r"^(?P<base>.*?)(?:\s+(?P<number>\d+))?$", value)
    if not match:
        return value, 1
    base = str(match.group("base") or value).strip() or value
    number = int(match.group("number")) if match.group("number") else 1
    return base, number


def normalize_name_key(name: str) -> str:
    return " ".join(str(name or "").strip().lower().split())


def ensure_unique_fleet_name(state: dict, side: str, requested_name: str, *, exclude_fleet_id: str | None = None) -> str:
    raw_name = str(requested_name or "").strip()
    if not raw_name:
        raise ValueError("Fleet name is required.")
    existing = {
        normalize_name_key(fleet["name"])
        for fleet in state["fleets"]
        if fleet["side"] == side and fleet["id"] != exclude_fleet_id
    }
    if normalize_name_key(raw_name) not in existing:
        return raw_name
    suffix = 2
    while True:
        candidate = f"{raw_name} (Imported {suffix})"
        if normalize_name_key(candidate) not in existing:
            return candidate
        suffix += 1


def create_ship_for_side(state: dict, side: str, payload: dict) -> dict:
    if side not in SIDES:
        raise ValueError("Invalid side.")
    allow_fleet_assignment = bool(payload.get("_allow_fleet_assignment", False))
    if not catalog_is_available(state.get("catalogs", {})):
        raise ValueError("Ship catalog is unavailable. Configure ammo database and cost matrix sources before creating ships.")
    state["ship_counter"] = int(state.get("ship_counter", 0)) + 1
    sea_power_type = str(payload.get("sea_power_type") or "usn_dd_spruance")
    ship_index = set(state["catalogs"].get("ship_index", []))
    if sea_power_type not in ship_index:
        raise ValueError("Ship class must be selected from the available database options.")
    profile = class_profile(state["catalogs"], sea_power_type)
    requested_name = payload.get("name") or f"{profile['display_name'] or sea_power_type} {next_ship_name_suffix(state, side, profile['display_name'] or sea_power_type)}"
    unique_name = ensure_unique_ship_name(state, side, requested_name)
    ship = normalize_ship_record(
        {
            "id": payload.get("id") or f"{side.lower()}_ship_{state['ship_counter']}",
            "side": side,
            "name": unique_name,
            "sea_power_type": sea_power_type,
            "variant_reference": payload.get("variant_reference") or "Variant1",
            "loadout": payload.get("loadout") or profile["max_loadout"],
            "subsystems": payload.get("subsystems") or [],
            "history": ["Created in planner"],
            "unit_type": payload.get("unit_type") or "Surface",
            "speed_kts": payload.get("speed_kts", 0.0),
            "heading_deg": payload.get("heading_deg", 0.0),
            "telegraph": payload.get("telegraph", 2),
            "detection_radius_nm": payload.get("detection_radius_nm", 100.0),
        },
        state["catalogs"],
        state["ship_counter"],
    )
    ship["side"] = side

    fleet_id = payload.get("fleet_id")
    port_id = payload.get("port_id")
    if fleet_id:
        if not allow_fleet_assignment:
            raise ValueError("New ships must be created at a friendly port, then assigned into fleets later.")
        fleet = fleet_by_id(state, str(fleet_id))
        if fleet["side"] != side:
            raise ValueError("Ship can only be assigned to a friendly fleet.")
        fleet["ship_ids"].append(ship["id"])
        ship["fleet_id"] = fleet["id"]
        ship["port_id"] = fleet.get("docked_port_id")
        synchronize_ship_with_fleet(ship, fleet)
    elif port_id:
        port = port_by_id(state, str(port_id))
        if port["side"] != side:
            raise ValueError("Ship can only be assigned to a friendly port.")
        ship["fleet_id"] = None
        ship["port_id"] = port["id"]
        ship["lat"] = port["lat"]
        ship["lon"] = port["lon"]
        ship["status"] = "Reserve"
    else:
        raise ValueError("New ships must be created at a friendly port.")

    state["ships"].append(ship)
    refresh_all_fleets(state)
    state["updated_at"] = utc_now()
    return ship_view_snapshot(state, ship, state["catalogs"])


def create_ships_for_side(state: dict, side: str, payload: dict) -> list[dict]:
    quantity = int(payload.get("quantity", 1) or 1)
    if quantity < 1 or quantity > 12:
        raise ValueError("Ship quantity must be between 1 and 12.")
    sea_power_type = str(payload.get("sea_power_type") or "usn_dd_spruance")
    ship_option = ship_option_for_id(state["catalogs"], sea_power_type)
    provided_name = str(payload.get("name") or "").strip()
    base_name = provided_name or ship_option["name"]
    next_suffix = next_ship_name_suffix(state, side, base_name)
    created = []
    for index in range(quantity):
        item_payload = copy.deepcopy(payload)
        item_payload.pop("quantity", None)
        if not provided_name:
            item_payload["name"] = f"{base_name} {next_suffix + index}"
        elif quantity == 1:
            item_payload["name"] = base_name
        else:
            item_payload["name"] = f"{base_name} {next_suffix + index}"
        created.append(create_ship_for_side(state, side, item_payload))
    return created


def update_port(state: dict, port_id: str, updates: dict) -> dict:
    port = port_by_id(state, port_id)
    previous_lat = port["lat"]
    previous_lon = port["lon"]
    allowed_fields = {"name", "lat", "lon", "radius_nm"}
    for key in updates:
        if key not in allowed_fields:
            raise ValueError(f"Field '{key}' cannot be edited on a port.")
    if "name" in updates:
        port["name"] = str(updates["name"]).strip() or port["name"]
    if "lat" in updates:
        port["lat"] = float(updates["lat"])
    if "lon" in updates:
        port["lon"] = float(updates["lon"])
    if "radius_nm" in updates:
        port["radius_nm"] = max(0.1, float(updates["radius_nm"]))
    validate_lat_lon(port["lat"], port["lon"])
    if port["lat"] != previous_lat or port["lon"] != previous_lon:
        if not terrain.point_is_coastal_land(port["lat"], port["lon"]):
            port["lat"] = previous_lat
            port["lon"] = previous_lon
            raise ValueError("Ports must stay on a coastal land point.")
    if port["lat"] != previous_lat or port["lon"] != previous_lon:
        for ship in state["ships"]:
            if ship.get("port_id") == port["id"] and not ship.get("fleet_id"):
                ship["lat"] = port["lat"]
                ship["lon"] = port["lon"]
    refresh_all_fleets(state)
    refresh_contacts_for_current_state(state)
    state["updated_at"] = utc_now()
    return port_view_snapshot(port)


def update_fleet(state: dict, fleet_id: str, updates: dict, *, admin: bool = False) -> dict:
    fleet = fleet_by_id(state, fleet_id)
    allowed_fields = {"name"} if not admin else {"name", "lat", "lon", "heading_deg", "speed_kts", "detection_radius_nm", "status", "telegraph"}
    for key in updates:
        if key not in allowed_fields:
            raise ValueError(f"Field '{key}' cannot be edited on a fleet.")
    if "name" in updates:
        fleet["name"] = str(updates["name"]).strip() or fleet["name"]
    if "lat" in updates:
        fleet["lat"] = float(updates["lat"])
    if "lon" in updates:
        fleet["lon"] = float(updates["lon"])
    if "heading_deg" in updates:
        fleet["heading_deg"] = float(updates["heading_deg"]) % 360.0
    if "speed_kts" in updates:
        fleet["speed_kts"] = max(0.0, float(updates["speed_kts"]))
    if "detection_radius_nm" in updates:
        fleet["detection_radius_nm"] = max(0.0, float(updates["detection_radius_nm"]))
    if "status" in updates:
        fleet["status"] = str(updates["status"]).strip() or fleet["status"]
    if "telegraph" in updates:
        fleet["telegraph"] = int(updates["telegraph"])
    validate_lat_lon(fleet["lat"], fleet["lon"])
    validate_state_position(state, fleet["unit_type"], fleet["lat"], fleet["lon"])
    synchronize_ships_with_fleet(state, fleet)
    refresh_contacts_for_current_state(state)
    state["updated_at"] = utc_now()
    return fleet_view_snapshot(state, fleet)


def admin_update_fleet(state: dict, fleet_id: str, updates: dict) -> dict:
    return update_fleet(state, fleet_id, updates, admin=True)


def update_ship(state: dict, ship_id: str, updates: dict) -> dict:
    ship = ship_by_id(state, ship_id)
    allowed_fields = {"name"}
    for key in updates:
        if key not in allowed_fields:
            raise ValueError(f"Field '{key}' cannot be edited on a ship.")
    if "name" in updates:
        requested_name = str(updates["name"]).strip()
        if not requested_name:
            raise ValueError("Ship name is required.")
        normalized = normalize_name_key(requested_name)
        duplicate = next(
            (other for other in state["ships"] if other["side"] == ship["side"] and other["id"] != ship_id and normalize_name_key(other["name"]) == normalized),
            None,
        )
        if duplicate is not None:
            raise ValueError(f"Ship name '{requested_name}' is already in use for {ship['side']}.")
        ship["name"] = requested_name
    state["updated_at"] = utc_now()
    return ship_view_snapshot(state, ship, state["catalogs"])


def update_side_economy(state: dict, side: str, updates: dict) -> dict:
    side = normalize_side_name(side)
    allowed_fields = {"resources", "income_per_turn"}
    for key in updates:
        if key not in allowed_fields:
            raise ValueError(f"Field '{key}' cannot be edited on side economy.")
    side_info = state["side_state"][side]
    if "resources" in updates:
        side_info["resources"] = int(updates["resources"])
    if "income_per_turn" in updates:
        side_info["income_per_turn"] = int(updates["income_per_turn"])
    state["updated_at"] = utc_now()
    return player_side_state_snapshot(state, side)


def detach_ship_to_singleton_fleet(state: dict, ship: dict, source_fleet: dict, *, new_fleet_name: str | None = None) -> dict:
    remove_ship_from_fleet(source_fleet, ship["id"])
    singleton = create_fleet_for_side(
        state,
        ship["side"],
        {
            "name": new_fleet_name or f"{ship['name']} Group",
            "_allow_empty": True,
            "lat": source_fleet["lat"],
            "lon": source_fleet["lon"],
            "heading_deg": source_fleet["heading_deg"],
            "speed_kts": ship["speed_kts"] or source_fleet["speed_kts"],
            "telegraph": source_fleet["telegraph"],
            "unit_type": ship["unit_type"],
            "detection_radius_nm": ship["detection_radius_nm"] or source_fleet["detection_radius_nm"],
            "status": "Docked" if source_fleet.get("docked_port_id") else "Active",
            "port_id": source_fleet.get("docked_port_id"),
        },
    )
    singleton_fleet = fleet_by_id(state, singleton["id"])
    singleton_fleet["ship_ids"].append(ship["id"])
    ship["fleet_id"] = singleton_fleet["id"]
    ship["port_id"] = singleton_fleet.get("docked_port_id")
    ship["status"] = "Docked" if singleton_fleet.get("docked_port_id") else "Active"
    synchronize_ship_with_fleet(ship, singleton_fleet)
    remove_empty_fleet(state, source_fleet)
    refresh_all_fleets(state)
    return singleton_fleet


def transfer_ship(state: dict, ship_id: str, payload: dict) -> dict:
    ship = ship_by_id(state, ship_id)
    source_fleet = fleet_by_id(state, ship["fleet_id"]) if ship.get("fleet_id") else None
    target_fleet_id = str(payload.get("target_fleet_id") or "").strip()
    dock_port_id = str(payload.get("dock_port_id") or "").strip()
    to_reserve = bool(payload.get("to_reserve", False))
    new_fleet_name = str(payload.get("new_fleet_name") or f"{ship['name']} Group")

    if to_reserve:
        port_id = ship.get("port_id")
        if not port_id and source_fleet and source_fleet.get("docked_port_id"):
            port_id = source_fleet["docked_port_id"]
        if not port_id:
            raise ValueError("Ships can only enter reserve while docked at a friendly port.")
        port = port_by_id(state, port_id)
        if port["side"] != ship["side"]:
            raise ValueError("Ships can only enter reserve at a friendly port.")
        if source_fleet:
            remove_ship_from_fleet(source_fleet, ship["id"])
            remove_empty_fleet(state, source_fleet)
        ship["fleet_id"] = None
        ship["port_id"] = port["id"]
        ship["lat"] = port["lat"]
        ship["lon"] = port["lon"]
        ship["status"] = "Reserve"
        ship["history"].append(f"Moved to reserve at {port['name']}")
        refresh_all_fleets(state)
        state["updated_at"] = utc_now()
        return ship_view_snapshot(state, ship, state["catalogs"])

    if dock_port_id:
        port = port_by_id(state, dock_port_id)
        if port["side"] != ship["side"]:
            raise ValueError("Ships can only dock at friendly ports.")
        if not source_fleet:
            if ship.get("port_id") == port["id"]:
                raise ValueError("Ship is already in reserve at that port.")
            raise ValueError("Reserve ships must join a fleet before moving to another port.")
        if nautical_miles_between(source_fleet, port) > float(port.get("radius_nm", 5.0)):
            raise ValueError("Ship's fleet must be within port radius to dock.")
        docking_fleet = source_fleet
        if len(source_fleet["ship_ids"]) > 1:
            docking_fleet = detach_ship_to_singleton_fleet(state, ship, source_fleet, new_fleet_name=new_fleet_name)
            ship["history"].append(f"Detached into fleet {docking_fleet['name']} for docking")
        dock_fleet(state, docking_fleet["id"], {"port_id": port["id"]})
        ship["history"].append(f"Docked at {port['name']}")
        refresh_all_fleets(state)
        state["updated_at"] = utc_now()
        return ship_view_snapshot(state, ship, state["catalogs"])

    if target_fleet_id:
        target = fleet_by_id(state, target_fleet_id)
        if target["side"] != ship["side"]:
            raise ValueError("Ship can only transfer to a friendly fleet.")
        if source_fleet:
            if source_fleet["id"] == target["id"]:
                raise ValueError("Ship is already in that fleet.")
            if not fleets_can_transfer(source_fleet, target):
                raise ValueError("Fleets must be co-located within 1 nm or share a docked port to transfer ships.")
            remove_ship_from_fleet(source_fleet, ship["id"])
            remove_empty_fleet(state, source_fleet)
        elif ship.get("port_id") and target.get("docked_port_id") != ship["port_id"]:
            raise ValueError("Reserve ships can only join fleets docked at the same port.")
        target["ship_ids"].append(ship["id"])
        ship["fleet_id"] = target["id"]
        ship["port_id"] = target.get("docked_port_id")
        ship["status"] = "Docked" if target.get("docked_port_id") else "Active"
        synchronize_ship_with_fleet(ship, target)
        ship["history"].append(f"Transferred to fleet {target['name']}")
        refresh_all_fleets(state)
        state["updated_at"] = utc_now()
        return ship_view_snapshot(state, ship, state["catalogs"])

    if not source_fleet:
        raise ValueError("Only ships currently in a fleet can detach into a new sea group.")
    singleton_fleet = detach_ship_to_singleton_fleet(state, ship, source_fleet, new_fleet_name=new_fleet_name)
    ship["history"].append(f"Detached into fleet {singleton_fleet['name']}")
    state["updated_at"] = utc_now()
    return ship_view_snapshot(state, ship, state["catalogs"])


def dock_fleet(state: dict, fleet_id: str, payload: dict) -> dict:
    fleet = fleet_by_id(state, fleet_id)
    action = str(payload.get("action") or "dock")
    if action == "undock":
        fleet["docked_port_id"] = None
        fleet["status"] = "Active"
        for ship in ships_for_fleet(state, fleet["id"]):
            ship["port_id"] = None
            ship["status"] = "Active"
        state["updated_at"] = utc_now()
        return fleet_view_snapshot(state, fleet)

    port = port_by_id(state, str(payload.get("port_id") or ""))
    if port["side"] != fleet["side"]:
        raise ValueError("Fleets can only dock at friendly ports.")
    if nautical_miles_between(fleet, port) > float(port.get("radius_nm", 5.0)):
        raise ValueError("Fleet must be within port radius to dock.")
    fleet["lat"] = port["lat"]
    fleet["lon"] = port["lon"]
    fleet["docked_port_id"] = port["id"]
    fleet["status"] = "Docked"
    for ship in ships_for_fleet(state, fleet["id"]):
        ship["port_id"] = port["id"]
        ship["status"] = "Docked"
        synchronize_ship_with_fleet(ship, fleet)
    state["updated_at"] = utc_now()
    return fleet_view_snapshot(state, fleet)


def merge_fleets(state: dict, source_fleet_id: str, target_fleet_id: str) -> dict:
    source = fleet_by_id(state, source_fleet_id)
    target = fleet_by_id(state, target_fleet_id)
    if source["side"] != target["side"]:
        raise ValueError("Only same-side fleets can merge.")
    if source["id"] == target["id"]:
        raise ValueError("Cannot merge a fleet into itself.")
    if not fleets_can_transfer(source, target):
        raise ValueError("Fleets must be co-located within 1 nm or share a docked port to merge.")
    for ship_id in list(source["ship_ids"]):
        ship = ship_by_id(state, ship_id)
        ship["fleet_id"] = target["id"]
        ship["port_id"] = target.get("docked_port_id")
        ship["status"] = "Docked" if target.get("docked_port_id") else "Active"
        target["ship_ids"].append(ship_id)
    state["fleets"] = [fleet for fleet in state["fleets"] if fleet["id"] != source["id"]]
    refresh_all_fleets(state)
    state["updated_at"] = utc_now()
    return fleet_view_snapshot(state, target)


def queue_ship_rearm(state: dict, ship_id: str, payload: dict) -> dict:
    ship = ship_by_id(state, ship_id)
    ensure_ship_docked_for_service(state, ship)
    if has_active_job(state["rearm_queue"], ship["id"]):
        raise ValueError("Ship already has an active rearm job.")

    mode = str(payload.get("mode") or "full")
    desired_loadout = copy.deepcopy(ship.get("max_loadout", {})) if mode == "full" else normalize_loadout_payload(payload.get("desired_loadout"))
    admin_override = bool(payload.get("admin_override", False))
    if not admin_override:
        enforce_loadout_caps(ship, desired_loadout)

    deltas = {}
    for weapon_id, desired in desired_loadout.items():
        current = int(ship["loadout"].get(weapon_id, 0))
        delta = int(desired) - current
        if delta > 0:
            deltas[weapon_id] = delta
    if not deltas:
        raise ValueError("Desired loadout does not increase any ammunition.")

    cost, work_units, line_items = rearm_cost_and_work(state["catalogs"].get("weapon_prices", {}), deltas)
    ready_turn = int(payload.get("ready_turn", 0) or 0)
    if ready_turn <= 0:
        work_units_per_turn = float(state["catalogs"].get("work_units_per_turn", 8.0)) or 8.0
        ready_turn = int(state["current_turn"]) + max(1, math.ceil(work_units / work_units_per_turn))
    if "cost" in payload:
        cost = float(payload["cost"])

    charge_side_cost(state, ship["side"], cost)
    job_id = f"rearm_{len(state['rearm_queue']) + 1}"
    job = {
        "id": job_id,
        "ship_id": ship["id"],
        "side": ship["side"],
        "port_id": ship.get("port_id"),
        "started_turn": int(state["current_turn"]),
        "ready_turn": int(ready_turn),
        "cost": round(cost, 4),
        "state": "queued",
        "mode": mode,
        "desired_loadout": desired_loadout,
        "line_items": line_items,
        "work_units": work_units,
    }
    state["rearm_queue"].append(job)
    ship["history"].append(f"Queued rearm job {job_id} on turn {state['current_turn']}")
    state["updated_at"] = utc_now()
    return copy.deepcopy(job)


def queue_ship_repair(state: dict, ship_id: str, payload: dict) -> dict:
    ship = ship_by_id(state, ship_id)
    ensure_ship_docked_for_service(state, ship)
    subsystem = subsystem_by_id(ship, str(payload.get("subsystem_id") or ""))
    if not subsystem.get("repairable", True):
        raise ValueError("Subsystem is not repairable.")
    if has_active_job(state["repair_queue"], ship["id"], subsystem["id"]):
        raise ValueError("Subsystem already has an active repair job.")

    missing_integrity = float(subsystem["nominal_integrity"]) - float(subsystem["current_integrity"])
    if missing_integrity <= 0:
        raise ValueError("Subsystem does not need repair.")

    total_nominal = sum(max(1, int(item.get("nominal_integrity", 1))) for item in ship.get("subsystems", [])) or 1
    base_hull = float(ship.get("class_costs", {}).get("base_hull") or ship.get("class_costs", {}).get("total_value") or 100.0)
    category = subsystem.get("category", "control")
    multiplier = REPAIR_CATEGORY_MULTIPLIER.get(category, 1.0)
    turn_rate = REPAIR_CATEGORY_TURNS.get(category, 0.5)
    damage_fraction = missing_integrity / total_nominal
    cost = base_hull * damage_fraction * multiplier
    ready_turn = int(payload.get("ready_turn", 0) or 0)
    if ready_turn <= 0:
        ready_turn = int(state["current_turn"]) + max(1, math.ceil(missing_integrity * turn_rate))
    if "cost" in payload:
        cost = float(payload["cost"])

    charge_side_cost(state, ship["side"], cost)
    job_id = f"repair_{len(state['repair_queue']) + 1}"
    job = {
        "id": job_id,
        "ship_id": ship["id"],
        "subsystem_id": subsystem["id"],
        "side": ship["side"],
        "port_id": ship.get("port_id"),
        "started_turn": int(state["current_turn"]),
        "ready_turn": int(ready_turn),
        "cost": round(cost, 4),
        "state": "queued",
        "category": category,
        "missing_integrity": round(missing_integrity, 4),
    }
    state["repair_queue"].append(job)
    ship["history"].append(f"Queued repair job {job_id} for {subsystem['name']} on turn {state['current_turn']}")
    state["updated_at"] = utc_now()
    return copy.deepcopy(job)


def export_scenario_ini(state: dict) -> str:
    center = state["map_center"]
    env = state["environment"]
    blue_fleets = [fleet for fleet in state["fleets"] if fleet["side"] == BLUE and fleet["ship_ids"]]
    red_fleets = [fleet for fleet in state["fleets"] if fleet["side"] == RED and fleet["ship_ids"]]

    lines = [
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
        f"NumberOfTaskforce1Vessels={count_export_vessels(blue_fleets)}",
        f"NumberOfTaskforce2Vessels={count_export_vessels(red_fleets)}",
        "NumberOfTaskforce1Submarines=0",
        "NumberOfTaskforce2Submarines=0",
        "NumberOfTaskforce1Weapons=0",
        "NumberOfTaskforce2Weapons=0",
    ]

    append_taskforce(lines, state, center, "Taskforce1", blue_fleets)
    append_taskforce(lines, state, center, "Taskforce2", red_fleets)
    return "\n".join(lines) + "\n"


def count_export_vessels(fleets: list[dict]) -> int:
    return sum(len(fleet["ship_ids"]) for fleet in fleets)


def append_taskforce(lines: list[str], state: dict, center: dict, section_prefix: str, fleets: list[dict]) -> None:
    lines.append(f"[{section_prefix}]")
    lines.append("Airstrikes=0")
    vessel_index = 1
    formation_index = 1
    for fleet in fleets:
        ships = ships_for_fleet(state, fleet["id"])
        if len(ships) > 1:
            members = ",".join(f"{section_prefix}Vessel{vessel_index + offset}" for offset in range(len(ships)))
            lines.append(f"{section_prefix}_Formation{formation_index}={members}|{fleet['name']}|Loose|1.5")
            formation_index += 1
        east_nm, north_nm = relative_position_nm(center, fleet)
        for ship in ships:
            lines.extend(
                [
                    f"[{section_prefix}Vessel{vessel_index}]",
                    f"Type={ship['sea_power_type']}",
                    f"VariantReference={ship['variant_reference']}",
                    f"Name={ship['name']}",
                    f"RelativePositionInNM={east_nm:.2f},0,{north_nm:.2f}",
                    f"Telegraph={fleet['telegraph']}",
                    f"Heading={int(round(fleet['heading_deg'])) % 360}",
                ]
            )
            if fleet.get("station_role"):
                lines.append(f"StationRole={fleet['station_role']}")
            vessel_index += 1


def relative_position_nm(center: dict, fleet: dict) -> tuple[float, float]:
    lat_factor = 60.0
    north_nm = (fleet["lat"] - center["lat"]) * lat_factor
    avg_lat = math.radians((fleet["lat"] + center["lat"]) / 2.0)
    east_nm = (fleet["lon"] - center["lon"]) * lat_factor * math.cos(avg_lat)
    return east_nm, north_nm


def nautical_miles_between(a: dict, b: dict) -> float:
    start_lat, start_lon = extract_lat_lon(a)
    end_lat, end_lon = extract_lat_lon(b)
    lat1 = math.radians(start_lat)
    lat2 = math.radians(end_lat)
    dlat = lat2 - lat1
    dlon = math.radians(end_lon - start_lon)
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 3440.065 * 2 * math.asin(min(1.0, math.sqrt(hav)))


def bearing_degrees(start: dict | tuple[float, float], end: dict | tuple[float, float]) -> float:
    start_lat, start_lon = extract_lat_lon(start)
    end_lat, end_lon = extract_lat_lon(end)
    lat1 = math.radians(start_lat)
    lat2 = math.radians(end_lat)
    dlon = math.radians(end_lon - start_lon)
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


def extract_lat_lon(value: dict | tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, tuple):
        return value
    return float(value["lat"]), float(value["lon"])


def first_port_for_side(state: dict, side: str) -> dict:
    for port in state["ports"]:
        if port["side"] == side:
            return port
    raise ValueError(f"No port exists for {side}.")


def next_port_id(state: dict, side: str) -> str:
    state["port_counter"] = int(state.get("port_counter", 0)) + 1
    return f"{side.lower()}_port_{state['port_counter']}"


def normalize_side_name(raw: str) -> str:
    value = raw.strip().lower()
    if value == "blue":
        return BLUE
    if value == "red":
        return RED
    raise ValueError("Side must be Blue or Red.")


def ships_for_fleet(state: dict, fleet_id: str) -> list[dict]:
    return [ship for ship in state["ships"] if ship.get("fleet_id") == fleet_id]


def synchronize_ship_with_fleet(ship: dict, fleet: dict) -> None:
    ship["lat"] = fleet["lat"]
    ship["lon"] = fleet["lon"]
    ship["heading_deg"] = fleet["heading_deg"]
    ship["speed_kts"] = fleet["speed_kts"]
    ship["telegraph"] = fleet["telegraph"]
    ship["port_id"] = fleet.get("docked_port_id")


def synchronize_ships_with_fleet(state: dict, fleet: dict) -> None:
    for ship in ships_for_fleet(state, fleet["id"]):
        synchronize_ship_with_fleet(ship, fleet)


def assign_docked_ship_ports(state: dict) -> None:
    for ship in state["ships"]:
        if ship.get("fleet_id"):
            fleet = fleet_by_id(state, ship["fleet_id"])
            if fleet.get("docked_port_id"):
                ship["port_id"] = fleet["docked_port_id"]


def refresh_all_fleets(state: dict) -> None:
    for fleet in state["fleets"]:
        ships = ships_for_fleet(state, fleet["id"])
        fleet["ship_ids"] = [ship["id"] for ship in ships]
        if not ships:
            continue
        fleet["unit_type"] = "Subsurface" if all(ship["unit_type"] == "Subsurface" for ship in ships) else "Surface"
        if any(ship["speed_kts"] for ship in ships):
            fleet["speed_kts"] = min(ship["speed_kts"] for ship in ships if ship["speed_kts"] >= 0)
        fleet["detection_radius_nm"] = max(ship.get("detection_radius_nm", 100.0) for ship in ships)
        if fleet.get("docked_port_id"):
            port = port_by_id(state, fleet["docked_port_id"])
            fleet["lat"] = port["lat"]
            fleet["lon"] = port["lon"]
        for ship in ships:
            synchronize_ship_with_fleet(ship, fleet)
    state["map_center"] = normalize_map_center(None, [fleet for fleet in state["fleets"] if fleet["ship_ids"]], state["ports"])


def remove_ship_from_fleet(fleet: dict, ship_id: str) -> None:
    fleet["ship_ids"] = [entry for entry in fleet["ship_ids"] if entry != ship_id]


def remove_empty_fleet(state: dict, fleet: dict) -> None:
    if fleet["ship_ids"]:
        return
    state["fleets"] = [entry for entry in state["fleets"] if entry["id"] != fleet["id"]]


def fleets_can_transfer(source: dict, target: dict) -> bool:
    if source.get("docked_port_id") and source.get("docked_port_id") == target.get("docked_port_id"):
        return True
    return nautical_miles_between(source, target) <= 1.0


def ensure_ship_docked_for_service(state: dict, ship: dict) -> None:
    port_id = ship.get("port_id")
    if not port_id:
        raise ValueError("Ship must be docked at a friendly port for this action.")
    port = port_by_id(state, port_id)
    if port["side"] != ship["side"]:
        raise ValueError("Ship must be docked at a friendly port for this action.")


def has_active_job(queue: list[dict], ship_id: str, subsystem_id: str | None = None) -> bool:
    for job in queue:
        if job["state"] != "queued":
            continue
        if job["ship_id"] != ship_id:
            continue
        if subsystem_id is None or job.get("subsystem_id") == subsystem_id:
            return True
    return False


def normalize_loadout_payload(payload: dict | None) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError("Custom rearm requires a desired_loadout object.")
    return {str(weapon_id): int(quantity) for weapon_id, quantity in payload.items()}


def enforce_loadout_caps(ship: dict, desired_loadout: dict[str, int]) -> None:
    max_loadout = ship.get("max_loadout", {})
    for weapon_id, quantity in desired_loadout.items():
        maximum = max_loadout.get(weapon_id)
        if maximum is not None and int(quantity) > int(maximum):
            raise ValueError(f"Desired ammunition for '{weapon_id}' exceeds class maximum.")


def charge_side_cost(state: dict, side: str, cost: float) -> None:
    rounded_cost = int(math.ceil(cost))
    if state["side_state"][side]["resources"] < rounded_cost:
        raise ValueError(f"{side} does not have enough resources.")
    state["side_state"][side]["resources"] -= rounded_cost
    state["side_state"][side]["total_spent"] += rounded_cost


def subsystem_by_id(ship: dict, subsystem_id: str) -> dict:
    for subsystem in ship.get("subsystems", []):
        if subsystem["id"] == subsystem_id:
            return subsystem
    raise ValueError(f"Unknown subsystem '{subsystem_id}'.")
