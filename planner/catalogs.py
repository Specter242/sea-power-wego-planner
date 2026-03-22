from __future__ import annotations

import configparser
import json
import re
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_WORK_UNITS_PER_TURN = 8.0
DEFAULT_EXTERNAL_CATALOG_DIR = Path(r"c:\Users\budzp\Desktop\seapower aux")
DEFAULT_AMMO_DATABASE_NAME = "ammo_database.json"
DEFAULT_COST_MATRIX_NAME = "sea_power_cost_matrix_hull_plus_weapons_updated.html"
SAVE_SECTION_PATTERN = re.compile(r"^(Taskforce1|Taskforce2)(Vessel|Submarine)\d+$")
WEAPON_SYSTEM_TOKENS = ("WeaponSystemLauncher", "WeaponSystemGun", "WeaponSystemCIWS", "WeaponSystemChaff")
NATION_LABELS = {
    "usn": "United States",
    "ir": "Iran",
    "rn": "Royal Navy",
    "sov": "Soviet Union",
    "ussr": "Soviet Union",
    "plan": "China",
    "pla": "China",
    "jmsdf": "Japan",
}


def load_catalogs(config: dict | None) -> dict:
    paths = resolve_catalog_paths(config or {})
    ammo_database = {}
    ship_costs = {}
    weapon_prices = {}
    html_loadouts = {}
    save_inference = {}

    ammo_path = _path_from_config(paths, "ammo_database")
    if ammo_path and ammo_path.exists():
        ammo_database = parse_ammo_database(ammo_path)

    cost_matrix_path = _path_from_config(paths, "cost_matrix_html")
    if cost_matrix_path and cost_matrix_path.exists():
        ship_costs, weapon_prices, html_loadouts = parse_cost_matrix(cost_matrix_path)

    save_paths = [path for path in _paths_from_config(paths, "sav_files") if path.exists()]
    if save_paths:
        save_inference = parse_save_loadout_fallbacks(save_paths)

    ship_index = sorted(set(ammo_database) | set(ship_costs) | set(save_inference))
    ship_options = build_ship_options(ship_index, ship_costs, ammo_database, html_loadouts, save_inference)
    status = build_catalog_status(ship_index, ammo_database, ship_costs, weapon_prices, save_inference)
    return {
        "paths": {
            "ammo_database": str(ammo_path) if ammo_path else "",
            "cost_matrix_html": str(cost_matrix_path) if cost_matrix_path else "",
            "sav_files": [str(path) for path in save_paths],
        },
        "status": status,
        "ammo_database": ammo_database,
        "ship_costs": ship_costs,
        "weapon_prices": weapon_prices,
        "html_loadouts": html_loadouts,
        "save_inference": save_inference,
        "repair_nominal_overrides": {},
        "ship_index": ship_index,
        "ship_options": ship_options,
        "work_units_per_turn": DEFAULT_WORK_UNITS_PER_TURN,
    }


def resolve_catalog_paths(config: dict) -> dict:
    ammo_path = _existing_path(_path_from_config(config, "ammo_database"))
    cost_matrix_path = _existing_path(_path_from_config(config, "cost_matrix_html"))
    save_paths = [path for path in _paths_from_config(config, "sav_files") if path.exists()]

    if not ammo_path and not cost_matrix_path:
        defaults = default_catalog_paths()
        ammo_path = defaults.get("ammo_database")
        cost_matrix_path = defaults.get("cost_matrix_html")
        if not save_paths:
            save_paths = defaults.get("sav_files", [])
    elif not save_paths:
        defaults = default_catalog_paths()
        save_paths = defaults.get("sav_files", [])

    return {
        "ammo_database": str(ammo_path) if ammo_path else "",
        "cost_matrix_html": str(cost_matrix_path) if cost_matrix_path else "",
        "sav_files": [str(path) for path in save_paths],
    }


