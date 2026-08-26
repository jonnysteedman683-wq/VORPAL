# Spike Communication Reference

## Module

- Path: `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\adapters\omnibus-swarm\spike-comm.js`
- Exports:
  - `hashIntentToPhase(intent, source)`
  - `encodeIntentToSpikes(intentObj)`
  - `decodeSpikesToIntent(spikePayload)`
  - `groupByPhase(spikePayloads)`
  - `PHASE_BUCKETS`

## Bridge Loading

Load from `neurocore-bridge.cjs` with dynamic `import('file://' + path.join(NEUROCORE_ROOT, 'adapters', 'omnibus-swarm', 'spike-comm.js'))`.

Do not use `require('file://...')`; it fails in this environment.

## Backend Route

`POST /api/neurocore/intent` accepts `phase` and returns `phase` in the response.

## Frontend Usage

In `agent_system.js` `dispatch()`:
```js
const phase = ((() => {
  const str = `${config.provider}:${taskText}`;
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0;
  return ((h % 8) + 8) % 8;
})());
```

Send `phase` with the intent body.
