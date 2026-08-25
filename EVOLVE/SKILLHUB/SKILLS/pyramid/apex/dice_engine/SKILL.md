---
name: dice_engine
description: "D6-based decision engine for the OMNICORE dual-agent loop. Rolls a D6 each cycle; the roll value, parity (odd/even), double status, and high/low threshold influence queue priority, transform selection, and genesis goal choice for both agents."
version: 0.1.0
author: OMNICORE, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [omnicore, evolution, dice, dual_agent]
    related_skills: [evolution_cycle, dual_agent_loop]
---

# Dice Engine Skill

## When to Use
- OMNICORE dual-agent circular loop needs stochastic decision influence per cycle.
- Two agents (Gatekeeper A, Optimizer B) share a D6 roll; parity and value drive different behaviors.
- You need reproducible "dice-mediated" routing without external randomness libraries.

## Prerequisites
- Python 3.11+ (stdlib only: `random`, `json`, `re`, `datetime`, `pathlib`)
- `dual_agent_loop.py` at EVOLVE/SKILLHUB root (imports dice functions directly)
- `evolution_cycle.py` at EVOLVE/SKILLHUB root (reads dice from state dict)

## How to Run
- Import from `dual_agent_loop.py`:
  ```python
  from dual_agent_loop import roll_dice, dice_odd_even, dice_double, dice_is_high, dice_select_by_parity, DICE_FACES
  ```
- Roll per cycle: `roll_dice()` returns 1..6
- Use parity for binary decisions: `dice_odd_even(n)` → "odd" | "even"
- Use double status: `dice_double(n)` → True for 2,4,6
- Use high/low: `dice_is_high(n)` → True for 4,5,6
- Select from list by parity: `dice_select_by_parity(options, roll)`

## Quick Reference
- DICE_FACES: 6
- Roll range: 1..6
- Odd: 1, 3, 5 | Even: 2, 4, 6
- Double (even): 2, 4, 6
- High (>3): 4, 5, 6

## Procedure
1. Call `roll_dice()` at cycle start.
2. Derive parity, double, high from the roll.
3. Inject into state dict: `state["dice_roll"]`, `state["dice_parity"]`.
4. Both agents read dice from state for queue/transform/genesis decisions.
5. Record dice_roll + dice_parity in cycle record for the metrics ledger.
6. (Optional) Use `dice_is_high` for risk escalation: high roll → agent takes a bigger risk this cycle.

## Verification
- `python3 EVOLVE/SKILLHUB/SKILLS/pyramid/apex/dice_engine/hermes_verify_dice_engine.py` — runs 200-roll statistical test + edge case tests.
- All assertions must pass.

## Dice-Mediated Decision Points (Current)

### Queue Priority (both agents)
- **Gatekeeper**: even roll → P1 considered before logic_hallucination; odd → P1 last resort
- **Optimizer**: odd roll → P1 first, hard problems; even → overlap/merge first, then P1

### Transform Selection (evolution_cycle._mutate)
- When `state["dice_roll"]` and `state["agent_preferred_transforms"]` present:
  - Filter preferred list by parity (odd→first half, even→second half)
  - Remove any agent's avoid transforms from pool
  - Pick by `(roll - 1) % len(pool)`
- Fallback: cycle-based deterministic selection when no dice in state

### Genesis Goal Choice (both agents)
- **Gatekeeper**: odd → first leaf; even → second leaf if available
- **Optimizer**: odd → first leaf; even → last leaf (most ambitious)

## Edge Cases Handled
- Empty options list in `dice_select_by_parity` → returns None
- Odd-length option list → first half gets the extra element
- Single-element list → that element always selected
- Unknown transform name in `_mutate` → falls back to normalize_spacing
- Missing dice in state → falls back to cycle-based selection

## Extension Points
- Add `dice_re_roll(roll, condition)` → re-roll when condition met (e.g., roll on 6 triggers re-prioritize)
- Add `dice_threshold(roll, threshold)` → gate decisions on roll value (not just parity)
- Add per-agent dice interpretation tables for finer-grained behavior

## Related Files
- `dual_agent_loop.py` — main dice consumer (imports + uses all functions)
- `evolution_cycle.py` — _mutate reads dice from state for transform selection
- `SKILL_METRICS.json` — dice_roll + dice_parity recorded per cycle
