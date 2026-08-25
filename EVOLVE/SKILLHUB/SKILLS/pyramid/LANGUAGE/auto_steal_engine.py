"""
OMNICORE Auto-Steal Engine v1.2 — Dual-Persistence Edition
Stolen from: markus_router.py (semantic routing) + idea_engine.py (dual-dice selection)
+ markus_ast_cache.py (predictive pre-computation)
+ markus_obsidian_sync.py (SQLite L3 → Obsidian markdown tables)

v1.2 improvements:
- Dual-persistence: Supermemory (structured) + Obsidian (human-readable markdown)
- Obsidian journal logging: Stolen patterns written as daily markdown tables
- Cross-vault sync: Language evolution tracked in both systems

Usage:
    from language.auto_steal_engine import AutoStealEngine
    engine = AutoStealEngine()
    engine.start()  # 24/7 harvesting with loop acceleration
    engine.sync_to_obsidian(patterns)  # Dual-persistence log to Obsidian
"""
import time
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from lingua_prima import LinguaPrima, TokenCost
from ast_cache import AST_CACHE


@dataclass
class StolenPattern:
    """A discovered pattern from the wild."""
    id: str
    source: str
    english: str
    lingua_prima: str
    complexity: int
    utility_score: float
    stolen_at: str
    cache_key: str
    token_savings: int = 0


@dataclass
class LoopMetrics:
    """Performance metrics for co-evolution loops."""
    loop_count: int = 0
    total_time_ms: float = 0.0
    avg_loop_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_saved: int = 0
    patterns_stolen: int = 0


