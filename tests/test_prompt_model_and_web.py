from __future__ import annotations

import json
import socket
import urllib.error
from pathlib import Path
from unittest.mock import patch

from server import model_adapter, prompt_contract


ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def read(self) -> bytes:
        return self.body

    def getcode(self) -> int:
        return 200


def test_prompt_contract_states_current_boundaries() -> None:
    prompt = prompt_contract.build_clean_normal_chat_prompt("Who are you?")

    assert "Aurora Clean Build" in prompt
    assert "not active memory" in prompt
    assert "Do not claim access to memory" in prompt
    assert "tools" in prompt
    assert "vision" in prompt
    assert "vehicle control" in prompt
    assert "not connected" in prompt


def test_model_adapter_success_and_failures_are_parseable() -> None:
    with patch(
        "server.model_adapter.urllib.request.urlopen",
        return_value=FakeResponse({"response": "Short local reply."}),
    ):
        success = model_adapter.generate_normal_chat_reply("hello")

    assert success["ok"] is True
    assert success["reply"] == "Short local reply."
    assert success["status"]["route"] == "/api/normal-chat"

    with patch("server.model_adapter.urllib.request.urlopen", side_effect=socket.timeout):
        timeout = model_adapter.generate_normal_chat_reply("hello")
    assert timeout["ok"] is False
    assert timeout["error"] == "ollama_timeout"
    assert model_adapter.http_status_for_failure(timeout) == 504

    with patch(
        "server.model_adapter.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        unavailable = model_adapter.generate_normal_chat_reply("hello")
    assert unavailable["ok"] is False
    assert unavailable["error"] == "ollama_connection_failed"
    assert model_adapter.http_status_for_failure(unavailable) == 502


def test_public_web_surfaces_state_inactive_capabilities() -> None:
    app = (ROOT / "web" / "clean_app.html").read_text(encoding="utf-8")
    room = (ROOT / "web" / "clean_room.html").read_text(encoding="utf-8")
    dev = (ROOT / "web" / "clean_dev.html").read_text(encoding="utf-8")

    assert "No memory connected" in app
    assert "No profiles connected" in app
    assert "No tools connected" in app
    assert "No vehicle control" in app
    assert "No Vision Connected" in room
    assert "Read-only diagnostics" in dev
    assert "/api/memory absent" in dev
    assert "/api/profile absent" in dev


def test_web_surfaces_do_not_offer_privileged_controls() -> None:
    combined = "\n".join(
        (ROOT / "web" / name).read_text(encoding="utf-8")
        for name in ("clean_app.html", "clean_room.html", "clean_dev.html")
    )

    for label in ("Run Command", "Execute Shell", "Edit File", "Write Memory"):
        assert label not in combined
