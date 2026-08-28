# apex/__init__.py - OMNIPRIME Forge Node
# Watermarked [OMNIPRIME-FORGE]

# [◈VORPAL◈] The duplicate apex circuit_breaker.py was removed (2026-08-28):
# CORE.llm_circuit_breaker is now the canonical, wired-in breaker
# (see CORE/provider_handshake.py). The orphaned health_watchdog and
# self_healing_orchestrator modules that imported the duplicate were
# also removed — neither was referenced by the spine.
from .core.p2p_state_registry import PeerRegistry, PeerState, StateDelta, ConsensusResult
from .core.path_resolver import PathResolver
from .core.pyramid_walker import PyramidWalker, Tier, DegradationCategory

__all__ = [
    'PeerRegistry', 'PeerState', 'StateDelta', 'ConsensusResult',
    'PathResolver', 'PyramidWalker', 'Tier', 'DegradationCategory',
]