"""hermes_verify_dice_engine.py — 200-roll statistical test + edge cases.

Deterministic: uses random.seed(42) so failures are reproducible.
Covers: roll_dice range, odd_even correctness, double status, is_high threshold,
dice_select_by_parity for even/odd/edge cases, dice_re_roll, dice_threshold,
dice_interpret, and integration spot-checks.

Loads dual_agent_loop.py by walking up from this file's location until it finds
registry.json (the SKILLHUB root marker), then loads the module directly.
"""

import importlib.util
import random
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Walk up from this file's resolved absolute location to find SKILLHUB root
check = SCRIPT_DIR.resolve()
while True:
    if (check / "registry.json").exists():
        SKILLHUB_DIR = check
        break
    parent = check.parent
    if parent == check:
        raise RuntimeError(f"Cannot find SKILLHUB root from {SCRIPT_DIR}")
    check = parent

DUAL_AGENT_PATH = SKILLHUB_DIR / "dual_agent_loop.py"
if not DUAL_AGENT_PATH.exists():
    raise RuntimeError(f"dual_agent_loop.py not found at {DUAL_AGENT_PATH}")

spec = importlib.util.spec_from_file_location("dual_agent_loop", DUAL_AGENT_PATH)
dual_agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dual_agent)

roll_dice = dual_agent.roll_dice
dice_odd_even = dual_agent.dice_odd_even
dice_double = dual_agent.dice_double
dice_is_high = dual_agent.dice_is_high
dice_select_by_parity = dual_agent.dice_select_by_parity
dice_re_roll = dual_agent.dice_re_roll
dice_threshold = dual_agent.dice_threshold
dice_interpret = dual_agent.dice_interpret
DICE_FACES = dual_agent.DICE_FACES

random.seed(42)


def test_roll_range() -> list[str]:
    errors = []
    for _ in range(200):
        r = roll_dice()
        if not (1 <= r <= DICE_FACES):
            errors.append(f"roll_dice out of range: {r}")
    return errors


def test_odd_even() -> list[str]:
    expected = {1: "odd", 2: "even", 3: "odd", 4: "even", 5: "odd", 6: "even"}
    errors = []
    for n in range(1, DICE_FACES + 1):
        if dice_odd_even(n) != expected[n]:
            errors.append(f"dice_odd_even({n}) wrong")
    return errors


def test_double() -> list[str]:
    expected = {1: False, 2: True, 3: False, 4: True, 5: False, 6: True}
    errors = []
    for n in range(1, DICE_FACES + 1):
        if dice_double(n) != expected[n]:
            errors.append(f"dice_double({n}) wrong")
    return errors


def test_is_high() -> list[str]:
    expected = {1: False, 2: False, 3: False, 4: True, 5: True, 6: True}
    errors = []
    for n in range(1, DICE_FACES + 1):
        if dice_is_high(n) != expected[n]:
            errors.append(f"dice_is_high({n}) wrong")
    return errors


def test_is_high_custom_midpoint() -> list[str]:
    expected = {1: False, 2: False, 3: False, 4: False, 5: True, 6: True}
    errors = []
    for n in range(1, DICE_FACES + 1):
        if dice_is_high(n, midpoint=4) != expected[n]:
            errors.append(f"dice_is_high({n}, mp=4) wrong")
    return errors


def test_select_by_parity_even_list() -> list[str]:
    opts = ["a", "b", "c", "d", "e", "f"]
    errors = []
    for roll in [1, 3, 5]:
        got = dice_select_by_parity(opts, roll)
        if got not in ["a", "b", "c"]:
            errors.append(f"odd roll {roll}: got {got}")
    for roll in [2, 4, 6]:
        got = dice_select_by_parity(opts, roll)
        if got not in ["d", "e", "f"]:
            errors.append(f"even roll {roll}: got {got}")
    seen = set(dice_select_by_parity(opts, r) for r in range(1, 7))
    if seen != set(opts):
        errors.append(f"not all reachable: {seen}")
    return errors


def test_select_by_parity_odd_list() -> list[str]:
    opts = ["a", "b", "c", "d", "e"]
    errors = []
    for roll in [1, 3, 5]:
        got = dice_select_by_parity(opts, roll)
        if got not in ["a", "b", "c"]:
            errors.append(f"odd roll {roll} on 5-list: got {got}")
    for roll in [2, 4, 6]:
        got = dice_select_by_parity(opts, roll)
        if got not in ["d", "e"]:
            errors.append(f"even roll {roll} on 5-list: got {got}")
    return errors


def test_select_by_parity_single() -> list[str]:
    for roll in range(1, 20):
        if dice_select_by_parity(["only"], roll) != "only":
            return [f"single-element roll {roll} failed"]
    return []


def test_select_by_parity_empty() -> list[str]:
    for roll in range(1, 10):
        if dice_select_by_parity([], roll) is not None:
            return [f"empty list roll {roll} failed"]
    return []


