from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path


LAND = "land"
WATER = "water"
NM_PER_DEGREE_LAT = 60.0


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


def point_is_coastal_land(lat: float, lon: float, *, water_search_nm: float = 3.0) -> bool:
    if not point_on_land(lat, lon):
        return False
    return nearest_water_distance_nm(lat, lon, max_distance_nm=water_search_nm) is not None


def nearest_water_distance_nm(lat: float, lon: float, *, max_distance_nm: float = 10.0, step_nm: float = 0.5) -> float | None:
    if not point_on_land(lat, lon):
        return 0.0
    radius = max(step_nm, 0.5)
    while radius <= max_distance_nm + 1e-9:
        for bearing in range(0, 360, 15):
            sample_lat, sample_lon = offset_point(lat, lon, radius, bearing)
            if not point_on_land(sample_lat, sample_lon):
                return round(radius, 3)
        radius += step_nm
    return None


def snap_port_to_coast(
    lat: float,
    lon: float,
    *,
    max_search_nm: float = 24.0,
    step_nm: float = 1.0,
    coastal_water_nm: float = 3.0,
) -> dict:
    if point_is_coastal_land(lat, lon, water_search_nm=coastal_water_nm):
        return {"lat": round(lat, 6), "lon": round(normalize_lon(lon), 6), "distance_nm": 0.0}

    best: dict | None = None
    radius = max(step_nm, 0.5)
    bearings = list(range(0, 360, 12))
    while radius <= max_search_nm + 1e-9:
        for bearing in bearings:
            sample_lat, sample_lon = offset_point(lat, lon, radius, bearing)
            if not point_is_coastal_land(sample_lat, sample_lon, water_search_nm=coastal_water_nm):
                continue
            candidate = {
                "lat": round(sample_lat, 6),
                "lon": round(normalize_lon(sample_lon), 6),
                "distance_nm": round(radius, 3),
            }
            if best is None or candidate["distance_nm"] < best["distance_nm"]:
                best = candidate
        if best is not None:
            return best
        radius += step_nm
    raise ValueError("No coastal placement found near the selected point.")


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


def offset_point(lat: float, lon: float, distance_nm: float, bearing_deg: float) -> tuple[float, float]:
    radians = math.radians(bearing_deg)
    delta_lat = (distance_nm / NM_PER_DEGREE_LAT) * math.cos(radians)
    lat_scale = max(0.01, math.cos(math.radians(lat)))
    delta_lon = (distance_nm / (NM_PER_DEGREE_LAT * lat_scale)) * math.sin(radians)
    return lat + delta_lat, normalize_lon(lon + delta_lon)
