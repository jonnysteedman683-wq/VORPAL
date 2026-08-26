# OMNIBUS Hive Status Widget Reference

## HTML additions

Add two elements near the header status badges:
- `#hiveSwarmStatus` badge with `#hiveSwarmStatusText`
- `#hiveQueueWidget` badge with `#hiveQueueText`

## JS behavior

- `initHiveSwarmMind()` starts polling with `setInterval(updateHiveSwarmStatus, 5000)`
- `updateHiveSwarmStatus()` fetches `/api/neurocore/status`
- Green: connected, lastProvider shown, peers count
- Yellow: available but disconnected
- Red: unavailable/error
- Queue widget shows `Queue: N` only when connected

## Polling contract

Endpoint: `GET /api/neurocore/status`
Response shape:
```json
{
  "success": true,
  "connected": true,
  "neurocoreAvailable": true,
  "hermesAvailable": true,
  "lastHealthCheck": 1234567890,
  "lastProvider": "hermes",
  "peers": [],
  "queueSize": 0
}
```

## Pitfalls

- Do not call `node --check app.js` in this repo because `package.json` has `"type": "module"` and `app.js` is loaded as a browser script; the lint failure is pre-existing and not introduced by this widget.
- Keep widget logic defensive: check element existence before updating.
