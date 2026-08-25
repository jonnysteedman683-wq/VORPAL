"""
OMNICORE Prompt Randomizer Engine v1.0

Bilingual prompt randomizer that ingests both English and Lingua Prima encoded concepts,
integrates with the auto-dice roller engine to generate random upgrade prompts for
downstream AI systems (not yet built).

Stolen from:
  - OMNICORE-A1/lib/upgrade_registry.ts (dice options 1-6, upgrade manifest patterns)
  - apex/core/idea_engine.py (dual-dice algorithm, roll history tracking)
  - LANGUAGE/lingua_prima.py (compress/expand, bilingual encoding)
  - auto_steal_engine.py (auto-steal patterns for upgrade target generation)

Design:
  1. Accept input in English or Lingua Prima encoded tokens
  2. Auto-detect language and decompress if needed
  3. Roll dual-dice to determine prompt category + intensity
  4. Select from 6 dice options (matching markus_dice_engine pattern)
  5. Generate structured prompt with metadata
  6. Track roll history for co-evolution feedback
"""
import random
import json
import os
import time
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

# === STOLE FROM: apex/core/idea_engine.py — dual-dice algorithm ===
@dataclass
class DiceRoll:
    """Result of a dual-dice roll — determines prompt category + intensity."""
    die_a: int  # Category selector (1-6)
    die_b: int  # Intensity modifier (1-6)
    combo: Tuple[int, int] = field(init=False)
    category: str = field(init=False)
    intensity: float = field(init=False)
    
    def __post_init__(self):
        self.combo = (self.die_a, self.die_b)
        self.category = DICE_CATEGORIES[self.die_a]
        # Intensity: 0.5 to 1.0 based on die_b
        self.intensity = 0.4 + (self.die_b - 1) * 0.12  # Range: 0.4 to 1.0 (die_b 1→0.4, 6→1.0)


# === STOLE FROM: OMNICORE-A1/lib/upgrade_registry.ts — dice options ===
DICE_CATEGORIES = {
    1: "upgrade_ui",           # Upgrade UI/Frontend
    2: "upgrade_backend",      # Upgrade Backend/API
    3: "upgrade_ai_agent",     # Upgrade AI Agent/Skill
    4: "find_missing",         # Find Something Missing
    5: "technical_alt",        # Technical Alternative Upgrade
    6: "reroll",               # Re-Roll
}

# === STOLE FROM: idea_engine.py — idea tiers ===
IDEA_TIERS = {
    1: ("nova", "revolutionary breakthrough"),
    2: ("spark", "creative extension"),
    3: ("refine", "incremental improvement"),
    4: ("harden", "security/stability fix"),
    5: ("optimize", "performance tuning"),
    6: ("audit", "quality/compliance check"),
}

# === STOLE FROM: lingua_prima.py — bilingual prompt templates ===
BILINGUAL_TEMPLATES = {
    "upgrade_ui": {
        "english": "Redesign the {component} UI with {framework} integration. "
                   "Focus on {intensity_desc} visual polish and user experience. "
                   "Target: {target}",
        "symbolic": "🧠🔧 {component} UI → {framework}. "
                    "🎯 {intensity_desc} UX. 🌍↔ {target}",
    },
    "upgrade_backend": {
        "english": "Refactor the {component} backend service. "
                   "Implement {pattern} pattern with {tech_stack}. "
                   "Add: {features_list}. Security: {security_focus}.",
        "symbolic": "💾🔧 {component} → {pattern} + {tech_stack}. "
                    "✨ {features}. 🛡 {security}.",
    },
    "upgrade_ai_agent": {
        "english": "Enhance the {component} AI agent. "
                   "Add skill: {skill_name}. "
                   "Improvement: {improvement_desc}. "
                   "Metric: {metric}.",
        "symbolic": "🧠🔮 {component} → 🌱 {skill}. "
                    "📈 {improvement}. 📊 {metric}.",
    },
    "find_missing": {
        "english": "Audit {component} for missing capabilities. "
                   "Priority: {priority}. "
                   "Gap: {gap_desc}. "
                   "Suggested fix: {fix}.",
        "symbolic": "🔍 {component} → ⚠ {priority}. "
                    "🕳 {gap}. 🔧 {fix}.",
    },
    "technical_alt": {
        "english": "Explore alternative implementation for {component}. "
                   "Current tech: {current}. "
                   "Alternative: {alternative}. "
                   "Benefit: {benefit}.",
        "symbolic": "🔄 {component}: {current} → {alternative}. "
                    "🏆 {benefit}.",
    },
    "reroll": {
        "english": "Insufficient context. Re-rolling with expanded entropy.",
        "symbolic": "🎲 ↻",
    },
}

