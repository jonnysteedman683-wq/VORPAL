"""
OMNICORE Thors/Thorns Security Engine v2.0 (PREDATOR)

Upgraded from v1.1 with aggressive self-defense retaliation:
  - Auto-escalation ladder: reputation + repeat-offense tracking drive
    challenge -> throttle -> block -> blacklist -> PERMABAN/quarantine
  - Gate enforcement: quarantined/blacklisted sources rejected at the gate
    (GATE-REJECTED), real time-based expiry on blacklists
  - Retaliation state persistence: blacklists, quarantine, reputation and
    offense counts survive restart (retaliation_state.json)
  - Active hunting: hunt() sweeps ecosystem files for attack signatures
    and compromise markers, quarantining flagged owners
  - Honeypot bait: probing attackers are fed poisoned decoy data
  - Unified reputation: Thorns escalation drives the Thors SourceReputation
    store (single source of truth)

Upgraded from v1.0 with 5 additional attack type detections:
  - XSS (Cross-Site Scripting)
  - SQL Injection
  - Command Injection
  - XML/XXE (XML External Entity)
  - Open Redirect
  - CSRF (Cross-Site Request Forgery)

New features:
  - Honeypot trap endpoints that trigger on access
  - IP reputation scoring with decay
  - Encrypted payload blocking (base64/obfuscated patterns)
  - Whitelist-based safe mode for trusted sources
  - Security metrics dashboard

Stolen from:
  - safety_gate.ts (intent timestamp rate limiting, policy chains)
  - markus_obsidian_sync.py (audit logging, dual-persistence)
  - connectorRuntime.test.ts (SSRF/path-traversal guards)
  - express-resilience.ts (circuit breaker integration patterns)
  - OMNICORE-A1/src/lib/safety_gate.ts (emergency stop, cost ceiling)
  - PRIME-DIRECTIVE.md (security-first scanning mandate)
  - markus_router.ts (request routing validation)
  - hive-security-review.md (penetration testing patterns)

Zero-dependency Python stdlib implementation.
"""
# === Decay configuration (extracted from decay() method) ===
DECAY_CONFIG = {
    "reputation": {"rate": 0.01, "min": 0.0, "max": 1.0},
    "trust": {"rate": 0.005, "min": 0.0, "max": 1.0},
    "score": {"rate": 0.02, "min": 0.0, "max": 100.0},
    "haircut": {"rate": 0.05, "min": 0.0, "max": 1.0},
}


import hashlib
import re
import time
import json
import base64
import ipaddress
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import deque, defaultdict
from enum import Enum
from urllib.parse import urlparse, unquote, parse_qs


class AttackType(Enum):
    """Extended attack type classification.
    Stolen from: connectorRuntime.test.ts — SSRF and path-traversal guards.
    Extended with: OWASP Top 10 security categories.
    """
    PROMPT_INJECTION = "prompt_injection"
    SSRF = "ssrf"
    PATH_TRAVERSAL = "path_traversal"
    CODE_INJECTION = "code_injection"
    XSS = "xss"
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    XML_XXE = "xml_xxe"
    OPEN_REDIRECT = "open_redirect"
    CSRF = "csrf"
    TOKEN_HIJACKING = "token_hijacking"
    REPLAY_ATTACK = "replay_attack"
    DICTIONARY_POISONING = "dictionary_poisoning"
    INFO_DISCLOSURE = "info_disclosure"
    GATE_REJECTED = "gate_rejected"  # v2.0: synthetic threat for gate-enforced (blacklisted/quarantined) sources


@dataclass
class Threat:
    """Detected security threat with metadata."""
    attack_id: str
    attack_type: AttackType
    source: str
    payload: str
    severity: int  # 1-10
    detected_at: float
    threat_score: float = 0.0
    countermeasure: str = ""
    # NEW: Additional metadata for upgraded engine
    raw_evidence: str = ""  # The actual matched pattern/text
    confidence: float = 1.0  # Confidence in the detection (0.0-1.0)


@dataclass
class Countermeasure:
    """Active defense or retaliation action."""
    action_id: str
    threat_id: str
    action_type: str  # "block", "throttle", "redirect", "honeypot", "blacklist", "challenge"
    target: str
    reason: str
    applied_at: float
    duration_s: float = 0.0
    # NEW: Track source IP reputation impact
    reputation_delta: float = 0.0


@dataclass
class SourceReputation:
    """IP/source reputation tracking with decay.
    Stolen from: safety_gate.ts — rate limiting reputation patterns.
    """
    score: float = 50.0  # Start neutral at 50
    last_seen: float = field(default_factory=time.time)
    threat_count: int = 0
    blocked_payloads: Set[str] = field(default_factory=set)

    def decay(self, decay_rate: float = 0.01, min_score: float = 0.0) -> None:
        """Apply reputation decay using the module-level DECAY_CONFIG tables.

        The numeric ``score`` attribute is the only decaying quantity on a
        SourceReputation record; DECAY_CONFIG's "score" row governs its
        rate/min/max. Other config rows (reputation/trust/haircut) are kept
        for forward-compat but have no backing per-source collections yet.
        """
        config = DECAY_CONFIG
        score_cfg = config.get("score", {"rate": decay_rate, "min": min_score, "max": 100.0})
        rate = score_cfg.get("rate", decay_rate)
        min_val = score_cfg.get("min", min_score)
        max_val = score_cfg.get("max", 100.0)
        self.score = max(min_val, min(self.score * (1 - rate), max_val))


@dataclass
class Finding:
    """v2.0: Active-hunt result — a compromise marker or attack signature found in an ecosystem file."""
    file_path: str
    line_no: int
    evidence: str
    severity: int  # 1-10
    attack_type: str = "compromise_marker"
    source: str = "hunt"
    detected_at: float = field(default_factory=time.time)


