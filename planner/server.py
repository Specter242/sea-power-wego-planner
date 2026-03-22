from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import core
from .store import JSONCampaignStore
from .ui import INDEX_HTML


class PlannerServer(ThreadingHTTPServer):
    def __init__(self, server_address, store: JSONCampaignStore):
        super().__init__(server_address, PlannerRequestHandler)
        self.store = store


class PlannerRequestHandler(BaseHTTPRequestHandler):
    server: PlannerServer

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            return self.respond_html(INDEX_HTML)
        if path == "/example-seed.json":
            example_path = Path(__file__).resolve().parents[1] / "examples" / "scenario_seed.json"
            return self.respond_json(json.loads(example_path.read_text(encoding="utf-8")))
        if path == "/terrain/land.geojson":
            terrain_path = Path(__file__).resolve().parent / "data" / "ne_110m_land.geojson"
            return self.respond_json(json.loads(terrain_path.read_text(encoding="utf-8")))
        if path == "/api/campaign/view":
            return self.handle_get_campaign_view(query)
        if path == "/api/campaign/export/scenario.ini":
            return self.handle_export(query)

        self.respond_error(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        parts = [part for part in path.split("/") if part]

        if path == "/api/campaign/import-save":
            return self.handle_import_campaign(query)
        if path == "/api/campaign/import-save/preview":
            return self.handle_import_campaign_preview(query)
        if path == "/api/campaign/reset":
            return self.handle_reset_campaign(query)
        if path == "/api/campaign/resolve":
            return self.handle_resolve(query)
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "ports":
            return self.handle_create_port(query)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "ports" and parts[2] == "preview":
            return self.handle_preview_port(query)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "ports":
            return self.handle_update_port(parts[2], query)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "sides":
            return self.handle_update_side(parts[2], query)
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "fleets":
            return self.handle_create_fleet(query)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "fleets":
            return self.handle_update_fleet(parts[2], query)
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "fleets" and parts[3] == "dock":
            return self.handle_dock_fleet(parts[2], query)
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "fleets" and parts[3] == "merge":
            return self.handle_merge_fleets(parts[2], query)
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "ships":
            return self.handle_create_ship(query)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "ships":
            return self.handle_update_ship(parts[2], query)
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "ships" and parts[3] == "transfer":
            return self.handle_transfer_ship(parts[2], query)
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "ships" and parts[3] == "rearm":
            return self.handle_rearm_ship(parts[2], query)
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "ships" and parts[3] == "repair":
            return self.handle_repair_ship(parts[2], query)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "turns":
            return self.handle_submit_turn(parts[2], query)

        self.respond_error(HTTPStatus.NOT_FOUND, "Not found.")

    def handle_get_campaign_view(self, query: dict):
        state = self.server.store.get_state()
        role = self.require_role(query)
        if role is None:
            return
        self.respond_json(core.build_role_view(state, role))

    def handle_import_campaign(self, query: dict):
        if not self.require_admin(query):
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            result = self.server.store.import_save(payload)
        except (ValueError, FileNotFoundError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.respond_json({"campaign": result["campaign"], "imported": {key: value for key, value in result.items() if key != "campaign"}})

    def handle_import_campaign_preview(self, query: dict):
        if not self.require_admin(query):
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            preview = self.server.store.preview_import_save(payload)
        except (ValueError, FileNotFoundError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.respond_json({"preview": preview})

    def handle_reset_campaign(self, query: dict):
        if not self.require_admin(query):
            return
        payload = self.read_json_body()
        if payload is None:
            return
        state = self.server.store.reset_campaign(payload)
        self.respond_json({"campaign": core.build_admin_view(state)})

    def handle_submit_turn(self, side: str, query: dict):
        state = self.server.store.get_state()
        role = self.require_side_or_admin(query, side)
        if role is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            result = core.submit_turn(state, core.normalize_side_name(side), int(payload.get("turn_number")), payload.get("orders", []))
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json(result)

    def handle_create_port(self, query: dict):
        state = self.server.store.get_state()
        payload = self.read_json_body()
        if payload is None:
            return
        side = str(payload.get("side") or "")
        if self.require_side_or_admin(query, side) is None:
            return
        try:
            port = core.create_port_for_side(state, core.normalize_side_name(side), payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"port": port})

    def handle_preview_port(self, query: dict):
        state = self.server.store.get_state()
        payload = self.read_json_body()
        if payload is None:
            return
        side = str(payload.get("side") or "")
        if self.require_side_or_admin(query, side) is None:
            return
        try:
            preview = core.preview_port_placement(state, core.normalize_side_name(side), payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.respond_json({"placement": preview})

    def handle_update_port(self, port_id: str, query: dict):
        state = self.server.store.get_state()
        port = self.safe_port_lookup(state, port_id)
        if port is None:
            return
        if self.require_side_or_admin(query, port["side"]) is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            updated = core.update_port(state, port_id, payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"port": updated})

    def handle_update_side(self, side: str, query: dict):
        if not self.require_admin(query):
            return
        state = self.server.store.get_state()
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            updated = core.update_side_economy(state, side, payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"side": updated})

    def handle_create_fleet(self, query: dict):
        state = self.server.store.get_state()
        payload = self.read_json_body()
        if payload is None:
            return
        side = str(payload.get("side") or "")
        if self.require_side_or_admin(query, side) is None:
            return
        try:
            fleet = core.create_fleet_for_side(state, core.normalize_side_name(side), payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"fleet": fleet})

    def handle_update_fleet(self, fleet_id: str, query: dict):
        state = self.server.store.get_state()
        fleet = self.safe_fleet_lookup(state, fleet_id)
        if fleet is None:
            return
        role = self.require_side_or_admin(query, fleet["side"])
        if role is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            updated = core.update_fleet(state, fleet_id, payload, admin=role == core.ADMIN)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"fleet": updated})

    def handle_create_ship(self, query: dict):
        state = self.server.store.get_state()
        payload = self.read_json_body()
        if payload is None:
            return
        side = str(payload.get("side") or "")
        if self.require_side_or_admin(query, side) is None:
            return
        try:
            ships = core.create_ships_for_side(state, core.normalize_side_name(side), payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"ship": ships[0], "ships": ships})

    def handle_update_ship(self, ship_id: str, query: dict):
        state = self.server.store.get_state()
        ship = self.safe_ship_lookup(state, ship_id)
        if ship is None:
            return
        if self.require_side_or_admin(query, ship["side"]) is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            updated = core.update_ship(state, ship_id, payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"ship": updated})

    def handle_transfer_ship(self, ship_id: str, query: dict):
        state = self.server.store.get_state()
        ship = self.safe_ship_lookup(state, ship_id)
        if ship is None:
            return
        if self.require_side_or_admin(query, ship["side"]) is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            updated = core.transfer_ship(state, ship_id, payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"ship": updated})

    def handle_rearm_ship(self, ship_id: str, query: dict):
        state = self.server.store.get_state()
        ship = self.safe_ship_lookup(state, ship_id)
        if ship is None:
            return
        role = self.require_side_or_admin(query, ship["side"])
        if role is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        if role == core.ADMIN:
            payload["admin_override"] = bool(payload.get("admin_override", True))
        try:
            job = core.queue_ship_rearm(state, ship_id, payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"job": job})

    def handle_repair_ship(self, ship_id: str, query: dict):
        state = self.server.store.get_state()
        ship = self.safe_ship_lookup(state, ship_id)
        if ship is None:
            return
        if self.require_side_or_admin(query, ship["side"]) is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            job = core.queue_ship_repair(state, ship_id, payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"job": job})

    def handle_dock_fleet(self, fleet_id: str, query: dict):
        state = self.server.store.get_state()
        fleet = self.safe_fleet_lookup(state, fleet_id)
        if fleet is None:
            return
        if self.require_side_or_admin(query, fleet["side"]) is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            updated = core.dock_fleet(state, fleet_id, payload)
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"fleet": updated})

    def handle_merge_fleets(self, fleet_id: str, query: dict):
        state = self.server.store.get_state()
        fleet = self.safe_fleet_lookup(state, fleet_id)
        if fleet is None:
            return
        if self.require_side_or_admin(query, fleet["side"]) is None:
            return
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            merged = core.merge_fleets(state, fleet_id, str(payload.get("target_fleet_id", "")))
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json({"fleet": merged})

    def handle_resolve(self, query: dict):
        if not self.require_admin(query):
            return
        state = self.server.store.get_state()
        try:
            summary = core.resolve_current_turn(state)
        except ValueError as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json(summary)

    def handle_export(self, query: dict):
        if not self.require_admin(query):
            return
        state = self.server.store.get_state()
        payload = core.export_scenario_ini(state)
        encoded = payload.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="campaign.ini"')
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def require_role(self, query: dict) -> str | None:
        try:
            return core.normalize_role_name(first_query_value(query, "role"))
        except ValueError as exc:
            self.respond_error(HTTPStatus.FORBIDDEN, str(exc))
            return None

    def require_admin(self, query: dict) -> bool:
        role = self.require_role(query)
        if role is None:
            return False
        if role != core.ADMIN:
            self.respond_error(HTTPStatus.FORBIDDEN, "Admin role required.")
            return False
        return True

    def require_side_or_admin(self, query: dict, side: str) -> str | None:
        try:
            normalized_side = core.normalize_side_name(side)
        except ValueError as exc:
            self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
            return None
        role = self.require_role(query)
        if role is None:
            return None
        if role == core.ADMIN or role == normalized_side:
            return role
        self.respond_error(HTTPStatus.FORBIDDEN, "Role does not match the requested side.")
        return None

    def safe_fleet_lookup(self, state: dict, fleet_id: str) -> dict | None:
        try:
            return core.fleet_by_id(state, fleet_id)
        except ValueError as exc:
            self.respond_error(HTTPStatus.NOT_FOUND, str(exc))
            return None

    def safe_ship_lookup(self, state: dict, ship_id: str) -> dict | None:
        try:
            return core.ship_by_id(state, ship_id)
        except ValueError as exc:
            self.respond_error(HTTPStatus.NOT_FOUND, str(exc))
            return None

    def safe_port_lookup(self, state: dict, port_id: str) -> dict | None:
        try:
            return core.port_by_id(state, port_id)
        except ValueError as exc:
            self.respond_error(HTTPStatus.NOT_FOUND, str(exc))
            return None

    def read_json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.respond_error(HTTPStatus.BAD_REQUEST, "Invalid Content-Length header.")
        try:
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.respond_error(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON.")
            return None

    def respond_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_html(self, payload: str, status: HTTPStatus = HTTPStatus.OK):
        body = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_error(self, status: HTTPStatus, message: str):
        self.respond_json({"error": message}, status=status)

    def log_message(self, fmt, *args):
        return


def first_query_value(query: dict, key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def create_server(
    host: str,
    port: int,
    campaign_path: str | Path,
    legacy_db_path: str | Path | None = None,
) -> PlannerServer:
    store = JSONCampaignStore(campaign_path, legacy_db_path=legacy_db_path)
    return PlannerServer((host, port), store)
