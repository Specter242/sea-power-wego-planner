from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


LAND = "land"
WATER = "water"


@lru_cache(maxsize=1)
def land_polygons() -> list[dict]:
    land_path = Path(__file__).resolve().parent / "data" / "ne_110m_land.geojson"
    payload = json.loads(land_path.read_text())
    polygons = []
    for feature in payload.get("features", []):
        geometry = feature.get("geometry") or {}
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates") or []
        if geom_type == "Polygon":
            polygons.append(build_polygon_record(coordinates))
        elif geom_type == "MultiPolygon":
            for polygon in coordinates:
                polygons.append(build_polygon_record(polygon))
    return polygons


def build_polygon_record(rings: list[list[list[float]]]) -> dict:
    all_points = [point for ring in rings for point in ring]
    lons = [point[0] for point in all_points]
    lats = [point[1] for point in all_points]
    return {
        "rings": rings,
        "bbox": (min(lons), min(lats), max(lons), max(lats)),
    }


def unit_domain(unit_type: str) -> str | None:
    normalized = (unit_type or "").strip().lower()
    if not normalized:
        return None

    water_keywords = ("surface", "subsurface", "naval", "sea", "ship", "submarine", "convoy")
    land_keywords = ("land", "ground", "shore", "coastal", "airbase", "sam", "site", "battery")

    if any(keyword in normalized for keyword in water_keywords):
        return WATER
    if any(keyword in normalized for keyword in land_keywords):
        return LAND
    return None


def point_on_land(lat: float, lon: float) -> bool:
    lon = normalize_lon(lon)
    for polygon in land_polygons():
        min_lon, min_lat, max_lon, max_lat = polygon["bbox"]
        if lon < min_lon or lon > max_lon or lat < min_lat or lat > max_lat:
            continue
        if point_in_polygon(lat, lon, polygon["rings"]):
            return True
    return False


def validate_unit_position(unit_type: str, lat: float, lon: float) -> None:
    domain = unit_domain(unit_type)
    if domain is None:
        return

    is_land = point_on_land(lat, lon)
    if domain == WATER and is_land:
        raise ValueError(f"{unit_type} units must stay on water.")
    if domain == LAND and not is_land:
        raise ValueError(f"{unit_type} units must stay on land.")


def validate_movement_segment(
    unit_type: str,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    samples: int = 16,
) -> None:
    domain = unit_domain(unit_type)
    if domain is None:
        return

    validate_unit_position(unit_type, end_lat, end_lon)
    for sample_index in range(1, samples + 1):
        fraction = sample_index / samples
        lat = start_lat + (end_lat - start_lat) * fraction
        lon = start_lon + (end_lon - start_lon) * fraction
        validate_unit_position(unit_type, lat, lon)


def point_in_polygon(lat: float, lon: float, rings: list[list[list[float]]]) -> bool:
    if not rings:
        return False
    if not point_in_ring(lat, lon, rings[0]):
        return False
    for hole in rings[1:]:
        if point_in_ring(lat, lon, hole):
            return False
    return True


def point_in_ring(lat: float, lon: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def normalize_lon(lon: float) -> float:
    return ((float(lon) + 180.0) % 360.0) - 180.0
