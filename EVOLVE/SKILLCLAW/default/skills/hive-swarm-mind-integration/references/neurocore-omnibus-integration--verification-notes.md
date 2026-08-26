# Neurocore-OMNIBUS Verification Notes

## Observed Behavior on Windows + OneDrive

- Neurocore root: `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore`
- OMNIBUS root: `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS`
- `tsc --noEmit` succeeds from Neurocore root using path aliases `@/contracts`, `@/core`, `@/lib`.
- `npm test` in Neurocore runs `node --import tsx --test tests/neurocore_integration.test.ts`.
- `npm test` in OMNIBUS runs `npx tsx --test tests/*.test.ts`; current pass count is 41/41.
- `server.cjs` starts on port 3000 by default and loads `neurocore-bridge.cjs` at startup.
- `neurocore-bridge.cjs` dynamically imports TS modules using `file://` URLs; forward slashes are required even on Windows.
- Bridge caches loaded modules in `_moduleCache`; server restart is required after Neurocore code changes.

## Endpoint Smoke Checks

- `GET /api/neurocore/health` returns:
  - `success: true`
  - `status: healthy`
  - `neurocoreConnected: true`
  - `hermesAvailable: true`
  - `capabilities.roles` may be minimal in mock mode, e.g. `["Mock Routing"]`
- `POST /api/neurocore/intent` accepts:
  - `intent`, `source`, `confidence`, `features`, `requiresConfirmation`, `phase`
  - returns `success: true`, `actionId`, `status: completed` when adapter is connected
- Missing `adapters/neural-decoder/` does not currently break startup; CI workflow references it but tests do not import it.
