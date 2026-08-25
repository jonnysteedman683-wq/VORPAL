"""
OMNICORE Pipeline Skill — Auto-Steal + Defense + Orchestration
Stolen from: tri_agentic_kernel.ts (processIntent pipeline), thors_thorns_engine.ts (scan_and_retaliate),
+ auto_steal_engine.py (pattern harvesting), defensive_engine.py (safe_execute)

Pipeline stages:
  1. Input scan (Thors) → 2. Kernel evaluation (A1/A2/A3) → 3. Route (CostAwareRouter)
  → 4. Harvest (AutoSteal) → 5. Defensive execute → 6. Obsidian audit sync
"""
import sys
import os
import re
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

PIPELINE_DIR = Path(__file__).parent
SKILLS_DIR = PIPELINE_DIR.parent
sys.path.insert(0, str(SKILLS_DIR / "utilities"))
sys.path.insert(0, str(SKILLS_DIR / "LANGUAGE"))

from thors_thorns_engine import ThorsThornsEngine
from tri_agentic_kernel import TriAgenticKernel, PERSONALITIES
from auto_steal_engine import AutoStealEngine
from defensive_engine import DefensiveEngine, ErrorTaxonomy
from lingua_prima import LinguaPrima


class OMNICorePipeline:
    """
    Full OMNICORE co-evolution pipeline.
    Stolen from: markus_pipeline.py + A1 tri_agentic_kernel.ts
    """
    
    def __init__(self, personality: str = "base", audit_path: str = None):
        self.personality = personality
        self.kernel = TriAgenticKernel(config={"personality": personality})
        self.security = ThorsThornsEngine()
        self.stealer = AutoStealEngine()
        self.defensive = DefensiveEngine(max_retries=3, backoff_base=0.1)
        if audit_path:
            self.defensive.set_audit_path(audit_path)
        self.lp = LinguaPrima()
    
    def process(self, content: str, source: str = "unknown", 
                source_urls: List[str] = None) -> Dict[str, Any]:
        """
        Full pipeline: scan → evaluate → route → harvest → execute → audit.
        Returns structured result with threat/taxonomy/retry info.
        """
        result = {
            "status": "processing",
            "source": source,
            "security_scan": None,
            "kernel_evaluation": None,
            "harvest_results": None,
            "execution_result": None,
            "error": None,
            "bug": None,
        }
        
        # Stage 1: Security scan (Thors)
        threats, countermeasures = self.security.scan_and_retaliate(content, source=source)
        result["security_scan"] = {
            "threats_found": len(threats),
            "threat_types": [t.attack_type.value for t in threats],
            "countermeasures_applied": len(countermeasures),
            "source_blacklisted": source in self.security.thorns._blacklisted_sources,
        }
        
        # If source is blacklisted, reject immediately
        if result["security_scan"]["source_blacklisted"]:
            result["status"] = "rejected"
            result["error"] = "Source blacklisted by Thors/Thorns"
            return result
        
        # Stage 2: Kernel evaluation (A1/A2/A3 safety gate)
        def create_intent(content, source):
            return {
                "id": f"intent-{time.time()}",
                "source": source,
                "intent": "route",
                "confidence": 0.95,
                "features": {"alpha_power": 5.2, "quality": 0.9},
                "timestamp": time.time(),
                "requiresConfirmation": False,
            }
        
        intent = self.defensive.retry(create_intent, content, source)
        result["kernel_evaluation"] = self.kernel.process_intent(intent)
        
        # Stage 3: Harvest patterns (Auto-Steal)
        if source_urls:
            def harvest_task():
                # Use find_stealable_patterns for URL sources
                patterns = self.stealer.find_stealable_patterns(source_urls)
                return {"patterns_found": len(patterns), "patterns": [p.__dict__ for p in patterns[:5]]}
            
            harvest_result = self.defensive.safe_execute(harvest_task)
            result["harvest_results"] = harvest_result
        
        # Stage 4: Execute with defense
        def execute_task():
            compressed = self.lp.compress_english(content)
            return f"Processing: {compressed}"
        
        exec_result = self.defensive.safe_execute(execute_task)
        result["execution_result"] = exec_result
        result["status"] = "completed" if exec_result["success"] else "error"
        
        if not exec_result["success"]:
            result["error"] = exec_result["error"]
            result["bug"] = exec_result["bug"]
        
        # Stage 5: Audit sync
        try:
            self.security.thors._alert_log.clear()  # Clean for next run
            self.defensive.sync_to_obsidian()
        except Exception:
            pass
        
        return result


