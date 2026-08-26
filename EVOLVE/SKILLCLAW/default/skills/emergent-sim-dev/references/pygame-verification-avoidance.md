# Pygame Verification Avoidance

Importing `arise.agent` or `arise.simulation` triggers pygame transitively. This causes verification scripts to hang or timeout.

## The problem

```python
# WRONG — triggers pygame, may hang or timeout at 10s
from arise.simulation import Simulation
sim = Simulation()  # generates terrain (~3s), initializes pygame
```

## The solution — source-only checks

```python
# CORRECT — no pygame, instant
with open('C:/Users/jonny/OneDrive/Documents/AEGIS/ARISE/arise/simulation.py') as f:
    src = f.read()
assert 'self.weather' in src
assert 'self.communication' in src
print('OK simulation.py')
```

## Pattern for verification scripts

```python
import sys
sys.path.insert(0, 'C:/Users/jonny/OneDrive/Documents/AEGIS/ARISE')

errors = []

# 1. Source-only checks (no imports)
try:
    with open('C:/Users/jonny/OneDrive/Documents/AEGIS/ARISE/arise/agent.py') as f:
        src = f.read()
    for kw in ['expected_keyword', 'another_keyword']:
        assert kw in src, f'{kw} missing'
    print('OK agent.py')
except Exception as e:
    errors.append(f'agent: {e}')

# 2. Import checks (only when needed, may trigger pygame)
try:
    from arise.genetics import GENE_NAMES
    assert len(GENE_NAMES) == 16
    print('OK genetics')
except Exception as e:
    errors.append(f'genetics: {e}')

if errors:
    for e in errors: print(f'FAIL: {e}')
    sys.exit(1)
print('ALL VERIFIED')
```

## When you CAN import

Modules that DON'T trigger pygame:
- `arise.genetics` — pure numpy
- `arise.config` — pure constants
- `arise.biology` — pure numpy
- `arise.communication` — pure numpy (but needs config)
- `arise.agent_memory` — pure numpy
- `arise.personality` — pure numpy
- `arise.roles` — pure enums

Modules that DO trigger pygame:
- `arise.agent` — imports brain which imports pygame
- `arise.simulation` — imports agent
- `arise.renderer` — imports pygame directly
- `arise.save` — imports simulation

## Terrain generation cost

Even without pygame, `Simulation()` generates terrain (~3s on first call). For performance benchmarks, call `sim.tick()` twice (warm up) before measuring.
