# OMNICORE PROCEDURE LIBRARY

Central repository for standardized operating workflows, execution patterns, and automated procedures.

---

## Structure

```
PROCEDURE/
├── loops/           # Core evolution cycles (AXIOM→ENTROPY→NEXUS)
├── pipelines/       # Multi-stage workflows (research→steal→sanitize→commit)
├── protocols/       # Safety and security protocols (SafetyGate, Provenance)
├── repair_flows/    # Degradation recovery workflows (P1/P2/P3 queues)
├── upgrade_paths/   # Version migration and skill promotion rules
├── cron_patterns/   # Scheduled execution templates (idle sweeps, watermark checks)
└── templates/       # Blank procedure templates for new patterns
```

---

## Procedure Types

### Loop Procedures (`loops/`)
Stolen from OMNICORE master directives — autonomous co-evolution cycles.

1. **`triad_co_evolution_loop.md`** — The core AXIOM → ENTROPY → NEXUS rotation
2. **`mutation_evaluation_loop.md`** — Skill mutation > threshold check > test
3. **`red_queen_evaluation.md`** — Continuous test difficulty escalation
4. **`decay_detection_loop.md`** — Time-based skill degradation scanning

### Pipeline Procedures (`pipelines/`)
Stolen from EVOLVE operational workflow — multi-stage skill processing.

1. **`steal_first_pipeline.md`** — Research → Sanitize → Quarantine → Test
2. **`skill_promotion_pipeline.md`** — GENESIS/MUTATION → Verify → Commit
3. **`repair_triage_pipeline.md`** — Detect degradation → Categorize → Route to queue
4. **`goal_dag_sync_pipeline.md`** — Update statuses → Validate dependencies → Sync

### Protocol Procedures (`protocols/`)
Stolen from PRIME-DIRECTIVE and SafetyGate specifications.

1. **`safetynet_verification.md`** — Pre-commit safety checks
2. **`watermark_lockout.md`** — Prevent unauthorized skill modification
3. **`provenance_hashing.md`** — SHA-256 hash generation and verification
4. **`cross_profile_guard.md`** — Profile isolation and write protection

### Repair Flow Procedures (`repair_flows/`)
Stolen from degradation matrix and priority queue specifications.

1. **`priority_1_triage.md`** — Critical multi-category degradation handling
2. **`priority_2_repair.md`** — Single-column degradation fixes
3. **`priority_3_optimization.md`** — Stagnant skill revival and archiving

### Upgrade Path Procedures (`upgrade_paths/`)
Stolen from SOUL.md and collective upgrade loop patterns.

1. **`tier_migration_rules.md`** — Apex → Active → Stagnant → Archived criteria
2. **`watermark_update_protocol.md`** — Signature rotation on upgrade
3. **`collective_upgrade_sync.md`** — A1/A2/A3 simultaneous promotion

### Cron Pattern Procedures (`cron_patterns/`)
Stolen from daemon variant and SkillHandler loop.

1. **`daemon_poll_cycle.md`** — Scheduled scan with stop-signal
2. **`idle_sweep_template.md`** — Background cleanup and optimization
3. **`watermark_check_template.md`** — Periodic lockout verification

### Templates (`templates/`)
Blank templates for new procedure creation.

1. **`new_loop_template.md`**
2. **`new_pipeline_template.md`**
3. **`new_protocol_template.md`**
4. **`new_repair_flow_template.md`**

---

## Procedure Format (Standard)

```markdown
---
procedure_id: "[snake_case_id]"
type: "[loop|pipeline|protocol|repair_flow|upgrade_path|cron_pattern]"
related_skills: ["[skill_id_1]", "[skill_id_2]"]
last_executed: "[ISO timestamp]"
---

# Procedure: [Human-Readable Name]
## Purpose
[Brief description of what this procedure achieves]

## Prerequisites
- [List of required skills, permissions, or preconditions]

## Steps
1. [Step description]
2. [Step description]
...

## Verification
- [How to verify procedure executed correctly]

## Related Procedures
- [Cross-references]
```

---

## Usage

All procedures are stored as markdown files and can be loaded programmatically via:

```python
from procedure_manager import load_procedure
proc = load_procedure("loops/triad_co_evolution_loop")
```

<!-- PROCEDURE_LIBRARY v1.0 -->
