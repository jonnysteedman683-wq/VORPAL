# Agent Memory — Ported from ARGUS

Ported from ARGUS (personal digital twin repo) into ARISE for agent memory, drives, and anomaly detection.

## Key patterns from ARGUS

### Exponential half-life decay
```
strength * 0.5^(ticks_since_update / half_life)
```
- `hunger`: 50 tick half-life
- `energy`: 80 tick half-life  
- `fear`: 30 tick half-life (fast decay)
- `curiosity`: 120 tick half-life (slow decay)
- `reproduction_drive`: 200 tick half-life (very slow)

### Preference/drive resolution (ARGUS multi-signal scoring)
```python
score = (tier_rank, effective_strength, recency)
# Higher tier wins ties, then stronger drive, then more recent
```

### Drive tiers
```python
DRIVE_TIERS = {
    "survival": 4,      # hunger, energy, danger
    "reproduction": 3,  # finding mate, shelter
    "social": 2,        # communication, cooperation
    "exploration": 1,   # curiosity, tasks
    "comfort": 0,       # rest, contentment
}
```

### Anomaly detection (Z-score)
```python
def detect_anomaly(self, agent_id, current_value, window=20, threshold=2.0):
    history = self._metric_history[agent_id][-window:]
    mean = np.mean(history)
    std = np.std(history)
    if std < 0.001: return False
    return abs(current_value - mean) / std > threshold
```

### Trend forecasting (least-squares)
```python
def forecast_trend(self, agent_id, horizon=10):
    recent = history[-20:]
    x = np.arange(len(recent))
    # y = mx + b via least squares
    m = (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x²)
    return m * (len(recent) + horizon) + b
```

## Integration points

1. **simulation.py**: `self.agent_memory = AgentMemorySystem()` in `__init__`
2. **simulation.py**: Initialize drives from genome for each agent
3. **simulation.py**: Update hunger/energy drives per tick based on agent state
4. **simulation.py**: Biological clock — reproduction drive increases with age (see reproduction-incentives.md)
5. **simulation.py**: Social pressure — nearby parents boost reproduction drive
6. **simulation.py**: `self.agent_memory.cleanup(alive_ids)` for dead agents
7. **save.py**: `from .agent_memory import AgentMemorySystem` + `sim.agent_memory = AgentMemorySystem()`
8. **agent.py**: `agent._agent_memory = self.agent_memory` passed to agents

## Pitfalls

1. **Drive initialization**: Must initialize drives for newborns too (not just initial agents)
2. **Cleanup**: Must call `cleanup(alive_ids)` or dead agents accumulate in memory
3. **Save/load**: AgentMemorySystem is stateless (drives/events reset on load) — just init fresh