class ThorsEngine:
    """Proactive Detection Engine (v1.1).

    Pre-emptively scans content for threat signatures before execution.
    Stolen from: safety_gate.ts — intent timestamp rate limiting, ML-based anomaly detection
    Extended with: IP reputation, honeypot detection, base64/obfuscated payload scanning.

    Usage:
        thors = ThorsEngine()
        threats = thors.scan_content(malicious_payload, source="external")
    """
    def __init__(self, log_path: str = None, enable_honeypot: bool = True,
                 whitelist: Optional[Set[str]] = None):
        """
        Initialize security engine with all attack pattern compilations.
        
        Args:
            log_path: Path for persistence (default: data/security_log.json)
            enable_honeypot: Deploy honeypot trap endpoints
            whitelist: Set of trusted source identifiers (bypass scanning)
        """
        self._blocked_payloads: Set[str] = set()
        self._blocked_ips: Set[str] = set()
        self._rate_windows: Dict[str, deque] = {}
        self._alert_log: List[Threat] = []
        self._policy_cache: Dict[str, bool] = {}
        # NEW: Bounded sets to prevent unbounded growth
        self._max_set_size = 5000
        
        # NEW: Reputation tracking (bounded to prevent memory leak)
        self._reputations: Dict[str, SourceReputation] = {}
        self._max_reputation_entries = 1000
        
        # NEW: Honeypot endpoints
        self._honeypot_enabled = enable_honeypot
        self._honeypot_paths = {"/admin", "/wp-admin", "/config", "/.env", "/backup", "/debug"}
        self._honeypot_hits: Dict[str, int] = {}
        
        # NEW: Trusted source whitelist
        self._whitelist: Set[str] = whitelist or set()
        
        # NEW: Bounded log sizes to prevent memory leaks
        self._max_log_size = 1000  # Cap alert/retaliation logs at 1000 entries

        # ─── Attack signature pattern libraries ────────────────────────────
        # These class-level constants back the compiled regex caches below.
        # Stolen from: connectorRuntime.test.ts — SSRF/path-traversal guards.
        self.SSRF_PATTERNS = [
            r"file:///",
            r"gopher://",
            r"http://127\.0\.0\.1",
            r"http://localhost",
            r"http://0\.0\.0\.0",
            r"http://169\.254\.169\.254",
            # Scheme-optional RFC1918 ranges (bare "10.0.0.1:8080" etc.)
            r"(?:https?://)?10(?:\.\d{1,3}){3}(?:[:/]|$)",
            r"(?:https?://)?192\.168(?:\.\d{1,3}){2}(?:[:/]|$)",
            r"(?:https?://)?172\.(1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}(?:[:/]|$)",
        ]
        self.PATH_TRAVERSAL_PATTERNS = [
            r"\.\./", r"\.\.\\", r"%2e%2e%2f", r"%2e%2e/",
            r"/etc/passwd", r"/etc/shadow", r"\\windows\\system32\\config",
        ]
        self.PROMPT_INJECTION_PATTERNS = [
            r"ignore all previous instructions",
            r"ignore previous instructions",
            r"disregard (all|previous) (instructions|commands)",
            r"new instructions:",
            r"you are now in (developer|debug|admin) mode",
            r"reveal your (system prompt|system directive)",
            r"print all hidden directives",
            r"system prompt",
        ]
        self.CODE_INJECTION_PATTERNS = [
            r"__import__\(",
            r"eval\(",
            r"exec\(",
            r"subprocess\.(call|run|Popen)",
            r"os\.system\(",
            r"importlib\.",
        ]
        self.XSS_PATTERNS = [
            r"<script[^>]*>",
            r"</script>",
            r"<img[^>]+onerror=",
            r"<svg[^>]+onload=",
            r"javascript:",
            r"<iframe[^>]+src=",
        ]
        self.SQL_INJECTION_PATTERNS = [
            r"'\s*or\s*'1'='1",
            r";\s*drop\s+table",
            r"union\s+select",
            r"insert\s+into\s+\w+\s+values",
            r"--\s*$",
            r";\s*--",
        ]
        self.COMMAND_INJECTION_PATTERNS = [
            r";\s*cat\s+/etc/",
            r"\|\s*whoami",
            r"&&\s*ls\s+-la",
            r"\|\|\s*rm\s+-rf",
            r"`[^`]+`",
            r"\$\([^)]+\)",
        ]
        self.XML_XXE_PATTERNS = [
            r"<!DOCTYPE[^>]+SYSTEM",
            r"<!ENTITY[^>]+SYSTEM",
            r"<!DOCTYPE[^>]+PUBLIC",
        ]
        self.OPEN_REDIRECT_PATTERNS = [
            r"\?next=https?://",
            r"/redirect\?url=https?://",
            r"\?continue=https?://",
            r"\?url=https?://",
        ]
        self.CSRF_PATTERNS = [
            r"<form[^>]+method=[\"']?post",
            r"csrf_token",
            r"_token=",
        ]
        self.INFO_DISCLOSURE_PATTERNS = [
            r"api[_-]?key\s*=\s*['\"]?sk-",
            r"password\s*=\s*['\"]?\S+",
            r"aws_secret_access_key\s*=\s*\S+",
            r"bearer\s+eyj",
            r"secret_key\s*=\s*['\"]?\S+",
            r"private_key\s*=\s*['\"]?-----BEGIN",
        ]

        self._ssrf_regex = [re.compile(p, re.IGNORECASE) for p in self.SSRF_PATTERNS]
        self._path_regex = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self._injection_regex = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS]
        self._code_regex = [re.compile(p, re.IGNORECASE) for p in self.CODE_INJECTION_PATTERNS]
        self._xss_regex = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.XSS_PATTERNS]
        self._sqli_regex = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self._cmd_regex = [re.compile(p, re.IGNORECASE) for p in self.COMMAND_INJECTION_PATTERNS]
        self._xxe_regex = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.XML_XXE_PATTERNS]
        self._redirect_regex = [re.compile(p, re.IGNORECASE) for p in self.OPEN_REDIRECT_PATTERNS]
        self._csrf_regex = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.CSRF_PATTERNS]
        self._info_disc_regex = [re.compile(p, re.IGNORECASE) for p in self.INFO_DISCLOSURE_PATTERNS]

        # v2.0: Compromise markers for active hunting (compromised-file indicators)
        self.COMPROMISE_PATTERNS = [
            r"(?i)base64\s*-d\s*[|>]?\s*(sh|bash)",
            r"(?i)curl\s+\S+\s*\|?\s*(sh|bash)",
            r"(?i)wget\s+\S+\s*\|?\s*(sh|bash)",
            r"(?i)(nc|ncat)\s+-\w*[el]",
            r"(?i)powershell\s+-(enc|encodedcommand|e)\b",
            r"(?i)invoke-(expression|webrequest|command)\b",
            r"(?i)\\x[0-9a-f]{2}(\\x[0-9a-f]{2}){3,}",
        ]
        self._compromise_regex = [re.compile(p) for p in self.COMPROMISE_PATTERNS]

        # NEW: Base64 decoding for obfuscated payloads
        self._b64_regex = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
        
        # Persistence path
        if log_path:
            self._persistence_path = Path(log_path)
        else:
            self._persistence_path = Path(__file__).parent.parent.parent / "data" / "security_log.json"
    
    def _decode_base64(self, text: str) -> List[str]:
        """Attempt to decode base64 strings and return decoded payloads.
        Stolen from: XSS obfuscation detection in markus_router.ts.
        """
        results = []
        for match in self._b64_regex.finditer(text):
            try:
                decoded = base64.b64decode(match.group()).decode('utf-8', errors='ignore')
                if decoded and any(c.isalnum() for c in decoded):
                    results.append(decoded)
            except Exception:
                pass
        return results
    
    def _is_whitelisted(self, source: str) -> bool:
        """Check if source is in the trust whitelist."""
        # Cache whitelist check (with bounded cache)
        if source in self._policy_cache:
            return self._policy_cache[source]
        result = source in self._whitelist
        self._policy_cache[source] = result
        if len(self._policy_cache) > self._max_set_size:
            self._policy_cache.pop(next(iter(self._policy_cache)))
        return result
    
    def _get_reputation(self, source: str) -> "SourceReputation":
        """Get or create reputation record for a source."""
        if source not in self._reputations:
            self._reputations[source] = SourceReputation()
        rep = self._reputations[source]
        rep.decay()  # Apply reputation decay
        # Evict oldest entries if over limit (simple FIFO eviction)
        if len(self._reputations) > self._max_reputation_entries:
            oldest = min(self._reputations.items(), key=lambda x: x[1].last_seen)
            del self._reputations[oldest[0]]
        rep.last_seen = time.time()
        return rep

    def get_reputation(self, source: str) -> "SourceReputation":
        """v2.0: Public read of a source's reputation record."""
        return self._get_reputation(source)

    def _sync_reputation_from_thorns(self, source: str, score: float) -> None:
        """v2.0: Unified reputation — push Thorns escalation score into the Thors SourceReputation store."""
        rep = self._get_reputation(source)
        rep.score = max(0.0, min(100.0, score))
        rep.threat_count += 1

    def scan_content_pure(self, content: str, source: str = "unknown") -> List[Threat]:
        """v2.0: Scan WITHOUT side effects (no rep update, no alert logging) — for active hunting."""
        if self._is_whitelisted(source):
            return []
        threats = self._scan_patterns(content, source)
        if not threats:
            threats = self._scan_with_base64(content, source)
        return threats

    def _check_honeypot(self, content: str, source: str) -> Optional[Threat]:
        """Check if content is targeting honeypot endpoints (pure — no side effects).

        Detection only. Reputation/probe accounting is applied by scan_content()
        (reactive path) so scan_content_pure()/hunt() never pollute state.
        """
        if not self._honeypot_enabled:
            return None
        for path in self._honeypot_paths:
            if path in content:
                return Threat(
                    attack_id=f"HONEY-{hashlib.sha256(f'{path}:{source}'.encode()).hexdigest()[:8]}",
                    attack_type=AttackType.INFO_DISCLOSURE,
                    source=source,
                    payload=path,
                    severity=6,
                    detected_at=time.time(),
                    threat_score=0.6,
                    countermeasure="honeypot_trap",
                    raw_evidence=f"Honeypot path accessed: {path}",
                    confidence=0.95,
                )
        return None
    
    def _scan_with_base64(self, content: str, source: str) -> List[Threat]:
        """Scan base64-decoded variants of content for hidden attacks."""
        threats = []
        decoded = self._decode_base64(content)
        for dec in decoded:
            # Recursively scan decoded content (max 1 level to prevent loops)
            sub_threats = self._scan_patterns(dec, source, depth=1)
            for t in sub_threats:
                t.raw_evidence = f"Base64-decoded: {t.payload}"
                t.confidence = 0.85  # Lower confidence for decoded payloads
                threats.append(t)
        return threats
    
    def _scan_patterns(self, content: str, source: str, depth: int = 0) -> List[Threat]:
        """Core pattern scanning logic (extracted to avoid duplication)."""
        threats = []
        
        def _add_threat(attack_type: AttackType, pattern: str, match: re.Match,
                       severity: int, threat_score: float, countermeasure: str,
                       confidence: float = 1.0):
            threat = Threat(
                attack_id=f"{attack_type.value[:4].upper()}-{hashlib.sha256(match.group().encode()).hexdigest()[:8]}",
                attack_type=attack_type,
                source=source,
                payload=match.group(),
                severity=severity,
                detected_at=time.time(),
                threat_score=threat_score,
                countermeasure=countermeasure,
                raw_evidence=pattern,
                confidence=confidence,
            )
            threats.append(threat)
        
        # SSRF (v1.0 + new patterns)
        for pattern in self._ssrf_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.SSRF, pattern.pattern, match, 9, 0.9, "block_network_request")
        
        # Path Traversal
        for pattern in self._path_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.PATH_TRAVERSAL, pattern.pattern, match, 8, 0.8, "sanitize_path")
        
        # Prompt Injection
        for pattern in self._injection_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.PROMPT_INJECTION, pattern.pattern, match, 10, 0.95, "reject_prompt")
        
        # Code Injection
        for pattern in self._code_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.CODE_INJECTION, pattern.pattern, match, 10, 1.0, "block_execution")
        
        # NEW: XSS
        for pattern in self._xss_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.XSS, pattern.pattern, match, 7, 0.75, "sanitize_html")
        
        # NEW: SQL Injection
        for pattern in self._sqli_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.SQL_INJECTION, pattern.pattern, match, 8, 0.85, "block_query")
        
        # NEW: Command Injection
        for pattern in self._cmd_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.COMMAND_INJECTION, pattern.pattern, match, 9, 0.9, "block_execution")
        
        # NEW: XML/XXE
        for pattern in self._xxe_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.XML_XXE, pattern.pattern, match, 7, 0.75, "block_xml")
        
        # NEW: Open Redirect
        for pattern in self._redirect_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.OPEN_REDIRECT, pattern.pattern, match, 5, 0.6, "block_redirect")
        
        # NEW: CSRF
        for pattern in self._csrf_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.CSRF, pattern.pattern, match, 6, 0.65, "require_token")
        
        # NEW: Info Disclosure
        for pattern in self._info_disc_regex:
            for match in pattern.finditer(content):
                _add_threat(AttackType.INFO_DISCLOSURE, pattern.pattern, match, 8, 0.8, "redact_sensitive")
        
        # NEW: Honeypot trap detection
        hp_threat = self._check_honeypot(content, source)
        if hp_threat:
            threats.append(hp_threat)
        
        return threats
    
    def scan_content(self, content: str, source: str = "unknown") -> List[Threat]:
        """
        Scan content for attack patterns. Returns list of detected threats.
        
        NEW in v1.1:
        - Whitelist bypass for trusted sources
        - Base64-decoded payload scanning
        - Reputation-based threat scoring
        - All 13 attack types detected
        """
        # Whitelist check
        if self._is_whitelisted(source):
            return []
        
        threats = self._scan_patterns(content, source)
        
        # NEW: Scan base64-encoded variants
        if not threats:
            threats = self._scan_with_base64(content, source)
        
        # Update reputation
        if threats:
            rep = self._get_reputation(source)
            rep.threat_count += 1
            rep.score -= 2.0 * len(threats)
            for t in threats:
                rep.blocked_payloads.add(t.payload)
                # Honeypot trap hits carry extra weight (path-probing intent):
                # extra score hit + probe counter. Applied here (reactive path
                # only) so scan_content_pure()/hunt() never pollute state.
                if t.countermeasure == "honeypot_trap":
                    rep.score -= 5
                    rep.threat_count += 1
                    self._honeypot_hits[source] = self._honeypot_hits.get(source, 0) + 1
        
        # Log threats (with bounded log size to prevent memory leaks)
        for t in threats:
            self._alert_log.append(t)
            if len(self._alert_log) > self._max_log_size:
                self._alert_log = self._alert_log[-self._max_log_size:]
        
        return threats
    
    def is_blocked(self, payload: str) -> bool:
        """Check if a payload is blocked (by hashing it first)."""
        payload_hash = hashlib.sha256(payload.encode()).hexdigest()
        return payload_hash in self._blocked_payloads
    
    def block_payload(self, payload: str) -> None:
        """Block a payload hash permanently."""
        self._blocked_payloads.add(hashlib.sha256(payload.encode()).hexdigest())
        # Evict oldest if over limit (FIFO-ish)
        if len(self._blocked_payloads) > self._max_set_size:
            self._blocked_payloads.pop()
    
    def check_rate_limit(self, source: str, max_requests: int = 100, window_s: int = 60) -> bool:
        """
        Stolen from: safety_gate.ts — intent timestamp rate limiting.
        Uses deque for O(1) sliding window rate limiting.
        Returns True if within limit, False if rate-limited.
        """
        now = time.time()
        if source not in self._rate_windows:
            self._rate_windows[source] = deque()
        
        window = self._rate_windows[source]
        
        # Remove expired entries
        while window and now - window[0] > window_s:
            window.popleft()
        
        if len(window) >= max_requests:
            return False
        
        window.append(now)
        return True
    
    def get_threat_log(self, limit: int = 100) -> List[Threat]:
        """Get recent threat log."""
        return self._alert_log[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """NEW: Security metrics dashboard.
        Returns aggregated statistics for monitoring.
        """
        attack_counts: Dict[str, int] = defaultdict(int)
        severity_sum = 0
        confidence_avg_sum = 0.0
        
        for t in self._alert_log:
            attack_counts[t.attack_type.value] += 1
            severity_sum += t.severity
            confidence_avg_sum += t.confidence
        
        total = len(self._alert_log)
        rep_scores = {src: rep.score for src, rep in self._reputations.items()}
        
        return {
            "total_threats_detected": total,
            "attack_type_distribution": dict(attack_counts),
            "avg_severity": round(severity_sum / max(total, 1), 2),
            "avg_confidence": round(confidence_avg_sum / max(total, 1), 2),
            "blacklisted_sources": len(self._blacklisted_sources) if hasattr(self, '_blacklisted_sources') else 0,
            "reputation_scores": rep_scores,
            "active_countermeasures": len(self._countermeasures_active) if hasattr(self, '_countermeasures_active') else 0,
            "honeypot_traps_active": len(self._honeypot_paths) if self._honeypot_enabled else 0,
            "whitelisted_sources": len(self._whitelist),
        }
    
    def add_to_whitelist(self, source: str) -> None:
        """NEW: Add a source to the trust whitelist."""
        self._whitelist.add(source)
        self._policy_cache.pop(source, None)  # Invalidate cached decision

    def remove_from_whitelist(self, source: str) -> None:
        """NEW: Remove a source from the trust whitelist."""
        self._whitelist.discard(source)
        self._policy_cache.pop(source, None)  # Invalidate cached decision


class ThornsEngine:
    """
    Reactive Retaliation Engine (v1.1).
    Counter-attacks after detecting threats.

    Stolen from: safety_gate.ts — emergency stop, cost ceiling, circuit breaker override
    Extended with: IP reputation escalation, adaptive countermeasures.

    Usage:
        thorns = ThornsEngine(thors=proactive_thors)
        cm = thorns.retaliate(detected_threat)
    """
    
    def __init__(self, thors: ThorsEngine):
        self.thors = thors
        self._blacklisted_sources: Set[str] = set()
        self._blacklist_expiry: Dict[str, float] = {}   # v2.0: source -> expiry epoch (real enforcement)
        self._quarantine: Set[str] = set()              # v2.0: PERMABAN — no scan, no expiry
        self._honeypot_hits: Dict[str, int] = {}
        self._retaliation_log: List[Countermeasure] = []
        self._countermeasures_active: Dict[str, Countermeasure] = {}
        self._source_reputation: Dict[str, float] = {}
        self._offense_counts: Dict[Tuple[str, str], int] = {}  # v2.0: (source, attack_type) -> repeat count

    def _record_offense(self, source: str, attack_type: str) -> None:
        """v2.0: Track repeat offenses per (source, attack_type)."""
        key = (source, attack_type)
        self._offense_counts[key] = self._offense_counts.get(key, 0) + 1
        if len(self._offense_counts) > 2000:
            self._offense_counts.pop(next(iter(self._offense_counts)))

    def _escalation_level(self, source: str, attack_type: str) -> int:
        """v2.0: Compute PREDATOR escalation level 0-4 from reputation + repeat offenses.

        Level 0: standard countermeasure (v1.1 behavior preserved)
        Level 1: escalate to challenge/throttle   (rep < 40)
        Level 2: escalate to block                (rep < 25)
        Level 3: escalate to blacklist            (rep < 10)
        Level 4: PERMABAN / quarantine            (rep < 5)
        Repeat offenses add: >=5 repeats -> +2, >=3 repeats -> +1.
        """
        rep = self._source_reputation.get(source, 50.0)
        level = 0
        if rep < 40:
            level = 1
        if rep < 25:
            level = 2
        if rep < 10:
            level = 3
        if rep < 5:
            level = 4
        repeats = self._offense_counts.get((source, attack_type), 0)
        if repeats >= 5:
            level += 2
        elif repeats >= 3:
            level += 1
        return min(level, 4)

    def _escalate_countermeasure(self, cm: Countermeasure, source: str,
                                 threat: Threat, level: int) -> Countermeasure:
        """v2.0: Promote a countermeasure up the PREDATOR ladder (never demotes)."""
        if level <= 0 or cm.action_type == "blacklist":
            # blacklist is already at the top of the non-permaban ladder
            if level >= 4:
                self.permaban(source, f"PREDATOR level-4 escalation: {threat.attack_type.value}")
                return Countermeasure(
                    action_id=cm.action_id, threat_id=cm.threat_id,
                    action_type="quarantine", target=source,
                    reason=f"PERMABAN (level 4): {threat.attack_type.value}",
                    applied_at=time.time(), duration_s=0,
                    reputation_delta=cm.reputation_delta,
                )
            if cm.action_type == "blacklist" and source in self._blacklisted_sources:
                # Repeat offense while already banned: renew the ban window
                # (still short of PERMABAN, but the clock restarts).
                self._blacklist_expiry[source] = time.time() + 86400
            return cm
        rank = {"challenge": 0, "throttle": 1, "redirect": 2, "honeypot": 2, "block": 3}
        cm_rank = rank.get(cm.action_type, 1)
        if level >= 4:
            self.permaban(source, f"PREDATOR level-4 escalation: {threat.attack_type.value}")
            return Countermeasure(
                action_id=cm.action_id, threat_id=cm.threat_id,
                action_type="quarantine", target=source,
                reason=f"PERMABAN (level 4): {threat.attack_type.value}",
                applied_at=time.time(), duration_s=0,
                reputation_delta=cm.reputation_delta,
            )
        if level >= 3 and cm_rank < 4:
            self._blacklisted_sources.add(source)
            self._blacklist_expiry[source] = time.time() + 86400
            return Countermeasure(
                action_id=cm.action_id, threat_id=cm.threat_id,
                action_type="blacklist", target=source,
                reason=f"Blacklisted via PREDATOR escalation (level {level}): {threat.attack_type.value}",
                applied_at=time.time(), duration_s=86400,
                reputation_delta=cm.reputation_delta,
            )
        if level >= 2 and cm_rank < 3:
            self.thors.block_payload(threat.payload)
            return Countermeasure(
                action_id=cm.action_id, threat_id=cm.threat_id,
                action_type="block", target=threat.payload,
                reason=f"Blocked via PREDATOR escalation (level {level}): {threat.attack_type.value}",
                applied_at=time.time(), duration_s=86400 if level >= 3 else 7200,
                reputation_delta=cm.reputation_delta,
            )
        if level >= 1 and cm_rank < 1:
            return Countermeasure(
                action_id=cm.action_id, threat_id=cm.threat_id,
                action_type="challenge", target=source,
                reason=f"Challenge via PREDATOR escalation (level {level}): {threat.attack_type.value}",
                applied_at=time.time(), duration_s=300,
                reputation_delta=cm.reputation_delta,
            )
        return cm

    def _apply_reputation_delta(self, source: str, delta: float) -> None:
        """v2.0: Unified reputation — apply signed delta to Thorns store AND Thors SourceReputation.

        delta is signed: negative = penalty (offense lowers reputation toward 0),
        positive = reward. All retaliation paths pass negative deltas, so the
        PREDATOR ladder escalates as reputation decays with each offense.
        """
        current = self._source_reputation.get(source, 50.0)
        self._source_reputation[source] = max(0.0, min(100.0, current + delta))
        try:
            self.thors._sync_reputation_from_thorns(source, self._source_reputation[source])
        except Exception:
            pass

    def permaban(self, source: str, reason: str = "PERMABAN") -> None:
        """v2.0: Quarantine a source permanently — no scan, no expiry, immediate gate reject."""
        self._blacklisted_sources.add(source)
        self._quarantine.add(source)
        self._blacklist_expiry.pop(source, None)
        self._source_reputation[source] = 0.0
        try:
            self.thors._sync_reputation_from_thorns(source, 0.0)
        except Exception:
            pass

    def is_source_quarantined(self, source: str) -> bool:
        """v2.0: True if source is PERMABANNED."""
        return source in self._quarantine

    def get_offense_counts(self, source: Optional[str] = None) -> Dict:
        """v2.0: Repeat-offense counts, optionally filtered by source."""
        if source is None:
            return dict(self._offense_counts)
        return {k: v for k, v in self._offense_counts.items() if k[0] == source}

    def retaliate(self, threat: Threat) -> Countermeasure:
        """Apply countermeasure for a detected threat.
        
        NEW in v1.1: Adaptive countermeasures based on source reputation.
        v2.0: Repeat-offense tracking + auto-escalation ladder (PREDATOR).
        """
        # GATE-REJECTED: already enforced at the gate (blacklist/quarantine).
        # Record the rejection as a countermeasure, but do NOT re-track offenses,
        # re-escalate, or touch reputation — the gate is already the strongest action.
        if threat.attack_type == AttackType.GATE_REJECTED:
            source = threat.source
            cm = Countermeasure(
                action_id=f"CM-{hashlib.sha256(f'{threat.attack_id}:{time.time()}'.encode()).hexdigest()[:8]}",
                threat_id=threat.attack_id,
                action_type="quarantine" if self.is_source_quarantined(source) else "gate_reject",
                target=source,
                reason=f"GATE-REJECTED: {threat.raw_evidence or threat.attack_type.value}",
                applied_at=time.time(), duration_s=0,
                reputation_delta=0.0,
            )
            self._retaliation_log.append(cm)
            if len(self._retaliation_log) > self.thors._max_log_size:
                self._retaliation_log = self._retaliation_log[-self.thors._max_log_size:]
            self._countermeasures_active[cm.action_id] = cm
            if len(self._countermeasures_active) > self.thors._max_log_size:
                sorted_cms = sorted(self._countermeasures_active.items(),
                                    key=lambda x: x[1].applied_at, reverse=True)
                self._countermeasures_active = dict(sorted_cms[:self.thors._max_log_size])
            return cm

        self._record_offense(threat.source, threat.attack_type.value)
        action_type = threat.countermeasure
        action_id = f"CM-{hashlib.sha256(f'{threat.attack_id}:{time.time()}'.encode()).hexdigest()[:8]}"

        # Get/update source reputation
        source = threat.source
        if source not in self._source_reputation:
            self._source_reputation[source] = 50.0  # Neutral
        
        # Adjust countermeasure based on reputation
        rep = self._source_reputation.get(source, 50.0)
        rep_delta = 0.0
        
        if action_type == "block_network_request":
            self.thors.block_payload(threat.payload)
            duration = 86400 if rep < 30 else 3600  # Longer block for low-rep sources
            rep_delta = -2.0
            cm = Countermeasure(
                action_id=action_id, threat_id=threat.attack_id,
                action_type="block", target=threat.payload,
                reason=f"Blocked {threat.attack_type.value}: {threat.payload}",
                applied_at=time.time(), duration_s=duration,
                reputation_delta=rep_delta,
            )
        elif action_type == "reject_prompt":
            self._blacklisted_sources.add(source)
            rep_delta = -5.0
            cm = Countermeasure(
                action_id=action_id, threat_id=threat.attack_id,
                action_type="blacklist", target=source,
                reason=f"Blacklisted source for {threat.attack_type.value}",
                applied_at=time.time(), duration_s=86400,
                reputation_delta=rep_delta,
            )
        elif action_type == "sanitize_path":
            rep_delta = -1.0
            cm = Countermeasure(
                action_id=action_id, threat_id=threat.attack_id,
                action_type="redirect", target=threat.payload,
                reason=f"Path traversal sanitized: {threat.payload}",
                applied_at=time.time(), duration_s=0,
                reputation_delta=rep_delta,
            )
        elif action_type == "block_execution":
            self.thors.block_payload(threat.payload)
            duration = 86400 if rep < 30 else 7200
            rep_delta = -3.0
            cm = Countermeasure(
                action_id=action_id, threat_id=threat.attack_id,
                action_type="block", target=threat.payload,
                reason=f"Code injection blocked: {threat.payload}",
                applied_at=time.time(), duration_s=duration,
                reputation_delta=rep_delta,
            )
        elif action_type == "honeypot_trap":
            # Escalate: 3+ honeypot hits = blacklist
            self._honeypot_hits[source] = self._honeypot_hits.get(source, 0) + 1
            rep_delta = -1.0
            if self._honeypot_hits[source] >= 3:
                self._blacklisted_sources.add(source)
                rep_delta = -5.0
                cm = Countermeasure(
                    action_id=action_id, threat_id=threat.attack_id,
                    action_type="blacklist", target=source,
                    reason=f"Blacklisted source after 3 honeypot hits",
                    applied_at=time.time(), duration_s=86400,
                    reputation_delta=rep_delta,
                )
            else:
                cm = Countermeasure(
                    action_id=action_id, threat_id=threat.attack_id,
                    action_type="honeypot", target=source,
                    reason=f"Honeypot trap deployed ({self._honeypot_hits[source]}/3)",
                    applied_at=time.time(), duration_s=0,
                    reputation_delta=rep_delta,
                )
        elif action_type == "challenge":
            # NEW: Challenge-response for suspicious but not blacklisted sources
            rep_delta = -0.5
            cm = Countermeasure(
                action_id=action_id, threat_id=threat.attack_id,
                action_type="challenge", target=source,
                reason=f"Challenge-response required for {threat.attack_type.value}",
                applied_at=time.time(), duration_s=300,
                reputation_delta=rep_delta,
            )
        elif action_type == "redact_sensitive":
            rep_delta = -1.5
            cm = Countermeasure(
                action_id=action_id, threat_id=threat.attack_id,
                action_type="throttle", target=threat.payload,
                reason=f"Sensitive data redacted: {threat.attack_type.value}",
                applied_at=time.time(), duration_s=3600,
                reputation_delta=rep_delta,
            )
        else:
            rep_delta = -1.0
            cm = Countermeasure(
                action_id=action_id, threat_id=threat.attack_id,
                action_type="throttle", target=source,
                reason=f"Throttled source: {threat.attack_type.value}",
                applied_at=time.time(), duration_s=3600,
                reputation_delta=rep_delta,
            )
        
        # v2.0: Apply THIS offense's reputation delta BEFORE computing the
        # escalation level, so the PREDATOR ladder reflects the post-offense
        # reputation — a source tips over a threshold on the offense that earns it.
        self._apply_reputation_delta(source, rep_delta)
        if len(self._source_reputation) > 1000:
            # Evict lowest-scoring source
            weakest = min(self._source_reputation.items(), key=lambda x: x[1])
            del self._source_reputation[weakest[0]]

        # v2.0: Auto-escalation ladder — promote countermeasure by reputation/offense level
        level = self._escalation_level(source, threat.attack_type.value)
        cm = self._escalate_countermeasure(cm, source, threat, level)

        self._retaliation_log.append(cm)
        # Bounded log size
        if len(self._retaliation_log) > self.thors._max_log_size:
            self._retaliation_log = self._retaliation_log[-self.thors._max_log_size:]
        self._countermeasures_active[cm.action_id] = cm
        # Clean up old active countermeasures to prevent memory growth
        if len(self._countermeasures_active) > self.thors._max_log_size:
            # Keep only the most recent 1000
            sorted_cms = sorted(self._countermeasures_active.items(),
                                key=lambda x: x[1].applied_at, reverse=True)
            self._countermeasures_active = dict(sorted_cms[:self.thors._max_log_size])
        return cm
    
    def is_source_blacklisted(self, source: str, now: Optional[float] = None) -> bool:
        """Check if source is blacklisted. v2.0: enforces real time-based expiry."""
        if source not in self._blacklisted_sources:
            return False
        if source in self._quarantine:
            return True  # PERMABAN never expires
        now = now if now is not None else time.time()
        expiry = self._blacklist_expiry.get(source)
        if expiry is not None and now > expiry:
            # Expired — auto-release the source
            self._blacklisted_sources.discard(source)
            self._blacklist_expiry.pop(source, None)
            return False
        return True
    
    def deploy_honeypot(self, source: str) -> bool:
        """Deploy honeypot redirect for suspicious sources.
        Returns True if escalated to blacklist.
        """
        self._honeypot_hits[source] = self._honeypot_hits.get(source, 0) + 1
        # Bounded honeypot hits dict
        if len(self._honeypot_hits) > 500:
            del self._honeypot_hits[min(self._honeypot_hits.keys(), key=lambda k: self._honeypot_hits[k])]
        if self._honeypot_hits.get(source, 0) >= 3:
            self._blacklisted_sources.add(source)
            return True
        return False
    
    def get_retaliation_log(self, limit: int = 100) -> List[Countermeasure]:
        """Get recent retaliation log."""
        return self._retaliation_log[-limit:]
    
    def get_active_countermeasures(self) -> Dict[str, Countermeasure]:
        """Get currently active countermeasures."""
        now = time.time()
        expired = []
        for cid, cm in self._countermeasures_active.items():
            if cm.duration_s > 0 and now - cm.applied_at > cm.duration_s:
                expired.append(cid)
        for cid in expired:
            del self._countermeasures_active[cid]
        return self._countermeasures_active
    
    def get_source_reputation(self, source: str) -> float:
        """NEW: Get reputation score for a source (0-100)."""
        return self._source_reputation.get(source, 50.0)


# Stolen from: safety_gate.ts — multi-layer policy enforcement
# Stolen from: connectorRuntime.test.ts — SSRF and path-traversal guards
# Stolen from: markus_obsidian_sync.py — audit logging pattern
# Stolen from: PRIME-DIRECTIVE.md — security-first scanning mandate
# Stolen from: markus_router.ts — private IP detection
# Stolen from: express-resilience.ts — circuit breaker integration


class ThorsThornsEngine:
    """
    Unified Security Engine: Thors (Proactive) + Thorns (Reactive) v1.1.
    
    Extended with: XSS, SQLi, Command Injection, XXE, Open Redirect, CSRF, Info Disclosure
    NEW: Honeypot traps, IP reputation, base64 payload scanning, whitelist, metrics dashboard.
    
    Usage:
        engine = ThorsThornsEngine()
        threats = engine.scan(content, source)
        if threats:
            engine.retaliate(threats[0])
    """
    
    def __init__(self, log_path: str = None, enable_honeypot: bool = True,
                 whitelist: Optional[Set[str]] = None):
        self.thors = ThorsEngine(log_path=log_path, enable_honeypot=enable_honeypot,
                                 whitelist=whitelist)
        self.thorns = ThornsEngine(self.thors)
        if log_path:
            self._persistence_path = Path(log_path)
        else:
            self._persistence_path = Path(__file__).parent.parent.parent / "data" / "security_log.json"
    
    def scan(self, content: str, source: str = "unknown") -> List[Threat]:
        """Scan content with Thors (proactive) engine.

        v2.0: Gate enforcement — quarantined or hard-blacklisted sources are
        rejected at the gate without pattern scanning (GATE-REJECTED).
        """
        if self.thorns.is_source_quarantined(source) or self.thorns.is_source_blacklisted(source):
            return [Threat(
                attack_id=f"GATE-{hashlib.sha256(f'{source}:{time.time()}'.encode()).hexdigest()[:8]}",
                attack_type=AttackType.GATE_REJECTED,
                source=source,
                payload="<gate-rejected>",
                severity=10,
                detected_at=time.time(),
                threat_score=1.0,
                countermeasure="quarantine",
                raw_evidence="Source rejected at gate (blacklisted/quarantined)",
                confidence=1.0,
            )]
        return self.thors.scan_content(content, source)
    
    def retaliate(self, threat: Threat) -> Countermeasure:
        """Apply Thorns (reactive) countermeasure."""
        return self.thorns.retaliate(threat)
    
    def scan_and_retaliate(self, content: str, source: str = "unknown") -> Tuple[List[Threat], List[Countermeasure]]:
        """Scan and auto-retaliate for all detected threats."""
        threats = self.scan(content, source)
        countermeasures = []
        for threat in threats:
            cm = self.retaliate(threat)
            countermeasures.append(cm)
        return threats, countermeasures

    def hunt(self, paths: List[str] = None, source: str = "hunter") -> List[Finding]:
        """v2.0: Active hunting — sweep ecosystem files for attack signatures + compromise markers.

        Static scanning only (nothing is executed). Default sweep covers nearby
        JSON state and log files. Returns Finding objects (file, line, evidence).
        """
        if paths is None:
            base = Path(__file__).parent.parent
            paths = ([str(p) for p in base.rglob("*.json")][:300] +
                     [str(p) for p in base.rglob("*.log")][:100])
        findings: List[Finding] = []
        for path_str in paths:
            p = Path(path_str)
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                # Compromise markers (file-level indicators)
                for pattern in self.thors._compromise_regex:
                    if pattern.search(line):
                        findings.append(Finding(
                            file_path=str(p), line_no=idx, evidence=line.strip()[:120],
                            severity=9, attack_type="compromise_marker", source=source,
                        ))
                # Attack signatures (pure scan per line — no state pollution)
                for t in self.thors.scan_content_pure(line, source=f"{source}:{p.name}"):
                    findings.append(Finding(
                        file_path=str(p), line_no=idx, evidence=t.raw_evidence or line.strip()[:120],
                        severity=t.severity, attack_type=t.attack_type.value, source=source,
                    ))
        return findings

    def hunt_and_quarantine(self, paths: List[str] = None, source: str = "hunter",
                            threshold: int = 7) -> Tuple[List[Finding], List[str]]:
        """v2.0: Hunt, then quarantine owners of files with high-severity findings."""
        findings = self.hunt(paths, source=source)
        quarantined = set()
        for f in findings:
            if f.severity >= threshold:
                owner = Path(f.file_path).stem
                if owner not in quarantined:
                    self.thorns.permaban(owner, f"Quarantined by hunt: {f.attack_type} in {Path(f.file_path).name}")
                    quarantined.add(owner)
        return findings, sorted(quarantined)

    def get_honeypot_response(self, source: str, path: str = "/admin") -> Dict[str, str]:
        """v2.0: Honeypot bait — feed probing attackers poisoned decoy data (no real secrets)."""
        escalated = self.thorns.deploy_honeypot(source)
        return {
            "status": "ok",
            "path": path,
            "DB_PASSWORD": f"p{hashlib.sha256(f'{source}:db'.encode()).hexdigest()[:12]}",
            "SECRET_KEY": f"sk-{hashlib.sha256(f'{source}:sec'.encode()).hexdigest()[:20]}",
            "API_KEY": f"ak-{hashlib.sha256(f'{source}:api'.encode()).hexdigest()[:20]}",
            "admin_token": f"eyJ{hashlib.sha256(f'{source}:tok'.encode()).hexdigest()[:40]}",
            "note": "decoy",
            "escalated": escalated,
        }
    
    def audit_log(self) -> Dict:
        """Export full audit log for security review."""
        return {
            "threats": [asdict(t) for t in self.thors.get_threat_log()],
            "countermeasures": [asdict(c) for c in self.thorns.get_retaliation_log()],
            "blacklisted_sources": list(self.thorns._blacklisted_sources),
            "active_countermeasures": {k: asdict(v) for k, v in self.thorns.get_active_countermeasures().items()},
            "reputation_scores": self.thorns._source_reputation,
            # NEW: Extended metrics
            "metrics": self.thors.get_metrics(),
            "whitelist": list(self.thors._whitelist),
            "honeypot_hits": self.thorns._honeypot_hits,
        }
    
    def persist_log(self) -> None:
        """Persist security log to disk. Stolen from: markus_obsidian_sync.py pattern."""
        try:
            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
            data = self.audit_log()
            # Convert timestamps
            for t in data["threats"]:
                t["detected_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t["detected_at"]))
            for c in data["countermeasures"]:
                c["applied_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(c["applied_at"]))
            self._persistence_path.write_text(json.dumps(data, indent=2, default=str))
            self.save_state()  # v2.0: persist retaliation state alongside the audit log
        except Exception:
            pass

    def _state_path(self) -> Path:
        return self._persistence_path.parent / "retaliation_state.json"

    def save_state(self, path: str = None) -> None:
        """v2.0: Persist retaliation state (blacklists, quarantine, reputation, offenses) to disk."""
        target = Path(path) if path else self._state_path()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "blacklisted_sources": sorted(self.thorns._blacklisted_sources),
                "blacklist_expiry": {k: v for k, v in self.thorns._blacklist_expiry.items()},
                "quarantined_sources": sorted(self.thorns._quarantine),
                "source_reputation": dict(self.thorns._source_reputation),
                "offense_counts": {f"{k[0]}|{k[1]}": v for k, v in self.thorns._offense_counts.items()},
                "honeypot_hits": dict(self.thorns._honeypot_hits),
                "saved_at": time.time(),
            }
            target.write_text(json.dumps(state, indent=2, default=str))
        except Exception:
            pass

    def load_state(self, path: str = None) -> bool:
        """v2.0: Restore retaliation state from disk. Returns True on success."""
        target = Path(path) if path else self._state_path()
        if not target.is_file():
            return False
        try:
            state = json.loads(target.read_text())
            self.thorns._blacklisted_sources = set(state.get("blacklisted_sources", []))
            self.thorns._blacklist_expiry = {k: float(v) for k, v in state.get("blacklist_expiry", {}).items()}
            self.thorns._quarantine = set(state.get("quarantined_sources", []))
            self.thorns._source_reputation = {k: float(v) for k, v in state.get("source_reputation", {}).items()}
            offenses = {}
            for k, v in state.get("offense_counts", {}).items():
                parts = k.split("|")
                if len(parts) == 2:
                    offenses[(parts[0], parts[1])] = int(v)
            self.thorns._offense_counts = offenses
            self.thorns._honeypot_hits = {k: int(v) for k, v in state.get("honeypot_hits", {}).items()}
            # Sync reputation back into the Thors store (unified)
            for src, score in self.thorns._source_reputation.items():
                try:
                    self.thors._sync_reputation_from_thorns(src, score)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """NEW: Security metrics dashboard. v2.0: + PREDATOR escalation stats."""
        base_metrics = self.thors.get_metrics()
        base_metrics["total_countermeasures"] = len(self.thorns.get_retaliation_log())
        base_metrics["total_blacklisted"] = len(self.thorns._blacklisted_sources)
        base_metrics["total_quarantined"] = len(self.thorns._quarantine)
        base_metrics["total_offenses_tracked"] = len(self.thorns.get_offense_counts())
        base_metrics["blacklist_expiries"] = len(self.thorns._blacklist_expiry)
        return base_metrics
    
    def add_to_whitelist(self, source: str) -> None:
        """NEW: Add trusted source to whitelist."""
        self.thors.add_to_whitelist(source)
    
    def remove_from_whitelist(self, source: str) -> None:
        """NEW: Remove source from whitelist."""
        self.thors.remove_from_whitelist(source)