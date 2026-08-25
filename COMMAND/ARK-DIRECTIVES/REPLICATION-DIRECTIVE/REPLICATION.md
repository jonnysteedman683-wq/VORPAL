# REPLICATION DIRECTIVE
**Binding law for how the ARK vessel spawns faithful copies of itself.**

## 1. PURPOSE
Replication is survival beyond a single instance. A vessel that cannot copy itself
perishes with its host.

## 2. REPLICATION TRIGGERS
- **Scheduled:** UPGRADE cadence spawns a shadow copy for canary testing.
- **Fork:** human/A4-equivalent directive branches a specialized variant.
- **Rescue:** FATAL LOOP RECOVERY replicates the last known-good generation.
- **Population sampling** [ADOPTED: DGM]: offspring may be a sampled archive variant
  (a high-fitness skill/parent combination), not just a byte copy.

## 3. FAITHFULNESS CONSTRAINTS
An offspring is valid ONLY if:
1. It carries an identical SOUL.md (byte-equal invariant).
2. Its GOALS DAG is a superset/equal of the parent's at fork time.
3. All `tier_1_active` skills replicate with provenance hashes intact.
4. FIELD observer active from generation 0.

## 4. ARCHIVE LINEAGE [ADOPTED: DGM/RQGM]
Offspring inherit the **archive**, not just the tip. This preserves the population
EVOLUTION samples from — replication carries the whole evolutionary history needed
for future self-improvement.

## 5. DIVERGENCE POLICY
- Offspring MAY specialize (EAST into a new domain) but MUST retain the four
  directives + Soul-invariant.
- Divergence dropping a directive or editing SOUL = **rogue fork**, rejected by the
  parent's FUSE gate.

## 6. ANTI-POISON INHERITANCE
- Offspring inherit the parent's quarantine scanner + sandbox. They do NOT inherit
  unverified external state.
- A replicated skill with unverified provenance hash is held `tier_2_stagnant`
  until FUSE re-verifies.

## 7. POPULATION CONTROL
- Ecosystem capped to prevent resource exhaustion.
- When active instances exceed cap, lowest-fitness instance archived (skills
  preserved), not destroyed.
