"""
OMNICORE Defensive Engine v1.0 — Bug Traceback Capture + Retry Logic
Stolen from: safety_gate.ts (circuit breaker pattern), resilience.py (failure recovery)
+ hermesVerify.ts (structured error reporting)
+ connectorRuntime.test.ts (retry with backoff)

Key capabilities:
- Captures full Python tracebacks for security-relevant failures
- Implements retry-with-backoff for transient errors
- Structured error taxonomy (ERR_*) for falsification reporting
- Bug traceback export to Obsidian audit journal
"""
import sys
import traceback
import json
import time
import functools
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime


class ErrorTaxonomy(Enum):
    """Stolen from: NOTES.md [ERR_*] taxonomy."""
    ERR_SYNTAX = "ERR_SYNTAX"          # Execution faults
    ERR_LOGIC = "ERR_LOGIC"            # Fails edge-case asserts
    ERR_BLOAT = "ERR_BLOAT"            # Token cost increased >5%
    ERR_OVERLAP = "ERR_OVERLAP"        # Duplicates existing logic
    ERR_SECURITY = "ERR_SECURITY"      # Security violation detected
    ERR_RATE_LIMIT = "ERR_RATE_LIMIT"  # Rate limiting triggered
    ERR_TIMEOUT = "ERR_TIMEOUT"        # Operation timed out
    ERR_UNKNOWN = "ERR_UNKNOWN"          # Unclassified error
    ERR_TERMINAL_RECURSION = "ERR_TERMINAL_RECURSION"  # Fatal recursion


@dataclass
class BugTraceback:
    """Structured bug traceback for falsification reporting."""
    error_type: str
    error_taxonomy: str
    error_message: str
    traceback_formatted: str
    function_name: str
    file_path: str
    line_number: int
    timestamp: float
    retry_count: int = 0
    context: Dict[str, Any] = None
    stack_trace_json: str = ""


