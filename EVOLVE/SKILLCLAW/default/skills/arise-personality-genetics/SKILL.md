---
name: arise-personality-genetics
description: "Use when adding personality, emotions, or genetics to sims."
version: 1.0.0
author: Hermes
metadata:
  hermes.tags:
    - genetics
    - personality
    - emotions
    - agent-simulation
    - ARISE
---

# ARISE Personality & Genetics Patterns

## 16-Gene Genetics System

Expanded from 8 to 16 genes. Each gene has a range, default, mutation rate, and species bias.

### Gene Table

| Gene | Effect | Range | Default | Mutation Rate |
|------|--------|-------|---------|---------------|
| speed | Movement speed | 0.5-2.0 | 1.0 | 0.08 |
| size | Body size, hunger | 0.5-2.0 | 1.0 | 0.06 |
| sense | Perception range | 0.5-2.0 | 1.0 | 0.07 |
| metabolism | Hunger rate | 0.5-2.0 | 1.0 | 0.05 |
| fertility | Reproduction ease | 0.5-2.0 | 1.0 | 0.06 |
| longevity | Max lifespan | 0.5-2.0 | 1.0 | 0.04 |
| aggression | Conflict tendency | 0.0-1.0 | 0.3 | 0.10 |
| sociability | Social learning | 0.0-1.0 | 0.5 | 0.08 |
| camouflage | Predator detection resistance | 0.0-1.0 | 0.5 | 0.07 |
| resistance | Disease/parasite resistance | 0.0-1.0 | 0.5 | 0.06 |
| fat_storage | Energy reserves | 0.5-2.0 | 1.0 | 0.05 |
| curiosity | Exploration/ICM bonus | 0.0-1.0 | 0.5 | 0.09 |
| cooperation | Food sharing tendency | 0.0-1.0 | 0.3 | 0.08 |
| stress_tolerance | Weather/hunger resistance | 0.0-1.0 | 0.5 | 0.06 |
| regeneration | Energy recovery speed | 0.5-2.0 | 1.0 | 0.05 |
| color_vivid | Visual brightness | 0.0-1.0 | 0.5 | 0.10 |

### Species Genome Initialization

Each species gets biased starting genomes:

```python
def create_initial_genome(species):
    genome = Genome.random()
    if species == "red":      # fast, aggressive, curious
        genome.set("speed", genome.get("speed") * 1.2)
        genome.set("aggression", min(1.0, genome.get("aggression") + 0.2))
        genome.set("curiosity", min(1.0, genome.get("curiosity") + 0.15))
        genome.set("camouflage", max(0.0, genome.get("camouflage") - 0.1))
    elif species == "green":  # efficient, resistant, camouflaged
        genome.set("metabolism", genome.get("metabolism") * 0.85)
        genome.set("sense", genome.get("sense") * 1.2)
        genome.set("resistance", min(1.0, genome.get("resistance") + 0.15))
        genome.set("camouflage", min(1.0, genome.get("camouflage") + 0.15))
    elif species == "blue":   # social, cooperative, regenerating
        genome.set("sociability", min(1.0, genome.get("sociability") + 0.2))
        genome.set("cooperation", min(1.0, genome.get("cooperation") + 0.2))
        genome.set("regeneration", genome.get("regeneration") * 1.2)
```

### Wiring Genes to Behavior

In `simulation.py _single_tick()`, apply gene effects per agent:

```python
genome = agent.genome
agent._speed_mult *= genome.get("speed")
agent._power_mult *= (0.5 + genome.get("size") * 0.5)
agent._hunger_mult *= genome.get("metabolism") * genome.get("size")
agent._hunger_mult *= (0.8 + genome.get("fat_storage") * 0.2)
agent._speed_mult *= (0.8 + genome.get("stress_tolerance") * 0.2)
agent.energy = min(MAX_ENERGY, agent.energy + genome.get("regeneration") * 0.01)
agent._camouflage = genome.get("camouflage")
agent._resistance = genome.get("resistance")
agent._curiosity_bonus = genome.get("curiosity") * 0.5
agent._cooperation = genome.get("cooperation")
agent._vivid = genome.get("color_vivid")
```

### Gene Effects on Specific Systems

- **Camouflage**: In predator.py, multiply detection distance by `(1.0 + camouflage * 1.5)` — camouflaged prey are 2.5× harder to detect
- **Resistance**: In simulation.py plague check, multiply infection chance by `(1.0 - gene_resist)`
- **Curiosity**: In agent.py brain.learn, multiply intrinsic reward by `(1.0 + curiosity_bonus)`
- **Cooperation**: In agent._social_tick, agents with cooperation > 0.3 share food with nearby hungry allies (5% chance per tick)
- **Longevity**: In biology.py, `is_old_age_death(age, longevity_gene)` — effective max = MAX_LIFESPAN × longevity
- **Regeneration**: Passive energy recovery per tick

