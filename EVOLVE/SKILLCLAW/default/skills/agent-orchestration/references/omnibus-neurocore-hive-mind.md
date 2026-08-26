# OMNIBUS + Neurocore Hive Swarm Mind — Validated Local Pattern

## Verified endpoints
- `POST /api/neurocore/connect` → returns `success: true`, `capabilities`, `hermesEnabled`
- `POST /api/neurocore/intent` → accepts `{ intent, confidence, features, requiresConfirmation }`, returns `actionId`
- `GET /api/neurocore/health` → returns `success: true`, `status: "healthy"`, `capabilities`
- `GET /api/neurocore/peers` → returns `peers` + `capabilities`
- `POST /api/neurocore/emergency-stop` → returns `{ success: true, stopped: true }`

## Verified smoke test sequence
```bash
node --check server.cjs
node server.cjs &
curl -s http://localhost:3000/api/neurocore/health
curl -s -X POST http://localhost:3000/api/neurocore/connect -H "Content-Type: application/json" -d '{"baseUrl":"http://localhost:8080/v1","enableHermes":true}'
curl -s -X POST http://localhost:3000/api/neurocore/intent -H "Content-Type: application/json" -d '{"intent":"test","confidence":0.9}'
curl -s -X POST http://localhost:3000/api/neurocore/intent -H "Content-Type: application/json" -d '{"intent":"test","confidence":0.6}'
curl -s -X POST http://localhost:3000/api/neurocore/intent -H "Content-Type: application/json" -d '{"intent":"test","confidence":0.3}'
curl -s http://localhost:3000/api/neurocore/health
curl -s -X POST http://localhost:3000/api/neurocore/emergency-stop
```

## Verified test command
```bash
npx tsx --test tests/*.test.ts
# 41 pass, 0 fail across Neurocore adapter/stream/debate/safety/upgrade suites
```

## Important path caveat on Windows
When OMNIBUS and Neurocore are not true siblings, use an absolute `require('C:/Users/jonny/OneDrive/Documents/AEGIS/neurocore/neurocore-bridge.cjs')` from `server.cjs`. Relative paths like `../AEGIS/...` can resolve against the working directory rather than the server location.
