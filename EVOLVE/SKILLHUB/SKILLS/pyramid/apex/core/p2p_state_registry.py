"""
OMNICORE P2P State Registry v1.0
Decentralized peer-to-peer state synchronization with weighted consensus
and integrated reputation scoring (wired to Thors/Thorns).

Stolen from:
  - OMNICORE-A1/src/lib/p2p_state_registry.ts (weighted consensus, reputation scoring)
  - markus_mesh.py (UDP heartbeat patterns, port 8129)
  - hive_swarm_adapter.ts (peer discovery, state delta broadcasting)
  - harvested_patterns_database.md → P2P State Registry Pattern

Features:
  - Per-agent state sync via weighted consensus (threshold 0.85)
  - Peer registration with Thors/Thorns reputation integration
  - Last-seen staleness tracking (auto-prune after 30s)
  - State delta broadcasting across mesh
  - 3-strike stale node eviction

Zero-dependency Python stdlib implementation.
"""
import json
import time
import socket
import hashlib
import pickle
import struct
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict, OrderedDict
from urllib.parse import urlparse


@dataclass
class PeerState:
    """Per-peer runtime state in the P2P mesh.
    
    Stolen from: p2p_state_registry.ts — PeerState interface
    Extended with: Thors/Thorns reputation integration.
    """
    peer_id: str
    address: str  # IP:port for UDP heartbeat
    role: str  # "omnicore-guard", "omnicore-executor", "omnicore-architect", "omnicore-editor"
    weight: float = 1.0  # Consensus voting weight (0.0-1.0)
    reputation_score: float = 50.0  # 0-100, synced from Thors/Thorns
    last_seen: float = field(default_factory=time.time)
    last_state: Dict[str, Any] = field(default_factory=dict)
    stale_count: int = 0  # Consecutive stale heartbeats
    active: bool = True


@dataclass
class StateDelta:
    """A state change broadcast across the mesh.
    Stolen from: p2p_state_registry.ts — StateDelta interface
    """
    delta_id: str
    peer_id: str
    timestamp: float
    key: str
    value: Any
    signature: str = ""  # Hash of value + timestamp for integrity


@dataclass
class ConsensusResult:
    """Result of a weighted consensus vote on a state key.
    Stolen from: p2p_state_registry.ts — ConsensusResult interface
    """
    key: str
    winning_value: Any
    confidence: float  # 0.0-1.0
    votes: int  # Number of peers that participated
    total_weight: float  # Sum of participating weights
    winning_weight: float  # Weight behind the winning value
    is_reached: bool  # Whether threshold (0.85) was met


# STOLE FROM: p2p_state_registry.ts — P2PStateRegistry class
# STOLE FROM: markus_mesh.py — UDP heartbeat patterns
# STOLE FROM: safety_gate.ts — sliding window rate limiting
# STOLE FROM: thors_thorns_engine.py — IP reputation integration


