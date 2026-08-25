#!/usr/bin/env python3
# hermes_verify_lingua_boot.py -- [ERR_LINGUA_BOOT_GAP] verification harness
# [OMNIPRIME-FORGE] | Lingua: a->b->t->V3
#
# Closes [ERR_LINGUA_BOOT_GAP] (VERIFICATION_LOG.md:117, triad-wide, OMNIPRIME
# sub-items). The degradation: LP dictionary stability was claimed while NO LP
# boot events existed, so the claim was VACUOUSLY true. A harness that only
# asserts "no contradictions found" over an empty event set proves nothing.
#
# Claims under attack:
#   L1  the canonical engine is where LINGUA.md says it is (no forks)
#   L2  boot() emits REAL LP events onto the bus (non-empty event set)
#   L3  the boot lexicon round-trips: encode -> decode == original concept
#   L4  the boot chain actually compresses (regression guard on [ERR_LP_NOCOMPRESS])
#   L5  ASCII-arrow chains compress too -- 'a -> b -> t' was a ratio-1.0 no-op
#   L6  dictionary fingerprint is STABLE across repeated cold boots
#   L7  NON-VACUITY: a perturbed dictionary yields a DIFFERENT fingerprint.
#       Without this the stability check would pass on a constant function.
#   L8  stability_report() self-declares vacuity instead of hiding it
#   L9  safety text (paths/commands) is NOT mangled by the compressor
#   L10 boot fails CLOSED (status F) when the engine is missing

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .../OMNIPRIME
BOOT_MODULE = ROOT / "lingua_boot.py"