def default_catalog_paths() -> dict:
    ammo_path = _existing_path(DEFAULT_EXTERNAL_CATALOG_DIR / DEFAULT_AMMO_DATABASE_NAME)
    cost_matrix_path = _existing_path(DEFAULT_EXTERNAL_CATALOG_DIR / DEFAULT_COST_MATRIX_NAME)
    save_paths = sorted(path for path in DEFAULT_EXTERNAL_CATALOG_DIR.glob("*.sav") if path.is_file())
    return {
        "ammo_database": ammo_path,
        "cost_matrix_html": cost_matrix_path,
        "sav_files": save_paths,
    }


def catalog_path_snapshot(catalogs: dict) -> dict:
    paths = catalogs.get("paths", {}) if isinstance(catalogs, dict) else {}
    return {
        "ammo_database": str(paths.get("ammo_database") or ""),
        "cost_matrix_html": str(paths.get("cost_matrix_html") or ""),
        "sav_files": [str(item) for item in (paths.get("sav_files") or [])],
    }


def catalog_is_available(catalogs: dict) -> bool:
    return bool((catalogs or {}).get("ship_index"))


def parse_ammo_database(path: str | Path) -> dict[str, dict[str, int]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    ships = payload.get("ships", {})
    normalized = {}
    for ship_id, loadout in ships.items():
        if not isinstance(loadout, dict):
            continue
        normalized[str(ship_id)] = {str(ammo_id): int(quantity) for ammo_id, quantity in loadout.items()}
    return normalized


def parse_cost_matrix(path: str | Path) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict[str, int]]]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    ship_costs: dict[str, dict] = {}
    weapon_prices: dict[str, dict] = {}
    html_loadouts: dict[str, dict[str, int]] = {}

    parser = CostMatrixHTMLParser()
    parser.feed(text)
    for row in parser.ship_rows:
        ship_id = row["ship_id"]
        loadout_rows = row["loadout_rows"]
        html_loadout = {entry["weapon_id"]: entry["quantity"] for entry in loadout_rows if entry["quantity"] > 0}
        if html_loadout:
            html_loadouts[ship_id] = html_loadout
        ship_costs[ship_id] = {
            "ship_id": ship_id,
            "name": row["name"],
            "role": row["role"],
            "search_text": row["search_text"],
            "sensors": row["sensors"],
            "summary_note": row["summary_note"],
            "base_hull": row["base_hull"],
            "weapons_value": row["weapons_value"],
            "total_value": row["total_value"],
            "loadout_rows": loadout_rows,
        }

    for row in parser.weapon_rows:
        weapon_prices[row["weapon_id"]] = row

    return ship_costs, weapon_prices, html_loadouts


class CostMatrixHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ship_rows: list[dict] = []
        self.weapon_rows: list[dict] = []
        self.current_ship: dict | None = None
        self.current_weapon: dict | None = None
        self.current_loadout_row: list[str] | None = None
        self.current_ship_cells: list[str] | None = None
        self.current_weapon_cells: list[str] | None = None
        self.current_text: list[str] | None = None
        self.suspended_text: list[str] | None = None
        self.in_loadout_table = False
        self.in_details = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attributes = {key: value or "" for key, value in attrs}
        class_names = set((attributes.get("class") or "").split())
        if tag == "tr" and "ship-row" in class_names:
            self.current_ship = {"attrs": attributes, "loadout_rows": []}
            self.current_ship_cells = []
            return
        if tag == "tr" and self.current_ship is not None and self.in_loadout_table:
            self.current_loadout_row = []
            return
        if tag == "tr" and "weapon-row" in class_names:
            self.current_weapon = {}
            self.current_weapon_cells = []
            return
        if tag == "table" and self.current_ship is not None and "loadout-table" in class_names:
            self.in_loadout_table = True
            return
        if tag == "details" and self.current_ship is not None:
            self.in_details = True
            return
        if tag in ("td", "th"):
            if self.current_loadout_row is not None:
                if self.current_text is not None:
                    self.suspended_text = self.current_text
                self.current_text = []
            elif self.current_weapon is not None:
                self.current_text = []
            elif self.current_ship_cells is not None and not self.in_loadout_table:
                self.current_text = []
            return
        if tag == "br" and self.current_text is not None:
            self.current_text.append(" ")

    def handle_endtag(self, tag: str):
        if tag in ("td", "th") and self.current_text is not None:
            value = collapse_whitespace("".join(self.current_text))
            if self.current_loadout_row is not None:
                self.current_loadout_row.append(value)
                self.current_text = self.suspended_text
                self.suspended_text = None
            elif self.current_weapon_cells is not None:
                self.current_weapon_cells.append(value)
                self.current_text = None
            elif self.current_ship_cells is not None and not self.in_loadout_table:
                self.current_ship_cells.append(value)
                self.current_text = None
            return
        if tag == "details" and self.current_ship is not None:
            self.in_details = False
            return
        if tag == "table" and self.in_loadout_table:
            self.in_loadout_table = False
            return
        if tag == "tr" and self.current_loadout_row is not None:
            self._finalize_loadout_row()
            return
        if tag == "tr" and self.current_weapon_cells is not None:
            self._finalize_weapon_row()
            return
        if tag == "tr" and self.current_ship_cells is not None and self.current_ship is not None:
            self._finalize_ship_row()

    def handle_data(self, data: str):
        if self.current_text is None:
            return
        if self.current_loadout_row is not None or self.current_weapon_cells is not None:
            self.current_text.append(data)
        elif not self.in_details:
            self.current_text.append(data)

    def _finalize_loadout_row(self):
        cells = self.current_loadout_row or []
        if len(cells) >= 6 and str(cells[1]).lower() != "id":
            self.current_ship["loadout_rows"].append(
                {
                    "name": cells[0],
                    "weapon_id": cells[1],
                    "quantity": int(parse_number(cells[2])),
                    "basis": cells[3],
                    "unit_price": parse_number(cells[4]),
                    "extended_cost": parse_number(cells[5]),
                }
            )
        self.current_loadout_row = None

    def _finalize_weapon_row(self):
        cells = self.current_weapon_cells or []
        if len(cells) >= 4:
            self.weapon_rows.append(
                {
                    "weapon_id": cells[1],
                    "name": cells[0],
                    "basis": cells[2],
                    "unit_price": parse_number(cells[3]),
                }
            )
        self.current_weapon = None
        self.current_weapon_cells = None

    def _finalize_ship_row(self):
        cells = self.current_ship_cells or []
        attrs = self.current_ship.get("attrs", {}) if self.current_ship else {}
        ship_id = self._ship_id_for_row(cells, attrs)
        if ship_id:
            self.ship_rows.append(
                {
                    "ship_id": ship_id,
                    "name": str(attrs.get("data-name") or humanize_ship_id(ship_id)),
                    "role": str(attrs.get("data-role") or (cells[1] if len(cells) > 1 else "Unknown")),
                    "search_text": str(attrs.get("data-search") or ""),
                    "sensors": cells[2] if len(cells) > 2 else "",
                    "summary_note": cells[6] if len(cells) > 6 else "",
                    "base_hull": parse_number(str(attrs.get("data-base") or (cells[3] if len(cells) > 3 else 0))),
                    "weapons_value": parse_number(str(attrs.get("data-weapons") or (cells[4] if len(cells) > 4 else 0))),
                    "total_value": parse_number(str(attrs.get("data-total") or (cells[5] if len(cells) > 5 else 0))),
                    "loadout_rows": list(self.current_ship.get("loadout_rows", [])),
                }
            )
        self.current_ship = None
        self.current_ship_cells = None

    def _ship_id_for_row(self, cells: list[str], attrs: dict) -> str:
        search_tokens = str(attrs.get("data-search") or "").split()
        if search_tokens and "_" in search_tokens[0]:
            return search_tokens[0]
        first_cell = cells[0] if cells else ""
        for token in str(first_cell).split():
            if "_" in token:
                return token
        return ""


def parse_save_loadout_fallbacks(paths: list[str | Path]) -> dict[str, dict[str, int]]:
    inferred: dict[str, dict[str, int]] = {}
    for raw_path in paths:
        path = Path(raw_path)
        parser = configparser.RawConfigParser(strict=False)
        parser.optionxform = str
        parser.read(path, encoding="utf-8")
        sections = parser.sections()
        for section in sections:
            if not SAVE_SECTION_PATTERN.match(section):
                continue
            ship_id = parser.get(section, "Type", fallback="").strip()
            if not ship_id:
                continue
            loadout = infer_unit_loadout_from_save(parser, sections, section)
            if not loadout:
                continue
            merged = inferred.setdefault(ship_id, {})
            for ammo_id, quantity in loadout.items():
                merged[ammo_id] = max(merged.get(ammo_id, 0), quantity)
    return inferred


