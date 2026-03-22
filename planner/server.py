from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import core
from .store import SQLiteSessionStore
from .ui import INDEX_HTML


class PlannerServer(ThreadingHTTPServer):
    def __init__(self, server_address, store: SQLiteSessionStore):
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
            return self.respond_json(json.loads(example_path.read_text()))

        parts = [part for part in path.split("/") if part]
        if len(parts) == 3 and parts[0] == "sessions" and parts[2] == "view":
            return self.handle_get_view(parts[1], query)
        if len(parts) == 4 and parts[0] == "sessions" and parts[2] == "export" and parts[3] == "scenario.ini":
            return self.handle_export(parts[1], query)

        self.respond_error(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        parts = [part for part in path.split("/") if part]

        if path == "/sessions":
            return self.handle_create_session()
        if len(parts) == 4 and parts[0] == "sessions" and parts[2] == "turns":
            return self.handle_submit_turn(parts[1], parts[3], query)
        if len(parts) == 3 and parts[0] == "sessions" and parts[2] == "resolve":
            return self.handle_resolve(parts[1], query)

        self.respond_error(HTTPStatus.NOT_FOUND, "Not found.")

    def handle_create_session(self):
        payload = self.read_json_body()
        if payload is None:
            return
        try:
            state = self.server.store.create_session(payload)
        except ValueError as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))

        base_url = f"http://{self.headers.get('Host', 'localhost')}"
        response = {
            "session_id": state["session_id"],
            "blue_token": state["tokens"][core.BLUE],
            "red_token": state["tokens"][core.RED],
            "admin_token": state["tokens"]["admin"],
            "blue_url": f"{base_url}/?session={state['session_id']}&token={state['tokens'][core.BLUE]}",
            "red_url": f"{base_url}/?session={state['session_id']}&token={state['tokens'][core.RED]}",
            "export_url": f"{base_url}/sessions/{state['session_id']}/export/scenario.ini?admin_token={state['tokens']['admin']}",
        }
        self.respond_json(response, status=HTTPStatus.CREATED)

    def handle_get_view(self, session_id: str, query: dict):
        state = self.server.store.get_state(session_id)
        if state is None:
            return self.respond_error(HTTPStatus.NOT_FOUND, "Session not found.")

        token = first_query_value(query, "token")
        role = self.server.store.session_role_for_token(state, token)
        if role not in core.SIDES:
            return self.respond_error(HTTPStatus.FORBIDDEN, "A valid side token is required.")

        self.respond_json(core.build_player_view(state, role))

    def handle_submit_turn(self, session_id: str, side: str, query: dict):
        state = self.server.store.get_state(session_id)
        if state is None:
            return self.respond_error(HTTPStatus.NOT_FOUND, "Session not found.")

        token = first_query_value(query, "token")
        role = self.server.store.session_role_for_token(state, token)
        if role != side:
            return self.respond_error(HTTPStatus.FORBIDDEN, "Token does not match the requested side.")

        payload = self.read_json_body()
        if payload is None:
            return
        try:
            result = core.submit_turn(state, side, int(payload.get("turn_number")), payload.get("orders", []))
        except (ValueError, TypeError) as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))

        self.server.store.save_state(state)
        self.respond_json(result)

    def handle_resolve(self, session_id: str, query: dict):
        state = self.server.store.get_state(session_id)
        if state is None:
            return self.respond_error(HTTPStatus.NOT_FOUND, "Session not found.")

        admin_token = first_query_value(query, "admin_token")
        if self.server.store.session_role_for_token(state, admin_token) != "admin":
            return self.respond_error(HTTPStatus.FORBIDDEN, "Admin token required.")

        try:
            summary = core.resolve_current_turn(state)
        except ValueError as exc:
            return self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        self.server.store.save_state(state)
        self.respond_json(summary)

    def handle_export(self, session_id: str, query: dict):
        state = self.server.store.get_state(session_id)
        if state is None:
            return self.respond_error(HTTPStatus.NOT_FOUND, "Session not found.")
        admin_token = first_query_value(query, "admin_token")
        if self.server.store.session_role_for_token(state, admin_token) != "admin":
            return self.respond_error(HTTPStatus.FORBIDDEN, "Admin token required.")

        payload = core.export_scenario_ini(state)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{session_id}.ini"')
        encoded = payload.encode("utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

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


def create_server(host: str, port: int, db_path: str | Path) -> PlannerServer:
    store = SQLiteSessionStore(db_path)
    return PlannerServer((host, port), store)
