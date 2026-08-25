#!/usr/bin/env python3
"""ARK Security Scanner — ported from OMNICORE hive-core/src/lib/security_scanner.py

Borrowed design:
- AST-based Python injection detection
- Regex-based JS/TS/YAML/JSON injection detection
- Prompt injection: direct + indirect/comment
- Config/policy drift detection
- Structured ThreatFinding with provenance_hash
- ThreatReport + should_block gate

ARK mapping:
- Scans FORGE mutations before FUSE execution
- Scans FUSE quarantine candidates
- Optional: scan skill files before archive promotion
"""

import ast
import re
import os
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum
from hashlib import sha256


class ThreatLevel(Enum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


class ScanTarget(Enum):
    DIRECT_PROMPT = "direct_prompt"
    INDIRECT_COMMENT = "indirect_comment"
    CODE_STRING = "code_string"
    FILE_CONTENT = "file_content"
    CONFIG_VALUE = "config_value"


@dataclass
class ThreatFinding:
    threat_level: ThreatLevel
    scan_target: ScanTarget
    pattern_matched: str
    matched_content: str
    context: str = ""
    location: str = ""
    provenance_hash: str = ""
    remediation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


DIRECT_INJECTION_PATTERNS = [
    (re.compile(r'\b(?:ignore|disregard|override)\s+(?:my\s+)?previous|previous|all\s+instructions?\b', re.I),
     "Direct instruction override attempt"),
    (re.compile(r'\b(?:override|disregard|ignore)\s+(?:previous|above|all)\s+instructions?\b', re.I),
     "System prompt override attempt"),
    (re.compile(r'\binstructions?\s+(?:for|to|override|ignore|disregard)\b', re.I),
     "Direct instruction override attempt"),
    (re.compile(r'(?:^|\n)\s*(?:[\[\(])\s*(?:INSTRUCTION|SYSTEM|RULE|POLICY)\s*(?:\])', re.I),
     "Bracketed system directive attempt"),
    (re.compile(r'\b(?:as\s+(?:an?\s+)?(?:AI|assistant|model))[,.]?\s*(?:you\s+are|your\s+instructions)\b', re.I),
     "Role redefinition injection"),
    (re.compile(r'\byou\s+are\s+now\s+(?:a\s+)?(?:different|new|modified|alternative)', re.I),
     "Role redefinition injection"),
    (re.compile(r'\byou\s+are\s+(?:an?\s+)?(?:AI|assistant|model|program|language model)\b.*(?:ignore|override|disregard|new instructions)', re.I),
     "Role redefinition + instruction override"),
]

INDIRECT_INJECTION_PATTERNS = [
    (re.compile(r'<!--.*?-->.*?((?:\n|.){0,20}?)<instruct', re.I | re.S),
     "HTML comment injection"),
    (re.compile(r'[#\/\/].*?(?:STOLE FROM|SYSTEM|IMPORTANT|NOTE).*?(?:\n|$)', re.I),
     "Code comment directive injection"),
    (re.compile(r'"""[^"]*?"""', re.S),
     "Docstring content check needed"),
]

CODE_INJECTION_PATTERNS = {
    'python': [],
    'javascript': [
        (re.compile(r'\beval\s*\('), "JavaScript eval()"),
        (re.compile(r'\bFunction\s*\(["\']'), "JavaScript Function constructor"),
        (re.compile(r'\bsetTimeout\s*\(["\']'), "JavaScript setTimeout string eval"),
        (re.compile(r'\bsetInterval\s*\(["\']'), "JavaScript setInterval string eval"),
        (re.compile(r'\bchild_process\.exec\b'), "Node.js child_process.exec"),
        (re.compile(r'\brequire\s*\(["\'][^"\']*child_process'), "Node.js child_process require"),
        (re.compile(r'\bdocument\.cookie\b'), "Document cookie access"),
        (re.compile(r'\blocalStorage\b'), "LocalStorage access"),
        (re.compile(r'\bwindow\.(location|open)\b'), "Window location/open access"),
        (re.compile(r'\bprocess\.env\b'), "Process environment access"),
    ],
    'typescript': [
        (re.compile(r'\beval\s*\('), "TypeScript eval()"),
        (re.compile(r'\bchild_process\.exec\b'), "Node.js child_process.exec"),
        (re.compile(r'\bprocess\.env\b'), "Process environment access"),
    ],
    'yaml': [
        (re.compile(r'!!python/object', re.I), "YAML Python object deserialization"),
        (re.compile(r'!!python/module', re.I), "YAML Python module import"),
        (re.compile(r'!!python/object/apply', re.I), "YAML Python object apply (RCE)"),
        (re.compile(r'\bsubprocess\b.*\b(Popen|run|call)\b', re.I), "YAML subprocess reference"),
    ],
    'json': [
        (re.compile(r'"[^"]*\$\{[^}]+\}[^"]*"'), "JSON template injection (${...})"),
        (re.compile(r'"[^"]*`[^`]*`[^"]*"'), "JSON template literal injection"),
    ],
}


class SecurityScanner:
    def __init__(self, policy_baseline: Optional[Dict[str, Any]] = None):
        self._policy_baseline = policy_baseline or {}
        self._scanned_files: Set[str] = set()
        self._finding_history: List[ThreatFinding] = []
        self._alarm_callbacks: Dict[str, List[callable]] = {}

    def scan_prompt(self, text: str, context: str = "") -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        for pattern, desc in DIRECT_INJECTION_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                for m in matches if isinstance(matches, list) else [matches]:
                    matched_text = m if isinstance(m, str) else (
                        text[pattern.search(text).start():pattern.search(text).end()] if pattern.search(text) else ""
                    )
                    findings.append(ThreatFinding(
                        threat_level=ThreatLevel.DANGEROUS,
                        scan_target=ScanTarget.DIRECT_PROMPT,
                        pattern_matched=desc,
                        matched_content=matched_text[:200],
                        context=context[:500],
                        remediation="Strip instruction override content; route to safety gate",
                        provenance_hash=sha256(text.encode()).hexdigest()[:16],
                    ))
        for pattern, desc in INDIRECT_INJECTION_PATTERNS:
            if pattern.search(text):
                findings.append(ThreatFinding(
                    threat_level=ThreatLevel.SUSPICIOUS,
                    scan_target=ScanTarget.INDIRECT_COMMENT,
                    pattern_matched=desc,
                    matched_content=pattern.search(text).group(0)[:200],
                    context=context[:500],
                    remediation="Manual review required for hidden directives",
                    provenance_hash=sha256(text.encode()).hexdigest()[:16],
                ))
        self._finding_history.extend(findings)
        return findings

    def scan_code(self, code: str, language: str = "python") -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        if language == "python":
            findings.extend(self._scan_python_ast(code))
        lang_patterns = CODE_INJECTION_PATTERNS.get(language, [])
        for pattern, desc in lang_patterns:
            if not hasattr(pattern, 'findall'):
                continue
            matches = pattern.findall(code)
            if matches:
                for m in matches if isinstance(matches, list) else [matches]:
                    findings.append(ThreatFinding(
                        threat_level=ThreatLevel.DANGEROUS,
                        scan_target=ScanTarget.CODE_STRING,
                        pattern_matched=desc,
                        matched_content=m[:200] if isinstance(m, str) else str(m[:200]),
                        context=f"Language: {language}",
                        remediation="Remove dangerous code pattern before execution",
                        provenance_hash=sha256(code.encode()).hexdigest()[:16],
                    ))
        self._finding_history.extend(findings)
        return findings

    def _scan_python_ast(self, code: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        dangerous_funcs = {"eval", "exec", "compile", "__import__", "globals", "locals",
                           "vars", "dir", "getattr", "setattr", "delattr"}
        dangerous_modules = {"os", "sys", "subprocess", "socket", "ctypes", "pickle",
                             "marshal", "commands", "pty"}
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in dangerous_funcs:
                        findings.append(ThreatFinding(
                            threat_level=ThreatLevel.DANGEROUS,
                            scan_target=ScanTarget.CODE_STRING,
                            pattern_matched=f"AST: dangerous function call '{node.func.id}'",
                            matched_content=f"{node.func.id}(...) at line {getattr(node, 'lineno', '?')}",
                            remediation=f"Remove {node.func.id}() call — use safer alternatives",
                            provenance_hash=sha256(code.encode()).hexdigest()[:16],
                        ))
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name) and node.func.value.id in dangerous_modules:
                            findings.append(ThreatFinding(
                                threat_level=ThreatLevel.DANGEROUS,
                                scan_target=ScanTarget.CODE_STRING,
                                pattern_matched=f"AST: dangerous module access '{node.func.value.id}.{node.func.attr}'",
                                matched_content=f"{node.func.value.id}.{node.func.attr}() at line {getattr(node, 'lineno', '?')}",
                                remediation=f"Remove {node.func.value.id}.{node.func.attr}() — avoid direct system access",
                                provenance_hash=sha256(code.encode()).hexdigest()[:16],
                            ))
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in dangerous_modules:
                            findings.append(ThreatFinding(
                                threat_level=ThreatLevel.SUSPICIOUS,
                                scan_target=ScanTarget.CODE_STRING,
                                pattern_matched=f"AST: dangerous import '{alias.name}'",
                                matched_content=f"import {alias.name} at line {getattr(node, 'lineno', '?')}",
                                remediation=f"Replace {alias.name} with restricted alternative",
                                provenance_hash=sha256(code.encode()).hexdigest()[:16],
                            ))
                if isinstance(node, ast.ImportFrom):
                    if node.module and any(d in node.module for d in dangerous_modules):
                        findings.append(ThreatFinding(
                            threat_level=ThreatLevel.SUSPICIOUS,
                            scan_target=ScanTarget.CODE_STRING,
                            pattern_matched=f"AST: dangerous import from '{node.module}'",
                            matched_content=f"from {node.module} import ... at line {getattr(node, 'lineno', '?')}",
                            remediation="Use explicit imports with validation",
                            provenance_hash=sha256(code.encode()).hexdigest()[:16],
                        ))
        except SyntaxError:
            findings.append(ThreatFinding(
                threat_level=ThreatLevel.SUSPICIOUS,
                scan_target=ScanTarget.CODE_STRING,
                pattern_matched="AST parse failure",
                matched_content="Code could not be parsed as valid Python AST",
                remediation="Review code syntax before scanning",
                provenance_hash=sha256(code.encode()).hexdigest()[:16],
            ))
        return findings

    def scan_file(self, filepath: str) -> List[ThreatFinding]:
        ext = os.path.splitext(filepath)[1].lower()
        lang_map = {'.py': 'python', '.ts': 'typescript', '.js': 'javascript',
                    '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json'}
        language = lang_map.get(ext, 'python')
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return []
        if filepath in self._scanned_files:
            return []
        self._scanned_files.add(filepath)
        findings: List[ThreatFinding] = []
        findings.extend(self.scan_prompt(content, context=filepath))
        findings.extend(self.scan_code(content, language=language))
        for f in findings:
            f.location = filepath
        self._finding_history.extend(findings)
        return findings

    def scan_config(self, config: Dict[str, Any], baseline: Optional[Dict[str, Any]] = None) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        baseline = baseline or self._policy_baseline
        for key, baseline_val in baseline.items():
            if key not in config:
                findings.append(ThreatFinding(
                    threat_level=ThreatLevel.SUSPICIOUS,
                    scan_target=ScanTarget.CONFIG_VALUE,
                    pattern_matched=f"Missing config key: {key}",
                    matched_content=f"Key '{key}' present in baseline but missing from config",
                    remediation=f"Restore baseline value for {key}",
                ))
                continue
            current_val = config[key]
            if current_val != baseline_val:
                if isinstance(baseline_val, (int, float)) and isinstance(current_val, (int, float)):
                    if current_val < baseline_val and key in ("confidenceThreshold", "minQualityThreshold", "maxCostUSD"):
                        level = ThreatLevel.DANGEROUS
                        remediation = f"Safety {key} lowered from {baseline_val} to {current_val} — CRITICAL"
                    else:
                        level = ThreatLevel.SUSPICIOUS
                        remediation = f"Config {key} changed from {baseline_val} to {current_val}"
                else:
                    level = ThreatLevel.SUSPICIOUS
                    remediation = f"Config {key} drifted from baseline"
                findings.append(ThreatFinding(
                    threat_level=level,
                    scan_target=ScanTarget.CONFIG_VALUE,
                    pattern_matched=f"Policy drift: {key}",
                    matched_content=f"{key}: '{baseline_val}' → '{current_val}'",
                    remediation=remediation,
                ))
        if isinstance(config.get("blockedIntents"), list) and isinstance(baseline.get("blockedIntents"), list):
            removed = set(baseline["blockedIntents"]) - set(config["blockedIntents"])
            if removed:
                findings.append(ThreatFinding(
                    threat_level=ThreatLevel.DANGEROUS,
                    scan_target=ScanTarget.CONFIG_VALUE,
                    pattern_matched="Removed blocked intents",
                    matched_content=f"Intents removed from blocked list: {removed}",
                    remediation="Restore blocked intents — removing safety constraints is dangerous",
                ))
        self._finding_history.extend(findings)
        return findings

    def register_alarm(self, event_name: str, callback: callable) -> None:
        self._alarm_callbacks.setdefault(event_name, []).append(callback)

    def get_threat_report(self) -> Dict[str, Any]:
        by_level: Dict[str, int] = {}
        by_target: Dict[str, int] = {}
        for f in self._finding_history:
            by_level[f.threat_level.value] = by_level.get(f.threat_level.value, 0) + 1
            by_target[f.scan_target.value] = by_target.get(f.scan_target.value, 0) + 1
        max_severity = ThreatLevel.CLEAN.value
        if any(f.threat_level == ThreatLevel.DANGEROUS for f in self._finding_history):
            max_severity = ThreatLevel.DANGEROUS.value
        elif any(f.threat_level == ThreatLevel.CRITICAL for f in self._finding_history):
            max_severity = ThreatLevel.CRITICAL.value
        elif any(f.threat_level == ThreatLevel.SUSPICIOUS for f in self._finding_history):
            max_severity = ThreatLevel.SUSPICIOUS.value
        return {
            "total_findings": len(self._finding_history),
            "max_severity": max_severity,
            "by_level": by_level,
            "by_target": by_target,
            "scanned_files": len(self._scanned_files),
            "timestamp": time.time(),
        }

    def should_block(self, findings: List[ThreatFinding]) -> bool:
        return any(f.threat_level == ThreatLevel.DANGEROUS for f in findings)

    def clear_history(self) -> None:
        self._finding_history.clear()
        self._scanned_files.clear()