def infer_unit_loadout_from_save(
    parser: configparser.RawConfigParser,
    sections: list[str],
    section: str,
) -> dict[str, int]:
    loadout: dict[str, int] = {}
    related_sections = [entry for entry in sections if entry.startswith(section) and entry != section]
    pending_magazine_count: int | None = None
    for related in related_sections:
        if "WeaponMagazineSystem" in related:
            pending_magazine_count = parse_save_ammunition_count(parser, related)
            continue
        if any(token in related for token in WEAPON_SYSTEM_TOKENS):
            ammo_id, loaded_count = parse_save_loaded_ammunition(parser.get(related, "LoadedAmmunitions", fallback=""))
            if not ammo_id:
                continue
            loadout[ammo_id] = loadout.get(ammo_id, 0) + loaded_count
            if pending_magazine_count is not None:
                loadout[ammo_id] = loadout.get(ammo_id, 0) + pending_magazine_count
                pending_magazine_count = None
    return loadout


def parse_save_ammunition_count(parser: configparser.RawConfigParser, section: str) -> int:
    total = 0
    for option, value in parser.items(section):
        if not option.startswith("Ammunition") or not option.endswith("_Count"):
            continue
        try:
            total += int(float(value or 0))
        except ValueError:
            continue
    return total


def parse_save_loaded_ammunition(raw: str) -> tuple[str, int]:
    if "," not in str(raw or ""):
        return "", 0
    ammo_id, count = raw.split(",", 1)
    ammo_id = ammo_id.strip()
    if not ammo_id:
        return "", 0
    try:
        return ammo_id, int(float(count.strip() or 0))
    except ValueError:
        return ammo_id, 0


def class_profile(catalogs: dict, sea_power_type: str) -> dict:
    ship_costs = catalogs.get("ship_costs", {})
    ship_option = ship_option_for_id(catalogs, sea_power_type)
    max_loadout, loadout_source = max_loadout_for_ship(catalogs, sea_power_type)
    return {
        "sea_power_type": sea_power_type,
        "max_loadout": max_loadout,
        "loadout_source": loadout_source,
        "costs": dict(ship_costs.get(sea_power_type, {})),
        "display_name": ship_option["name"],
        "role": ship_option["role"],
        "nation_code": ship_option["nation_code"],
        "nation_label": ship_option["nation_label"],
        "display_label": ship_option["display_label"],
        "search_text": ship_option["search_text"],
        "sensors": ship_option["sensors"],
        "summary_note": ship_option["summary_note"],
    }


def max_loadout_for_ship(catalogs: dict, ship_id: str) -> tuple[dict[str, int], str]:
    ammo_database = catalogs.get("ammo_database", {}) if isinstance(catalogs, dict) else {}
    if ship_id in ammo_database:
        return dict(ammo_database.get(ship_id, {})), "ammo_database"
    html_loadouts = catalogs.get("html_loadouts", {}) if isinstance(catalogs, dict) else {}
    if ship_id in html_loadouts:
        return dict(html_loadouts.get(ship_id, {})), "cost_matrix_html"
    save_inference = catalogs.get("save_inference", {}) if isinstance(catalogs, dict) else {}
    if ship_id in save_inference:
        return dict(save_inference.get(ship_id, {})), "save_inference"
    return {}, "unavailable"


