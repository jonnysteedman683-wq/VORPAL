# Agent Intelligence Patterns

How to make agents smarter without increasing brain size.

## State Vector (14 inputs)

```python
return np.array([
    hunger_norm,           # 0  — self.hunger / MAX_HUNGER
    energy_norm,           # 1  — self.energy / MAX_ENERGY
    currency_norm,         # 2  — min(self.currency / 50, 1.0)
    t_angle_norm,          # 3  — nearest task angle (0-1)
    t_dist_norm,           # 4  — nearest task distance (0-1)
    t_type_norm,           # 5  — task type / 3
    t_diff_norm,           # 6  — task difficulty / 3
    m_angle_norm,          # 7  — nearest market angle
    m_dist_norm,           # 8  — nearest market distance
    a_dist_norm,           # 9  — nearest agent distance (cached)
    a_fitness,             # 10 — nearest agent fitness (cached)
    goal_food,             # 11 — 1.0 if hunger > 40
    goal_task,             # 12 — 1.0 if hunger < 30 and energy > 30
    goal_social,           # 13 — 1.0 if dominant emotion is happiness/curiosity
], dtype=np.float32)
```

Goal inputs (11-13) give the brain awareness of the agent's current objective,
allowing it to learn action→goal associations rather than just action→state.

## Goal Persistence

Agents stick with working actions for 3-8 ticks. Reduces brain.think() churn
and creates more coherent behavior (agents commit to goals):

```python
if not hasattr(self, '_goal_persistence'):
    self._goal_persistence = 0
    self._goal_action = action

if self._prev_action is not None and action == self._prev_action:
    self._goal_persistence = min(self._goal_persistence + 1, 8)
elif self._goal_persistence > 3:
    action = self._goal_action  # keep current goal
    self._goal_persistence -= 1
else:
    self._goal_action = action
    self._goal_persistence = 0
```

Why 3-8 ticks: short enough to adapt, long enough to complete multi-step actions.

## Social Learning

Every 10 ticks, agents scan nearby agents within ~63px (d² < 4000).
If a fitter agent exists, 20% chance to copy their last action.
Only triggers when `_social_mod > 0.5` (emotion-based).

```python
if hasattr(self, '_social_mod') and self._social_mod > 0.5 and self.age % 10 == 0:
    best_other = None
    best_fitness = self.fitness
    for other in agents:
        if other.id == self.id or not other.alive: continue
        dx = other.x - self.x; dy = other.y - self.y
        # inline toroidal distance squared
        d = dx*dx + dy*dy
        if d < 4000 and other.fitness > best_fitness:
            best_fitness = other.fitness
            best_other = other
    if best_other and best_other._prev_action is not None:
        if np.random.random() < 0.2:
            action = best_other._prev_action
```

Effect: successful strategies spread through the population via imitation.
Combined with genetics (sociability gene affects `_social_mod`), this creates
cultural evolution alongside genetic evolution.

## Curiosity Gene → ICM Bonus

The curiosity gene amplifies intrinsic motivation (ICM exploration bonus):

```python
intrinsic = self.brain.learn(prev_state, prev_action, reward, state)
curiosity_bonus = getattr(self, '_curiosity_bonus', 0.0)
self.stats.intrinsic_reward_total += intrinsic * (1.0 + curiosity_bonus)
```

With curiosity=0.5, agents get 25% more exploration reward. Curious agents
explore more, find more food sources, and share locations via communication.

## Cooperation Gene → Food Sharing

Agents with high cooperation gene share food with nearby hungry allies:

```python
cooperation = getattr(self, '_cooperation', 0.3)
if cooperation > 0.3 and self.hunger < 30 and np.random.random() < cooperation * 0.05:
    for other in agents:
        d = toroidal_distance(self.x, self.y, other.x, other.y)
        if d < 25 and other.hunger > 50:
            transfer = min(10, self.hunger)
            self.hunger += transfer
            other.hunger = max(0, other.hunger - transfer)
            break
```

This creates reciprocal altruism — cooperative agents help each other survive.

## Integration Checklist

When adding new intelligence features:

1. Add gene to `genetics.py` (GENE_NAMES, GENE_DEFAULTS, GENE_RANGES, MUTATION_RATES)
2. Apply gene effect in `simulation.py` `_single_tick` (inside the per-agent loop)
3. Add behavior in `agent.py` (act(), _social_tick(), or _try_* methods)
4. Update state vector if adding new sensory input (increment BRAIN_INPUTS in config.py)
5. Add resize helpers in `save.py` if BRAIN_INPUTS changed
6. Update renderer to show new info in agent inspection panel
7. Update species initialization in `genetics.py` create_initial_genome()

## Reward Shaping Pattern

User said "dont force just make it worth it". Shape rewards to guide behavior without overriding actions:

```python
def _compute_reward(self, world):
    r = 0.01  # living reward
    if self.hunger > 70: r -= 0.1       # hunger penalty
    if self.hunger < 30: r += 0.05      # satisfaction
    if self.energy > 80: r += 0.03      # energy reward
    r += self.currency * 0.005           # currency feels good
    if self.stats.children_born > 0:
        r += self.stats.children_born * 0.5  # HUGE ongoing reproduction reward
    if self._cached_a_dist < 0.3: r += 0.02  # social proximity
    return r
```

For desired actions, also add intrinsic reward when the action is ATTEMPTED (not just when it succeeds):
```python
elif action == Brain.ACT_REPRODUCE:
    newborn = self._try_reproduce(agents)
    rep_drive = self._agent_memory.get_drive_strength(self.id, "reproduction_drive", self.age)
    if rep_drive > 0.3:
        self.stats.intrinsic_reward_total += rep_drive * 0.3
```

This teaches the brain that the action is worth trying, even if conditions aren't always met.
