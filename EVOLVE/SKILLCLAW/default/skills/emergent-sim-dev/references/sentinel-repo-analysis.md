# Sentinel Repo Analysis — Reusable Components for ARISE

**Repo**: `jonnysteedman683-wq/sentinel-main` (private)
**Stack**: TypeScript, React 19, TF.js, Firebase, XState
**Clone**: `git clone https://github.com/jonnysteedman683-wq/sentinel-main.git`

## High-Value Components

### 1. Options Framework (`src/lib/options.ts`)
Hierarchical RL — agents adopt multi-step strategies instead of single actions.

```typescript
interface Option {
  id: string;
  name: string;
  policy: QNetwork;
  actionSpace: string[];
  maxDuration: number;
  canInitiate(state: number[]): boolean;
  terminationProbability(state: number[]): number;
  get_action(state: number[], epsilon?: number): number;
}
```

**Concrete options**: IdleExplorer (NUDGE/INSIGHT), DeepConsolidator (CONSOLIDATE/CONSOLIDATE_CHATS), HybridSyncRAG, SystemSelfRepair.

**ARISE use**: Warriors adopt "hunt" option (approach→attack→retreat), farmers adopt "cultivate" option (plant→tend→harvest), scouts adopt "explore" option (move→scan→report). Each option has its own Q-network and termination condition.

**Porting**: Convert TypeScript interfaces to Python dataclasses. Replace TF.js QNetwork with our NumPy QNetwork. `canInitiate()` maps to role-based conditions. `terminationProbability()` maps to drive decay.

### 2. QuadTree Spatial Partitioning (`src/lib/spatial-lod-manager.ts`)
Dynamic QuadTree with LOD for spatial queries.

```typescript
class QuadTreeNode {
  bounds: QuadTreeBounds;
  capacity: number;
  nodes: SpatialNode[];
  children: QuadTreeNode[];
  subdivide(): void;
  insert(node: SpatialNode): void;
  query(range: QuadTreeBounds): SpatialNode[];
}
```

**ARISE use**: Replace grid-based spatial indexing for agent-agent queries, signal perception, resource lookups. QuadTree is O(log n) vs grid's O(n/k) — better for uneven distributions.

**Porting**: ~200 lines of TypeScript → Python. Key methods: `subdivide()`, `insert()`, `query()`. Use for nearest-agent, nearest-food, signal perception.

### 3. World Model (`src/lib/world-model.ts`)
Dreamer-style GRU world model with latent variables.

```typescript
class WorldModel {
  predictStep(state, action, prevHidden?): {
    nextStateMean, nextStateLogVar,
    reward, done, latentMean, latentLogVar, hidden
  }
}
```

Architecture: stateEmbed + actionEmbed → GRU → latent distribution → decoder (next_state, reward, done).

**ARISE use**: Agents can "imagine" futures before acting. "If I go left, I'll find food. If I go right, I'll find a mate." Dramatically smarter planning.

**Porting**: Replace TF.js with NumPy. GRU → simple RNN or skip temporal. Latent dim 16, embed dim 32. Train on agent experience tuples (state, action, next_state, reward).

### 4. Active Inference (`src/lib/active-inference.ts`)
Free Energy Principle agent with policy network.

```typescript
class ActiveInferenceAgent {
  selectAction(state): Promise<RLDecision & { efe: number; confidence?: number }>
}
```

Uses Expected Free Energy (EFE) to balance exploitation and exploration. Policy network with confidence thresholding (>0.6 = use policy, else plan).

**ARISE use**: Replace epsilon-greedy with EFE-based action selection. Agents minimize surprise, seek preferred states. More principled than random exploration.

### 5. Self-Healing Orchestrator (`src/lib/self-healing-orchestrator.ts`)
System health monitoring with RL-based maintenance.

```typescript
class SelfHealingOrchestrator {
  runCycle(): void {
    const metrics = SystemHealthCollector.getMetrics();
    const action = this.selectBestAction(state);
    await this.executeAction(action);
    // train model on (state, action, nextState) tuples
  }
}
```

**ARISE use**: Population self-regulation. Monitor agent health, food supply, genetic diversity. Trigger interventions (resource booms, migration nudges) when metrics drop below thresholds.

### 6. Debate Machine (`src/machines/debateMachine.ts`)
XState state machine for structured debates between agents.

Roles: Logician (analyzes), Catalyst (challenges), Auditor (verifies).
Flow: brainstorming → drafting → refining → finalizing.

**ARISE use**: Territory/resource conflicts resolved through structured debate instead of random combat. Winner determined by confidence scores.

### 7. Triangulation Engine (`src/lib/triangulation-engine.ts`)
Dual-kernel (Primary/Shadow) decision making with ethical constraints.

- Primary kernel: high plasticity, goal-focused
- Shadow kernel: deontological strictness, frozen reference
- Cognitive reframing loop with confidence decay
- Terminal humility fallback

**ARISE use**: Agent morality system. Primary kernel = survival instinct. Shadow kernel = ethical constraints (don't attack same-species, share with kin). Agents with stronger shadow kernels are more cooperative.

## Porting Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| 1 | Options Framework | Medium | High — dramatically smarter agents |
| 2 | QuadTree | Low | Medium — better performance |
| 3 | World Model | High | High — agent imagination |
| 4 | Active Inference | High | Medium — principled exploration |
| 5 | Self-Healing | Medium | Medium — population stability |
| 6 | Debate Machine | Medium | Medium — conflict resolution |
| 7 | Triangulation | High | Low — ethics overlay |
