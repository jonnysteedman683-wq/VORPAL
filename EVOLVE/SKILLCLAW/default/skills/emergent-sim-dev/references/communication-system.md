# Emergent Communication System

## Architecture

Species develop independent vocabularies through signal-response reinforcement.

### Signal types
```python
SIGNAL_FOOD = 0      # "food here" — emitted when hungry agent finds food
SIGNAL_DANGER = 1    # "danger" — emitted when sick
SIGNAL_SOCIAL = 2    # "come here" — emitted occasionally
SIGNAL_TERRITORY = 3 # "my area" — emitted during territory claims
SIGNAL_CALL = 4      # general call
SIGNAL_WARNING = 5   # "predator nearby" — emitted when fleeing
```

### Vocabulary convergence

Each species has vocabulary centers that drift toward successful signals:
```python
species_vocab = {
    "red": {"food_center": 0.15, "danger_center": 0.45, "social_center": 0.7, "territory_center": 0.9},
    "green": {...},
    "blue": {...},
}
```

Reinforcement: `vocab_center += lr * (signal_value - vocab_center)`
- Success: lr = 0.02 (fast learning)
- Failure: lr = -0.005 (slow unlearning)

Over time, each species converges on its own "language" — the same signal value means different things to different species.

### Agent integration

In `_social_tick()`:
1. Check agent state → emit appropriate signal
2. Perceive nearby signals (range = 80 × sense_gene)
3. Interpret signal using species vocabulary
4. React: food→move toward, danger→flee, social→approach
5. Reinforce vocabulary on successful interpretation

### 3-file wiring

1. `communication.py`: CommunicationSystem class
2. `simulation.py`: `self.communication = CommunicationSystem()` in `__init__`, `self.communication.tick()` in `_single_tick`, pass to agents via `agent._communication = self.communication`
3. `agent.py`: emit/perceive/interpret/reinforce in `_social_tick()`

### Renderer

Show active signal count in stats bar: `Signals: {self.sim.communication.active_count}`

### Save/load

CommunicationSystem is stateless (vocabularies reset on load). Just init in `save.py load()`:
```python
from .communication import CommunicationSystem
sim.communication = CommunicationSystem()
```
