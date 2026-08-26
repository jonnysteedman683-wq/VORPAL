# ARC Sentinel + OMNIBUS Integration

**Session:** 2026-08-05  
**User:** jonnysteedman683  
**Systems:** OMNIBUS (neurocore swarm backend) + ARC Sentinel UI (sophisticated debate engine UI)

## Paths

- **ARC dist:** `C:\Users\jonny\OneDrive\Documents\AEGIS\ARCANE QUANTUM BRAIN\dist`
- **OMNIBUS:** `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS`
- **Neurocore bridge:** `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\neurocore-bridge.cjs`

## Mount Configuration

```javascript
const arcDistPath = 'C:\\Users\\jonny\\OneDrive\\Documents\\AEGIS\\ARCANE QUANTUM BRAIN\\dist';
if (fs.existsSync(arcDistPath)) {
  app.use('/sentinel/assets', express.static(path.join(arcDistPath, 'assets')));
  app.get('/sentinel', (req, res) => {
    const indexPath = path.join(arcDistPath, 'index.html');
    let html = fs.readFileSync(indexPath, 'utf8');
    html = html.replace(/src="\/assets\//g, 'src="./assets/').replace(/href="\/assets\//g, 'href="./assets/');
    res.type('html').send(html);
  });
}
```

## Bridge Endpoints

### POST `/api/swarm/initiate`
Initiated by Sentinel UI. Translates to `/api/neurocore/intent`.

**Request:**
```json
{ "task": "string describing swarm task" }
```

**Response:**
```json
{
  "swarmId": "swarm-1785921529368",
  "state": {
    "swarmId": "swarm-1785921529368",
    "status": "running",
    "messages": [],
    "scratchpad": "JSON stringified result",
    "activeAgent": null
  }
}
```

### GET `/api/swarm/poll?swarmId=<id>`
Polls swarm state. Fetches from `/api/neurocore/status` internally.

**Response:**
```json
{
  "state": {
    "swarmId": "swarm-...",
    "status": "running|completed|pending",
    "messages": [],
    "scratchpad": "...",
    "activeAgent": "hermes|ollama|nous|null"
  }
}
```

## Integration Notes

- ARC app expects `/assets/` to be relative from `/sentinel` route
- Confidence triage: `0.82 → hermes` provider
- Neurocore `/api/neurocore/connect` must be called before first intent (returns capabilities)
- Poll state stored in `Map<swarmId, { state, status }>` — no TTL cleanup yet (future improvement)
- Test suite: 41/41 passing after integration
