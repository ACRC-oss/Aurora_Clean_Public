# Public Memory Design

## Status

Memory is planned and is not active in this repository.

## Review-First Principle

Any future memory record must begin as a pending-review candidate. A candidate is proposed information, not active truth, and must not influence replies while pending.

Nothing may become active until a human reviews and approves it. Storage approval, UI planning, or schema documentation does not approve automatic writing or context injection.

## Clean-Build Boundary

- No old memory import.
- No profile import.
- No automatic remembering.
- No memory route in the current server.
- No memory content is added to prompts.

Future implementation would require a separate approved writer contract, denial tests, rollback behavior, and a later separately approved read path.
