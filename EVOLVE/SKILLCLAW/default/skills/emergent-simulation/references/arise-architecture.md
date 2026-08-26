## ARISE Architecture Reference

### Module Dependency Graph
```
config.py ← (all modules import from here)
brain.py ← agent.py
hebbian.py ← agent.py
terrain.py ← world.py
world.py ← simulation.py, agent.py
tasks.py ← world.py, agent.py
memory.py ← agent.py
lineage.py ← simulation.py
resources.py ← simulation.py, agent.py
territory.py ← simulation.py, agent.py
signals.py ← simulation.py, agent.py
culture.py ← simulation.py, agent.py
conflict.py ← simulation.py, agent.py
trade_routes.py ← simulation.py, agent.py
technology.py ← simulation.py, agent.py
architecture.py ← simulation.py, agent.py
language.py ← simulation.py, agent.py
simulation.py ← main.py
renderer.py ← main.py
torus_renderer.py ← renderer.py
save.py ← renderer.py, main.py
main.py ← entry point
```

### Agent Brain Actions (9 total)
| Index | Action | Description |
|---|---|---|
| 0 | MOVE_TOWARD_TASK | Navigate to nearest unsolved task |
| 1 | MOVE_TOWARD_MARKET | Navigate to nearest food market |
| 2 | MOVE_TOWARD_AGENT | Navigate to nearest other agent |
| 3 | MOVE_RANDOM | Random walk |
| 4 | ATTEMPT_TASK | Try to solve nearest task (within 25px) |
| 5 | BUY_FOOD | Buy food at market (3 currency → -50 hunger) |
| 6 | REPRODUCE | Spawn child (costs 5 currency + 15 hunger + 20 energy) |
| 7 | TRADE | Trade currency with nearby hungry agent |
| 8 | FORAGE | Harvest food from resource nodes (15 food, within 20px) |

### Task Types (6)
| Type | Name | Example Easy | Example Hard |
|---|---|---|---|
| 0 | Logic | AND(1,0) | XOR(AND(a,b), OR(b,c)) |
| 1 | Pattern | 2,4,6,8 → ? | Fibonacci sequence |
| 2 | Math | 7 + 13 | a² + b² − c |
| 3 | String | reverse(hello) | LCS("abcdef","abcxyz") |
| 4 | Sorting | min([3,7,2,9,1]) | inversions([5,3,8,1,7,2]) |
| 5 | Creative | essence("fire") | complexity(φ,5) |

### Economy Constants
| Constant | Value | Effect |
|---|---|---|
| HUNGER_PER_TICK | 0.03 | Hunger gained per tick (100/0.03 = 3333 ticks to starve) |
| FOOD_COST | 3 | Currency to buy food at market |
| FOOD_HUNGER_RESTORE | 50 | Hunger removed when eating |
| TASK_BASE_SUCCESS | 0.5 | Base probability of solving a task |
| REPRODUCE_CURRENCY | 5 | Currency cost to reproduce |
| REPRODUCE_HUNGER | 15 | Hunger cost to reproduce |
| REPRODUCE_ENERGY | 20 | Energy cost to reproduce |

### Save Format
Each agent saved as JSON with brain_type field:
- `qnet`: serializes q_online (3 Dense layers), ICM (encoder + forward + inverse), epsilon, lr, gamma
- `hebbnet-*`: serializes hidden layer (weight, win_rate, rule, theta), readout (weight, bias), rule name
