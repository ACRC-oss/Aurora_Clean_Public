# Safety Boundaries

## Current Boundary

Aurora Clean Build is a bounded local prototype. Its current runtime provides public-safe web pages, health status, normal chat through one route, and an optional loopback Ollama adapter.

## Not Connected

- No active memory.
- No profiles.
- No tools or action execution.
- No vision or camera connection.
- No vehicle control.
- No hidden autonomy or background actions.
- No access to old Aurora runtime material.
- No arbitrary file serving or editing.

## Route Boundary

The only chat action route is `POST /api/normal-chat`. The server also provides read-only `GET` pages and status responses at `/`, `/app`, `/room`, `/dev`, `/health`, and `/api/normal-chat`.

The following routes are absent or blocked: `/api/memory`, `/api/profile`, `/api/chat-lite`, `/api/chat`, and `/developer`. Unknown paths return a JSON `404` response.

## Change Rule

Future capability changes require an explicit contract, focused tests, human review, and approval. Documentation does not activate a capability.
