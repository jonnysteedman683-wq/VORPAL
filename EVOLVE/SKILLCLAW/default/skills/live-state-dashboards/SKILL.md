---
name: live-state-dashboards
description: Use when building a dashboard rendering live state.
---

# Live-State Dashboards

Use when the user asks to build or upgrade a dashboard, orb, memory palace, code
garden, or visual surface that shows LIVE state (not static mock data). The user's
project ARK-NEXUS is the canonical instance — see `references/ark-nexus.md` for its
data-source map, palette, and panel wiring.

## Architecture (proven, zero deps)

1. **Self-contained single HTML** — one file, inline CSS+JS, no libraries, works
   from `file://` via `open_preview`. Canvas for 3D/animated surfaces.
2. **Python data-builder script** (`scripts/build_nexus_data.py` style) — reads the
   live state files, computes aggregates (counts, by-kind census, tier splits,
   verdicts, feed dedupe), writes a `*.json` snapshot.
3. **Inline injection** — the HTML carries a `/*__NEXUS_DATA__*/` marker; the
   builder replaces it with `window.NEXUS_DATA = {...};` and writes the HTML. The
   dashboard renders from the embedded object, so it works offline AND re-injects
   cleanly on every rebuild. Keep the marker; don't hardcode data by hand.

## Workflow

1. **Inventory data sources first.** Find every state file that maps to a panel
   (JSON manifests, index files, logs, ledger jsonl). Panel → real file, always.
2. Write the builder (stdlib only: json, pathlib, datetime). Emit both raw slices
   and aggregates so the front-end stays dumb.
3. `python -m py_compile scripts/<builder>.py` → run it → confirm printed counts
   match what you saw in the files.
4. Inject: read HTML, `json.dumps(data)`, replace marker, write back.
5. **Verify the JS**: extract every `<script>...</script>` block to a temp file
   (join with `\n;\n` if multiple) and `node --check` it. Fix syntax before
   previewing.
6. `open_preview` + `read_preview` — confirm the rendered text shows REAL numbers
   (e.g. gate counts, generation), not placeholders. A preview that renders is not
   proof; check that live values appear.

## Recurring patterns

- **Adaptive 60/10 FPS**: run at 60 while visible+interacting; drop to 10 when the
  tab is hidden (`visibilitychange`) or idle > ~25s (interaction timestamp check on
  an interval). Live FPS readout in the header.
- **Auto-sync**: only when served over HTTP (`location.protocol === 'http:'`) —
  `setInterval` fetch of the JSON (~30s), hot re-render without reload, with a
  sync-state indicator. For `file://`, a REFRESH button re-fetches/reloads.
- **Detail drawer**: click any orb node / list row / garden stalk → slide-in panel.
  Keep a single `openDetail(node)` + shared focus helper so all three surfaces
  cross-link.

## Pitfalls (learned the hard way)

- **The `patch` tool can mangle multi-branch Python edits** — a replace whose
  context shares lines with an adjacent branch can silently drop the `elif`
  keyword. After any patch touching control flow, re-read the region and
  `py_compile` before trusting it.
- **If you reassign the data object on auto-sync, declare `let D = ...`**, never
  `const D` — reassignment throws silently in the interval and the feed never
  updates.
- **innerHTML with the embedded local JSON snapshot is safe** (all values come from
  trusted local files; search filters only toggle display). Keep a comment saying
  so; never route user input into it.
- **Log/feed parsing**: when walking a bus log backwards, dedupe consecutive
  identical bursts (e.g. repeating `LP_LEXICON` entries) by keying
  `(agent, concept, token)` and skipping repeats — otherwise the feed is wall-to-wall
  noise.
- Canvas sizing: multiply by `devicePixelRatio` for crisp lines and call
  `ctx.setTransform(dpr,0,0,dpr,0,0)` each frame.

## Support files

- `references/ark-nexus.md` — ARK-NEXUS data-source map, palette, the three
  surfaces, and the v2 upgrade log.
