"""
OMNICORE Skills Engine v1.0 — Loadable Framework
A discovery, validation, and loading engine for SKILL.md-formatted skills in
the pyramid, stolen from the Hermes SKILL.md schema + Hermes Tool Format.

Stolen from:
  - Hermes SKILL.md schema (YAML frontmatter: name, description, version, metadata)
  - Hermes skill_view / skills_list tool format (trigger-first descriptions)
  - pyramid_walker.py (tier classification)
  - registry.json structure (tier, status, verification_harness)

Features:
  - Discover SKILL.md files under the pyramid
  - Parse YAML frontmatter (name, description, version, tags, related_skills)
  - Validate required frontmatter fields
  - Load skill body / references / scripts
  - Index skills by tier, tag, and purpose
  - Render a skills_list-style summary (trigger-first, 57-char window)
  - Emit typed events to the event bus (GOAL_6.3 integration)

Zero-dependency Python stdlib implementation (frontmatter parsed manually).
"""
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# YAML frontmatter delimiter: --- at start and end
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class LoadedSkill:
    """A skill discovered and loaded from the pyramid."""
    name: str
    path: Path
    description: str = ""
    version: str = ""
    author: str = ""
    license: str = ""
    tier: str = "unknown"
    tags: List[str] = field(default_factory=list)
    related_skills: List[str] = field(default_factory=list)
    body: str = ""
    purpose: str = ""  # First line of body, trigger-first window
    registered: bool = False  # Present in registry.json
    verification_harness: str = ""

    def summary(self, window: int = 57) -> str:
        """Trigger-first summary like Hermes skills_list: first `window`
        chars of description, then '...' if truncated."""
        desc = self.description or self.purpose
        if len(desc) > window:
            return desc[:window] + "..."
        return desc