def rearm_cost_and_work(weapon_prices: dict, deltas: dict[str, int]) -> tuple[float, float, list[dict]]:
    total_cost = 0.0
    total_work = 0.0
    line_items = []
    for weapon_id, quantity in sorted(deltas.items()):
        if quantity <= 0:
            continue
        pricing = weapon_prices.get(weapon_id, {})
        basis = pricing.get("basis", "each")
        unit_price = float(pricing.get("unit_price", 0.0))
        multiplier = basis_to_multiplier(basis)
        extended_cost = quantity * multiplier * unit_price
        work_units = quantity * multiplier
        total_cost += extended_cost
        total_work += work_units
        line_items.append(
            {
                "weapon_id": weapon_id,
                "quantity": int(quantity),
                "basis": basis,
                "unit_price": unit_price,
                "extended_cost": round(extended_cost, 4),
                "work_units": round(work_units, 4),
            }
        )
    return round(total_cost, 4), round(total_work, 4), line_items


def basis_to_multiplier(basis: str) -> float:
    normalized = (basis or "each").strip().lower()
    return {
        "each": 1.0,
        "per 10": 0.1,
        "per 50": 0.02,
        "per 100": 0.01,
        "per 1000": 0.001,
    }.get(normalized, 1.0)


def parse_number(raw: str) -> float:
    cleaned = str(raw or "").replace(",", "").strip()
    return float(cleaned) if cleaned else 0.0


def html_unescape(value: str) -> str:
    return (
        str(value or "")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )


def strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return collapse_whitespace(html_unescape(text))


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def build_ship_options(
    ship_index: list[str],
    ship_costs: dict[str, dict],
    ammo_database: dict[str, dict[str, int]],
    html_loadouts: dict[str, dict[str, int]],
    save_inference: dict[str, dict[str, int]],
) -> list[dict]:
    options = []
    for ship_id in ship_index:
        cost_entry = ship_costs.get(ship_id, {})
        role = str(cost_entry.get("role") or "Unknown")
        display_name = str(cost_entry.get("name") or humanize_ship_id(ship_id))
        class_group = broad_class_group(ship_id, display_name, role)
        nation_code = nation_code_from_ship_id(ship_id)
        nation_label = nation_label_from_code(nation_code)
        _, loadout_source = max_loadout_for_ship(
            {
                "ammo_database": ammo_database,
                "html_loadouts": html_loadouts,
                "save_inference": save_inference,
            },
            ship_id,
        )
        search_text = collapse_whitespace(
            " ".join(
                [
                    ship_id,
                    display_name,
                    role,
                    str(cost_entry.get("search_text") or ""),
                    str(cost_entry.get("sensors") or ""),
                    str(cost_entry.get("summary_note") or ""),
                ]
            )
        )
        options.append(
            {
                "ship_id": ship_id,
                "name": display_name,
                "role": role,
                "class_group": class_group,
                "nation_code": nation_code,
                "nation_label": nation_label,
                "display_label": f"{display_name} ({ship_id})",
                "search_text": search_text,
                "sensors": str(cost_entry.get("sensors") or ""),
                "summary_note": str(cost_entry.get("summary_note") or ""),
                "class_base_hull": float(cost_entry.get("base_hull", 0.0) or 0.0),
                "class_weapons_value": float(cost_entry.get("weapons_value", 0.0) or 0.0),
                "class_total_value": float(cost_entry.get("total_value", 0.0) or 0.0),
                "loadout_reference": loadout_source,
            }
        )
    options.sort(key=lambda item: (item["nation_label"], item["class_group"], item["name"], item["ship_id"]))
    return options


def ship_option_for_id(catalogs: dict, ship_id: str) -> dict:
    for option in catalogs.get("ship_options", []):
        if option.get("ship_id") == ship_id:
            return dict(option)
    nation_code = nation_code_from_ship_id(ship_id)
    nation_label = nation_label_from_code(nation_code)
    display_name = humanize_ship_id(ship_id)
    _, loadout_source = max_loadout_for_ship(catalogs, ship_id)
    return {
        "ship_id": ship_id,
        "name": display_name,
        "role": "Unknown",
        "class_group": broad_class_group(ship_id, display_name, "Unknown"),
        "nation_code": nation_code,
        "nation_label": nation_label,
        "display_label": f"{display_name} ({ship_id})",
        "search_text": f"{display_name} {ship_id}",
        "sensors": "",
        "summary_note": "",
        "class_base_hull": 0.0,
        "class_weapons_value": 0.0,
        "class_total_value": 0.0,
        "loadout_reference": loadout_source,
    }