def test_statistical_distribution() -> list[str]:
    random.seed(42)
    counts = {i: 0 for i in range(1, DICE_FACES + 1)}
    for _ in range(2000):
        counts[roll_dice()] += 1
    expected = 2000 / DICE_FACES
    errors = []
    for face, count in counts.items():
        if abs(count - expected) > 60:
            errors.append(f"face {face}: {count} vs expected ~{expected:.0f}")
    return errors


def test_dice_interpret() -> list[str]:
    errors = []
    for n in range(1, DICE_FACES + 1):
        d = dice_interpret(n)
        if d["roll"] != n:
            errors.append(f"interpret roll mismatch: {d['roll']} vs {n}")
        if d["parity"] != dice_odd_even(n):
            errors.append(f"interpret parity mismatch for {n}")
        if d["is_double"] != dice_double(n):
            errors.append(f"interpret double mismatch for {n}")
        if d["is_high"] != dice_is_high(n):
            errors.append(f"interpret high mismatch for {n}")
    return errors


def test_dice_re_roll_no_condition() -> list[str]:
    errors = []
    for roll in range(1, DICE_FACES + 1):
        result = dice_re_roll(roll, condition=False, max_rerolls=3)
        if result != roll:
            errors.append(f"re_roll({roll}, False) returned {result}")
    return errors


def test_dice_re_roll_with_condition() -> list[str]:
    errors = []
    for roll in range(1, DICE_FACES + 1):
        result = dice_re_roll(roll, condition=True, max_rerolls=0)
        if result != roll:
            errors.append(f"re_roll({roll}, True, max=0) should return {roll}, got {result}")
    result = dice_re_roll(1, condition=True, max_rerolls=2)
    if not (1 <= result <= DICE_FACES):
        errors.append(f"re_roll returned out-of-range: {result}")
    return errors


def test_dice_threshold() -> list[str]:
    errors = []
    for n in range(1, DICE_FACES + 1):
        expected = n >= 4
        got = dice_threshold(n, threshold=4, high_is_aggressive=True)
        if got != expected:
            errors.append(f"threshold({n}, 4, agg=True): got {got}, expected {expected}")
    for n in range(1, DICE_FACES + 1):
        expected = n <= 3
        got = dice_threshold(n, threshold=3, high_is_aggressive=False)
        if got != expected:
            errors.append(f"threshold({n}, 3, agg=False): got {got}, expected {expected}")
    return errors


def test_dice_interpret_perspectives() -> list[str]:
    errors = []
    for n in range(1, DICE_FACES + 1):
        d_gk = dice_interpret(n, "gatekeeper")
        if "gatekeeper_risk" not in d_gk:
            errors.append(f"gatekeeper interpret missing gatekeeper_risk for {n}")
        d_opt = dice_interpret(n, "optimizer")
        if "optimizer_aggressiveness" not in d_opt:
            errors.append(f"optimizer interpret missing optimizer_aggressiveness for {n}")
        d_neu = dice_interpret(n, "neutral")
        if "gatekeeper_risk" in d_neu or "optimizer_aggressiveness" in d_neu:
            errors.append(f"neutral interpret should not have agent-specific keys for {n}")
    return errors


def main() -> int:
    tests = [
        ("roll_range (200 rolls)", test_roll_range),
        ("odd_even correctness", test_odd_even),
        ("double status", test_double),
        ("is_high threshold", test_is_high),
        ("is_high custom midpoint", test_is_high_custom_midpoint),
        ("select_by_parity even list", test_select_by_parity_even_list),
        ("select_by_parity odd list", test_select_by_parity_odd_list),
        ("select_by_parity single element", test_select_by_parity_single),
        ("select_by_parity empty", test_select_by_parity_empty),
        ("statistical distribution (2000 rolls)", test_statistical_distribution),
        ("dice_interpret correctness", test_dice_interpret),
        ("dice_re_roll no condition", test_dice_re_roll_no_condition),
        ("dice_re_roll with condition", test_dice_re_roll_with_condition),
        ("dice_threshold", test_dice_threshold),
        ("dice_interpret perspectives", test_dice_interpret_perspectives),
    ]

    total_errors = 0
    total_tests = 0
    for name, test_fn in tests:
        total_tests += 1
        errors = test_fn()
        if errors:
            total_errors += len(errors)
            print(f"[FAIL] {name}: {len(errors)} error(s)")
            for e in errors[:3]:
                print(f"  - {e}")
            if len(errors) > 3:
                print(f"  ... ({len(errors) - 3} more)")
        else:
            print(f"[PASS] {name}")

    print(f"\n{'='*60}")
    print(f"Results: {total_tests - total_errors}/{total_tests} tests passed")
    if total_errors:
        print(f"FAILED: {total_errors} error(s)")
        return 1
    print("ALL GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
