"""Clean Aurora server entrypoint for minimal health and normal-chat routes."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from . import model_adapter
except ImportError:  # pragma: no cover - direct script execution path
    import model_adapter


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766
HOST_ENV_VAR = "AURORA_CLEAN_HOST"
PORT_ENV_VAR = "AURORA_CLEAN_PORT"
SERVER_NAME = "Aurora_Clean_Build"
CLEAN_MODE = "clean"
SERVER_DIR = Path(__file__).resolve().parent
APP_UI_FILE = SERVER_DIR.parent / "web" / "clean_app.html"
ROOM_UI_FILE = SERVER_DIR.parent / "web" / "clean_room.html"
DEV_UI_FILE = SERVER_DIR.parent / "web" / "clean_dev.html"
HTML_ROUTE_FILES = {
    "/": APP_UI_FILE,
    "/app": APP_UI_FILE,
    "/room": ROOM_UI_FILE,
    "/dev": DEV_UI_FILE,
}
ALLOWED_GET_ROUTES = frozenset({"/", "/app", "/room", "/dev", "/health", "/api/normal-chat"})
ALLOWED_POST_ROUTES = frozenset({"/api/normal-chat"})
FORBIDDEN_ROUTES = frozenset(
    {
        "/api/chat-lite",
        "/api/chat",
        "/api/memory",
        "/api/profile",
        "/developer",
    }
)
IMPLEMENTED_ROUTES = frozenset({"/", "/app", "/room", "/dev", "/health", "/api/normal-chat"})


def normalize_path(path: str) -> str:
    clean_path = (path or "/").split("?", 1)[0].strip()
    if not clean_path.startswith("/"):
        clean_path = f"/{clean_path}"
    return clean_path or "/"


def health_payload() -> dict[str, object]:
    return {
        "ok": True,
        "server": SERVER_NAME,
        "mode": CLEAN_MODE,
    }


def normal_chat_get_payload() -> dict[str, object]:
    return {
        "ok": True,
        "route": "/api/normal-chat",
        "method": "POST required",
    }


def normal_chat_missing_payload() -> dict[str, object]:
    return model_adapter.missing_message_response()


def not_found_payload() -> dict[str, str]:
    return {"error": "Not found"}


def html_for_route(route: str) -> str:
    return HTML_ROUTE_FILES[route].read_text(encoding="utf-8")


def parse_json_message(raw_body: bytes) -> str:
    if not raw_body:
        return ""
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    message = payload.get("message", "")
    if not isinstance(message, str):
        return ""
    return message.strip()


def resolve_host() -> str:
    host = os.getenv(HOST_ENV_VAR, DEFAULT_HOST).strip()
    return host or DEFAULT_HOST


def resolve_port() -> int:
    raw_port = os.getenv(PORT_ENV_VAR, str(DEFAULT_PORT)).strip()
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise SystemExit(f"{PORT_ENV_VAR} must be an integer.") from exc
    if not (0 < port < 65536):
        raise SystemExit(f"{PORT_ENV_VAR} must be between 1 and 65535.")
    return port


class CleanPhoneHandler(BaseHTTPRequestHandler):
    server_version = "AuroraCleanHTTP/0.1"

    def _send_html(self, status_code: int, body_text: str) -> None:
        body = body_text.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        route = normalize_path(self.path)
        if route in HTML_ROUTE_FILES:
            self._send_html(HTTPStatus.OK, html_for_route(route))
            return
        if route == "/health":
            self._send_json(HTTPStatus.OK, health_payload())
            return
        if route == "/api/normal-chat":
            self._send_json(HTTPStatus.OK, normal_chat_get_payload())
            return
        self._send_json(HTTPStatus.NOT_FOUND, not_found_payload())

    def do_POST(self) -> None:  # noqa: N802
        route = normalize_path(self.path)
        if route != "/api/normal-chat":
            self._send_json(HTTPStatus.NOT_FOUND, not_found_payload())
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b""
        message = parse_json_message(raw_body)
        if not message:
            self._send_json(HTTPStatus.BAD_REQUEST, normal_chat_missing_payload())
            return
        adapter_response = model_adapter.generate_normal_chat_reply(message)
        if adapter_response.get("ok") is True:
            self._send_json(HTTPStatus.OK, adapter_response)
            return
        self._send_json(model_adapter.http_status_for_failure(adapter_response), adapter_response)

    def log_message(self, format: str, *args: object) -> None:
        """Keep the clean server quiet during local tests."""


def create_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    resolved_host = host or resolve_host()
    resolved_port = port if port is not None else resolve_port()
    return ThreadingHTTPServer((resolved_host, resolved_port), CleanPhoneHandler)


def serve(host: str | None = None, port: int | None = None) -> None:
    server = create_server(host=host, port=port)
    listen_host, listen_port = server.server_address
    print(f"{SERVER_NAME} clean server listening on http://{listen_host}:{listen_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