def build_catalog_status(
    ship_index: list[str],
    ammo_database: dict[str, dict[str, int]],
    ship_costs: dict[str, dict],
    weapon_prices: dict[str, dict],
    save_inference: dict[str, dict[str, int]],
) -> dict:
    available = bool(ship_index)
    message = (
        f"{len(ship_index)} ship classes loaded."
        if available
        else "Catalog unavailable. Add ammo database and cost matrix sources to enable ship creation."
    )
    return {
        "available": available,
        "message": message,
        "ship_count": len(ship_index),
        "ammo_database_loaded": bool(ammo_database),
        "cost_matrix_loaded": bool(ship_costs),
        "weapon_price_count": len(weapon_prices),
        "save_inference_loaded": bool(save_inference),
        "save_inference_count": len(save_inference),
    }


def nation_code_from_ship_id(ship_id: str) -> str:
    return str(ship_id or "").split("_", 1)[0].lower() or "unknown"


def nation_label_from_code(nation_code: str) -> str:
    return NATION_LABELS.get(str(nation_code or "").lower(), str(nation_code or "unknown").upper())


def humanize_ship_id(ship_id: str) -> str:
    parts = [part for part in str(ship_id or "").split("_") if part]
    if len(parts) > 1:
        parts = parts[1:]
    if not parts:
        return str(ship_id or "Unknown Ship")
    return " ".join(part.capitalize() for part in parts)


def broad_class_group(ship_id: str, display_name: str, role: str) -> str:
    tokens = normalized_ship_tokens(ship_id, display_name)
    for token in tokens:
        if token in {"dd", "ddg", "ddh"}:
            return "Destroyer"
        if token in {"cg", "cgn"}:
            return "Cruiser"
        if token in {"ff", "ffg", "fsg"}:
            return "Frigate"
        if token in {"pc", "pt", "pb", "corvette"}:
            return "Patrol"
        if token in {"ss", "ssn", "ssk", "ssbn", "ssgn"}:
            return "Submarine"
        if token in {"cv", "cva", "cvn", "cve"}:
            return "Carrier"
        if token in {"lha", "lhd", "lpd", "lst", "lsm"}:
            return "Amphibious"
        if token in {"ao", "aoe", "aor", "ae", "afs", "aux"}:
            return "Auxiliary"
        if token in {"mcm", "ms", "mso", "mcs"}:
            return "Mine Warfare"
    return broad_group_from_role(role)


def normalized_ship_tokens(ship_id: str, display_name: str) -> list[str]:
    raw_parts = [part.lower() for part in re.split(r"[^a-z0-9]+", f"{ship_id} {display_name}") if part]
    if raw_parts and len(raw_parts) > 1 and raw_parts[0] == nation_code_from_ship_id(ship_id):
        raw_parts = raw_parts[1:]
    return raw_parts


def broad_group_from_role(role: str) -> str:
    normalized = str(role or "").strip().lower()
    if not normalized:
        return "Other"
    if "destroy" in normalized:
        return "Destroyer"
    if "cruis" in normalized:
        return "Cruiser"
    if "frigate" in normalized:
        return "Frigate"
    if any(token in normalized for token in ("patrol", "corvette", "missile boat", "fast attack")):
        return "Patrol"
    if "sub" in normalized:
        return "Submarine"
    if "carrier" in normalized:
        return "Carrier"
    if any(token in normalized for token in ("amphib", "landing", "assault ship")):
        return "Amphibious"
    if any(token in normalized for token in ("aux", "replenishment", "tanker", "cargo", "support")):
        return "Auxiliary"
    if "mine" in normalized:
        return "Mine Warfare"
    return "Other"


def _path_from_config(config: dict, key: str) -> Path | None:
    value = config.get(key)
    if not value:
        return None
    return Path(str(value))


def _paths_from_config(config: dict, key: str) -> list[Path]:
    value = config.get(key) or []
    if isinstance(value, (str, Path)):
        value = [value]
    if not isinstance(value, list):
        return []
    return [Path(str(item)) for item in value if str(item).strip()]


def _existing_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.exists() else None
