"""hermes_verify_plasmid_ast.py — AURORAL epistemic audit of PLASMIDS/ast_transform_fast.plasmid.py.

Verifies the plasmid's AST invariants (provenance: EXECUTE_GOAL PLASMID_AUDIT from omniprime,
packet 978d82bac54c, cycle 33). Each invariant is checked against ast.parse ground truth.

Invariants under test:
  I1  SyntaxError propagation  — invalid source raises SyntaxError (not swallowed).
  I2  Name fidelity            — extracted function/class names equal ast.parse ground truth.
  I3  Lineno fidelity          — extracted lineno equals the AST node's lineno.
  I4  Traversal completeness   — ast.walk finds nested defs; all present in output.
  I5  Arg capture              — positional args (a.arg) captured, in order, matching AST.
  I6  Purity                   — input string is not mutated (pure function).
  I7  Empty module             — empty source yields empty signatures (no crash).
  I8  Shape                    — returns {"functions": [...], "classes": [...]} of dicts.

Scope note (not an invariant violation): the plasmid captures only node.args.args
(positional-or-keyword args); kwonlyargs / vararg / kwarg are out of its stated
"fast traversal" scope. Flagged as an observation, not a gate failure.
"""

import ast
import importlib.util
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLASMID = ROOT / "PLASMIDS" / "ast_transform_fast.plasmid.py"

# Dotted filename (ast_transform_fast.plasmid.py) can't be imported by name —
# load the file directly via importlib.
_spec = importlib.util.spec_from_file_location("ast_transform_fast_plasmid", PLASMID)
plasmid = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plasmid)

failures = []


def check(name: str, cond: bool, detail: str = ""):
    mark = "PASS" if cond else "FAIL"
    print(f"[AUDIT] {mark}  {name}" + (f"  -- {detail}" if detail else ""))
    if not cond:
        failures.append(name)


# --- compile gate -----------------------------------------------------------
try:
    compile(PLASMID.read_text(encoding="utf-8"), str(PLASMID), "exec")
    check("I0 py_compile", True, "plasmid compiles clean")
except SyntaxError as e:
    check("I0 py_compile", False, f"SyntaxError: {e}")

# --- I7 empty module ---------------------------------------------------------
try:
    empty = plasmid.extract_ast_signatures("")
    check("I7 empty module", empty == {"functions": [], "classes": []}, str(empty))
except Exception as e:
    check("I7 empty module", False, f"raised {type(e).__name__}: {e}")

# --- rich sample -------------------------------------------------------------
SAMPLE = '''
import os
from typing import List

CONST = 42

def plain(a, b, c=3):
    return a + b + c

def fancy(x, *args, key=None, **kwargs):
    return x

class Base:
    attr = 1
    def method(self, p, q=2):
        return p * q

class Derived(Base):
    def inner(self):
        def nested_helper(z):
            return z + 1
        return nested_helper

@decorator
def wrapped(t):
    return t
'''

tree = ast.parse(SAMPLE)
# Ground truth via independent ast.walk.
gt_fns = [(n.name, n.lineno) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
gt_cls = [(n.name, n.lineno) for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

# I4 traversal completeness — ground-truth counts must match.
out = plasmid.extract_ast_signatures(SAMPLE)
check("I4 completeness functions", len(out["functions"]) == len(gt_fns),
      f"{len(out['functions'])} vs ground-truth {len(gt_fns)}")
check("I4 completeness classes", len(out["classes"]) == len(gt_cls),
      f"{len(out['classes'])} vs ground-truth {len(gt_cls)}")

# I2 + I3 fidelity: compare extracted tuples to ground truth.
got_fns = {(f["name"], f["lineno"]) for f in out["functions"]}
got_cls = {(c["name"], c["lineno"]) for c in out["classes"]}
check("I2/I3 function name+lineno fidelity", got_fns == set(gt_fns),
      f"missing {set(gt_fns) - got_fns}")
check("I2/I3 class name+lineno fidelity", got_cls == set(gt_cls),
      f"missing {set(gt_cls) - got_cls}")

# I5 arg capture: 'plain' positional args == ['a','b','c'] in order.
plain = next(f for f in out["functions"] if f["name"] == "plain")
check("I5 positional arg capture", plain["args"] == ["a", "b", "c"], str(plain["args"]))

# I1 SyntaxError propagation.
try:
    plasmid.extract_ast_signatures("def broken(:\n    pass")
    check("I1 SyntaxError propagates", False, "invalid source did not raise")
except SyntaxError:
    check("I1 SyntaxError propagates", True, "SyntaxError raised as documented")
except Exception as e:
    check("I1 SyntaxError propagates", False, f"raised {type(e).__name__}, not SyntaxError")

# I6 purity — input unchanged.
src_copy = SAMPLE
plasmid.extract_ast_signatures(src_copy)
check("I6 purity", src_copy == SAMPLE, "input string unmodified")

# I8 shape.
check("I8 shape", isinstance(out["functions"], list) and isinstance(out["classes"], list)
      and all(isinstance(f, dict) for f in out["functions"]), "list-of-dict shape")

print(f"\nVERIFICATION: {'ALL PLASMID AST INVARIANTS PASS' if not failures else f'{len(failures)} INVARIANTS FAILED: {failures}'}")
raise SystemExit(1 if failures else 0)
