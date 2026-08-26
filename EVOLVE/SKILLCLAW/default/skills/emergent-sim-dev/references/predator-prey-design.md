# Predator/Prey Design Patterns

## Key Design Decisions

**Inter-species only**: Predators hunt agents of DIFFERENT species. Same-species hunting would collapse populations too fast.

**Skill threshold**: Agents need combat Lv3+ to become predators. This means predators emerge over time, not instantly.

**Flee mechanic**: Prey gets +0.4 speed bonus when fleeing. Creates an arms race: predators need speed too.

**XP for both sides**: Predator gains combat XP (3 on success, 1 on fail). Prey gains combat XP (2) and scouting XP (1) on survival. This means prey LEARNS from encounters.

**Cooldown**: 30-tick cooldown between hunts per predator. Prevents one predator from wiping out everyone.

## Tuning Constants

```python
HUNT_RANGE = 35           # close-range (increased from 25)
HUNT_DAMAGE = 20          # significant (increased from 15)
HUNT_COOLDOWN = 20        # faster hunting (reduced from 30)
FLEE_RANGE = 50           # prey detects predator at longer range
FLEE_SPEED_BONUS = 0.5    # meaningful escape boost (increased from 0.4)
PREDATOR_MIN_COMBAT = 1   # predators emerge immediately after 1 task
```

## Camouflage Gene

Prey with high camouflage gene is harder for predators to detect:

```python
camouflage = getattr(other, '_camouflage', 0.0)
effective_dist = dist * (1.0 + camouflage * 1.5)  # up to 2.5x harder to detect

if effective_dist < best_dist:  # predator sees through camouflage at close range
    # check if prey is weaker
```

Green species starts with higher camouflage (0.6-0.9), red starts lower (0.0-0.3).

## Success Chance Formula

```python
success_chance = 0.3 + (attacker_combat - prey_combat) * 0.1
success_chance = max(0.1, min(0.9, success_chance))
```

- Equal combat: 30% success (prey often escapes)
- +3 combat advantage: 60% success (predator usually wins)
- +6 combat advantage: 90% cap (always risky)

## Resource Scarcity Interaction

Food scarcity + predation creates compounding pressure:
1. Food depletes → agents get hungry
2. Hungry agents are weaker (less energy for tasks)
3. Weak agents get hunted by predators
4. Dead agents leave food for survivors
5. Survivors reproduce, passing on better genes

This is the core evolution loop.
