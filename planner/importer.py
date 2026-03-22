from __future__ import annotations

import configparser
import re
from pathlib import Path

from .catalogs import class_profile


TASKFORCE_SIDE_MAP = {
    "Taskforce1": "Blue",
    "Taskforce2": "Red",
}

STANDARD_INTEGRITY_BUCKETS = (1, 5, 8, 10, 20, 30, 40, 60)


def parse_save_file(
    save_path: str | Path,
    catalogs: dict,
    *,
    scenario_name: str | None = None,
    turn_duration_minutes: int = 60,
) -> dict:
    preview = parse_save_candidates(
        save_path,
        catalogs,
        scenario_name=scenario_name,
        turn_duration_minutes=turn_duration_minutes,
    )
    fleets = build_seed_fleets_from_candidates(preview["fleet_candidates"])
    ports = derive_default_ports(fleets)
    average_center = average_fleet_position(fleets)

    side_state = {
        "Blue": {
            "display_name": "Blue",
            "resources": 100,
            "total_spent": 0,
            "income_per_turn": 0,
        },
        "Red": {
            "display_name": "Red",
            "resources": 100,
            "total_spent": 0,
            "income_per_turn": 0,
        },
    }

    return {
        "scenario_name": preview["scenario_name"],
        "turn_duration_minutes": int(preview["turn_duration_minutes"]),
        "map_center": average_center,
        "environment": preview["environment"],
        "side_state": side_state,
        "ports": ports,
        "fleets": fleets,
        "catalogs": catalogs,
        "terrain_enforced": False,
    }


def parse_save_candidates(
    save_path: str | Path,
    catalogs: dict,
    *,
    scenario_name: str | None = None,
    turn_duration_minutes: int = 60,
) -> dict:
    path = Path(save_path)
    if not path.exists():
        raise FileNotFoundError(f"Save file '{path}' does not exist.")
    parser = configparser.RawConfigParser(strict=False)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")

    formations = parse_formations(parser)
    units = parse_units(parser, catalogs)
    fleet_candidates = build_import_candidate_fleets(formations, units)
    environment = {
        "date": parser.get("Environment", "Date", fallback="1985,6,26"),
        "time": parser.get("Environment", "Time", fallback="10,0"),
        "convert_time_to_local": parser.getboolean("Environment", "ConvertTimeToLocal", fallback=False),
        "sea_state": parser.getint("Environment", "SeaState", fallback=3),
        "clouds": parser.get("Environment", "Clouds", fallback="Scattered_1"),
        "wind_direction": parser.get("Environment", "WindDirection", fallback="E"),
        "load_background_data": parser.getboolean("Environment", "LoadBackgroundData", fallback=False),
    }
    return {
        "save_path": str(path),
        "scenario_name": scenario_name or path.stem,
        "turn_duration_minutes": int(turn_duration_minutes),
        "environment": environment,
        "fleet_candidates": fleet_candidates,
        "sides": group_candidate_fleets_by_side(fleet_candidates),
    }


def parse_formations(parser: configparser.RawConfigParser) -> dict[str, dict]:
    formations: dict[str, dict] = {}
    if not parser.has_section("Mission"):
        return formations

    for key, value in parser.items("Mission"):
        if "_Formation" not in key:
            continue
        side_prefix = key.split("_", 1)[0]
        side = TASKFORCE_SIDE_MAP.get(side_prefix)
        if not side:
            continue
        members_raw, name, shape, spacing = (value.split("|") + ["", "", ""])[:4]
        members = [member.strip() for member in members_raw.split(",") if member.strip()]
        formation_id = key
        formations[formation_id] = {
            "id": formation_id,
            "side": side,
            "name": name.strip() or formation_id,
            "members": members,
            "shape": shape.strip(),
            "spacing": spacing.strip(),
        }
    return formations


def parse_units(parser: configparser.RawConfigParser, catalogs: dict) -> dict[str, dict]:
    sections = parser.sections()
    units: dict[str, dict] = {}
    for section in sections:
        match = re.match(r"^(Taskforce1|Taskforce2)(Vessel|Submarine)(\d+)$", section)
        if not match:
            continue
        section_prefix = match.group(1)
        side = TASKFORCE_SIDE_MAP[section_prefix]
        kind = match.group(2)
        unit = parse_unit(parser, sections, section, side, kind, catalogs)
        units[section] = unit
    return units


