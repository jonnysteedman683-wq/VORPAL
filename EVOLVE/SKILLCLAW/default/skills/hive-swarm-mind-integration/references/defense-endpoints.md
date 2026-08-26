# Defensible Swarm Defense Endpoints

Server: `server.cjs` on OMNIBUS.

## Request validation
- `POST /api/neurocore/intent` requires `intent`, accepts `source`, `confidence`, `features`, `requiresConfirmation`, `phase`.
- Confidence bounds: numeric, default `0.5`.
- Rejects with `400` on schema violation.

## Rate limiting
- Per-IP bucket in `defense.rateLimitBuckets`.
- Config: `defense.rateLimitWindowMs`, `defense.rateLimitMax`.
- Response: `429` with `code: RATE_LIMIT_EXCEEDED`.

## Circuit breaker
- Per provider: `defense.circuitBreaker.hermes|ollama|nous`.
- Threshold: `defense.circuitFailureThreshold`.
- Cooldown: `defense.circuitCooldownMs`.
- Response: `503` with `code: CIRCUIT_OPEN`.

## Emergency stop
- `POST /api/neurocore/emergency-stop` requires matching `token`.
- Token generated on first stop request if missing.
- Response `403` with `code: EMERGENCY_STOP_TOKEN_REQUIRED` when missing/invalid.
- `POST /api/neurocore/emergency-stop/reset` requires same token.

## Audit log
- `defense.auditLog` append-only array.
- Fields: `intentId`, `intent`, `provider`, `confidence`, `status`, `latencyMs`, `ip`, `timestamp`, optional `error`.

## Defense status endpoints
- `GET /api/neurocore/defense/status` → emergency flag, rate-limit config/active buckets, circuit breaker map, uptime.
- `GET /api/neurocore/defense/audit?limit=50` → last N audit entries, max 500.

## Health endpoint
- `GET /api/neurocore/health`
- Must remain above static fallback in route order.
- Returns `success`, `status`, `neurocoreConnected`, `neurocoreAvailable`, `hermesAvailable`, `lastHealthCheck`, `capabilities`, `emergencyStopActive`.
