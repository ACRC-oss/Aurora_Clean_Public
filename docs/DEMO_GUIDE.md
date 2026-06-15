# Public Demo Guide

## Start The Server Locally

```powershell
python -m server.clean_phone_server
```

The default address is `http://127.0.0.1:8766`.

## Open The Public-Safe Views

1. Open `/app` for normal chat.
2. Open `/room` for the presentation view.
3. Open `/dev` for read-only diagnostics.
4. Open `/health` to show the server status response.

## Run The Smoke Script

```powershell
python scripts/smoke_clean_routes.py --base-url http://127.0.0.1:8766
```

The script checks allowed pages, the normal-chat contract, CORS, blank-input handling, and blocked routes.

## Public-Safe Demo Order

1. State that this is a bounded local prototype.
2. Show `/app` and one normal-chat request.
3. Show `/room` as a public-safe presentation surface.
4. Show `/dev` and emphasize that it is read-only diagnostics.
5. Show `/health` and the route contract.
6. Run the smoke script and the public safety scan.
7. Close with the inactive-capability boundary.

## Do-Not-Claim List

Do not claim active memory, profiles, unrestricted tools, background autonomy, vehicle control, self-driving operation, human-like awareness, old runtime access, or production-grade identity and access control.
