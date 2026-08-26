# Hermes Hive Wiring Notes

## Project Layout
- Cloned from `https://github.com/jonnysteedman683-wq/HERMES-HIVE`
- Local path: `C:\Users\jonny\HERMES-HIVE`
- Anchored Hermes project: `HERMES HIVE` (`p_a69d0453`, primary_path `C:\Users\jonny\HERMES-HIVE`)
- UI entry: `src/App.tsx`
- Data hook: `src/client/hooks/useHiveData.ts`
- API middleware: `src/server/apiMiddleware.ts` (Vite plugin exposing `/api/*`)

## Startup
- Install: `cd C:\Users\jonny\HERMES-HIVE && npm install`
- Dev server: `npm run dev`
- Binds: `http://localhost:3000`
- Health check: `GET http://localhost:3000/api/health`
- First dev start took ~30s on this machine.

## Key APIs Observed
- `/api/health`
- `/api/events/stream` SSE
- `/api/events/stats`, `/api/events/dlq`, `/api/events/publish`
- `/api/hermes/command`, `/api/hermes/decisions`
- `/api/agents`, `/api/agents/:id/:action`
- `/api/missions`, `/api/missions/:id`
- `/api/memory`, `/api/tools`, `/api/tools/execute`
- `/api/diagnostics`
- `/api/quick-actions/templates`, `/api/quick-actions/trigger`, `/api/quick-actions/history`
- `/api/demo/trigger`
- Stage 2+ APIs under `/api/goals`, `/api/governance/*`, `/api/world/graph`, `/api/cognition/debates`, `/api/learning`, `/api/resources/budgets`, `/api/ledger/events`, `/api/loop/mode`
- Federation APIs: `/api/federation/*`
- Web capability protocol: `/api/v1/capabilities`, `/api/v1/capabilities/execute`, `/api/v1/executions/:id`, `/api/v1/approvals`, `/api/v1/events`, `/api/v1/audit`, `/api/v1/web/health`
- Diagnostics: `/api/v1/diagnostics/causal-traces`, `/api/v1/diagnostics/snapshots`, `/api/v1/diagnostics/chaos`, etc.
- Chat: `/api/v1/chat/conversations`, `/api/v1/chat/conversations/:id/messages`
- Learning/reputation/evolution: `/api/v1/learning/*`, `/api/v1/learning/reputation/*`, `/api/v1/learning/evolution/compositions/*`
- Symbiosis: `/api/v1/symbiosis/*`

## Observed Issues
- `package.json` name is still `react-example`; should align to `hermes-hive`.
- `.env.example` still contains AI Studio placeholders.
- Repo has placeholder stubs from the AI Studio template; real integration work remains.

## Integration Direction
- Backend: patch AQB `server.ts` `/api/chat` to optionally fall through to Hermes Hive `/api/chat` or `/api/hermes/command` when chat complexity exceeds local routing.
- Frontend: point Hive UI’s `useHiveData` chat actions to AQB’s `/api/chat` if a unified console is desired.
- Do NOT merge Hive UI into AQB; keep projects separate as requested.
