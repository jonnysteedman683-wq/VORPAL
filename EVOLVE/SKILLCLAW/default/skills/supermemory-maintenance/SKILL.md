---
name: supermemory-maintenance
description: "Use when clearing stale or conflicting supermemory entries."
---

# Supermemory Maintenance

Keep the supermemory store clean. It accumulates stale, conflicting, and duplicated cargo over time — and it is injected into every session, so poison here is live poison (conflicting goals, outdated identities, dead project facts).

## When to use
- Identity/project change (e.g. a consolidation) leaves old memories conflicting with new reality
- "start fresh on memory", "we're poisoned by old memories / conflicting goals"
- A reseed after a big purge
- Any large-scale forget/cleanup of the supermemory store

## The workflow: archive → purge → re-sweep → verify → seed

1. **ARCHIVE FIRST.** Dump the enumerated state to a markdown file on disk before touching anything (archive, never delete). Run `supermemory_search` per cluster, save the full result set to a file marked "do not re-seed — stale reference."
2. **PURGE by ID, in batches.** `supermemory_forget` with exact IDs (or a best-match query for a single prominent entry). Batch ~15 per call group.
3. **RE-SWEEP — the store duplicates content under different IDs.** One pass is NEVER enough. The same fact appears under multiple IDs, so each sweep surfaces fresh residue. Expect 3–6 sweeps on a large store. Keep re-searching the same clusters until a broad query returns only empty shells or nothing.
4. **Treat 404s as already-gone.** `Memory not found` on forget = empty index ghost / already deleted. Ignore, don't retry.
5. **VERIFY with a fresh search** before seeding — confirm the poison clusters return nothing.
6. **SEED the clean baseline.** Write compact declarative facts (identity, north star, protocol paths, operator prefs) with metadata tags (e.g. `{"kind": "identity"}`). Keep each entry a single fact.

## Pitfalls
- **Writes can be blocked while reads work.** A `402 Text tokens limit reached` on `store()` means credits are exhausted; `search()` (and often `forget()`) still function. If seeding fails with 402, do NOT retry — keep the clean baseline on disk (Hermes persistent memory, project files) and reseed later; the store re-learns from real use.
- **Verify `store()` works BEFORE promising a reseed.** Don't build a big seed plan until writes are confirmed unblocked.
- **Search similarity is fuzzy.** Use broad cluster queries (`hermes hive markus AURORAL swarm benchmark`) to catch duplicates, not narrow exact-phrase queries.
- **Archive is the safety net.** With the full dump on disk, aggressive purging is safe. The archive file should explicitly say "do not re-seed."
- Empty-content entries (blank `content`) still appear in results and forget returns 404 for them — they're ghosts, ignore.

## Reference
- Purge is done via the supermemory tool aliases: `supermemory_search` / `supermemory_forget` / `supermemory_store` / `supermemory_profile`.
