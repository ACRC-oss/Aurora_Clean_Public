# Public Export Audit

## Included Files

- Clean server, model adapter, and prompt contract under `server/`.
- Public-safe app, room, and diagnostics pages under `web/`.
- Route smoke runner and public safety scanner under `scripts/`.
- Public documentation, ownership notice, test configuration, and focused tests.

The `/` route intentionally serves the same reviewed page as `/app`, avoiding an extra source page outside the approved export list.

## Excluded Material

- Private Git history and private agent instructions.
- Old runtime modules and old runtime data.
- Memory, profile, log, session, cache, archive, and mobile-build material.
- Local environment files and generated test artifacts.
- Private project notes, continuity material, local machine paths, and private network addresses.
- Unused source dependencies and private migration tests.

## Scan Results

The curated export contained no blocking public-safety findings. Verification recorded:

- `PASS_PUBLIC_SAFETY_SCAN`
- `16 passed` in the public pytest suite
- all four requested Python compile checks passed
- the live loopback route smoke passed from the exported repository

The automated scanner checks filesystem exclusions, local path markers, private network markers, credential-shaped values, old runtime imports, implemented route boundaries, and misleading positive capability claims.

## Items Requiring Human Review

- Replace `[OWNER LEGAL NAME]` in `COPYRIGHT.md` before external publication.
- Review screenshots, repository description, and GitHub metadata before upload.
- Confirm that the desired all-rights-reserved distribution posture is intentional.

## Final Public-Safety Status

`PASS_PUBLIC_SAFE_LOCAL_EXPORT`

This status applies to the curated local export only. It is not a publication approval and does not claim production readiness.
