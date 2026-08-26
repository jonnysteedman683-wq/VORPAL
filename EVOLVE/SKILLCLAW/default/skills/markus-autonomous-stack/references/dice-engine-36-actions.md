# Markus DICE Engine — 36 Action Catalog (Upgrade 48)
Version: 2026-08-26
Status: ACTIVE

## Overview

The MARKUS DICE engine provides 36 deterministic upgrade actions, each mapped to a specific dice roll (1-36). The engine uses dual 6-sided dice rolled cryptographically.

## Action Catalog

```
Dice 1 \ Dice 2 | Action ID | Label | Description
----------------|-----------|-------|------------------
    1 \ 1       | 1 | UPGRADE_UI_ACCESSIBILITY | UI Refresh with Accessibility Overhaul
    1 \ 2       | 2 | UPGRADE_BACKEND_API        | Backend Refactor + API Expansion  
    1 \ 3       | 3 | UPGRADE_AI_MODEL           | AI Agent Model Swap & Prompt Optimization
    1 \ 4       | 4 | IMPLEMENT_FEATURE_GAP      | Feature Gap Analysis & Implementation
    1 \ 5       | 5 | TECHNICAL_ALTERNATIVE_EVAL | Technical Alternative Evaluation
    1 \ 6       | 6 | RE_ROLL_COOLDOWN           | Re-Roll (reset to uniform distribution)

    2 \ 1       | 7 | UPGRADE_UI_LOCALIZATION    | UI Localization & Theming Suite
    2 \ 2       | 8 | UPGRADE_DB_SCHEMA          | Database Schema Migration & Indexing
    2 \ 3       | 9 | ENHANCE_CORETEX            | Cognitive Cortex Enhancement
    2 \ 4       | 10 | SECURITY_HARDENING         | Security Hardening & Audit Suite
    2 \ 5       | 11 | PERFORMANCE_OPTIMIZE       | Performance Profiling & Optimization
    2 \ 6       | 12 | RE_ROLL_EXPLORATION        | Re-Roll (exploration mode)

    3 \ 1       | 13 | DEPLOY_OBSERVABILITY       | Observability Stack Deployment
    3 \ 2       | 14 | CACHE_INVALIDATION         | Cache Invalidation & Warmup
    3 \ 3       | 15 | UPDATE_DEPENDENCIES        | Dependency Update & Compatibility
    3 \ 4       | 16 | REFRESH_DASHBOARD          | Monitoring Dashboard Refresh
    3 \ 5       | 17 | TUNE_RATE_LIMITER          | Rate Limiter & Throttle Tuning
    3 \ 6       | 18 | RE_ROLL_STRATEGIC          | Re-Roll (strategic pause)

    4 \ 1       | 19 | EXPAND_INTEGRATIONS        | Integration Expansion Pack
    4 \ 2       | 20 | BOOST_EVENT_DRIVEN         | Event-Driven Architecture Boost
    4 \ 3       | 21 | ENHANCE_STREAMING          | Real-time Streaming Pipeline
    4 \ 4       | 22 | MODERNIZE_QUEUE            | Queue System Modernization
    4 \ 5       | 23 | SCALE_WORKER_POOL          | Worker Pool Scaling
    4 \ 6       | 24 | RE_ROLL_RESOURCE           | Re-Roll (resource rebalance)

    5 \ 1       | 25 | EXTEND_TEST_SUITE          | Edge Case & Boundary Test Suite
    5 \ 2       | 26 | VALIDATE_API_CONTRACT      | API Contract & Schema Validation
    5 \ 3       | 27 | CHECK_DATA_INTEGRITY       | Data Integrity & Corruption Check
    5 \ 4       | 28 | RUN_BACKUP_DRILL           | Backup & Recovery Drill
    5 \ 5       | 29 | SIMULATE_DR                | Disaster Recovery Simulation
    5 \ 6       | 30 | RE_ROLL_CRITICAL           | Re-Roll (critical systems)

    6 \ 1       | 31 | REFACTOR_DOCS              | Documentation Refactor & Audit
    6 \ 2       | 32 | OVERHAUL_CODE_QUALITY      | Code Quality & Lint Overhaul
    6 \ 3       | 33 | PAYDOWN_TECH_DEBT          | Technical Debt Paydown Sprint
    6 \ 4       | 34 | ARCHITECTURE_REVIEW        | Architecture Review & Refactor
    6 \ 5       | 35 | EXPAND_KNOWLEDGE_BASE      | Knowledge Base Expansion
    6 \ 6       | 36 | RE_ROLL_SYSTEM_RESET       | Re-Roll (system-wide reset)
```

## Implementation Details

### Dice Engine API (`markus_dice_engine.py`)

```python
from markus_dice_engine import MarkusDiceEngine

dice = MarkusDiceEngine()

# Roll a cryptographic die (1-36)
roll_id = dice.roll_cryptographic_dice()

# Get action label
label = dice.get_action_label(roll_id)

# Execute upgrade for specific roll
result = await dice.execute_upgrade_action(roll_id)
```

### Upgrade Execution Map

| Roll ID | Upgrade Method | Target Files |
|---------|---------------|--------------|
| 1 | `_upgrade_ui_accessibility()` | markus_chat.html, markus-os.html |
| 2 | `_upgrade_backend_api()` | phoenix_cli.py batch . |
| 3 | `_upgrade_ai_model()` | markus_kernel.py |
| 4 | `_implement_feature_gap()` | markus_devswarm.py |
| 5 | `_evaluate_alternative()` | markus_router.py |
| 6 | `RE_ROLL_COOLDOWN` | N/A (control) |
| 7 | `_upgrade_ui_localization()` | markus-os.html |
| 8 | `_upgrade_db_schema()` | markus_db.py |
| 9 | `_enhance_cortex()` | markus_cortex_replication.py |
| 10 | `_run_security_audit()` | markus_resilience.py |
| 11 | `_run_perf_profile()` | markus_latency_multi_upgrade.py |
| 12 | `RE_ROLL_EXPLORATION` | N/A (control) |
| ... | ... | ... |

## Log Format

Upgrade cycle logs are written to `~/.hermes/cron_log/`:

```json
{
  "cycle_id": "upgrade_1787722639",
  "timestamp": "2026-08-26 15:37:32",
  "dice_roll": 33,
  "action": "PAYDOWN_TECH_DEBT",
  "stages": [...],
  "validation_passed": true,
  "health_passed": true,
  "devswarm_healthy": true,
  "skill_patches": 0,
  "reward": 1.0,
  "elapsed_ms": 13062.76
}
```

## Common Roll Sequences

| Roll | Likely Interpretation | Typical Next Action |
|------|----------------------|---------------------|
| 33 | Technical Debt Paydown | Good follow-up: 34 (Architecture Review) |
| 29 | DR Simulation | Pair with: 28 (Backup Drill) or 27 (Data Integrity) |
| 11 | Performance Optimize | Pair with: 10 (Security) or 12 (Re-Roll Exploration) |
| 5 | Tech Alternative Eval | Research phase: document findings, plan migration |