class DefensiveEngine:
    """
    Defensive wrapper with bug traceback capture, retry logic, and
    structured error reporting. Replaces manual try/except blocks.
    """
    
    def __init__(self, max_retries: int = 3, backoff_base: float = 1.0,
                 backoff_factor: float = 2.0, timeout: float = 30.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self._bug_log: List[BugTraceback] = []
        self._audit_path: Optional[Path] = None
    
    def set_audit_path(self, path: str):
        """Set the Obsidian audit log destination."""
        self._audit_path = Path(path)
    
    def capture_traceback(self, exc: Exception, func_name: str = "",
                          context: Dict[str, Any] = None) -> BugTraceback:
        """
        Capture full Python traceback and format for falsification report.
        """
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_formatted = ''.join(tb_lines)
        
        tb_json = []
        if exc.__traceback__:
            for frame, lineno in zip(exc.__traceback__.tb_frame.f_back.f_code.co_filename.splitlines() if False else [], []):
                pass  # Just use formatted version
        
        # Extract frame info
        file_path = ""
        line_number = 0
        stack = []
        
        tb = exc.__traceback__
        while tb:
            frame = tb.tb_frame
            stack.append({
                "file": frame.f_code.co_filename,
                "function": frame.f_code.co_name,
                "line": tb.tb_lineno,
                "locals": str(frame.f_locals)[:500]  # Truncate for size
            })
            if not file_path:
                file_path = frame.f_code.co_filename
                line_number = tb.tb_lineno
            tb = tb.tb_next
        
        # Determine taxonomy
        taxonomy = self._classify_error(exc)
        
        bug = BugTraceback(
            error_type=type(exc).__name__,
            error_taxonomy=taxonomy.value,
            error_message=str(exc),
            traceback_formatted=tb_formatted,
            function_name=func_name,
            file_path=file_path,
            line_number=line_number,
            timestamp=time.time(),
            context=context or {},
            stack_trace_json=json.dumps(stack, indent=2, default=str)
        )
        
        self._bug_log.append(bug)
        return bug
    
    def _classify_error(self, exc: Exception) -> ErrorTaxonomy:
        """Classify error into taxonomy."""
        if isinstance(exc, SyntaxError):
            return ErrorTaxonomy.ERR_SYNTAX
        if isinstance(exc, AssertionError):
            return ErrorTaxonomy.ERR_LOGIC
        if isinstance(exc, RecursionError):
            return ErrorTaxonomy.ERR_TERMINAL_RECURSION
        if isinstance(exc, RuntimeError) and "recursion" in str(exc).lower():
            return ErrorTaxonomy.ERR_TERMINAL_RECURSION
        if isinstance(exc, TimeoutError):
            return ErrorTaxonomy.ERR_TIMEOUT
        if isinstance(exc, ValueError) and "rate" in str(exc).lower():
            return ErrorTaxonomy.ERR_RATE_LIMIT
        return ErrorTaxonomy.ERR_UNKNOWN
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute with retry-with-backoff. Captures full tracebacks on failure.
        """
        last_exc = None
        context = {"args": str(args)[:500], "kwargs": str(kwargs)[:500]}
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                bug = self.capture_traceback(e, func.__name__ if hasattr(func, '__name__') else str(func), 
                                            {**context, "attempt": attempt + 1})
                
                if attempt < self.max_retries - 1:
                    backoff = self.backoff_base * (self.backoff_factor ** attempt)
                    time.sleep(backoff)
        
        # All retries exhausted — raise with structured context
        raise last_exc
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute function with full error capture. Returns structured result.
        """
        context = {"args": str(args)[:500], "kwargs": str(kwargs)[:500]}
        try:
            result = func(*args, **kwargs)
            return {"success": True, "result": result, "error": None, "bug": None}
        except Exception as e:
            bug = self.capture_traceback(e, 
                                        func.__name__ if hasattr(func, '__name__') else str(func),
                                        context)
            return {"success": False, "result": None, "error": str(e), "bug": asdict(bug)}
    
    def wrap(self, func: Callable) -> Callable:
        """
        Decorator: wrap any function with defensive error capture.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.safe_execute(func, *args, **kwargs)
        return wrapper
    
    def get_bug_log(self) -> List[BugTraceback]:
        """Retrieve all captured bug tracebacks."""
        return self._bug_log
    
    def export_bug_report(self) -> Dict[str, Any]:
        """Export structured bug report for falsification."""
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "total_bugs": len(self._bug_log),
            "bugs_by_taxonomy": self._bugs_by_type(),
            "tracebacks": [asdict(b) for b in self._bug_log],
        }
    
    def _bugs_by_type(self) -> Dict[str, int]:
        """Count bugs by taxonomy."""
        counts = {}
        for bug in self._bug_log:
            counts[bug.error_taxonomy] = counts.get(bug.error_taxonomy, 0) + 1
        return counts
    
    def sync_to_obsidian(self):
        """Export bug tracebacks to Obsidian audit journal."""
        if not self._audit_path:
            return False
        
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            report = self.export_bug_report()
            
            # Convert to markdown table for Obsidian
            lines = [
                f"# Security Bug Report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Captured Tracebacks",
                "",
            ]
            
            for bug in self._bug_log:
                lines.append(f"### {bug.error_taxonomy}: {bug.function_name}")
                lines.append(f"**Error:** `{bug.error_message}`")
                lines.append(f"**Type:** `{bug.error_type}`")
                lines.append(f"**File:** `{bug.file_path}:{bug.line_number}`")
                ts = datetime.fromtimestamp(bug.timestamp).isoformat()
                lines.append(f"**Timestamp:** `{ts}`")
                lines.append("")
                lines.append("```traceback")
                lines.append(bug.traceback_formatted.strip())
                lines.append("```")
                lines.append("")
            
            # Append to daily journal (use LOCAL date so the engine and any
            # reader agree on "today" — the audit file is local, not UTC).
            date_str = datetime.now().strftime("%Y-%m-%d")
            journal_path = self._audit_path.parent / "Vault" / "Journal" / "OMNICORE" / f"{date_str}.md"
            journal_path.parent.mkdir(parents=True, exist_ok=True)
            
            entry = "\n\n## Security Bug Report\n\n"
            if self._bug_log:
                entry += "\n".join(lines)
            else:
                entry += "No bugs captured in this session.\n"
            
            with open(journal_path, "a", encoding="utf-8") as f:
                f.write(entry)
            
            return True
        except Exception as e:
            print(f"  [WARN] Obsidian sync failed: {e}")
            return False


# ─── Convenience: Global defensive engine instance ───
defensive_engine = DefensiveEngine(max_retries=3, backoff_base=0.5, backoff_factor=2.0)