PASSED = 0
FAILED = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {name}" + (f" -- {detail}" if detail else ""))
    else:
        FAILED += 1
        print(f"  [FAIL] {name}" + (f" -- {detail}" if detail else ""))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    print("=" * 64)
    print("HARNESS: hermes_verify_lingua_boot.py  ([ERR_LINGUA_BOOT_GAP])")
    print("=" * 64)

    if not BOOT_MODULE.exists():
        print(f"[FATAL] lingua_boot.py absent at {BOOT_MODULE}")
        return 1

    lb = load(BOOT_MODULE, "lingua_boot_under_test")

    # ---------- L1: canonical engine location ----------
    check("L1 canonical engine present at LINGUA.md path",
          lb.ENGINE_PATH.exists(),
          str(lb.ENGINE_PATH.relative_to(ROOT)).replace("\\", "/"))

    # ---------- L2: boot emits real events ----------
    before = len(lb.lp_events())
    rec = lb.boot(emit=True)
    after = len(lb.lp_events())
    emitted = after - before
    check("L2 boot emits real LP events onto the bus",
          rec.get("events_emitted", 0) > 0 and emitted == rec["events_emitted"],
          f"claimed={rec.get('events_emitted')} observed_on_bus=+{emitted} total={after}")

    check("L2b LP event set is NON-EMPTY (stability is non-vacuous)",
          after > 0, f"{after} LP events on bus")

    # ---------- L3: lexicon round-trip ----------
    lex = rec.get("lexicon", {})
    all_rt = bool(lex) and all(v.get("ok") for v in lex.values())
    check("L3 boot lexicon round-trips encode->decode",
          all_rt,
          " ".join(f"{k}={v.get('token')}" for k, v in lex.items()))

    # ---------- L4: boot chain compresses ----------
    chain = rec.get("chain", {})
    check("L4 boot chain compresses (ratio < 1.0)",
          bool(chain) and chain.get("ok") is True,
          f"'{chain.get('raw')}' -> '{chain.get('lingua')}' ratio={chain.get('ratio')}")

    # ---------- L5: ASCII arrow regression ([ERR_LP_NOCOMPRESS]) ----------
    lang = lb.load_engine().LinguaPrima()
    ascii_chain = "analyze -> build -> test"
    ascii_out = lang.compress_semantic_chain(ascii_chain)
    ascii_ratio = round(len(ascii_out) / len(ascii_chain), 3)
    unicode_out = lang.compress_semantic_chain("analyze then build then test")
    check("L5 ASCII-arrow chain compresses ([ERR_LP_NOCOMPRESS] closed)",
          ascii_ratio < 1.0,
          f"'{ascii_chain}' -> '{ascii_out}' ratio={ascii_ratio}")
    check("L5b ASCII and English spellings agree",
          ascii_out == unicode_out,
          f"ascii='{ascii_out}' english='{unicode_out}'")

    # ---------- L6: fingerprint stability across cold boots ----------
    prints = [lb.dictionary_fingerprint(lb.load_engine().LinguaPrima())
              for _ in range(5)]
    unique = set(prints)
    check("L6 dictionary fingerprint stable across 5 cold boots",
          len(unique) == 1,
          f"{len(unique)} unique fingerprint(s): {prints[0][:16]}...")

    # ---------- L7: NON-VACUITY -- perturbation must be detected ----------
    lang_mut = lb.load_engine().LinguaPrima()
    baseline = lb.dictionary_fingerprint(lang_mut)
    lang_mut._dict._tokens["\u00a7MUT"] = {
        "word": "harness_injected_probe", "category": "probe", "tier": 9,
        "source": "harness",
    }
    mutated = lb.dictionary_fingerprint(lang_mut)
    check("L7 NON-VACUITY: perturbed dictionary changes the fingerprint",
          mutated != baseline,
          f"{baseline[:12]}... != {mutated[:12]}...")

    lang_eph = lb.load_engine().LinguaPrima()
    base_eph = lb.dictionary_fingerprint(lang_eph)
    lang_eph.auto_alias("some_unknown_transient_concept")
    after_eph = lb.dictionary_fingerprint(lang_eph)
    check("L7b ephemeral auto_alias does NOT destabilise the fingerprint",
          after_eph == base_eph,
          "session aliases excluded from the stable surface")

    # ---------- L8: report declares vacuity honestly ----------
    rep = lb.stability_report(3, emit=False)
    check("L8 stability_report is explicit and non-vacuous",
          rep.get("vacuous") is False and rep.get("stable") is True
          and rep.get("samples") == 3 and rep.get("lp_events_on_bus", 0) > 0,
          json.dumps({k: rep[k] for k in
                      ("samples", "unique_fingerprints", "vacuous", "stable",
                       "lp_events_on_bus")}))

    single = lb.stability_report(1, emit=False)
    check("L8b single-sample report self-declares VACUOUS",
          single.get("vacuous") is True and single.get("stable") is False,
          f"samples=1 vacuous={single.get('vacuous')} stable={single.get('stable')}")

    # ---------- L9: safety text stays literal ----------
    safety = "C:/Users/jonny/OneDrive/Desktop/OMNIPRIME/scripts/bus_router.py"
    out = lang.compress_semantic_chain(safety)
    check("L9 safety text (a real path) survives unmangled",
          safety in out or out == safety,
          f"len {len(safety)} -> {len(out)}")

    # ---------- L10: fail closed when engine missing ----------
    tmp = Path(tempfile.mkdtemp(prefix="lp_gap_"))
    saved_engine, saved_bus, saved_events = lb.ENGINE_PATH, lb.BUS, lb.EVENTS
    try:
        lb.ENGINE_PATH = tmp / "absent_engine.py"
        lb.BUS = tmp / "bus"
        lb.EVENTS = lb.BUS / "events.jsonl"
        broken = lb.boot(emit=True)
        check("L10 boot fails CLOSED when engine is absent",
              broken.get("status") == "F" and "error" in broken,
              f"status={broken.get('status')} error={broken.get('error', '')[:48]}")
    finally:
        lb.ENGINE_PATH, lb.BUS, lb.EVENTS = saved_engine, saved_bus, saved_events
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    total = PASSED + FAILED
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed, {total} total")
    if FAILED == 0:
        print("[LINGUA-BOOT] PASS -- LP boots, emits real events, fingerprint stable "
              "AND perturbation-sensitive; [ERR_LINGUA_BOOT_GAP] closed non-vacuously")
    else:
        print("[LINGUA-BOOT] FAIL")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
