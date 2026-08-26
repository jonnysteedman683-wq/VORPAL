# Reproduction Incentives Pattern

User explicitly wants **reproduction as the primary evolutionary driver**. All costs are minimal, all rewards are high.

## Config values (current)

```python
REPRODUCE_HUNGER   = 5.0    # minimal hunger cost
REPRODUCE_ENERGY   = 10.0   # minimal energy cost
REPRODUCE_CURRENCY = 2.0    # very cheap reproduction
```

## Threshold

```python
# Can reproduce even when somewhat hungry
self.hunger < 70  # lenient threshold
and self.energy > C.REPRODUCE_ENERGY * 0.5  # only need half energy
and self.currency >= C.REPRODUCE_CURRENCY
```

## Fitness reward

```python
+ self.stats.children_born * 20.0  # reproduction is primary goal (was 10×)
```

## 5 Incentive mechanisms

### 1. Biological clock
Reproduction drive increases with age:
```python
age_factor = min(1.0, agent.age / 2000)  # peaks at age 2000
fertility = agent.genome.get("fertility")
rep_drive = fertility * 0.5 + age_factor * 0.4
```

### 2. Social pressure
Seeing nearby agents with children boosts drive:
```python
for other in self.alive_agents:
    d = dx*dx + dy*dy
    if d < 2500 and other.stats.children_born > 0:  # within 50px
        rep_drive += 0.15
        break
```

### 3. Emotional reward
Reproduction triggers happiness via personality system:
```python
self._personality.on_event(self.id, "reproduced")
# In personality.py: emotions.adjust("happiness", 0.2), contentment +0.1
```

### 4. Leadership reputation
Parents gain leadership reputation — reproduction is respected:
```python
if hasattr(self, '_leadership') and self._leadership:
    self._leadership.add_reputation(self.id, 5)
```

### 5. Energy bonus (biological reward)
Reproducing gives energy back — biological satisfaction:
```python
self.energy = min(C.MAX_ENERGY, self.energy + 10)
```

## Drive initialization

Reproduction drive starts strong (0.8× fertility):
```python
self.agent_memory.update_drive(agent.id, "reproduction_drive",
    agent.genome.get("fertility") * 0.8, 0, "reproduction")
```

Drive half-life = 200 ticks (slow decay — stays relevant).

## Design principle

Reproduction should be the EASIEST and MOST REWARDED action. This creates strong selection pressure for agents that reproduce early and often. Fast agents (speed=4.0) + cheap reproduction + long lifespan (7500) = rapid generational turnover with meaningful genetic evolution.

**CRITICAL**: User said "dont force just make it worth it". NEVER override the brain's action choice (e.g. `action = Brain.ACT_REPRODUCE`). Instead, shape rewards so the brain learns naturally:
- Intrinsic reward for attempting reproduction (scaled by drive strength)
- Ongoing fitness bonus per child (0.5 per child in `_compute_reward()`)
- Currency satisfaction reward (`self.currency * 0.005`)
- Social proximity reward for being near other agents

The brain must discover reproduction through exploration, not be forced into it. If it's not happening, increase exploration (epsilon) or boost rewards — never override actions.