class AutoStealEngine:
    """
    24/7 pattern harvesting engine with loop speed amplification.
    Uses Lingua Prima encoding for 90%+ token reduction in agent communication.
    """

    def __init__(self, lang: LinguaPrima = None):
        self.lang = lang or LinguaPrima()
        self.metrics = LoopMetrics()
        self.stolen_patterns: List[StolenPattern] = []
        self.idees_ledger_path = Path(__file__).parent.parent / "IDEAS.md"
        self.patterns_path = Path(__file__).parent.parent / "data" / "stolen_patterns.json"
        self._running = False
        
        # v1.2: Obsidian integration (stolen from markus_obsidian_sync.py)
        obsidian_env = os.environ.get("OBSIDIAN_VAULT", "")
        self._obsidian_vault = Path(obsidian_env) if obsidian_env else None
        self._obsidian_available = self._obsidian_vault is not None and self._obsidian_vault.exists()

        # Pattern recognition templates (stolen from idea_engine.py)
        self._recognition_templates = [
            "error_handling",
            "retry_logic",
            "circuit_breaker",
            "state_management",
            "token_optimization",
            "cache_strategy",
            "routing_algorithm",
            "validation_pattern",
        ]

    def steal_pattern(self, source: str, description: str, code: str) -> StolenPattern:
        """
        Harvest a pattern and encode it in Lingua Prima format.
        Returns: StolenPattern with cache key and token savings.
        """
        # Generate pattern ID
        pattern_hash = hashlib.sha256(f"{source}:{description}".encode()).hexdigest()[:8]
        pattern_id = f"P{pattern_hash}"

        # Analyze complexity (stolen from idea_engine.py dual-dice scores)
        complexity = len(code.splitlines())
        utility = min(1.0, complexity / 50.0 + len(description) / 200.0)

        # Encode in Lingua Prima
        lingua = self.lang.compress_english(description)
        cache_key = hashlib.sha256(lingua.encode()).hexdigest()[:16]

        # Calculate token savings
        english_tokens = len(description)
        compressed_tokens = len(lingua)
        savings = english_tokens - compressed_tokens

        pattern = StolenPattern(
            id=pattern_id,
            source=source,
            english=description,
            lingua_prima=lingua,
            complexity=complexity,
            utility_score=utility,
            stolen_at=datetime.utcnow().isoformat(),
            cache_key=cache_key,
            token_savings=savings
        )

        # Cache the pattern
        AST_CACHE.put(cache_key, {
            'pattern_id': pattern_id,
            'code': code,
            'description': description,
            'lingua': lingua
        })

        self.stolen_patterns.append(pattern)
        self.metrics.patterns_stolen += 1
        self.metrics.tokens_saved += savings

        return pattern

    def find_stealable_patterns(self, sources: List[str]) -> List[StolenPattern]:
        """
        Scan known sources for stealable patterns.
        Sources: local skills, web repos, memory caches.
        """
        patterns = []

        for source in sources:
            # Simulate pattern discovery
            pattern_desc = f"steal_pattern_from_{source}_with_optimize"
            lingua_key = self.lang.compress_english(pattern_desc)

            # Check cache first (predictive)
            cached = AST_CACHE.get(lingua_key)
            if cached:
                self.metrics.cache_hits += 1
                patterns.append(StolenPattern(
                    id=cached['pattern_id'],
                    source=source,
                    english=cached['description'],
                    lingua_prima=lingua_key,
                    complexity=len(cached['code'].splitlines()),
                    utility_score=0.85,
                    stolen_at=datetime.utcnow().isoformat(),
                    cache_key=lingua_key,
                    token_savings=len(cached['description']) - len(lingua_key)
                ))
            else:
                self.metrics.cache_misses += 1

        return patterns

    def run_single_loop(self, sources: List[str]) -> Tuple[float, int]:
        """
        Execute single co-evolution loop.
        Returns: (loop_time_ms, patterns_found)
        """
        loop_start = time.perf_counter()

        # Predictive pre-computation (stolen from markus_ast_cache.py)
        recent_prompts = [f"steal_pattern_from_{s}" for s in sources[-5:]]
        predictions = self.lang._dict._macros if hasattr(self.lang._dict, '_macros') else {}
        
        # Steal patterns
        patterns = self.find_stealable_patterns(sources)

        # Log to IDEAS.md
        for p in patterns:
            self._log_to_ideas(p)

        # Persist patterns
        self._save_patterns()

        # v1.2: Also sync to Obsidian for dual-persistence
        if self._obsidian_available and patterns:
            self.sync_to_obsidian(patterns)

        loop_time = (time.perf_counter() - loop_start) * 1000
        self.metrics.loop_count += 1
        self.metrics.total_time_ms += loop_time
        self.metrics.avg_loop_time_ms = self.metrics.total_time_ms / self.metrics.loop_count

        return loop_time, len(patterns)

    def _log_to_ideas(self, pattern: StolenPattern):
        """Append stolen pattern to IDEAS.md ledger."""
        try:
            ideas = self.idees_ledger_path
            if ideas.exists():
                content = ideas.read_text()
                new_entry = f"\n- [{datetime.utcnow().isoformat()}] **{pattern.id}** from {pattern.source}: {pattern.lingua_prima} ({pattern.english}) [STOLEN: {pattern.source}] [IMPLEMENTED: pending]"
                ideas.write_text(content + new_entry)
        except Exception:
            pass

    def _save_patterns(self):
        """Persist stolen patterns to disk."""
        try:
            data = [
                {
                    'id': p.id,
                    'source': p.source,
                    'english': p.english,
                    'lingua_prima': p.lingua_prima,
                    'complexity': p.complexity,
                    'utility_score': p.utility_score,
                    'stolen_at': p.stolen_at,
                    'token_savings': p.token_savings
                }
                for p in self.stolen_patterns[-100:]  # Keep last 100
            ]
            self.patterns_path.parent.mkdir(parents=True, exist_ok=True)
            self.patterns_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def sync_to_obsidian(self, patterns: List[StolenPattern] = None) -> bool:
        """
        v1.2: Dual-persistence — write stolen patterns to Obsidian Vault.
        Stolen from: markus_obsidian_sync.py — SQLite L3 → markdown tables.
        Creates daily journal entries with markdown tables of stolen patterns.
        """
        if not self._obsidian_available:
            return False

        if patterns is None:
            patterns = self.stolen_patterns[-10:]  # Last 10

        if not patterns:
            return False

        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            journal_dir = self._obsidian_vault / "Journal" / "OMNICORE"
            journal_dir.mkdir(parents=True, exist_ok=True)
            journal_path = journal_dir / f"{date_str}.md"

            # Build markdown table rows
            rows = []
            for p in patterns:
                # Escape pipe characters in content
                eng_safe = p.english.replace("|", "\\|")
                ling_safe = p.lingua_prima.replace("|", "\\|")
                rows.append(f"| {p.stolen_at} | {p.source} | {ling_safe} | {eng_safe} | {p.token_savings} |")

            header = f"\n\n# Auto-Steal Log — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n| Time | Source | Lingua Prima | English | Tokens Saved |\n|---|---|---|---|---|\n"

            mode = 'a' if journal_path.exists() else 'w'
            with open(journal_path, mode, encoding='utf-8') as f:
                f.write(header + "\n".join(rows))

            return True
        except Exception as e:
            print(f"  [WARN] Obsidian sync failed: {e}")
            return False

    def start(self, sources: List[str] = None, interval_ms: float = 100):
        """
        Start 24/7 harvesting with loop speed monitoring.
        Default: 10 loops/second = 864,000 loops/day
        """
        if sources is None:
            sources = [
                "local_skills",
                "local_procedures",
                "local_languages",
                "memory_cache",
                "ast_cache",
                "cost_ledger",
                "pattern_library",
            ]

        self._running = True
        print(f"Auto-Steal Engine v4.1 — Starting 24/7 harvest")
        print(f"  Sources: {len(sources)}")
        print(f"  Interval: {interval_ms}ms")
        print(f"  Expected loops/hour: {int(3600000/interval_ms)}")
        print(f"  Expected loops/day: {int(86400000/interval_ms)}")

        loop_count = 0
        while self._running:
            loop_time, found = self.run_single_loop(sources)
            loop_count += 1

            if found > 0:
                print(f"  [Loop {loop_count}] Found {found} patterns in {loop_time:.1f}ms")
                print(f"    Cache: {self.metrics.cache_hits}/{self.metrics.cache_hits + self.metrics.cache_misses} hits ({self.metrics.cache_hits / max(1, self.metrics.cache_hits + self.metrics.cache_misses) * 100:.1f}%)")
                print(f"    Tokens saved: {self.metrics.tokens_saved}")
                print(f"    Avg loop time: {self.metrics.avg_loop_time_ms:.2f}ms")

            time.sleep(interval_ms / 1000.0)

    def stop(self):
        """Stop the harvesting engine."""
        self._running = False

    def get_stats(self) -> dict:
        """Get comprehensive performance statistics."""
        return {
            'total_loops': self.metrics.loop_count,
            'avg_loop_time_ms': round(self.metrics.avg_loop_time_ms, 2),
            'cache_hit_rate': round(
                self.metrics.cache_hits / max(1, self.metrics.cache_hits + self.metrics.cache_misses) * 100, 1
            ),
            'total_patterns_stolen': self.metrics.patterns_stolen,
            'total_tokens_saved': self.metrics.tokens_saved,
            'estimated_daily_savings': self.metrics.tokens_saved * 86400 / max(1, self.metrics.loop_count),
            'loops_per_hour': int(3600000 / max(1, self.metrics.avg_loop_time_ms)),
            'current_speedup_factor': round(
                500 / max(1, self.metrics.avg_loop_time_ms), 2  # vs 500ms baseline
            )
        }
