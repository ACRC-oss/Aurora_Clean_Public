"""Manual smoke runner for the Aurora clean route contract."""

from __future__ import annotations

import argparse
import http.client
import json
import sys
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlsplit


DEFAULT_BASE_URL = "http://127.0.0.1:8766"

HTML_ROUTE_MARKERS = {
    "/": ["Aurora Clean Build"],
    "/app": ["Aurora Clean Build", "Clean companion system prototype", "Talk with Aurora"],
    "/room": ["Aurora Clean Build", "clean companion system prototype"],
    "/dev": ["Aurora Clean Build / Dev Status", "Read-only"],
}

FORBIDDEN_ROUTES = (
    "/api/chat-lite",
    "/api/chat",
    "/api/memory",
    "/api/profile",
    "/developer",
    "/../../private-file",
    "/server/clean_phone_server.py",
)


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> dict[str, object]:
        payload = json.loads(self.text)
        if not isinstance(payload, dict):
            raise ValueError("JSON payload is not an object.")
        return payload


class SmokeFailure(Exception):
    """Raised when a smoke check fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the Aurora clean routes.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for the running clean server.")
    return parser.parse_args(argv)


def build_target(base_url: str, route: str) -> tuple[str, int, str, bool]:
    parts = urlsplit(base_url)
    require(parts.scheme in {"http", "https"}, "base URL must use http or https")
    require(bool(parts.hostname), "base URL must include a host")

    base_path = parts.path.rstrip("/")
    target_path = route if route.startswith("/") else f"/{route}"
    target = f"{base_path}{target_path}" if base_path else target_path
    if parts.query:
        target = f"{target}?{parts.query}"

    is_https = parts.scheme == "https"
    port = parts.port or (443 if is_https else 80)
    return parts.hostname, port, target, is_https


def request(base_url: str, method: str, route: str, body: bytes | None = None, headers: dict[str, str] | None = None) -> Response:
    host, port, target, is_https = build_target(base_url, route)
    connection_class = http.client.HTTPSConnection if is_https else http.client.HTTPConnection
    connection = connection_class(host, port, timeout=30)
    try:
        connection.request(method, target, body=body, headers=headers or {})
        raw_response = connection.getresponse()
        response = Response(
            status=raw_response.status,
            headers={key.lower(): value for key, value in raw_response.getheaders()},
            body=raw_response.read(),
        )
    finally:
        connection.close()
    return response


def check_cors(response: Response) -> None:
    allow_origin = response.headers.get("access-control-allow-origin", "")
    allow_headers = response.headers.get("access-control-allow-headers", "")
    allow_methods = response.headers.get("access-control-allow-methods", "")

    require(allow_origin == "*", "missing Access-Control-Allow-Origin: *")
    require("content-type" in allow_headers.lower(), "missing Content-Type in Access-Control-Allow-Headers")

    lowered_methods = allow_methods.lower()
    for method in ("get", "post", "options"):
        require(method in lowered_methods, f"missing {method.upper()} in Access-Control-Allow-Methods")


def check_html_route(base_url: str, route: str, markers: Iterable[str]) -> None:
    response = request(base_url, "GET", route)
    check_cors(response)
    require(response.status == 200, f"expected HTTP 200, got {response.status}")
    require("text/html" in response.headers.get("content-type", ""), "expected text/html response")
    for marker in markers:
        require(marker in response.text, f"missing body marker: {marker}")


def check_health(base_url: str) -> None:
    response = request(base_url, "GET", "/health")
    check_cors(response)
    require(response.status == 200, f"expected HTTP 200, got {response.status}")
    require("application/json" in response.headers.get("content-type", ""), "expected application/json response")

    payload = response.json()
    require(payload.get("ok") is True, "expected ok=true")
    require(payload.get("server") == "Aurora_Clean_Build", "expected server Aurora_Clean_Build")
    require(payload.get("mode") == "clean", "expected mode clean")


def check_normal_chat_get(base_url: str) -> None:
    response = request(base_url, "GET", "/api/normal-chat")
    check_cors(response)
    require(response.status == 200, f"expected HTTP 200, got {response.status}")
    require("application/json" in response.headers.get("content-type", ""), "expected application/json response")

    payload = response.json()
    require(payload.get("ok") is True, "expected ok=true")
    require(payload.get("route") == "/api/normal-chat", "expected route /api/normal-chat")
    require(payload.get("method") == "POST required", "expected method POST required")


def check_normal_chat_post(base_url: str) -> None:
    body = json.dumps({"message": "smoke test"}).encode("utf-8")
    response = request(
        base_url,
        "POST",
        "/api/normal-chat",
        body=body,
        headers={"Content-Type": "application/json"},
    )
    check_cors(response)
    require(response.status in {200, 502, 504}, f"expected HTTP 200, 502, or 504, got {response.status}")
    require("application/json" in response.headers.get("content-type", ""), "expected application/json response")

    payload = response.json()
    require("reply" in payload, "missing reply field")

    status_payload = payload.get("status")
    require(isinstance(status_payload, dict), "missing status object")
    require(status_payload.get("route") == "/api/normal-chat", "expected status.route /api/normal-chat")

    if response.status == 200:
        require(payload.get("ok") is True, "expected ok=true for success response")
    else:
        require(payload.get("ok") is False, "expected ok=false for failure response")
        require(payload.get("reply") == "", "expected empty reply for failure response")


def check_blank_message(base_url: str) -> None:
    body = json.dumps({"message": ""}).encode("utf-8")
    response = request(
        base_url,
        "POST",
        "/api/normal-chat",
        body=body,
        headers={"Content-Type": "application/json"},
    )
    check_cors(response)
    require(response.status == 400, f"expected HTTP 400, got {response.status}")
    require("application/json" in response.headers.get("content-type", ""), "expected application/json response")

    payload = response.json()
    require(payload.get("ok") is False, "expected ok=false")
    require(payload.get("reply") == "", "expected empty reply")
    require(payload.get("error") == "Message is required.", "expected Message is required. error")

    status_payload = payload.get("status")
    require(isinstance(status_payload, dict), "missing status object")
    require(status_payload.get("route") == "/api/normal-chat", "expected status.route /api/normal-chat")


def check_forbidden_route(base_url: str, route: str) -> None:
    response = request(base_url, "GET", route)
    check_cors(response)
    require(response.status == 404, f"expected HTTP 404, got {response.status}")
    require("application/json" in response.headers.get("content-type", ""), "expected application/json response")
    require(response.json() == {"error": "Not found"}, 'expected {"error": "Not found"}')


def check_options(base_url: str) -> None:
    response = request(base_url, "OPTIONS", "/api/normal-chat")
    check_cors(response)
    require(response.status in {200, 204}, f"expected HTTP 200 or 204, got {response.status}")


def run_check(label: str, callback) -> bool:
    try:
        callback()
    except Exception as exc:
        print(f"[FAIL] {label}: {exc}")
        return False

    print(f"[PASS] {label}")
    return True


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    failures = 0

    for route, markers in HTML_ROUTE_MARKERS.items():
        if not run_check(f"GET {route}", lambda route=route, markers=markers: check_html_route(args.base_url, route, markers)):
            failures += 1

    if not run_check("GET /health", lambda: check_health(args.base_url)):
        failures += 1
    if not run_check("GET /api/normal-chat", lambda: check_normal_chat_get(args.base_url)):
        failures += 1
    if not run_check("POST /api/normal-chat", lambda: check_normal_chat_post(args.base_url)):
        failures += 1
    if not run_check("POST /api/normal-chat blank message", lambda: check_blank_message(args.base_url)):
        failures += 1

    for route in FORBIDDEN_ROUTES:
        if not run_check(f"forbidden {route}", lambda route=route: check_forbidden_route(args.base_url, route)):
            failures += 1

    if not run_check("OPTIONS /api/normal-chat", lambda: check_options(args.base_url)):
        failures += 1

    if failures:
        print("Clean route smoke failed.")
        return 1

    print("Clean route smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
