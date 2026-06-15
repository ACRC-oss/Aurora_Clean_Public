"""Minimal clean model adapter for local Ollama normal chat."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request

try:
    from . import prompt_contract
except ImportError:  # pragma: no cover - direct script execution path
    import prompt_contract


DEFAULT_MODEL = "llama3.2:latest"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_TIMEOUT_SECONDS = 25
MODEL_ENV_VAR = "AURORA_CLEAN_MODEL"
OLLAMA_URL_ENV_VAR = "AURORA_CLEAN_OLLAMA_URL"
TIMEOUT_ENV_VAR = "AURORA_CLEAN_MODEL_TIMEOUT_SECONDS"
NORMAL_CHAT_ROUTE = "/api/normal-chat"
MODEL_MODE = "clean_model"


def resolve_model() -> str:
    model = os.getenv(MODEL_ENV_VAR, DEFAULT_MODEL).strip()
    return model or DEFAULT_MODEL


def resolve_ollama_url() -> str:
    url = os.getenv(OLLAMA_URL_ENV_VAR, DEFAULT_OLLAMA_URL).strip()
    return url or DEFAULT_OLLAMA_URL


def resolve_timeout_seconds() -> float:
    raw_timeout = os.getenv(TIMEOUT_ENV_VAR, str(DEFAULT_TIMEOUT_SECONDS)).strip()
    try:
        timeout = float(raw_timeout)
    except ValueError:
        return float(DEFAULT_TIMEOUT_SECONDS)
    if timeout <= 0:
        return float(DEFAULT_TIMEOUT_SECONDS)
    return timeout


def _status_payload(model: str) -> dict[str, str]:
    return {
        "route": NORMAL_CHAT_ROUTE,
        "mode": MODEL_MODE,
        "model": model,
    }


def success_response(reply: str, model: str) -> dict[str, object]:
    return {
        "ok": True,
        "reply": reply.strip(),
        "status": _status_payload(model),
    }


def failure_response(error: str, model: str) -> dict[str, object]:
    return {
        "ok": False,
        "reply": "",
        "error": error,
        "status": _status_payload(model),
    }


def missing_message_response() -> dict[str, object]:
    return failure_response("Message is required.", resolve_model())


def http_status_for_failure(response: dict[str, object]) -> int:
    error = str(response.get("error", "")).strip()
    if error == "ollama_timeout":
        return 504
    return 502


def _build_request(message: str, model: str) -> urllib.request.Request:
    payload = {
        "model": model,
        "prompt": prompt_contract.build_clean_normal_chat_prompt(message),
        "stream": False,
    }
    body = json.dumps(payload).encode("utf-8")
    return urllib.request.Request(
        resolve_ollama_url(),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )


def generate_normal_chat_reply(message: str) -> dict[str, object]:
    model = resolve_model()
    clean_message = (message or "").strip()
    if not clean_message:
        return missing_message_response()

    request = _build_request(clean_message, model)
    timeout_seconds = resolve_timeout_seconds()

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw_response = response.read()
            status_code = response.getcode()
    except (TimeoutError, socket.timeout):
        return failure_response("ollama_timeout", model)
    except urllib.error.HTTPError as exc:
        return failure_response(f"ollama_http_{exc.code}", model)
    except urllib.error.URLError:
        return failure_response("ollama_connection_failed", model)
    except OSError:
        return failure_response("ollama_connection_failed", model)
    except Exception:
        return failure_response("ollama_request_failed", model)

    if status_code != 200:
        return failure_response(f"ollama_http_{status_code}", model)

    try:
        payload = json.loads(raw_response.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return failure_response("ollama_invalid_json", model)

    reply = payload.get("response", "")
    if not isinstance(reply, str) or not reply.strip():
        return failure_response("ollama_empty_response", model)

    return success_response(reply, model)
