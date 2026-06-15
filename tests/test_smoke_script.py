from __future__ import annotations

import os
import subprocess
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

from server import clean_phone_server


ROOT = Path(__file__).resolve().parents[1]


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


def test_smoke_script_passes_against_exported_server() -> None:
    environment = os.environ.copy()
    environment["AURORA_CLEAN_MODEL_TIMEOUT_SECONDS"] = "0.2"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    with running_server() as (host, port):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/smoke_clean_routes.py",
                "--base-url",
                f"http://{host}:{port}",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "[PASS] GET /app" in output
    assert "[PASS] GET /room" in output
    assert "[PASS] GET /dev" in output
    assert "[PASS] forbidden /api/memory" in output
    assert "Clean route smoke passed." in output
