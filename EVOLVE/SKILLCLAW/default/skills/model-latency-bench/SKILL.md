---
name: model-latency-bench
description: Bench model latency (TTFB) after a switch to verify speed.
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [benchmark, latency, model, ttfb, performance]
    related_skills: [adaptive-model-switcher, hermes-upgrade-check]
---

# Model Latency Bench

Compare model speed empirically after a model switch, instead of trusting the spec sheet.

## When to Use
- User asks "is X faster than Y?" or "did my upgrade help?"
- After changing `hermes config set model` / provider.
- Deciding between models for cron jobs or interactive use.

## Method
1. Get the auth token from `$LOCALAPPDATA/hermes/auth.json` (recursive find for `access_token`).
2. POST to the provider's `/chat/completions` with a tiny prompt (`"Say OK"`, `max_tokens: 8`).
3. Time **TTFB** (`time_starttransfer`) and **total** (`time_total`) via `curl -w`.
4. Run **3 samples per model**, sleep ~1s between. Free models stall intermittently — more samples = more honest variance.
5. Report **avg / median / min / max / spread**.

## Pitfalls
- **urllib gets HTTP 403** on the Nous endpoint; plain `curl` works. Use curl for timing, don't fight the UA block.
- **First sample is often the slowest** (cold cache / server warm-up) — always run ≥3 and look at median + spread, not just sample 1.
- Free-tier models have huge variance. A 9s+ stall in one sample is normal; it's the **spread** that decides "which feels faster" for interactive use.
- `is_byok: True` in usage means it's burning the user's own API key, not subscription credits — note it when reporting cost.
- A model referenced in a previous session override may no longer be in `config.yaml` — check before benching it.

## Reporting
- Consistency beats burst for interactive/loop work: report which model has the *tightest* spread, not just the lowest median.
- Note whether it's a thinking model (reasoning tokens in usage) — those pay a TTFB tax by design.

## Verification
- After any switch, the check is: `hermes status` shows the new model + one timed curl round-trip returning HTTP 200.
