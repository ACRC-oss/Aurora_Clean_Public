# Aurora Clean Build

Aurora Clean Build is a local-first experimental AI companion prototype. It currently demonstrates normal chat, clean web interfaces, read-only diagnostics, local model integration, route testing, and clear capability boundaries. Future capabilities such as reviewed memory, profiles, tools, vision, vehicle-adjacent context, and robotics research are planned behind review, tests, and human approval.

## What Aurora Clean Build Is

This repository is a curated public-safe prototype, exported without private Git history or old runtime material. It provides a small local HTTP server, a browser interface, an optional local Ollama connection, and tests that keep the current capability boundary explicit.

## What Works Today

- Normal chat works through `POST /api/normal-chat`.
- `/app` provides the main local chat interface.
- `/room` provides a public-safe presentation view.
- `/dev` provides read-only diagnostics.
- `/health` reports the clean server status.
- The local model adapter can call a separately installed Ollama service on loopback.
- Route, prompt, adapter, web-surface, and safety tests run locally.

## What Is Planned But Not Active

- Memory is not active. The public design starts with pending review and human approval.
- Profiles are not active.
- Tools are not active.
- Vision is not connected.
- Vehicle-adjacent context and robotics work remain future, simulation-first research.

Future features require review, tests, and human approval before implementation or connection.

## What Is Intentionally Not Connected

- Vehicle control is not connected.
- Old Aurora runtime access is not connected.
- There is no hidden autonomy or background action system.
- There is no command execution, arbitrary file editing, or unrestricted action layer.
- This local prototype does not claim production-grade identity or access control.

## Routes

| Method | Route | Status |
| --- | --- | --- |
| `GET` | `/` | Main public-safe app shell |
| `GET` | `/app` | Main public-safe app shell |
| `GET` | `/room` | Presentation view |
| `GET` | `/dev` | Read-only diagnostics |
| `GET` | `/health` | Server health |
| `GET` | `/api/normal-chat` | Route contract status |
| `POST` | `/api/normal-chat` | Normal chat |

`/api/memory` is absent. `/api/profile` is absent. `/api/chat-lite` is absent. `/api/chat` is not implemented yet.

## Local Demo Setup

Requirements: Python 3.11 or newer. Ollama is optional and must be installed separately for model replies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m server.clean_phone_server
```

Open `http://127.0.0.1:8766/app`. Without a running local Ollama model, the server returns a clear model-connection error rather than pretending a reply succeeded.

Run verification in another terminal:

```powershell
python scripts/public_safety_scan.py
python -m pytest -q
python scripts/smoke_clean_routes.py --base-url http://127.0.0.1:8766
```

## Safety Boundaries

The server exposes one chat POST route. Memory, profiles, tools, vision, vehicle control, arbitrary file serving, developer actions, and old runtime access remain disconnected. See [docs/SAFETY_BOUNDARIES.md](docs/SAFETY_BOUNDARIES.md).

## Do-Not-Claim List

I do not claim that this prototype has active memory, profiles, unrestricted tools, hidden autonomy, vehicle control, self-direction, human-like awareness, or production-grade identity and access control.

## Copyright / Ownership Notice

All rights are reserved. See [COPYRIGHT.md](COPYRIGHT.md). No open-source license is granted by this repository.

## AI-Assisted Material Note

Some material may be AI-assisted and then human-selected, arranged, edited, reviewed, or directed. See the ownership notice for the scope of the copyright statement.