# === STOLE FROM: auto_steal_engine.py — upgrade target candidates ===
UPGRADE_TARGETS = [
    "SafetyGate", "CostAwareRouter", "EventBus", "Dispatcher",
    "CircuitBreaker", "HealthWatchdog", "TriAgenticKernel",
    "ThorsThornsEngine", "DefensiveEngine", "AutoStealEngine",
    "LinguaPrimaTokenizer", "PyramidWalker", "StateMemoryManager",
    "TokenCompressor", "A1Gatekeeper", "A2Optimizer", "A3Architect",
    "A4Editor", "P2PStateRegistry", "A4Synthesizer",
    "PipelineSkills", "AuditLogger", "ObservabilityLayer",
]

TECH_STACKS = [
    "FastAPI + Redis", "Starlette + SQLite", "Flask + Celery",
    "Django + PostgreSQL", "Node.js + Express", "Go + Gin",
    "Rust + Actix", "Python + Ray", "TypeScript + Hono",
]

FRAMEWORKS = [
    "React + Tailwind", "Vue 3 + Vite", "SvelteKit",
    "Next.js 15", "Astro.build", "Svelte + DaisyUI",
]

SECURITY_FOCUSES = [
    "input sanitization + rate limiting",
    "JWT + PKCE auth flows",
    "CSP + X-Frame-Options",
    "SQL injection prevention + prepared statements",
    "end-to-end encryption + key rotation",
]


