# Hive UI Wiring Reference

## Panels and IDs

- `panel-chat` — unified chat with `chatMessagesStream`, `chatInputField`, `chatSendBtn`
- `panel-status` — swarm status cards: `statusHealth`, `statusPeers`, `statusLastIntent`, `statusLastProvider`, `statusQueue`, `statusHermes`
- `panel-phase` — `phaseOutput`
- `panel-memory` — `memoryTableBody`
- `panel-learning` — `learningProviderBody`, `learningThreshold`
- `panel-tools` — `toolSelect`, `toolsOutput`
- `panel-brainstorm` — `brainstormOutput`

## Tab switching

```js
const tabBar = document.getElementById('tabBar');
const panels = Array.from(document.querySelectorAll('.panel'));
function switchTab(panelId) {
  panels.forEach(p => p.classList.toggle('active', p.id === panelId));
  tabBar.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.panel === panelId));
}
```

## Connect helper

```js
window.connectNeurocore = async function(){
  const res = await fetch('/api/neurocore/connect', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ baseUrl:'http://localhost:8080/v1', enableHermes:true })
  });
  const data = await res.json();
  const el = document.getElementById('globalStatus');
  if (data.success) {
    el.textContent = 'connected';
    el.classList.add('success');
    el.classList.remove('warn','danger');
  } else {
    el.textContent = 'error';
    el.classList.add('danger');
  }
  return data;
};
```

## Emergency stop helper

```js
document.getElementById('emergencyStopBtn').addEventListener('click', async ()=>{
  const res = await fetch('/api/neurocore/emergency-stop', { method:'POST' });
  const data = await res.json();
  const el = document.getElementById('globalStatus');
  el.textContent = data.success && data.stopped ? 'stopped' : 'error';
  el.classList.add('danger');
  el.classList.remove('success','warn');
});
```

## Refresh pattern

```js
async function refreshStatus(){
  try {
    const res = await fetch('/api/neurocore/status');
    const data = await res.json();
    document.getElementById('statusHealth').textContent = data.success ? (data.connected ? 'healthy' : 'disconnected') : 'error';
    document.getElementById('statusPeers').textContent = `${data.peers?.length || 0} peers`;
    document.getElementById('statusLastIntent').textContent = data.lastIntent || '—';
    document.getElementById('statusLastProvider').textContent = data.lastProvider || '—';
    document.getElementById('statusQueue').textContent = `${data.queueSize ?? 0}`;
    document.getElementById('statusHermes').textContent = data.hermesAvailable ? 'available' : 'unavailable';
  } catch (e) {
    document.getElementById('statusHealth').textContent = 'error';
  }
}
```

## Memory table rendering

```js
const rows = (data.recent || []).map(r => `<tr>
  <td class="mono">${r.id}</td>
  <td>${r.intent}</td>
  <td>${r.provider || ''}</td>
  <td>${r.confidence ?? ''}</td>
  <td>${r.status}</td>
  <td class="mono">${r.latencyMs ?? ''}</td>
  <td class="mono">${new Date(r.timestamp).toLocaleTimeString()}</td>
</tr>`).join('');
tbody.innerHTML = rows || '<tr><td colspan="7" class="empty">No memory yet.</td></tr>';
```

## Learning table rendering

```js
const rows = (data.providerStats || []).map(s => `<tr>
  <td>${s.provider}</td>
  <td>${s.count}</td>
  <td>${(s.successRate*100).toFixed(1)}%</td>
  <td class="mono">${s.avgLatencyMs ?? '—'}</td>
</tr>`).join('');
```

## Tool harness

- Load tools: `GET /api/neurocore/tools`
- Run tool: `POST /api/neurocore/tools/call` with `{ tool, arguments: { message: '...' } }`

## Brainstorm stub

- Synthesize button currently returns a fixed JSON sample.
- Send to Chat button copies `brainstormOutput.textContent` into `chatInputField` and switches to `panel-chat`.
