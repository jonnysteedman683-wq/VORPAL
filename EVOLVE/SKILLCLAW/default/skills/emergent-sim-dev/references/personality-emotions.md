# Personality & Emotions System

Agents have persistent Big Five personality traits derived from genes, and dynamic emotional states that affect behavior.

## Personality (Big Five, from genes)

```python
@dataclass
class Personality:
    openness: float = 0.5           # from curiosity gene
    conscientiousness: float = 0.5  # from (metabolism + size) / 4
    extraversion: float = 0.5       # from sociability gene
    agreeableness: float = 0.5      # from cooperation gene
    neuroticism: float = 0.5        # from 1.0 - stress_tolerance gene
```

Personality is initialized once from genome, persists for agent's lifetime. Affects emotion decay rates.

## Emotions (5 dynamic states)

```python
@dataclass
class Emotions:
    happiness: float = 0.5    # baseline 0.5, decays toward 0.5
    fear: float = 0.0         # baseline 0.0
    anger: float = 0.0        # baseline 0.0
    curiosity: float = 0.3    # baseline 0.3
    contentment: float = 0.5  # baseline 0.5
```

Emotions decay toward baseline each tick. Personality affects decay:
- High neuroticism → fear/anger decay slower (emotions linger)
- High extraversion → happiness bounces back faster

## Emotion → Behavior Modifiers

```python
def get_behavior_modifiers(self) -> dict:
    mods = {"speed_mod": 1.0, "task_mod": 1.0, "combat_mod": 1.0,
            "social_mod": 1.0, "explore_mod": 1.0, "energy_mod": 1.0, "hunger_mod": 1.0}
    if self.happiness > 0.6:    mods["speed_mod"] += (happiness-0.5)*0.4; mods["task_mod"] += same
    if self.fear > 0.3:         mods["speed_mod"] += fear*0.3; mods["task_mod"] -= fear*0.3
    if self.anger > 0.3:        mods["combat_mod"] += anger*0.4; mods["social_mod"] -= anger*0.3
    if self.curiosity > 0.5:    mods["explore_mod"] += (curiosity-0.5)*0.5
    if self.contentment > 0.6:  mods["energy_mod"] += (contentment-0.5)*0.3; mods["hunger_mod"] -= same
    return mods
```

## Emotion Triggers (16 event types)

```python
"task_success"    → happiness +0.15, contentment +0.05
"task_fail"       → happiness -0.05, anger +0.08 (if neurotic)
"ate_food"        → happiness +0.1, contentment +0.1
"hurt"            → fear +0.2, anger +0.1
"predator_near"   → fear +0.25 * (1 + neuroticism*0.5)
"conflict_won"    → anger -0.1, happiness +0.1
"conflict_lost"   → anger +0.15, fear +0.1
"social_bond"     → happiness +0.08, contentment +0.06
"explored"        → curiosity +0.1 * openness
"shelter_rest"    → contentment +0.15, fear -0.1
"danger_signal"   → fear +0.15
"deceived"        → anger +0.2, happiness -0.1
"reproduced"      → happiness +0.2, contentment +0.1
"child_died"      → happiness -0.2, anger +0.1
```

## Renderer Integration

Emotion indicator — small colored dot above agent when intensity > 0.15:

```python
emotion_colors = {
    "happiness": (255, 255, 80),    "fear": (100, 100, 255),
    "anger": (255, 60, 60),         "curiosity": (200, 100, 255),
    "contentment": (100, 255, 150),
}
emo_radius = max(1, int(emotion_intensity * 3))
pygame.draw.circle(screen, emo_color, (ix, iy - radius - 3), emo_radius)
```

## 3-File Wiring

1. `personality.py` — Personality, Emotions, PersonalitySystem classes
2. `simulation.py` — `self.personality = PersonalitySystem()`, init per agent, apply behavior mods in tick, `personality.tick(alive_agents)` for decay
3. `agent.py` — emotion triggers on events (task_success, ate_food, reproduced, etc.)

## Hybrid Leadership Bonus

Hybrids (QNet × HebbNet brain) get +3 reputation every 50 ticks, making them natural leaders:

```python
if self.stats.tick % 50 == 0:
    self.leadership.update_followers(self.alive_agents)
    for agent in self.alive_agents:
        if agent.brain_type == "hybrid":
            self.leadership.add_reputation(agent.id, 3)
```

This creates an evolutionary pressure: hybrids are more likely to become leaders,
which gives them followers, which gives them coordination bonuses, which makes
them more successful, which spreads hybrid genes further. A positive feedback loop.

## Pitfalls

1. **PersonalitySystem must be in save.py load()** — `sim.personality = PersonalitySystem()` alongside other subsystems
2. **Emotions are per-agent state** — PersonalitySystem stores dicts keyed by agent_id, must cleanup dead agents
3. **Emotion modifiers multiply** — they compound with gene/role/weather modifiers, so extreme emotions can push speed_mult past 3.0
