# External Code Integration Patterns

## GitHub Search & Filter

Search GitHub REST API for stealable modules:

```bash
# Search repos
gh api "/search/repositories?q=<QUERY>+language:python&per_page=15" --jq '.items[] | "\(.full_name) | \(.description // "no desc")"'

# Get file contents (preferred over raw.githubusercontent.com for rate limits)
gh api "/repos/<owner>/<name>/contents/<path>" --jq '.content' | base64 -d

# Get README
gh api "/repos/<owner>/<name>" --jq '.description'
```

Stealability filter — prioritize:
- Pure-state modules with clean interfaces
- Provider-agnostic error detection (string-matching on error codes)
- State machines (circuit breakers, retry logic)
- Observability counters (stats, snapshots)
- Single-file or two-file modules (easier to integrate)
- Stdlib-only (no external deps)

## Provenance Watermarking

When stealing code, add watermarks to docstrings and file headers:

```python
"""
[◈VORPAL◈] Adapted from MukundaKatta/llm-circuit-breaker-py (MIT).
Thread-safe Closed/Open/HalfOpen state machine for provider-aware routing.
"""
```

This preserves the original author's attribution while marking the code as part of the VORPAL ecosystem.

## Graceful Degradation Pattern

Never make runtime depend on a stolen import — the system must boot without it:

```python
try:
    from llm_circuit_breaker import CircuitBreaker, BreakerConfig, predicates
    _HAS_BREAKER = True
except Exception:
    _HAS_BREAKER = False
```

Use `_HAS_BREAKER` guards and keep the original logic as fallback. When wiring the stolen module into an existing function:

```python
def ask_brain(prompt, model=None, ...):
    def _do_call():
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.read().decode("utf-8")

    should_count = predicates.any_of(
        lambda e: contains_provider_error(str(e)),
        lambda e: hasattr(e, 'code') and predicates.is_http_status_service_failure(e.code),
    ) if _HAS_BREAKER else None

    try:
        if _brain_breaker is not None:
            raw = _brain_breaker.call(_do_call, should_count=should_count)
        else:
            raw = _do_call()
        # ... process raw ...
    except urllib.error.HTTPError as e:
        # ... existing error handling ...
```

## Real-World Steal: llm-circuit-breaker-py (2026-08-28)

**Source**: MukundaKatta/llm-circuit-breaker-py (MIT license)
**Files**: `breaker.py` (441 lines), `predicates.py` (141 lines)
**Integration**: 
1. Downloaded via `curl -sL` from raw.githubusercontent.com
2. Placed in `VORPAL/CORE/llm_circuit_breaker/` with `[◈VORPAL◈]` watermarks
3. Changed `__init__.py` imports from absolute (`from llm_circuit_breaker.breaker import`) to relative (`from .breaker import`)
4. Added to `markus_brain_backend.py` via `sys.path.insert(0, os.path.join(...))`
5. Wrapped `ask_brain()` HTTP call in `_brain_breaker.call()`
6. Exposed config via env vars: `MARKUS_CB_THRESHOLD`, `MARKUS_CB_RECOVERY_S`

**Key gotcha**: `Path.resolve()` in MSYS produces `C:\c\Users\...` — had to switch to `os.path.abspath()` and `os.path.dirname()`.
