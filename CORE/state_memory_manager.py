"""
OMNICORE State Memory Manager
O(1) continuous state ledger manager for GOALS.md, IDEAS.md, and NOTES.md.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List

class StateMemoryManager:
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.goals_path = self.root / "GOALS.md"
        self.ideas_path = self._resolve_ideas_path()
        self.notes_path = self.root / "NOTES.md"

    def _resolve_ideas_path(self) -> Path:
        """Resolve the append-only IDEAS ledger to the existing/canonical path.

        Tolerant of three layouts:
          1. EVOLVE/IDEAS.md  (OMNIPRIME canonical append-only ledger)
          2. IDEAS.md         (legacy root-ledger, backward-compatible default)
          3. IDEA.md          (singular legacy stub)
        Prefers the first path that already exists; otherwise defaults to the
        legacy root/IDEAS.md for backward compatibility (so callers that create
        their own root ledger, e.g. test harnesses, keep working). At the real
        OMNIPRIME root, EVOLVE/IDEAS.md exists and is therefore selected,
        repointing appends to the canonical append-only ledger.
        """
        candidates = [
            self.root / "EVOLVE" / "IDEAS.md",
            self.root / "IDEAS.md",
            self.root / "IDEA.md",
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[1]

    def scan_queues(self) -> Dict[str, int]:
        """O(1) queue count scan."""
        p1_dir = self.root / "skill_repair" / "PRIORITY_1_CRITICAL" / "critical_multi_category"
        p2_base = self.root / "skill_repair" / "PRIORITY_2_SINGLE"
        
        p1_count = len(list(p1_dir.glob("*.md"))) if p1_dir.exists() else 0
        p2_count = len(list(p2_base.glob("*/*.md"))) if p2_base.exists() else 0
        overlap_dir = p2_base / "overlap_redundant"
        p3_count = len(list(overlap_dir.glob("*.md"))) if overlap_dir.exists() else 0
        
        return {
            "priority_1_count": p1_count,
            "priority_2_count": p2_count,
            "priority_3_count": p3_count
        }

    def append_idea(self, title: str, attribution: str, distilled_logic: str, target_goal_id: str = "GOAL_1.1") -> bool:
        """Append candidate idea to immutable IDEAS.md ledger."""
        entry = (
            f"\n## Idea: {title}\n"
            f"- Target: {target_goal_id}\n"
            f"- Attribution: {attribution}\n"
            f"```python\n{distilled_logic.strip()}\n```\n"
        )
        with open(self.ideas_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return True

    def mark_idea_implemented(self, title: str, skill_id: str) -> bool:
        """Append [IMPLEMENTED: skill_id] to matching idea entry."""
        if not self.ideas_path.exists():
            return False
        content = self.ideas_path.read_text(encoding="utf-8")
        pattern = rf"(## Idea:\s*{re.escape(title)}[\s\S]*?)(?=\n## Idea:|\Z)"
        match = re.search(pattern, content)
        if match and f"[IMPLEMENTED: {skill_id}]" not in match.group(1):
            updated_section = match.group(1).rstrip() + f"\n- Status: [IMPLEMENTED: {skill_id}]\n"
            content = content[:match.start()] + updated_section + content[match.end():]
            self.ideas_path.write_text(content, encoding="utf-8")
            return True
        return False

    def update_goal_status(self, goal_id: str, new_status: str, skill_name: str) -> bool:
        """Update GOALS.md goal node status."""
        if not self.goals_path.exists():
            return False
        content = self.goals_path.read_text(encoding="utf-8")
        pattern = rf"(-\s*\[[ x]\]\s*\*\*{re.escape(goal_id)}:\*\*[\s\S]*?-\s*\[STATUS:)[^\]]+(\])"
        if re.search(pattern, content):
            new_text = re.sub(pattern, rf"\g<1> {new_status}] (Skill: `{skill_name}`)", content)
            if "tier_0_apex" in new_status or "tier_1_active" in new_status:
                new_text = re.sub(rf"-\s*\[ \]\s*(\*\*{re.escape(goal_id)}:\*\*)", r"- [x] \1", new_text)
            self.goals_path.write_text(new_text, encoding="utf-8")
            return True
        return False

    def log_taxonomy_err(self, err_type: str, skill_id: str, details: str) -> bool:
        """Record error taxonomy in NOTES.md."""
        entry = f"\n- `{err_type}` [{skill_id}]: {details}"
        with open(self.notes_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