def _parse_frontmatter(text: str) -> Dict[str, Any]:
    """Parse YAML-ish frontmatter into a dict. Handles the subset Hermes
    SKILL.md uses (name, description, version, author, license, platforms,
    metadata.tags, metadata.related_skills)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm: Dict[str, Any] = {}
    current_key = None
    for raw_line in m.group(1).splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  ") or line.startswith("\t"):
            # continuation / nested value under previous key
            stripped = line.strip()
            if current_key and current_key == "metadata":
                continue
            if current_key and isinstance(fm.get(current_key), str):
                fm[current_key] += " " + stripped
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            current_key = key
            if key == "metadata":
                fm[key] = {}
                current_key = None
                continue
            # Handle inline lists
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                fm[key] = [i.strip().strip("'\"") for i in inner.split(",") if i.strip()]
            elif val.lower() in ("true", "false"):
                fm[key] = val.lower() == "true"
            elif val == "" or val.lower() == "null":
                fm[key] = ""
            else:
                # Strip surrounding quotes
                fm[key] = val.strip("\"'")
    # Post-process metadata.tags / metadata.related_skills (nested)
    return fm


def _extract_nested_fm(text: str) -> Dict[str, Any]:
    """Second pass: pull metadata.tags and metadata.related_skills lines."""
    result: Dict[str, Any] = {}
    for pat, key in [(r"tags:\s*\[(.*?)\]", "tags"),
                     (r"related_skills:\s*\[(.*?)\]", "related_skills")]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            inner = m.group(1)
            result[key] = [i.strip().strip("'\"")
                           for i in inner.split(",") if i.strip()]
    return result


class SkillsEngine:
    """
    Loadable framework for discovering, validating, and loading pyramid skills.

    SKILL.md format (Hermes-compatible):
      ---
      name: <slug>
      description: "<trigger-first one-liner>"
      version: x.y.z
      metadata:
        tags: [...]
        related_skills: [...]
      ---
      # <Title>
      ## When to Use / Procedure / Verification ...
    """

    REQUIRED_FIELDS = ["name", "description"]

    def __init__(self, pyramid_root: Optional[Path] = None,
                 registry: Optional[Dict] = None,
                 event_bus: Any = None):
        self._root = Path(pyramid_root) if pyramid_root else None
        self._registry = registry or {}
        self._event_bus = event_bus
        self._cache: Dict[str, LoadedSkill] = {}
        self._load_count = 0

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus is not None and hasattr(self._event_bus, "emit"):
            try:
                self._event_bus.emit(event_type, payload)
            except Exception:
                pass

    # ---- discovery ---------------------------------------------------------

    def discover(self, root: Optional[Path] = None) -> List[Path]:
        """Recursively find all SKILL.md files under the pyramid root."""
        base = Path(root) if root else self._root
        if base is None:
            raise ValueError("no pyramid root configured")
        return sorted(base.rglob("SKILL.md"))

    # ---- loading -----------------------------------------------------------

    def load(self, path: Path) -> Optional[LoadedSkill]:
        """Load a single SKILL.md file into a LoadedSkill."""
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        nested = _extract_nested_fm(text)

        name = fm.get("name") or path.parent.name
        description = fm.get("description", "")

        # Infer tier from path (apex/core, external/, etc.)
        rel = path.relative_to(self._root) if self._root else path
        parts = rel.parts
        tier = "unknown"
        if "apex" in parts:
            tier = "tier_0_apex"
        elif "active" in parts or "tier_1" in parts:
            tier = "tier_1_active"
        elif "external" in parts:
            tier = "tier_2_imported"
        elif "stagnant" in parts:
            tier = "tier_3_stagnant"

        body = text
        # Strip frontmatter from body
        m = FRONTMATTER_RE.match(body)
        if m:
            body = body[m.end():].strip()

        purpose = ""
        for line in body.splitlines():
            if line.strip() and not line.strip().startswith("#"):
                purpose = line.strip()
                break

        skill = LoadedSkill(
            name=name,
            path=path,
            description=description,
            version=fm.get("version", ""),
            author=fm.get("author", ""),
            license=fm.get("license", ""),
            tier=tier,
            tags=nested.get("tags", fm.get("tags", [])),
            related_skills=nested.get("related_skills", fm.get("related_skills", [])),
            body=body,
            purpose=purpose,
            registered=name in self._registry,
            verification_harness="",
        )
        # Attach verification harness from registry if present
        if skill.registered:
            reg = self._registry.get(name, {})
            if isinstance(reg, dict):
                skill.verification_harness = reg.get("verification_harness", "")

        self._cache[name] = skill
        self._load_count += 1
        return skill

    def load_all(self, root: Optional[Path] = None) -> List[LoadedSkill]:
        """Load every SKILL.md under the pyramid."""
        skills = []
        for p in self.discover(root):
            s = self.load(p)
            if s:
                skills.append(s)
        self._emit("skills.load_all", {"count": len(skills)})
        return skills

    # ---- validation --------------------------------------------------------

    def validate(self, skill: LoadedSkill) -> List[str]:
        """Return list of validation errors (empty = valid)."""
        errors = []
        for f in self.REQUIRED_FIELDS:
            if not getattr(skill, f):
                errors.append(f"missing required field: {f}")
        if not skill.description and not skill.purpose:
            errors.append("missing description and purpose (no trigger text)")
        return errors

    def validate_all(self, root: Optional[Path] = None) -> Dict[str, List[str]]:
        """Validate all skills; returns {name: [errors]}."""
        results = {}
        for s in self.load_all(root):
            results[s.name] = self.validate(s)
        return results

    # ---- indexing / querying ------------------------------------------------

    def by_tier(self, tier: str, root: Optional[Path] = None) -> List[LoadedSkill]:
        return [s for s in self.load_all(root) if s.tier == tier]

    def by_tag(self, tag: str, root: Optional[Path] = None) -> List[LoadedSkill]:
        return [s for s in self.load_all(root) if tag in s.tags]

    def get(self, name: str) -> Optional[LoadedSkill]:
        return self._cache.get(name)

    def search(self, query: str, root: Optional[Path] = None) -> List[LoadedSkill]:
        """Simple substring search over name, description, purpose, tags."""
        q = query.lower()
        out = []
        for s in self.load_all(root):
            haystack = " ".join([s.name, s.description, s.purpose,
                                 " ".join(s.tags)]).lower()
            if q in haystack:
                out.append(s)
        return out

    def skills_list(self, root: Optional[Path] = None) -> Dict[str, str]:
        """Hermes skills_list-style render: {name: trigger-first summary}."""
        return {s.name: s.summary() for s in self.load_all(root)}

    def skill_view(self, name: str) -> Optional[str]:
        """Hermes skill_view-style render of a loaded skill."""
        s = self.get(name)
        if s is None:
            return None
        header = f"# {s.name}  (v{s.version or '?'} · {s.tier})\n"
        if s.description:
            header += f"\n**{s.description}**\n"
        if s.tags:
            header += f"\nTags: {', '.join(s.tags)}\n"
        return header + "\n" + s.body

    # ---- persistence --------------------------------------------------------

    def build_registry_patch(self, root: Optional[Path] = None) -> Dict[str, Dict]:
        """Generate registry.json entries for unregistered discovered skills."""
        patch = {}
        for s in self.load_all(root):
            if s.registered:
                continue
            patch[s.name] = {
                "tier": s.tier,
                "status": "discovered",
                "version": s.version or "0.1.0",
                "last_touch": time.strftime("%Y-%m-%d"),
                "skill_path": str(s.path),
                "owned_by": "omniprime",
                "purpose": s.purpose or s.description,
            }
        return patch

    def audit_log(self) -> Dict[str, Any]:
        return {
            "skills_loaded": len(self._cache),
            "load_count": self._load_count,
            "root": str(self._root) if self._root else None,
            "registered_count": sum(1 for s in self._cache.values() if s.registered),
            "unregistered_count": sum(1 for s in self._cache.values() if not s.registered),
        }


def create_skills_engine(pyramid_root, registry=None, event_bus=None) -> SkillsEngine:
    return SkillsEngine(pyramid_root=pyramid_root, registry=registry,
                        event_bus=event_bus)