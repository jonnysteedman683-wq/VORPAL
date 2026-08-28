# apex/utilities/__init__.py - Utility Modules
# Watermarked [OMNIPRIME-FORGE]
# [◈VORPAL◈] self_healing_orchestrator removed 2026-08-28 (orphaned
# duplicate of CORE resilience; referenced nothing external).
# [◈VORPAL◈] BugTraceback never existed in auto_debugger; exporting the
# real public names.

from .auto_debugger import AutoDebugger, DebugReport, ErrorSeverity

__all__ = ['AutoDebugger', 'DebugReport', 'ErrorSeverity']