class PromptRandomizer:
    """
    Bilingual prompt randomizer integrating auto-dice roller engine.
    
    Ingests English or Lingua Prima encoded concepts, auto-detects language,
    decompresses if needed, then rolls dual-dice to generate structured
    upgrade prompts for downstream AI systems.
    
    Stolen from: OMNICORE-A1/lib/upgrade_registry.ts (dice options),
                 idea_engine.py (dual-dice algorithm),
                 lingua_prima.py (bilingual encoding)
    """
    
    def __init__(self, lang_path: str = None):
        """
        Initialize prompt randomizer.
        
        Args:
            lang_path: Path to Lingua Prima dictionary for bilingual support.
                      If None, uses default OMNICORE dictionary location.
        """
        self._roll_history: List[Dict] = []
        self._prompt_history: List[Dict] = []
        self._rng_entropy = random.SystemRandom()
        
        # Load Lingua Prima if available
        self._lang = None
        if lang_path:
            sys_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "LANGUAGE"
            )
            if sys_path not in os.sys.path:
                os.sys.path.insert(0, sys_path)
            try:
                from lingua_prima import LinguaPrima
                self._lang = LinguaPrima(lang_path=lang_path)
            except ImportError:
                pass
    
    def _roll_dice(self) -> DiceRoll:
        """Roll dual dice using cryptographic entropy."""
        die_a = self._rng_entropy.randint(1, 6)
        die_b = self._rng_entropy.randint(1, 6)
        roll = DiceRoll(die_a=die_a, die_b=die_b)
        
        # Track roll history (stolen from idea_engine.py pattern)
        self._roll_history.append({
            "combo": roll.combo,
            "category": roll.category,
            "intensity": roll.intensity,
            "timestamp": time.time(),
        })
        return roll
    
    def _detect_language(self, text: str) -> str:
        """
        Detect if input is English or Lingua Prima encoded.
        
        Stolen from: lingua_prima.py compress/expand logic.
        """
        # Check for Lingua Prima Unicode symbols
        unicode_symbols = ["🧠", "💾", "🌍", "🎯", "🔄", "🔍", "☉", "★",
                          "∧", "∨", "∈", "⊕", "∂", "¬", "√", "∞", "∴", "∵"]
        for sym in unicode_symbols:
            if sym in text:
                return "lingua_prima"
        return "english"
    
    def _decompress_if_needed(self, text: str) -> str:
        """
        Decompress Lingua Prima encoded text to English.
        
        Stolen from: lingua_prima.py expand() method.
        """
        lang = self._detect_language(text)
        if lang == "english":
            return text
        
        # Try to use Lingua Prima engine
        if self._lang:
            return self._lang.expand(text)
        return text
    
    def _generate_prompt_content(self, roll: DiceRoll, context: str) -> Dict[str, str]:
        """Dispatch to per-category prompt generators."""
        if roll.category == "reroll":
            return self._gen_reroll()
        if roll.category == "upgrade_ui":
            return self._gen_upgrade_ui(roll, context)
        if roll.category == "upgrade_backend":
            return self._gen_upgrade_backend(roll, context)
        if roll.category == "upgrade_ai_agent":
            return self._gen_upgrade_ai_agent(roll, context)
        if roll.category == "find_missing":
            return self._gen_find_missing(roll, context)
        if roll.category == "technical_alt":
            return self._gen_technical_alt(roll, context)
        return self._gen_fallback(roll, context)

    def _gen_reroll(self) -> Dict[str, str]:
        return {
            "english": BILINGUAL_TEMPLATES["reroll"]["english"],
            "symbolic": BILINGUAL_TEMPLATES["reroll"]["symbolic"],
        }

    def _gen_upgrade_ui(self, roll: DiceRoll, context: str) -> Dict[str, str]:
        tier_desc = IDEA_TIERS.get(roll.die_b, ("spark", "creative"))[1]
        target = self._rng_entropy.choice(UPGRADE_TARGETS)
        framework = self._rng_entropy.choice(FRAMEWORKS)
        t = BILINGUAL_TEMPLATES["upgrade_ui"]
        return {
            "english": t["english"].format(component=target, framework=framework,
                                           intensity_desc=tier_desc, target=context[:50]),
            "symbolic": t["symbolic"].format(component=target, framework=framework,
                                             intensity_desc=tier_desc, target=context[:30]),
        }

    def _gen_upgrade_backend(self, roll: DiceRoll, context: str) -> Dict[str, str]:
        tier_desc = IDEA_TIERS.get(roll.die_b, ("spark", "creative"))[1]
        target = self._rng_entropy.choice(UPGRADE_TARGETS)
        pattern = random.choice(["circuit-breaker", "event-sourced", "CQRS", "microservice", "serverless"])
        tech = self._rng_entropy.choice(TECH_STACKS)
        sec = self._rng_entropy.choice(SECURITY_FOCUSES)
        features = f"{tier_desc} capabilities with {roll.intensity:.1f} priority"
        t = BILINGUAL_TEMPLATES["upgrade_backend"]
        return {
            "english": t["english"].format(component=target, pattern=pattern, tech_stack=tech,
                                           features_list=features, security_focus=sec),
            "symbolic": t["symbolic"].format(component=target, pattern=pattern,
                                             tech_stack=tech, features=features, security=sec),
        }

    def _gen_upgrade_ai_agent(self, roll: DiceRoll, context: str) -> Dict[str, str]:
        tier_name, tier_desc = IDEA_TIERS.get(roll.die_b, ("spark", "creative"))
        target = self._rng_entropy.choice(UPGRADE_TARGETS)
        skill = f"{tier_name}_{target.lower()}_v{int(roll.intensity*10)}"
        improvement = f"{tier_desc} enhancement at {roll.intensity:.1f} intensity"
        metric = self._rng_entropy.choice(["accuracy", "latency", "token_efficiency",
                                           "test_coverage", "error_rate", "response_time"])
        t = BILINGUAL_TEMPLATES["upgrade_ai_agent"]
        return {
            "english": t["english"].format(component=target, skill_name=skill,
                                           improvement_desc=improvement, metric=metric),
            "symbolic": t["symbolic"].format(component=target, skill=skill,
                                             improvement=improvement, metric=metric),
        }

    def _gen_find_missing(self, roll: DiceRoll, context: str) -> Dict[str, str]:
        tier_name, tier_desc = IDEA_TIERS.get(roll.die_b, ("spark", "creative"))
        target = self._rng_entropy.choice(UPGRADE_TARGETS)
        priority = self._rng_entropy.choice(["critical", "high", "medium", "low"])
        gap = f"Missing {tier_desc} for {target}"
        fix = f"Implement {tier_name} module with error handling"
        t = BILINGUAL_TEMPLATES["find_missing"]
        return {
            "english": t["english"].format(component=target, priority=priority,
                                           gap_desc=gap, fix=fix),
            "symbolic": t["symbolic"].format(component=target, priority=priority,
                                             gap=gap, fix=fix),
        }

    def _gen_technical_alt(self, roll: DiceRoll, context: str) -> Dict[str, str]:
        tier_desc = IDEA_TIERS.get(roll.die_b, ("spark", "creative"))[1]
        target = self._rng_entropy.choice(UPGRADE_TARGETS)
        current = self._rng_entropy.choice(TECH_STACKS)
        alternative = random.choice(["Rust", "Go", "Zig", "Python+Numba", "C++"])
        benefit = f"{tier_desc} improvement, {roll.intensity*100:.0f}% better performance"
        t = BILINGUAL_TEMPLATES["technical_alt"]
        return {
            "english": t["english"].format(component=target, current=current,
                                           alternative=alternative, benefit=benefit),
            "symbolic": t["symbolic"].format(component=target, current=current,
                                             alternative=alternative, benefit=benefit),
        }

    def _gen_fallback(self, roll: DiceRoll, context: str) -> Dict[str, str]:
        tier_desc = IDEA_TIERS.get(roll.die_b, ("spark", "creative"))[1]
        target = self._rng_entropy.choice(UPGRADE_TARGETS)
        return {
            "english": f"Upgrade {target} with {tier_desc} focus. Context: {context[:100]}",
            "symbolic": f"🧠🔧 {target} → {tier_desc} ({roll.intensity:.1f})",
        }


    def generate_prompt(self, context: str = "", output_format: str = "english") -> Dict[str, Any]:
        """
        Main entry point: generate a random upgrade prompt.
        
        Flow:
          1. Ingest context (English or Lingua Prima)
          2. Decompress if Lingua Prima
          3. Roll dual-dice
          4. Handle reroll recursion (max 3 rolls)
          5. Generate bilingual prompt content
          6. Return structured payload
        
        Args:
            context: Input context (English or Lingua Prima encoded)
            output_format: "english", "symbolic", or "both"
            
        Returns:
            Structured prompt dictionary with metadata
        """
        # Step 1: Ingest + decompress
        decompressed = self._decompress_if_needed(context)
        
        # Step 2: Roll dice with reroll handling (max 3 rerolls)
        for attempt in range(3):
            roll = self._roll_dice()
            if roll.category != "reroll" or not context:
                break
        
        # Step 3: Generate prompt
        content = self._generate_prompt_content(roll, decompressed)
        
        # Select output format
        if output_format == "english":
            prompt = content["english"]
        elif output_format == "symbolic":
            prompt = content["symbolic"]
        else:
            prompt = content
        
        # Step 4: Build structured payload
        prompt_id = hashlib.sha256(
            f"{prompt}{time.time()}{len(self._prompt_history)}".encode()
        ).hexdigest()[:12]
        
        result = {
            "prompt_id": prompt_id,
            "prompt": prompt,
            "category": roll.category,
            "intensity": round(roll.intensity, 2),
            "tier": IDEA_TIERS.get(roll.die_b, ("unknown", ""))[0],
            "dice_combo": list(roll.combo),
            "language_detected": self._detect_language(context) if context else "none",
            "context_compressed": len(decompressed) > 0,
            "timestamp": time.time(),
            "roll_count": len(self._roll_history),
        }
        
        # Track in history
        self._prompt_history.append(result)
        return result
    
    def generate_batch(self, n: int = 5, context: str = "") -> List[Dict[str, Any]]:
        """
        Generate multiple random prompts in one batch.
        
        Stolen from: auto_steal_engine.py batch processing pattern.
        """
        prompts = []
        for _ in range(n):
            p = self.generate_prompt(context=context)
            prompts.append(p)
        return prompts
    
    def export_audit(self) -> Dict:
        """
        Export full audit log of all prompts generated.
        
        Stolen from: thors_thorns_engine.py audit_log pattern.
        """
        return {
            "total_prompts": len(self._prompt_history),
            "total_rolls": len(self._roll_history),
            "category_distribution": {
                cat: sum(1 for p in self._prompt_history if p["category"] == cat)
                for cat in DICE_CATEGORIES.values()
            },
            "roll_history": self._roll_history,
            "prompt_history": self._prompt_history,
        }
    
    def sync_to_obsidian(self, vault_path: str) -> bool:
        """
        Sync prompt generation history to Obsidian vault.
        
        Stolen from: thors_thorns_engine.py sync_to_obsidian + auto_steal_engine.py dual-persistence.
        """
        from datetime import datetime
        
        today = datetime.now().strftime("%Y-%m-%d")
        journal_path = Path(vault_path) / "Journal" / "OMNICORE" / f"{today}.md"
        
        lines = [
            f"# Prompt Randomizer Audit — {today}",
            "",
            f"## Summary",
            f"- Total prompts generated: {len(self._prompt_history)}",
            f"- Total dice rolls: {len(self._roll_history)}",
            "",
            "## Roll History",
        ]
        
        for roll in self._roll_history[-20:]:  # Last 20 rolls
            ts = datetime.fromtimestamp(roll["timestamp"]).strftime("%H:%M:%S")
            lines.append(f"- {ts} | {roll['category']} | intensity={roll['intensity']:.2f} | combo={roll['combo']}")
        
        lines.extend(["", "## Recent Prompts", ""])
        
        for p in self._prompt_history[-10:]:  # Last 10 prompts
            ts = datetime.fromtimestamp(p["timestamp"]).strftime("%H:%M:%S")
            lines.append(f"### {p['prompt_id']} @ {ts}")
            lines.append(f"- Category: `{p['category']}` | Intensity: {p['intensity']} | Tier: {p['tier']}")
            prompt_text = p['prompt']
            if isinstance(prompt_text, dict):
                prompt_text = prompt_text.get('english', str(prompt_text))
            lines.append(f"- Prompt: {prompt_text[:200]}")
            lines.append("")
        
        try:
            journal_path.parent.mkdir(parents=True, exist_ok=True)
            journal_path.write_text("\n".join(lines), encoding="utf-8")
            return True
        except Exception:
            return False


if __name__ == "__main__":
    # Demo
    pr = PromptRandomizer()
    print("=== Prompt Randomizer Demo ===\n")
    
    # Generate 5 prompts
    prompts = pr.generate_batch(5, "OMNICORE security layer")
    for p in prompts:
        print(f"[{p['category']}] intensity={p['intensity']} tier={p['tier']}")
        print(f"  → {p['prompt']}")
        print()
    
    # Generate symbolic (Lingua Prima) prompt
    symbolic = pr.generate_prompt("OMNICORE security", output_format="symbolic")
    print(f"\nSymbolic: {symbolic['prompt']}")
    
    # Export audit
    audit = pr.export_audit()
    print(f"\nAudit: {audit['total_prompts']} prompts, {audit['total_rolls']} rolls")
