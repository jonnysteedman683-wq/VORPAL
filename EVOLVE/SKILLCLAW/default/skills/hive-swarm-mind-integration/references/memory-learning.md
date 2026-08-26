# Memory and Learning Reference

## Modules

- Intent store: `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\lib\memory\learning.ts`
  - `IntentMemoryStore`
  - `LearningLogger`

## Bridge Loading

Load from `neurocore-bridge.cjs` with dynamic `import('file://' + path.join(NEUROCORE_LIB, 'memory', 'learning.ts'))`.

Expose accessors from the bridge:
- `getMemoryStore()`
- `getLearningLogger()`

## Backend Endpoints

- `GET /api/neurocore/memory`
- `GET /api/neurocore/learning`

## Outcome Logging

In `server.cjs` `/api/neurocore/intent`, after `swarmAdapter.start(intentObj)`:
- log intent record to `memoryStore.add(...)`
- log learning sample to `learningLogger.log(...)`

Fields to capture:
- `confidence`, `success`, `provider`, `latencyMs`, `intentHash`, `timestamp`

## UI Polling Pattern

Optional frontend polling for memory/learning observability:

```js
async function updateHiveMemoryLearningWidget() {
  const memoryEl = document.getElementById('hiveMemoryStatus');
  const learningEl = document.getElementById('hiveLearningStatus');
  if (!memoryEl && !learningEl) return;

  try {
    const [memoryRes, learningRes] = await Promise.all([
      fetch('/api/neurocore/memory'),
      fetch('/api/neurocore/learning')
    ]);
    const memoryData = await memoryRes.json();
    const learningData = await learningRes.json();

    if (memoryEl) {
      const recentCount = Array.isArray(memoryData.recent) ? memoryData.recent.length : 0;
      const failedCount = typeof memoryData.failedCount === 'number' ? memoryData.failedCount : 0;
      memoryEl.textContent = `Memory: ${recentCount} recent · ${failedCount} failed`;
      memoryEl.style.display = 'inline-flex';
      memoryEl.style.background = memoryData.connected ? 'rgba(0, 255, 136, 0.12)' : 'rgba(255, 187, 0, 0.12)';
      memoryEl.style.borderColor = memoryData.connected ? 'rgba(0, 255, 136, 0.3)' : 'rgba(255, 187, 0, 0.3)';
      memoryEl.style.color = memoryData.connected ? '#00ff88' : '#ffbb00';
    }

    if (learningEl) {
      const stats = Array.isArray(learningData.providerStats) ? learningData.providerStats : [];
      const top = stats.slice(0, 2).map(s => `${s.provider}:${(s.successRate * 100).toFixed(0)}%`).join(' · ') || 'no data';
      learningEl.textContent = `Learning: ${top}`;
      learningEl.style.display = 'inline-flex';
      learningEl.style.background = learningData.connected ? 'rgba(0, 240, 255, 0.12)' : 'rgba(255, 187, 0, 0.12)';
      learningEl.style.borderColor = learningData.connected ? 'rgba(0, 240, 255, 0.3)' : 'rgba(255, 187, 0, 0.3)';
      learningEl.style.color = learningData.connected ? '#00f0ff' : '#ffbb00';
    }
  } catch (err) {
    // Show error state if polling fails
    if (memoryEl) { memoryEl.textContent = 'Memory: error'; memoryEl.style.color = '#ff3c3c'; }
    if (learningEl) { learningEl.textContent = 'Learning: error'; learningEl.style.color = '#ff3c3c'; }
  }
}
```

HTML elements expected:
- `hiveMemoryStatus` / `hiveMemoryStatusText`
- `hiveLearningStatus` / `hiveLearningStatusText`

Fallback behavior:
- If `memoryStore` or `learningLogger` is unavailable, endpoints return `{ success: true, connected: false, reason: '...', ... }` with empty data.
- UI should render `no data` or an unavailable state rather than crashing.