def parse_unit(
    parser: configparser.RawConfigParser,
    sections: list[str],
    section: str,
    side: str,
    kind: str,
    catalogs: dict,
) -> dict:
    sea_power_type = parser.get(section, "Type", fallback="usn_dd_spruance")
    variant_reference = parser.get(section, "VariantReference", fallback="Variant1")
    name = parser.get(section, "Name", fallback=section)
    geo_position = parse_geo_position(parser.get(section, "GeoPosition", fallback="0,0,0"))
    ship_id = ship_id_from_section(section)
    profile = class_profile(catalogs, sea_power_type)
    subsystem_records = []
    loadout: dict[str, int] = {}
    history = [f"Imported from {section}"]

    related_sections = [entry for entry in sections if entry.startswith(section) and entry != section]
    pending_magazine_count: int | None = None
    for related in related_sections:
        subsystem = parse_subsystem(parser, related)
        if subsystem is not None:
            subsystem_records.append(subsystem)

        if "WeaponMagazineSystem" in related:
            pending_magazine_count = parse_ammunition_count(parser, related)
            continue

        if any(token in related for token in ("WeaponSystemLauncher", "WeaponSystemGun", "WeaponSystemCIWS", "WeaponSystemChaff")):
            ammo_id, loaded_count = parse_loaded_ammunition(parser.get(related, "LoadedAmmunitions", fallback=""))
            if ammo_id:
                loadout[ammo_id] = loadout.get(ammo_id, 0) + loaded_count
                if pending_magazine_count is not None:
                    loadout[ammo_id] = loadout.get(ammo_id, 0) + pending_magazine_count
                    pending_magazine_count = None

    return {
        "id": ship_id,
        "candidate_id": candidate_id("ship", section),
        "source_key": section,
        "name": name,
        "side": side,
        "sea_power_type": sea_power_type,
        "class_display_name": profile["display_name"],
        "class_role": profile["role"],
        "variant_reference": variant_reference,
        "fleet_id": None,
        "port_id": None,
        "status": "Active",
        "class_costs": profile["costs"],
        "max_loadout": profile["max_loadout"],
        "loadout": loadout,
        "subsystems": subsystem_records,
        "history": history,
        "lat": geo_position["lat"],
        "lon": geo_position["lon"],
        "heading_deg": float(parser.get(section, "Heading", fallback="0") or 0.0),
        "speed_kts": float(parser.get(section, "VelocityInKnots", fallback="0") or 0.0),
        "telegraph": int(float(parser.get(section, "Telegraph", fallback="2") or 2)),
        "station_role": parser.get(section, "StationRole", fallback=""),
        "unit_type": "Subsurface" if kind == "Submarine" else "Surface",
        "detection_radius_nm": 100.0,
    }


def build_import_candidate_fleets(formations: dict[str, dict], units: dict[str, dict]) -> list[dict]:
    fleets = []
    assigned_units = set()
    fleet_index = 1

    for formation in formations.values():
        member_units = [units[name] for name in formation["members"] if name in units]
        if not member_units:
            continue
        assigned_units.update(ship["id"] for ship in member_units)
        fleet = candidate_fleet_from_members(
            fleet_candidate_id=candidate_id("fleet", formation["id"]),
            source_key=formation["id"],
            source_kind="formation",
            side=formation["side"],
            name=formation["name"],
            members=member_units,
        )
        fleets.append(fleet)
        fleet_index += 1

    for unit in units.values():
        if unit["id"] in assigned_units:
            continue
        fleets.append(
            candidate_fleet_from_members(
                fleet_candidate_id=candidate_id("fleet", unit["id"]),
                source_key=unit["id"],
                source_kind="singleton",
                side=unit["side"],
                name=unit["name"],
                members=[unit],
            )
        )
        fleet_index += 1

    return fleets


def build_seed_fleets_from_candidates(fleet_candidates: list[dict], selected_ship_ids: set[str] | None = None) -> list[dict]:
    normalized = []
    for fleet in fleet_candidates:
        selected_ships = []
        for ship in fleet["ships"]:
            candidate_ship_id = ship.get("candidate_id") or candidate_id("ship", ship.get("source_key") or ship["id"])
            if selected_ship_ids is not None and candidate_ship_id not in selected_ship_ids:
                continue
            selected_ships.append(dict(ship))
        if not selected_ships:
            continue
        for ship in selected_ships:
            ship["fleet_id"] = fleet["id"]
        normalized.append(
            {
                "id": fleet["id"],
                "sp_id": fleet["id"].upper(),
                "name": fleet["name"],
                "side": fleet["side"],
                "unit_type": fleet["unit_type"],
                "lat": fleet["lat"],
                "lon": fleet["lon"],
                "heading_deg": fleet["heading_deg"],
                "speed_kts": fleet["speed_kts"],
                "telegraph": fleet["telegraph"],
                "detection_radius_nm": fleet["detection_radius_nm"],
                "status": "Active",
                "ship_ids": [ship["id"] for ship in selected_ships],
                "docked_port_id": None,
                "station_role": fleet["station_role"],
                "ships": selected_ships,
            }
        )
    return normalized


