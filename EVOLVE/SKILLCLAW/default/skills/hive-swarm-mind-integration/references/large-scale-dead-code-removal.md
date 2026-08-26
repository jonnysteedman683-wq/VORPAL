# Large-Scale Dead Code Removal — OMNIBUS v85 Upgrade Notes

## Scope

This reference captures the working large-scale cleanup recipe used in the OMNIBUS v85 swarm upgrade, when dead high-version endpoints, fake orchestrators, and dead UI branches were removed without breaking tests.

## server.cjs

- Preferred method: exact line-range deletion, not multiline regex.
- Remove dead endpoint blocks from highest version down to lowest.
- After removal, verify with:
  - `grep -n "app.post('/api/v" server.cjs`
  - `npm test`
- Real `/api/v11`, `/api/v60`, `/api/v65` ML routes can remain if they call actual `ExperimentalMLBackend` algorithms.

## app.js

- Dead render stubs can total 2000+ lines.
- Remove by block function name and brace-depth scan, from end to start.
- Validate with `node --check app.js`.

## experimental_ml.js

- Fake orchestrator classes often omit `class` and only appear in export lists or window assignments.
- Detection strategy:
  - grep fake version strings: `v70.0`, `v85.0`, `v100000.0`, etc.
  - grep export arrays/window assignments for suspicious names
- Removal strategy:
  - use exact line ranges when regex fails
  - preserve real algorithm classes by whitelist

## hive-unified-ui.html

- Remove dead tabs/panels and duplicated header widgets.
- Keep telemetry tab and emergency stop controls.

## Verification

- `npm test` must stay green.
- `PORT=3001 node server.cjs` background launch
- Smoke check:
  - `GET /api/neurocore/health`
  - `POST /api/neurocore/connect`
  - `POST /api/neurocore/intent`
  - `GET /api/telemetry/summary`
  - `GET /api/telemetry/histogram`

## Outcome

- server.cjs removed ~1613+ dead endpoint lines
- app.js removed ~2314 dead render lines
- experimental_ml.js removed ~566 fake orchestrator lines
- package.json bumped to v85.0.0
- tests remained 41/41 passing