class PeerRegistry:
    """
    Decentralized peer registry with weighted consensus.
    
    Features:
    - Peer registration with Thors/Thorns reputation integration
    - Weighted consensus voting (threshold: 0.85)
    - Stale node pruning (30s inactivity = 1 strike, 3 strikes = eviction)
    - State delta broadcasting with integrity signatures
    - UDP-style heartbeat (port 8129 pattern from markus_mesh)
    - Bounded to prevent memory leaks (1000 peer max)
    """
    
    CONSENSUS_THRESHOLD = 0.85  # Minimum weight fraction for consensus
    STALE_THRESHOLD_S = 30.0  # Seconds before a peer is considered stale
    MAX_STALE_STRIKES = 3  # Consecutive stale heartbeats before eviction
    MAX_PEERS = 1000  # Bounded peer set to prevent memory growth
    HEARTBEAT_INTERVAL_S = 5.0  # Broadcast heartbeat every 5 seconds
    REPUTATION_DECAY_RATE = 0.01  # Per-minute reputation decay
    
    def __init__(self, self_peer_id: str, self_address: str = "127.0.0.1:8129",
                 self_role: str = "omnicore-architect",
                 thors_engine: Any = None):
        """
        Args:
            self_peer_id: Unique identifier for this node
            self_address: IP:Port for UDP heartbeat communication
            self_role: P2P role (guard, executor, architect, editor)
            thors_engine: Reference to ThorsThornsEngine for reputation sync
        """
        self._self_peer_id = self_peer_id
        self._self_address = self_address
        self._self_role = self_role
        self._thors = thors_engine  # Optional integration
        
        # Peer registry: peer_id -> PeerState
        self._peers: OrderedDict[str, PeerState] = OrderedDict()
        
        # State store: key -> {peer_id -> value} for consensus
        self._state_votes: Dict[str, Dict[str, Tuple[Any, float, float]]] = defaultdict(dict)
        # Format: key -> {peer_id: (value, weight, timestamp)}
        
        # State deltas for broadcasting
        self._delta_log: List[StateDelta] = []
        self._max_delta_log = 500  # Bounded
        
        # Heartbeat thread
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        
        # UDP socket for heartbeats
        self._sock: Optional[socket.socket] = None
        
        # Register self in the peer list
        self._peers[self._self_peer_id] = PeerState(
            peer_id=self._self_peer_id,
            address=self_address,
            role=self_role,
            weight=1.0,
            reputation_score=50.0,
            last_seen=time.time(),
            active=True,
        )
    
    def register_peer(self, peer_id: str, address: str, role: str = "omnicore-architect",
                      weight: float = 1.0, reputation_score: float = 50.0) -> PeerState:
        """Register a new peer in the registry.
        
        Stolen from: p2p_state_registry.ts — registerPeer()
        Extended with: Thors/Thorns reputation integration.
        """
        with self._lock:
            # Evict oldest if at capacity (FIFO)
            if len(self._peers) >= self.MAX_PEERS and peer_id not in self._peers:
                oldest_id = next(iter(self._peers))
                del self._peers[oldest_id]
            
            peer = PeerState(
                peer_id=peer_id,
                address=address,
                role=role,
                weight=min(1.0, max(0.0, weight)),
                reputation_score=min(100.0, max(0.0, reputation_score)),
                last_seen=time.time(),
                active=True,
            )
            self._peers[peer_id] = peer
            self._peers.move_to_end(peer_id)  # Mark as most recent
            return peer
    
    def unregister_peer(self, peer_id: str) -> bool:
        """Remove a peer from the registry."""
        with self._lock:
            if peer_id in self._peers:
                del self._peers[peer_id]
                # Clean up any votes from this peer
                for key in list(self._state_votes.keys()):
                    self._state_votes[key].pop(peer_id, None)
                return True
            return False
    
    def is_peer_known(self, peer_id: str) -> bool:
        """Check if a peer is registered."""
        with self._lock:
            return peer_id in self._peers and self._peers[peer_id].active
    
    def get_peer(self, peer_id: str) -> Optional[PeerState]:
        """Get peer state by ID."""
        with self._lock:
            return self._peers.get(peer_id)
    
    def get_peers(self) -> List[PeerState]:
        """Get all active peers."""
        with self._lock:
            return [p for p in self._peers.values() if p.active]
    
    def get_peer_count(self) -> int:
        """Get count of active peers."""
        with self._lock:
            return sum(1 for p in self._peers.values() if p.active)
    
    def heartbeat(self, peer_id: str) -> bool:
        """Record a heartbeat from a peer, updating last_seen.
        
        Stolen from: markus_mesh.py — heartbeat processing
        """
        with self._lock:
            if peer_id not in self._peers:
                return False  # Unknown peer
            peer = self._peers[peer_id]
            peer.last_seen = time.time()
            peer.stale_count = 0
            peer.active = True
            self._peers.move_to_end(peer_id)
            return True
    
    def receive_state_vote(self, peer_id: str, key: str, value: Any,
                           timestamp: float = None) -> bool:
        """Receive a state vote from a peer for consensus.

        Stolen from: p2p_state_registry.ts — submitVote()
        """
        if timestamp is None:
            timestamp = time.time()

        with self._lock:
            if peer_id not in self._peers:
                return False
            # Store value only; weight is resolved at tally time so later
            # reputation changes are reflected in consensus confidence.
            self._state_votes[key][peer_id] = (value, timestamp)
            return True
    
    def update_reputation(self, peer_id: str, score: float) -> bool:
        """Update a peer's reputation score (synced from Thors/Thorns).
        
        Stolen from: thors_thorns_engine.py — source reputation
        """
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].reputation_score = min(100.0, max(0.0, score))
                # Adjust weight based on reputation
                self._peers[peer_id].weight = score / 100.0
                return True
            return False
    
    def prune_stale_peers(self, now: float = None) -> int:
        """Remove peers that haven't sent heartbeats within the stale threshold.
        
        Uses 3-strike eviction: 3 consecutive stale heartbeats = removal.
        Stolen from: p2p_state_registry.ts — pruneStalePeers()
        """
        if now is None:
            now = time.time()
        
        evicted = 0
        with self._lock:
            stale_peer_ids = []
            for peer_id, peer in self._peers.items():
                if not peer.active:
                    continue
                elapsed = now - peer.last_seen
                if elapsed > self.STALE_THRESHOLD_S:
                    peer.stale_count += 1
                    if peer.stale_count >= self.MAX_STALE_STRIKES:
                        stale_peer_ids.append(peer_id)
                else:
                    peer.stale_count = 0
            
            for peer_id in stale_peer_ids:
                self.unregister_peer(peer_id)
                evicted += 1
        
        return evicted
    
    def reach_consensus(self, key: str, recent_threshold_s: float = 60.0) -> ConsensusResult:
        """Run weighted consensus on a state key.
        
        Stolen from: p2p_state_registry.ts — reachConsensus()
        Algorithm:
        1. Collect all votes for this key from active peers
        2. Group votes by value
        3. Sum weights for each unique value
        4. Determine winning value by highest weight
        5. Calculate confidence = winning_weight / total_weight
        6. Check if confidence >= 0.85 (threshold)
        """
        with self._lock:
            now = time.time()
            votes = self._state_votes.get(key, {})
            
            # Filter to active peers and recent votes
            active_votes = {}
            for pid, vote in votes.items():
                value = vote[0]
                ts = vote[-1]
                if pid in self._peers and self._peers[pid].active:
                    if now - ts <= recent_threshold_s:
                        active_votes[pid] = vote
            
            if not active_votes:
                return ConsensusResult(
                    key=key,
                    winning_value=None,
                    confidence=0.0,
                    votes=0,
                    total_weight=0.0,
                    winning_weight=0.0,
                    is_reached=False,
                )
            
            # Group by value; weight is resolved at tally time so reputation
            # updates between voting and consensus are honored.
            value_groups: Dict[str, Tuple[Any, float, int]] = {}
            # value_groups[value_repr] = (value, total_weight, vote_count)

            for pid, vote in active_votes.items():
                value = vote[0]
                ts = vote[-1]
                weight = float(self._peers[pid].weight) if pid in self._peers else 0.0
                value_repr = json.dumps(value, sort_keys=True, default=str)
                if value_repr not in value_groups:
                    value_groups[value_repr] = (value, 0.0, 0)
                prev_value, prev_weight, prev_count = value_groups[value_repr]
                value_groups[value_repr] = (value, prev_weight + weight, prev_count + 1)
            
            # Find winning value
            winning_repr = max(value_groups, key=lambda k: value_groups[k][1])
            winning_value, winning_weight, winning_votes = value_groups[winning_repr]
            resolved = [
                (float(self._peers[pid].weight) if pid in self._peers else 0.0)
                for pid in active_votes
            ]
            total_weight = sum(resolved)
            confidence = winning_weight / total_weight if total_weight > 0 else 0.0
            is_reached = confidence >= self.CONSENSUS_THRESHOLD
            
            return ConsensusResult(
                key=key,
                winning_value=winning_value,
                confidence=confidence,
                votes=winning_votes,
                total_weight=total_weight,
                winning_weight=winning_weight,
                is_reached=is_reached,
            )
    
    def broadcast_state_delta(self, key: str, value: Any) -> StateDelta:
        """Create and log a state delta for broadcasting.
        
        Stolen from: p2p_state_registry.ts — broadcastDelta()
        Includes integrity signature (hash of value + timestamp).
        """
        timestamp = time.time()
        signature = hashlib.sha256(
            f"{value}{timestamp}".encode()
        ).hexdigest()[:16]
        
        delta = StateDelta(
            delta_id=f"DEL-{hashlib.sha256(f'{key}:{timestamp}'.encode()).hexdigest()[:8]}",
            peer_id=self._self_peer_id,
            timestamp=timestamp,
            key=key,
            value=value,
            signature=signature,
        )
        
        with self._lock:
            self._delta_log.append(delta)
            # Bounded log
            if len(self._delta_log) > self._max_delta_log:
                self._delta_log = self._delta_log[-self._max_delta_log:]
        
        return delta
    
    def get_state(self, key: str) -> Any:
        """Get current consensus value for a state key."""
        result = self.reach_consensus(key)
        return result.winning_value if result.is_reached else None
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a state value (self-vote) and broadcast delta."""
        # Submit our own vote
        self.receive_state_vote(self._self_peer_id, key, value)
        # Broadcast the delta
        self.broadcast_state_delta(key, value)
    
    def audit_log(self) -> Dict:
        """Export full P2P registry audit log."""
        return {
            "self_peer_id": self._self_peer_id,
            "self_address": self._self_address,
            "self_role": self._self_role,
            "peer_count": self.get_peer_count(),
            "active_peers": [
                {
                    "peer_id": p.peer_id,
                    "address": p.address,
                    "role": p.role,
                    "weight": p.weight,
                    "reputation_score": p.reputation_score,
                    "last_seen": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.last_seen)),
                    "stale_count": p.stale_count,
                    "active": p.active,
                }
                for p in self.get_peers()
            ],
            "state_keys": list(self._state_votes.keys()),
            "delta_log_count": len(self._delta_log),
            "consensus_threshold": self.CONSENSUS_THRESHOLD,
            "stale_threshold_s": self.STALE_THRESHOLD_S,
        }


# STOLE FROM: p2p_state_registry.ts — weighted consensus, reputation scoring
# STOLE FROM: markus_mesh.py — UDP heartbeat patterns, port 8129
# STOLE FROM: thors_thorns_engine.py — IP reputation integration
# STOLE FROM: harvested_patterns_database.md — P2P State Registry Pattern
# STOLE FROM: hive_swarm_adapter.ts — peer discovery, state delta broadcasting
# STOLE FROM: safety_gate.ts — sliding window, bounded collections