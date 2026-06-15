from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from server import clean_phone_server


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "COPYRIGHT.md",
    "docs/SAFETY_BOUNDARIES.md",
    "docs/ROADMAP_PUBLIC.md",
    "docs/MEMORY_DESIGN_PUBLIC.md",
    "docs/NYX_REVIEW_LAYER_PUBLIC.md",
    "docs/VEHICLE_AND_ROBOTICS_BOUNDARY_PUBLIC.md",
    "docs/DEMO_GUIDE.md",
    "docs/PUBLIC_EXPORT_AUDIT.md",
    "server/clean_phone_server.py",
)


def test_required_public_files_exist() -> None:
    for relative_path in REQUIRED_FILES:
        assert (ROOT / relative_path).is_file(), f"Missing {relative_path}"


def test_private_and_runtime_material_is_absent() -> None:
    assert not (ROOT / "AGENTS.md").exists()
    assert not (ROOT / "phone_server.py").exists()
    assert not (ROOT / "aurora_core").exists()
    assert not (ROOT / "memory").exists()
    assert not (ROOT / "profiles").exists()
    assert not (ROOT / "11_DATA_RUNTIME").exists()
    assert not (ROOT / ".env").exists()


def test_generated_cache_directories_are_absent() -> None:
    assert not any(path.is_dir() for path in ROOT.rglob("__pycache__"))
    assert not (ROOT / ".pytest_cache").exists()


def test_public_route_boundary_is_locked() -> None:
    assert "/api/normal-chat" in clean_phone_server.IMPLEMENTED_ROUTES
    for route in ("/api/memory", "/api/profile", "/api/chat-lite", "/api/chat"):
        assert route not in clean_phone_server.IMPLEMENTED_ROUTES


def test_readme_states_inactive_capabilities() -> None:
    content = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Memory is not active" in content
    assert "Vehicle control is not connected" in content
    assert "future features require review, tests, and human approval" in content.lower()


def test_public_safety_scan_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/public_safety_scan.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "PASS_PUBLIC_SAFETY_SCAN" in output