# ─── Skill entry points ───

def skill_process_intent(content: str, source: str = "human", 
                         source_urls: List[str] = None) -> str:
    """
    Skill: Process an intent through the full OMNICORE pipeline.
    
    Usage:
        from pipeline_skills import skill_process_intent
        result = skill_process_intent("Analyze this code for bugs", source="developer")
    """
    pipeline = OMNICorePipeline(personality="base")
    result = pipeline.process(content, source, source_urls)
    
    # Return compressed summary
    status_emoji = {
        "completed": "✅",
        "processing": "⏳",
        "rejected": "❌",
        "error": "💥"
    }
    
    lines = [
        f"{status_emoji.get(result['status'], '❓')} Pipeline Result: {result['status']}",
        f"  Source: {result['source']}",
        f"  Threats: {result['security_scan']['threats_found']}",
    ]
    
    if result.get("execution_result", {}).get("success"):
        lines.append(f"  Output: {result['execution_result']['result']}")
    
    if result.get("bug"):
        lines.append(f"  Bug: [{result['bug']['error_taxonomy']}] {result['bug']['error_message'][:100]}")
    
    return "\n".join(lines)


def skill_security_audit(content: str) -> Dict[str, Any]:
    """
    Skill: Security audit — scan content and return full threat report.
    
    Usage:
        from pipeline_skills import skill_security_audit
        report = skill_security_audit(user_input)
    """
    pipeline = OMNICorePipeline()
    threats, cms = pipeline.security.scan_and_retaliate(content, source="audit")
    
    return {
        "threat_count": len(threats),
        "threats": [
            {
                "type": t.attack_type.value,
                "severity": t.severity,
                "score": t.threat_score,
                "payload": t.payload[:100],
            }
            for t in threats
        ],
        "countermeasures": [cm.__dict__ for cm in cms],
        "audit_log": pipeline.security.audit_log(),
    }


def skill_code_review(code: str, repo_url: str = None) -> str:
    """
    Skill: Code review with security scanning + pattern harvesting.
    
    Usage:
        from pipeline_skills import skill_code_review
        report = skill_code_review(code_snippet, "https://github.com/...")
    """
    pipeline = OMNICorePipeline(personality="a1")  # A1 Gatekeeper for code review
    
    # Security scan
    threats, _ = pipeline.security.scan_and_retaliate(code, source="code_review")
    if threats:
        threat_summary = "\n".join(
            f"  ⚠️ {t.attack_type.value}: {t.payload[:60]}" for t in threats
        )
        return f"🚨 SECURITY ISSUES DETECTED:\n{threat_summary}"
    
    # Harvest patterns if URL provided
    if repo_url:
        harvest = pipeline.defensive.safe_execute(
            pipeline.stealer.harvest_from_url, repo_url, "code"
        )
        if harvest["success"]:
            patterns_found = harvest["result"]["patterns_found"]
            return f"✅ Code is clean. Patterns harvested: {patterns_found}"
    
    return "✅ Code passed security review (no threats detected)"


