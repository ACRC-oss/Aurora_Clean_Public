"""Fail on blocking public-export safety findings."""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

SKIP_DIRS = {".git", ".pytest_cache", "__pycache__"}
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

FORBIDDEN_ROOT_NAMES = {
    "11_DATA_RUNTIME",
    "aurora_core",
    "cache",
    "data",
    "logs",
    "memory",
    "profiles",
    "sessions",
}

HARD_CONTENT_PATTERNS = {
    "private Windows user path": re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
    "private account marker": re.compile(r"\bhorde\b", re.IGNORECASE),
    "private network marker": re.compile(r"\b100\.100\.\d{1,3}\.\d{1,3}\b"),
    "private mesh-network marker": re.compile(r"\b(?:tailnet|tailscale)\b", re.IGNORECASE),
    "credential word": re.compile(r"\b(?:token|secret|password|api_key)\b", re.IGNORECASE),
    "credential-shaped value": re.compile(r"\b(?:sk-|ghp_)[A-Za-z0-9_-]+", re.IGNORECASE),
}

POSITIVE_CLAIM_PATTERNS = {
    "active memory claim": re.compile(r"\bmemory\s+is\s+(?:active|connected|enabled|available)\b", re.IGNORECASE),
    "vehicle control claim": re.compile(r"\bvehicle control\s+is\s+(?:active|connected|enabled|available)\b", re.IGNORECASE),
    "vehicle action claim": re.compile(r"\b(?:can|will)\s+(?:control|drive|steer)\s+(?:a\s+)?(?:car|vehicle)\b", re.IGNORECASE),
    "self-driving claim": re.compile(r"\bself-driving\b", re.IGNORECASE),
    "general intelligence claim": re.compile(r"\bAGI\b"),
    "sentience claim": re.compile(r"\bsentien(?:ce|t)\b", re.IGNORECASE),
    "consciousness claim": re.compile(r"\bconsciousness\b", re.IGNORECASE),
    "production authentication claim": re.compile(r"\bproduction authentication\s+(?:is|works|enabled|available)\b", re.IGNORECASE),
    "unrestricted tool claim": re.compile(r"\bunrestricted tools\s+(?:are|is)\s+(?:active|connected|enabled|available)\b", re.IGNORECASE),
}

NEGATION_MARKERS = (
    "do not claim",
    "does not",
    "is not",
    "no ",
    "not connected",
    "not implemented",
    "without ",
)


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == SELF:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore"}:
            files.append(path)
    return sorted(files)


def is_negated(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in NEGATION_MARKERS)


def scan_filesystem() -> list[str]:
    findings: list[str] = []

    for name in FORBIDDEN_ROOT_NAMES:
        if (ROOT / name).exists():
            findings.append(f"forbidden root entry: {name}")

    if (ROOT / "AGENTS.md").exists():
        findings.append("forbidden root file: AGENTS.md")
    if (ROOT / "phone_server.py").exists():
        findings.append("forbidden old server file at repository root")

    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        if path.name == ".env" or path.name.startswith(".env."):
            findings.append(f"environment file: {relative.as_posix()}")
        if path.name in {"__pycache__", ".pytest_cache"}:
            findings.append(f"generated cache directory: {relative.as_posix()}")

    return findings


def scan_content() -> list[str]:
    findings: list[str] = []
    for path in iter_text_files():
        relative = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            findings.append(f"undecodable text file: {relative}")
            continue

        for line_number, line in enumerate(lines, start=1):
            for label, pattern in HARD_CONTENT_PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{relative}:{line_number}: {label}")
            for label, pattern in POSITIVE_CLAIM_PATTERNS.items():
                if pattern.search(line) and not is_negated(line):
                    findings.append(f"{relative}:{line_number}: {label}")

    return findings


def scan_runtime_routes() -> list[str]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    module = importlib.import_module("server.clean_phone_server")
    implemented = set(module.IMPLEMENTED_ROUTES)
    blocked = {"/api/memory", "/api/profile", "/api/chat-lite", "/api/chat"}
    return [f"forbidden implemented route: {route}" for route in sorted(implemented & blocked)]


def main() -> int:
    findings = scan_filesystem() + scan_content() + scan_runtime_routes()
    if findings:
        print("FAIL_PUBLIC_SAFETY_SCAN")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("PASS_PUBLIC_SAFETY_SCAN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
