# Time Warp — Accelerated Evolution

Press number keys 1-5 to skip ahead N ticks instantly without rendering. This accelerates genetic mutation and evolution.

## Key bindings

| Key | Ticks | Use case |
|-----|-------|----------|
| 1 | 10 | Quick test |
| 2 | 50 | Small evolution |
| 3 | 200 | Medium evolution |
| 4 | 1000 | Major evolution |
| 5 | 5000 | Full evolutionary cycle |

## Implementation

```python
def _time_warp(self, ticks: int):
    """Run N simulation ticks instantly without rendering."""
    import time
    start = time.time()
    for i in range(ticks):
        self.sim.tick()
    elapsed = time.time() - start
    print(f"[TIME WARP] {ticks} ticks in {elapsed:.1f}s ({ticks/max(elapsed,0.001):.0f} ticks/sec)")
    print(f"  Tick: {self.sim.stats.tick} | Alive: {len(self.sim.alive_agents)} | "
          f"Gen: {self.sim.stats.max_generation}")
    # auto-save after big warps
    if ticks >= 200:
        from . import save
        save.auto_save(self.sim)
        print(f"  Auto-saved.")
```

## Wiring

In `_handle_key()`:
```python
elif key == pygame.K_1:
    self._time_warp(10)
elif key == pygame.K_2:
    self._time_warp(50)
elif key == pygame.K_3:
    self._time_warp(200)
elif key == pygame.K_4:
    self._time_warp(1000)
elif key == pygame.K_5:
    self._time_warp(5000)
```

Stats bar shows: `[1] 10 ticks  [2] 50  [3] 200  [4] 1000  [5] 5000 — TIME WARP`

## Performance

- 40 agents: ~26 ticks/sec without rendering
- 120 agents: ~7 ticks/sec without rendering
- Auto-saves after warps ≥200 ticks
- Prints stats after each warp (ticks/sec, alive count, max generation)

## Save dependency

Requires `auto_save()` in save.py:
```python
def auto_save(sim: Simulation) -> str:
    from datetime import datetime
    name = datetime.now().strftime("%Y%m%d_%H%M%S")
    return save(sim, name)
```

## Pitfalls

1. **Pygame hang**: `_time_warp()` runs inside the pygame event loop. Don't call it from outside the renderer.
2. **No feedback during warp**: The warp blocks the UI. For very large warps (5000+), consider adding a progress indicator.
3. **Auto-save on big warps only**: warps < 200 ticks don't auto-save (too many saves).