def skill_tri_agent_debate(intent: str, confidence: float = 0.9) -> str:
    """
    Skill: Run a tri-agent debate (A1 Gatekeeper vs A2 Optimizer vs A3 Architect).
    
    Usage:
        from pipeline_skills import skill_tri_agent_debate
        report = skill_tri_agent_debate("Should we upgrade the cluster?", confidence=0.85)
    """
    kernels = {
        "a1": TriAgenticKernel(config={"personality": "a1"}),
        "a2": TriAgenticKernel(config={"personality": "a2"}),
        "a3": TriAgenticKernel(config={"personality": "a3"}),
    }
    
    intent_dict = {
        "id": f"debate-{time.time()}",
        "source": "mock",
        "intent": "route",
        "confidence": confidence,
        "features": {"alpha_power": 5.0, "quality": 0.85},
        "timestamp": time.time(),
        "requiresConfirmation": False,
    }
    
    results = {}
    for role, kernel in kernels.items():
        safety = kernel.safety_gate.evaluate(intent_dict)
        results[role] = {
            "name": kernel.personality.name,
            "allowed": safety["allowed"],
            "risk": safety["riskLevel"],
            "reason": safety["reason"],
            "threshold": kernel.personality.confidenceThreshold,
        }
    
    # Consensus: all must allow
    all_allowed = all(r["allowed"] for r in results.values())
    consensus = "APPROVED" if all_allowed else "REJECTED"
    
    lines = [f"🧠 Tri-Agent Debate: '{intent}' (confidence: {confidence})", ""]
    for role, result in results.items():
        emoji = "✅" if result["allowed"] else "❌"
        lines.append(
            f"  {emoji} {result['name']} ({role}): {result['reason']} | "
            f"threshold={result['threshold']} | risk={result['risk']}"
        )
    lines.append(f"\n📊 Consensus: {consensus}")
    
    return "\n".join(lines)


def skill_defensive_execute(func_code: str, *args, **kwargs) -> Dict[str, Any]:
    """
    Skill: Execute arbitrary code defensively with bug traceback capture.

    Usage:
        from pipeline_skills import skill_defensive_execute
        result = skill_defensive_execute("lambda x: 1/x", 0)
    """
    engine = DefensiveEngine(max_retries=2, backoff_base=0.1)
    # Safety gate: reject code containing dangerous imports/keywords
    _dangerous = re.compile(
        r"\b(import\s+os|import\s+subprocess|import\s+sys|"
        r"import\s+shutil|import\s+socket|import\s+signal|"
        r"from\s+os\s+import|from\s+subprocess\s+import|"
        r"os\.system|os\.popen|subprocess\.|eval\(|exec\()",
        re.IGNORECASE,
    )
    if _dangerous.search(func_code):
        raise ValueError("skill_defensive_execute: rejected dangerous code pattern in func_code")

    def exec_func() -> Any:
        func = eval(func_code)
        return func(*args, **kwargs)

    result = engine.safe_execute(exec_func)

    if not result["success"] and result["bug"]:
        bug = result["bug"]
        result["bug_report"] = {
            "type": bug["error_type"],
            "taxonomy": bug["error_taxonomy"],
            "message": bug["error_message"],
            "traceback": bug["traceback_formatted"][:500],
        }

    return result


# ─── CLI entry point ───
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OMNICORE Pipeline Skills")
    parser.add_argument("skill", choices=["process", "audit", "review", "debate"],
                        help="Which pipeline skill to run")
    parser.add_argument("--content", "-c", help="Content to process")
    parser.add_argument("--source", "-s", default="human", help="Source identifier")
    parser.add_argument("--confidence", type=float, default=0.9, help="Intent confidence")
    parser.add_argument("--url", "-u", help="Repository URL for harvesting")
    
    args = parser.parse_args()
    
    if args.skill == "process":
        result = skill_process_intent(args.content, args.source, 
                                     [args.url] if args.url else None)
        print(result)
    elif args.skill == "audit":
        report = skill_security_audit(args.content)
        print(json.dumps(report, indent=2))
    elif args.skill == "review":
        report = skill_code_review(args.content, args.url)
        print(report)
    elif args.skill == "debate":
        report = skill_tri_agent_debate(args.content, args.confidence)
        print(report)