def candidate_fleet_from_members(
    *,
    fleet_candidate_id: str,
    source_key: str,
    source_kind: str,
    side: str,
    name: str,
    members: list[dict],
) -> dict:
    lat = sum(ship["lat"] for ship in members) / len(members)
    lon = sum(ship["lon"] for ship in members) / len(members)
    speed = min(ship["speed_kts"] for ship in members) if members else 0.0
    heading = members[0]["heading_deg"] if members else 0.0
    telegraph = members[0]["telegraph"] if members else 2
    station_role = ",".join(sorted({ship["station_role"] for ship in members if ship["station_role"]}))
    unit_type = "Subsurface" if all(ship["unit_type"] == "Subsurface" for ship in members) else "Surface"
    detection_radius = max(ship.get("detection_radius_nm", 100.0) for ship in members) if members else 100.0
    return {
        "id": fleet_candidate_id,
        "candidate_id": fleet_candidate_id,
        "source_key": source_key,
        "source_kind": source_kind,
        "side": side,
        "name": name,
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "heading_deg": float(heading),
        "speed_kts": float(speed),
        "telegraph": int(telegraph),
        "station_role": station_role,
        "unit_type": unit_type,
        "detection_radius_nm": float(detection_radius),
        "ships": [dict(member) for member in members],
        "ship_count": len(members),
    }


def group_candidate_fleets_by_side(fleet_candidates: list[dict]) -> list[dict]:
    grouped = []
    for side in ("Blue", "Red"):
        side_fleets = [fleet for fleet in fleet_candidates if fleet["side"] == side]
        grouped.append(
            {
                "side": side,
                "fleet_count": len(side_fleets),
                "ship_count": sum(len(fleet.get("ships", [])) for fleet in side_fleets),
                "fleets": side_fleets,
            }
        )
    return grouped


def candidate_id(kind: str, source_key: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", str(source_key or "").lower()).strip("_")
    return f"{kind}_{cleaned or 'unknown'}"


def parse_geo_position(raw: str) -> dict[str, float]:
    parts = [part.strip() for part in raw.split(",")]
    first = float(parts[0]) if len(parts) > 0 and parts[0] else 0.0
    second = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
    return {"lat": first, "lon": second}


def parse_subsystem(parser: configparser.RawConfigParser, section: str) -> dict | None:
    if not parser.has_option(section, "CurrentIntegrity"):
        return None

    current = float(parser.get(section, "CurrentIntegrity", fallback="0") or 0.0)
    category = subsystem_category(section)
    return {
        "id": section,
        "name": section,
        "category": category,
        "current_integrity": current,
        "nominal_integrity": infer_nominal_integrity(current),
        "repairable": True,
        "state": "operational" if current > 0 else "damaged",
    }


def subsystem_category(section: str) -> str:
    if "WeaponMagazineSystem" in section:
        return "magazine"
    if any(token in section for token in ("WeaponSystemLauncher", "WeaponSystemGun", "WeaponSystemCIWS")):
        return "weapon"
    if "WeaponSystemChaff" in section:
        return "chaff"
    if "FlightDeck" in section:
        return "flightdeck"
    if "SensorSystemSonar" in section:
        return "sonar"
    if any(token in section for token in ("SensorSystemRadar", "SensorSystemVisual", "SensorSystemESM")):
        return "sensor"
    if "VesselControlCenterSystem" in section:
        return "control"
    if "PowerSystem" in section:
        return "power"
    if "VesselRudderSystem" in section:
        return "rudder"
    if "VesselPropulsionSystem" in section:
        return "propulsion"
    if "TowedSystem" in section:
        return "towed"
    if "DecoySystem" in section:
        return "decoy"
    if "CargoSystem" in section:
        return "cargo"
    return "control"


def infer_nominal_integrity(current: float) -> int:
    if current <= 0:
        return 1
    for bucket in STANDARD_INTEGRITY_BUCKETS:
        if current <= bucket:
            return bucket
    return STANDARD_INTEGRITY_BUCKETS[-1]


def parse_ammunition_count(parser: configparser.RawConfigParser, section: str) -> int:
    total = 0
    for key, value in parser.items(section):
        if key.startswith("Ammunition") and key.endswith("_Count"):
            total += int(float(value))
    return total


def parse_loaded_ammunition(raw: str) -> tuple[str, int]:
    if not raw:
        return "", 0
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) < 2:
        return "", 0
    ammo_id = parts[0]
    try:
        quantity = int(float(parts[1]))
    except ValueError:
        quantity = 0
    return ammo_id, quantity


def derive_default_ports(fleets: list[dict]) -> list[dict]:
    ports = []
    for side in ("Blue", "Red"):
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


def average_fleet_position(fleets: list[dict]) -> dict[str, float]:
    if not fleets:
        return {"lat": 0.0, "lon": 0.0}
    return {
        "lat": round(sum(fleet["lat"] for fleet in fleets) / len(fleets), 4),
        "lon": round(sum(fleet["lon"] for fleet in fleets) / len(fleets), 4),
    }


def ship_id_from_section(section: str) -> str:
    return (
        section.replace("Taskforce1", "blue_")
        .replace("Taskforce2", "red_")
        .replace("Vessel", "ship_")
        .replace("Submarine", "sub_")
        .lower()
    )
