from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.client import HTTPConnection
from unittest.mock import patch

from server import clean_phone_server


@contextmanager
def running_server():
    httpd = clean_phone_server.create_server(host="127.0.0.1", port=0)
    thread = threading.Thread(
        target=httpd.serve_forever,
        kwargs={"poll_interval": 0.01},
        daemon=True,
    )
    thread.start()
    try:
        yield httpd.server_address
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def request(method: str, path: str, body: bytes | None = None):
    with running_server() as (host, port):
        connection = HTTPConnection(host, port, timeout=5)
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result


def test_public_pages_and_health_are_available() -> None:
    for route in ("/", "/app", "/room", "/dev"):
        status, headers, body = request("GET", route)
        assert status == 200
        assert headers["Content-Type"] == "text/html; charset=utf-8"
        assert b"Aurora Clean Build" in body

    status, _headers, body = request("GET", "/health")
    assert status == 200
    assert json.loads(body) == {
        "ok": True,
        "server": "Aurora_Clean_Build",
        "mode": "clean",
    }


def test_dev_page_is_read_only_diagnostics() -> None:
    status, _headers, body = request("GET", "/dev")
    text = body.decode("utf-8")

    assert status == 200
    assert "Read-only diagnostics" in text
    assert "cannot run commands, edit files, write memory, or change settings" in text


def test_forbidden_routes_and_files_return_json_404() -> None:
    for route in (
        "/api/memory",
        "/api/profile",
        "/api/chat-lite",
        "/api/chat",
        "/developer",
        "/web/clean_app.html",
        "/../../server/clean_phone_server.py",
    ):
        status, headers, body = request("GET", route)
        assert status == 404
        assert headers["Content-Type"] == "application/json; charset=utf-8"
        assert json.loads(body) == {"error": "Not found"}


def test_normal_chat_rejects_blank_input() -> None:
    status, _headers, body = request(
        "POST",
        "/api/normal-chat",
        json.dumps({"message": ""}).encode("utf-8"),
    )
    payload = json.loads(body)

    assert status == 400
    assert payload["ok"] is False
    assert payload["reply"] == ""
    assert payload["error"] == "Message is required."


def test_normal_chat_uses_the_model_adapter_contract() -> None:
    response = {
        "ok": True,
        "reply": "Public-safe local reply.",
        "status": {
            "route": "/api/normal-chat",
            "mode": "clean_model",
            "model": "llama3.2:latest",
        },
    }
    with patch.object(clean_phone_server.model_adapter, "generate_normal_chat_reply", return_value=response):
        status, _headers, body = request(
            "POST",
            "/api/normal-chat",
            json.dumps({"message": "Hello"}).encode("utf-8"),
        )

    assert status == 200
    assert json.loads(body) == response
