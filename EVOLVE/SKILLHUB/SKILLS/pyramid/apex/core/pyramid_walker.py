"""
OMNICORE PYRAMID WALKER SKILL
Zero-dependency recursive directory walker with tier-based filtering and degradation detection.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Iterator, Optional
from enum import Enum

class Tier(str, Enum):
    APEX = "apex"
    ACTIVE = "active"
    STAGNANT = "stagnant"
    ARCHIVED = "archived"
    REPAIR = "repair"

class DegradationCategory(str, Enum):
    SYNTAX_CRASH = "syntax_crash"
    LOGIC_HALLUCINATION = "logic_hallucination"
    TOKEN_BLOAT = "token_bloat"
    OVERLAP_REDUNDANT = "overlap_redundant"
    CRITICAL_MULTI = "critical_multi_category"
    INACTIVITY_DECAY = "inactivity_decay"

class PyramidWalker:
    PYRAMID_ROOTS = {
        Tier.APEX: "apex/level_0",
        Tier.ACTIVE: "active/level_1",
        Tier.STAGNANT: "stagnant/level_2",
        Tier.ARCHIVED: "archived/level_3",
        Tier.REPAIR: "repair/level_4_base",
    }
    
    REPAIR_COLUMNS = {
        "priority_1": {
            DegradationCategory.CRITICAL_MULTI: "PRIORITY_1_CRITICAL/critical_multi_category",
        },
        "priority_2": {
            DegradationCategory.SYNTAX_CRASH: "PRIORITY_2_SINGLE/syntax_crash",
            DegradationCategory.LOGIC_HALLUCINATION: "PRIORITY_2_SINGLE/logic_hallucination",
            DegradationCategory.TOKEN_BLOAT: "PRIORITY_2_SINGLE/token_bloat",
            DegradationCategory.OVERLAP_REDUNDANT: "PRIORITY_2_SINGLE/overlap_redundant",
        },
        "priority_3": {
            DegradationCategory.INACTIVITY_DECAY: "PRIORITY_3/inactivity_decay",
        }
    }
    
    def __init__(self, root: str = "pyramid"):
        self.root = Path(root).resolve()

    def walk_tier(self, tier: Tier) -> Iterator[Path]:
        """Yield all .md files in a tier."""
        tier_path = self.root / self.PYRAMID_ROOTS[tier]
        if tier_path.exists():
            for md_file in tier_path.rglob("*.md"):
                yield md_file

    def walk_all_tiers(self) -> Dict[str, List[Path]]:
        """Walk all tiers and return files grouped by tier name."""
        result = {}
        for tier in Tier:
            files = list(self.walk_tier(tier))
            if files:
                result[tier.value] = files
        return result

    def scan_repair_columns(self) -> Dict[str, Dict[str, List[Path]]]:
        """Scan all repair columns for degraded skills."""
        result = {}
        repair_base = self.root / "repair/level_4_base"
        if not repair_base.exists():
            return result
            
        for priority_dir in repair_base.iterdir():
            if not priority_dir.is_dir():
                continue
            priority_name = priority_dir.name
            result[priority_name] = {}
            
            for category_dir in priority_dir.iterdir():
                if category_dir.is_dir():
                    files = list(category_dir.rglob("*.md"))
                    if files:
                        result[priority_name][category_dir.name] = files
        return result

    def detect_degradation(self, file_path: Path) -> List[DegradationCategory]:
        """Detect degradation categories by reading YAML linked_degradations field."""
        try:
            content = file_path.read_text(encoding='utf-8')
            match = re.search(r'linked_degradations:\s*\[(.*?)\]', content, re.DOTALL)
            if match:
                degradations = re.findall(r'"([^"]+)"', match.group(1))
                return [DegradationCategory(d) for d in degradations if d in [e.value for e in DegradationCategory]]
        except Exception:
            pass
        return []

    def identify_migration_target(self, file_path: Path) -> Optional[str]:
        """Suggest tier migration based on degradation and age."""
        degradations = self.detect_degradation(file_path)
        if not degradations:
            return Tier.ACTIVE.value
            
        if DegradationCategory.CRITICAL_MULTI in degradations:
            return "repair/PRIORITY_1_CRITICAL/critical_multi_category"
        elif DegradationCategory.SYNTAX_CRASH in degradations:
            return "repair/PRIORITY_2_SINGLE/syntax_crash"
        elif DegradationCategory.LOGIC_HALLUCINATION in degradations:
            return "repair/PRIORITY_2_SINGLE/logic_hallucination"
        elif DegradationCategory.TOKEN_BLOAT in degradations:
            return "repair/PRIORITY_2_SINGLE/token_bloat"
        elif DegradationCategory.OVERLAP_REDUNDANT in degradations:
            return "repair/PRIORITY_2_SINGLE/overlap_redundant"
        elif DegradationCategory.INACTIVITY_DECAY in degradations:
            return "repair/PRIORITY_3/inactivity_decay"
            
        return Tier.STAGNANT.value

    def get_pyramid_summary(self) -> Dict[str, Any]:
        """Return summary statistics of pyramid health."""
        summary = {
            'total_files': 0,
            'tier_counts': {},
            'repair_counts': {},
            'degraded_files': 0,
            'migration_candidates': {}
        }
        
        for tier in Tier:
            files = list(self.walk_tier(tier))
            summary['total_files'] += len(files)
            summary['tier_counts'][tier.value] = len(files)
            
        repair_scan = self.scan_repair_columns()
        for priority, cats in repair_scan.items():
            summary['repair_counts'][priority] = sum(len(v) for v in cats.values())
            summary['total_files'] += sum(len(v) for v in cats.values())
            
        for tier in [Tier.ACTIVE, Tier.STAGNANT]:
            for file in self.walk_tier(tier):
                degradations = self.detect_degradation(file)
                if degradations:
                    summary['degraded_files'] += 1
                migration = self.identify_migration_target(file)
                if migration and migration != Tier.ACTIVE.value:
                    summary['migration_candidates'][str(file.name)] = migration
                    
        return summary
