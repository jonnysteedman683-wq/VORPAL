# Confidence Triage Reference

## Server-side triage contract

Endpoint: `POST /api/neurocore/intent`

Input fields:
- `intent`: string
- `source`: optional string, ignored for routing
- `confidence`: number, `0.0` to `1.0`
- `features`: object
- `requiresConfirmation`: boolean
- `phase`: number or null

Server behavior:
- Normalize confidence to a number; default missing confidence to `0.5`.
- Route by confidence:
  - `>= 0.8` → provider `hermes`
  - `>= 0.5` → provider `ollama`
  - `< 0.5` → provider `nous`
- Override `source` with the routed provider.
- Persist intent outcome to memory store and learning logger when available.

Response shape:
```json
{
  "success": true,
  "phase": null,
  "triage": {
    "confidence": 0.95,
    "routedTo": "hermes"
  },
  "actionId": "action-neuro-...",
  "status": "completed"
}
```

## Frontend exposure

- Show `triage.routedTo` next to each chat action or status card.
- Show `triage.confidence` as a numeric or progress indicator.
- Use the routed provider value when displaying last provider in status panels.

## Thresholds

Do not hardcode different thresholds in the UI; the UI should reflect the server contract:
- high: `>= 0.8`
- mid: `>= 0.5`
- low: `< 0.5`

## Pitfalls

- Do not let the frontend silently override server triage with `config.provider`; if it does, label it clearly as a manual override.
- Do not treat missing confidence as `0`; the current server default is `0.5`.