### Color Mapping

Genes shift agent color for visual differentiation:

```python
GENE_COLOR_SHIFT = {
    "speed": (0.2, 0.0, 0.0),      # red = fast
    "size": (0.0, 0.2, 0.0),        # green = big
    "sense": (0.0, 0.0, 0.2),       # blue = good senses
    "camouflage": (0.0, 0.15, 0.15), # cyan = camouflaged
    "resistance": (0.0, 0.25, 0.0),  # green = resistant
    "curiosity": (0.15, 0.0, 0.15),  # purple = curious
    "cooperation": (0.0, 0.1, 0.2),  # teal = cooperative
    "color_vivid": (0.15, 0.15, 0.0),# gold = vivid
}
```

---

## Personality & Emotions System

### Architecture

`personality.py` contains:
- `Personality` — persistent Big Five traits derived from genes
- `Emotions` — dynamic state that decays toward baseline
- `PersonalitySystem` — manages per-agent personality + emotions

### Big Five from Genes

```python
Personality(
    openness=genome.get("curiosity"),
    conscientiousness=(genome.get("metabolism") + genome.get("size")) / 4.0,
    extraversion=genome.get("sociability"),
    agreeableness=genome.get("cooperation"),
    neuroticism=1.0 - genome.get("stress_tolerance"),
)
```

### 5 Emotions

| Emotion | Baseline | Decay Rate | Behavioral Effect |
|---------|----------|------------|-------------------|
| happiness | 0.5 | 0.995 | +speed, +task success |
| fear | 0.0 | 0.990 | +speed (flee), -task success |
| anger | 0.0 | 0.993 | +combat power, -social learning |
| curiosity | 0.3 | 0.997 | +exploration range |
| contentment | 0.5 | 0.996 | +energy regen, -hunger rate |

### Emotion Triggers

```python
personality.on_event(agent_id, "task_success")   # happiness +0.15
personality.on_event(agent_id, "ate_food")        # happiness +0.1, contentment +0.1
personality.on_event(agent_id, "reproduced")      # happiness +0.2, contentment +0.1
personality.on_event(agent_id, "predator_near")   # fear +0.25 (scaled by neuroticism)
personality.on_event(agent_id, "conflict_won")    # anger -0.1, happiness +0.1
personality.on_event(agent_id, "conflict_lost")   # anger +0.15, fear +0.1
personality.on_event(agent_id, "social_bond")     # happiness +0.08, contentment +0.06
personality.on_event(agent_id, "deceived")        # anger +0.2, happiness -0.1
```

### Behavior Modifiers

```python
mods = emotions.get_behavior_modifiers()
# Returns: speed_mod, task_mod, combat_mod, social_mod, explore_mod, energy_mod, hunger_mod
agent._speed_mult *= mods["speed_mod"]
agent._power_mult *= mods["combat_mod"]
```

### Personality Affects Decay

- High neuroticism → fear/anger decay slower (emotions linger)
- High extraversion → happiness recovers faster

### Visual Indicators

Colored dots above agents showing dominant emotion:
```python
emotion_colors = {
    "happiness": (255, 255, 80),    # yellow
    "fear": (100, 100, 255),         # blue
    "anger": (255, 60, 60),          # red
    "curiosity": (200, 100, 255),    # purple
    "contentment": (100, 255, 150),  # green
}
```

### Wiring

1. `personality.py`: PersonalitySystem class
2. `simulation.py`: `self.personality = PersonalitySystem()`, init per agent, pass to agents, tick + cleanup
3. `agent.py`: emotion triggers on events (task_success, ate_food, reproduced)
4. `save.py`: `from .personality import PersonalitySystem`, `sim.personality = PersonalitySystem()`
5. `renderer.py`: emotion dots above agents, import EMOTION_NAMES

### Pitfalls

1. **Personality is stateless on load**: PersonalitySystem creates fresh personalities on load. Old agents get default personalities. This is acceptable — personalities rebuild through experience.
2. **Emotion decay must run every tick**: `personality.tick(alive_agents)` in `_single_tick()`. Without this, emotions never decay.
3. **Neuroticism slows fear/anger decay**: `decay_rate ** (1.0 + neuroticism * 0.5)`. Higher exponent = slower decay.
4. **Emotion modifiers are multiplicative**: `agent._speed_mult *= mods["speed_mod"]`. Apply AFTER all other speed calculations.
5. **Cooperation food sharing**: Only triggers when cooperation > 0.3 AND agent hunger < 30 AND other hunger > 50. Transfer = min(10, self.hunger).
6. **Hybrid leadership bonus**: Hybrids get +3 reputation every 50 ticks in simulation.py. This makes them natural leaders over time.
