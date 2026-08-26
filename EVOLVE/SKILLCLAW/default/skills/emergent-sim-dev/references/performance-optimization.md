# Performance Optimization Patterns for ARISE

## Problem

ARISE with 120+ agents and 30+ subsystems hits ~989ms/tick without optimization.
Target: <200ms/tick (~5 FPS with rendering overhead).

## Profiling approach

```python
# Time individual subsystems
t = time.time()
for a in sim.alive_agents[:20]:
    a.act(sim.world, sim.alive_agents)
ms = (time.time()-t)*1000
print(f'act x20: {ms:.0f}ms ({ms/20:.1f}ms/agent)')
```

## Bottleneck breakdown (120 agents, unoptimized)

| Component | ms/tick | % of total |
|-----------|---------|------------|
| agent.act() | 360 | 36% |
| └─ sense() | 71 | 7% |
| └─ brain.think() | 25 | 3% |
| └─ brain.learn() | 28 | 3% |
| └─ _social_tick() | 94 | 10% |
| weather effects | 40 | 4% |
| migration bias | 30 | 3% |
| flee bonus | 15 | 2% |
| architecture bonuses | 5 | 1% |
| other | 332 | 33% |
| **TOTAL** | **989** | **100%** |

## Per-agent profiling (40 agents, optimized)

| Function | ms/call | Notes |
|----------|---------|-------|
| brain.learn() | 1.63 | **Bottleneck** — ICM forward+backward |
| sense() | 0.52 | nearest-agent cached every 5 ticks |
| brain.think() | 0.47 | QNetwork forward pass |
| _social_tick() | 0.47 | communication + territory + signals |
| comm_perceive | 0.02 | spatial grid lookup |
| arch_speed | 0.00 | dict lookup |
| weather_storm | 0.00 | dict lookup |
| disease_check | 0.00 | dict lookup |

Final: 65ms/tick with 40 agents = 15 FPS.

## Optimizations applied (989ms → 179ms, 5.5× speedup)

### 1. Spatial grid for O(n²) loops (4239ms → 22ms, 193×)

Communication perceive was the single biggest bottleneck. 76 agents × 228 signals × toroidal_distance = 4239ms.

Solution: spatial grid with 100px cells + inline squared distance.

```python
GRID_CELL_SIZE = 100

def _grid_key(self, x, y) -> tuple:
    return (int(x / GRID_CELL_SIZE) % self._grid_w,
            int(y / GRID_CELL_SIZE) % self._grid_h)

def _rebuild_grid(self):
    self._grid.clear()
    for sig in self.active_signals:
        key = self._grid_key(sig.x, sig.y)
        if key not in self._grid:
            self._grid[key] = []
        self._grid[key].append(sig)

def _get_nearby_signals(self, x, y, radius) -> list:
    cell_radius = int(radius / GRID_CELL_SIZE) + 1
    cx, cy = self._grid_key(x, y)
    results = []
    for dx in range(-cell_radius, cell_radius + 1):
        for dy in range(-cell_radius, cell_radius + 1):
            key = ((cx + dx) % self._grid_w, (cy + dy) % self._grid_h)
            if key in self._grid:
                results.extend(self._grid[key])
    return results
```

### 2. Inline toroidal distance squared

Avoid function call overhead + sqrt in hot loops:

```python
dx = x2 - x1; dy = y2 - y1
if dx > WORLD_WIDTH*0.5: dx -= WORLD_WIDTH
elif dx < -WORLD_WIDTH*0.5: dx += WORLD_WIDTH
if dy > WORLD_HEIGHT*0.5: dy -= WORLD_HEIGHT
elif dy < -WORLD_HEIGHT*0.5: dy += WORLD_HEIGHT
dist_sq = dx*dx + dy*dy
if dist_sq < range_sq:  # no sqrt needed
    # within range
```

### 3. Throttle expensive operations

| Operation | Frequency | Savings |
|-----------|-----------|---------|
| Weather effects | Every 3 ticks | ~40ms |
| Migration bias | Every 5 ticks | ~30ms |
| Flee bonus | Every 2 ticks | ~15ms |
| Brain learn | Every other tick | ~14ms |

### 4. Ring buffer instead of append/pop(0)

`pop(0)` is O(n). Ring buffer is O(1):

```python
if len(trail) < max_trail:
    trail.append(item)
else:
    trail[age % max_trail] = item
```

### 5. No per-element Surface creation

Creating `pygame.Surface((r*2, r*2), pygame.SRCALPHA)` per ripple/event is expensive.
Draw directly on screen with dimmed color:

```python
dim = alpha / 100
dim_color = (int(color[0]*dim), int(color[1]*dim), int(color[2]*dim))
pygame.draw.circle(self.screen, dim_color, (int(x), int(y)), radius, 2)
```

### 6. Cap collection sizes

- Max 200 active signals (was unlimited)
- Max 50 ripples (was unlimited)
- Max 30 rendered ripples
- Max 500 active signals in communication system

### 7. Module-level imports

Never use `from .world import toroidal_distance` inside functions.
Python treats local imports as local variables, causing `UnboundLocalError`
when other code paths in the same function try to use the module-level version.

```python
# WRONG — shadows module-level import
def _social_tick(self, agents, world):
    if condition:
        from .world import toroidal_distance  # creates local var
    d = toroidal_distance(...)  # UnboundLocalError if condition was False

# CORRECT — use module-level import
from .world import toroidal_distance  # at top of file
def _social_tick(self, agents, world):
    d = toroidal_distance(...)  # always works
```

### 8. Cached nearest-agent scan

The O(n²) nearest-agent scan in `sense()` runs every tick for every agent.
Cache the result every 5 ticks — agents don't move fast enough for per-tick precision:

```python
if not hasattr(self, '_cached_nearest_tick') or self.age - self._cached_nearest_tick > 5:
    # full scan with inline toroidal distance squared
    best_d = float("inf")
    for other in agents:
        if other.id == self.id or not other.alive: continue
        dx = other.x - self.x; dy = other.y - self.y
        if dx > hw: dx -= WORLD_WIDTH  # ... toroidal wrap
        d = dx*dx + dy*dy
        if d < best_d: best_d = d; ...
    self._cached_a_dist = a_dist_norm
    self._cached_a_fitness = a_fitness
    self._cached_nearest_tick = self.age
else:
    a_dist_norm = self._cached_a_dist  # use cached
```

### 9. Goal persistence

Agents stick with working actions for 3-8 ticks, reducing brain.think() churn:

```python
if action == self._prev_action:
    self._goal_persistence = min(self._goal_persistence + 1, 8)
elif self._goal_persistence > 3:
    action = self._goal_action  # keep current goal
    self._goal_persistence -= 1
else:
    self._goal_action = action
    self._goal_persistence = 0
```

### 10. State vector expansion (10→14 inputs)

Adding goal_food, goal_task, goal_social, a_fitness to the state vector increased
BRAIN_INPUTS from 10 to 14. Old saves need brain weight resizing:

```python
# save.py — resize helpers
def _resize_dense(dense, old_in, new_in):
    new_dense = Dense(new_in, dense.out_dim, dense.lr)
    copy_cols = min(old_in, new_in)
    new_dense.weight[:, :copy_cols] = dense.weight[:, :copy_cols]
    if new_in > old_in:
        new_dense.weight[:, old_in:] = np.random.randn(dense.out_dim, new_in - old_in) * 0.01
    new_dense.bias = dense.bias.copy()
    return new_dense
```

Apply to QNetwork.fc1, ICM encoder, and HebbNet hidden weights.
