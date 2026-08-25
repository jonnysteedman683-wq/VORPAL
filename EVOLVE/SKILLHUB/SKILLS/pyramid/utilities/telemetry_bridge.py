"""
OMNICORE Telemetry Bridge v1.0 — A4 Harmonizer
Inter-layer telemetry aggregation: collects metrics from A1/A2/A3
and produces unified cross-layer dashboard data.

Stolen from: markus_server.py — SSE/streaming telemetry
+ health_watchdog.py — health metrics aggregation
+ tri_agentic_kernel.ts — EvolutionMetrics aggregation
"""
import time
import json
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict


@dataclass
class TelemetrySample:
    agent_id: str
    agent_role: str
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    component: str = "general"


@dataclass
class AggregatedDashboard:
    timestamp: float
    layers: Dict[str, Dict[str, Any]]
    aggregate_metrics: Dict[str, Any]
    health_summary: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    window_seconds: float


class TelemetryBridge:
    def __init__(self, window_seconds: float = 300.0, on_update: Callable = None):
        self.window_seconds = window_seconds
        self._samples: deque = deque(maxlen=1000)
        self._by_layer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        self._on_update = on_update or (lambda d: None)
        self._dashboards: deque = deque(maxlen=50)
        self._alerts: deque = deque(maxlen=100)
        self._subscribers: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def record(self, sample: TelemetrySample):
        self._samples.append(sample)
        self._by_layer[sample.agent_id].append(sample)
        self._check_alerts(sample)

    def record_from_kernel(self, agent_id: str, agent_role: str,
                           metrics: Dict[str, Any], component: str = "general"):
        sample = TelemetrySample(
            agent_id=agent_id, agent_role=agent_role,
            metrics=metrics, component=component, tags=["kernel"],
        )
        self.record(sample)

    def _check_alerts(self, sample: TelemetrySample):
        conf = sample.metrics.get("avgConfidence", sample.metrics.get("confidence", 1.0))
        if isinstance(conf, (int, float)) and conf < 0.6:
            self._alerts.append({"timestamp": sample.timestamp, "severity": "warning",
                                  "agent": sample.agent_id, "message": f"Low confidence: {conf:.2f}",
                                  "metric": "confidence", "value": conf})
        cycles = sample.metrics.get("cycle", 0)
        if isinstance(cycles, (int, float)) and cycles > 100:
            self._alerts.append({"timestamp": sample.timestamp, "severity": "info",
                                  "agent": sample.agent_id, "message": f"High cycle count: {cycles}",
                                  "metric": "cycle", "value": cycles})
        reward = sample.metrics.get("reward", 0)
        if isinstance(reward, (int, float)) and reward < 0.3:
            self._alerts.append({"timestamp": sample.timestamp, "severity": "warning",
                                  "agent": sample.agent_id, "message": f"Low reward score: {reward:.3f}",
                                  "metric": "reward", "value": reward})

    def get_dashboard(self, layer_ids: List[str] = None) -> AggregatedDashboard:
        now = time.time()
        cutoff = now - self.window_seconds
        window_samples = [s for s in self._samples if s.timestamp >= cutoff]

        layers: Dict[str, Dict[str, Any]] = {}
        target_layers = layer_ids or list(self._by_layer.keys())
        for layer_id in target_layers:
            layer_samples = [s for s in window_samples if s.agent_id == layer_id][-10:]
            if layer_samples:
                aggregated = self._aggregate_layer_metrics(layer_samples)
                layers[layer_id] = {
                    "agent_role": layer_samples[0].agent_role,
                    "sample_count": len(layer_samples),
                    "last_sample": layer_samples[-1].timestamp,
                    "metrics": aggregated,
                    "tags": list(set(t for s in layer_samples for t in s.tags)),
                }

        aggregate = self._compute_cross_layer_aggregates(layers)
        health = self._compute_health_summary(layers)
        recent_alerts = [a for a in self._alerts if now - a["timestamp"] <= self.window_seconds]

        return AggregatedDashboard(
            timestamp=now, layers=layers, aggregate_metrics=aggregate,
            health_summary=health, alerts=recent_alerts[-20:], window_seconds=self.window_seconds,
        )

    def _aggregate_layer_metrics(self, samples: List[TelemetrySample]) -> Dict[str, Any]:
        if not samples:
            return {}
        all_keys = set()
        for s in samples:
            all_keys.update(s.metrics.keys())
        result = {}
        for key in all_keys:
            values = [s.metrics.get(key) for s in samples if isinstance(s.metrics.get(key), (int, float))]
            if values:
                result[f"{key}_avg"] = sum(values) / len(values)
                result[f"{key}_min"] = min(values)
                result[f"{key}_max"] = max(values)
                result[f"{key}_latest"] = samples[-1].metrics.get(key)
                result[f"{key}_samples"] = len(values)
            else:
                result[f"{key}_latest"] = samples[-1].metrics.get(key)
        return result

    def _compute_cross_layer_aggregates(self, layers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        aggregate = {}
        confidences = []
        for layer_data in layers.values():
            m = layer_data.get("metrics", {})
            conf = m.get("avgConfidence_latest") or m.get("confidence_latest", 0)
            if isinstance(conf, (int, float)):
                confidences.append(conf)
        if confidences:
            aggregate["cross_layer_avg_confidence"] = sum(confidences) / len(confidences)
            aggregate["cross_layer_min_confidence"] = min(confidences)
            aggregate["cross_layer_max_confidence"] = max(confidences)

        cycles = []
        for layer_data in layers.values():
            c = layer_data.get("metrics", {}).get("cycle_latest", 0)
            if isinstance(c, (int, float)):
                cycles.append(c)
        if cycles:
            aggregate["cross_layer_total_cycles"] = sum(cycles)
            aggregate["cross_layer_avg_cycles"] = sum(cycles) / len(cycles)

        aggregate["active_layers"] = len(layers)
        return aggregate

    def _compute_health_summary(self, layers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        summary = {"total_layers": len(layers), "healthy_layers": 0, "degraded_layers": 0, "layer_status": {}}
        for layer_id, data in layers.items():
            m = data.get("metrics", {})
            conf = m.get("avgConfidence_latest") or m.get("confidence_latest", 0)
            cycle = m.get("cycle_latest", 0)
            is_healthy = isinstance(conf, (int, float)) and conf >= 0.7 and isinstance(cycle, (int, float)) and cycle < 100
            status = "healthy" if is_healthy else "degraded"
            summary["layer_status"][layer_id] = status
            if is_healthy:
                summary["healthy_layers"] += 1
            else:
                summary["degraded_layers"] += 1
        summary["overall_health"] = "healthy" if summary["degraded_layers"] == 0 else "degraded" if summary["degraded_layers"] < summary["total_layers"] else "critical"
        return summary

    def subscribe(self, callback: Callable):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def start_auto_refresh(self, interval_seconds: float = 10.0):
        if self._running:
            return
        self._running = True

        def loop():
            while self._running:
                dashboard = self.get_dashboard()
                self._dashboards.append(dashboard)
                for sub in self._subscribers:
                    try:
                        sub(dashboard)
                    except Exception:
                        pass
                if self._on_update:
                    self._on_update(dashboard)
                time.sleep(interval_seconds)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop_auto_refresh(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    def get_recent_dashboards(self, limit: int = 10) -> list:
        return list(self._dashboards)[-limit:]

    def get_recent_alerts(self, limit: int = 20) -> list:
        return list(self._alerts)[-limit:]

    def export_json(self, dashboard: AggregatedDashboard = None) -> str:
        d = dashboard or self.get_dashboard()
        return json.dumps({
            "timestamp": d.timestamp, "layers": d.layers,
            "aggregates": d.aggregate_metrics, "health": d.health_summary, "alerts": d.alerts,
        }, indent=2, default=str)

    def summary(self) -> dict:
        now = time.time()
        return {
            "total_samples": len(self._samples),
            "by_layer": {k: len(v) for k, v in self._by_layer.items()},
            "recent_alerts": len([a for a in self._alerts if now - a["timestamp"] <= self.window_seconds]),
            "dashboards_generated": len(self._dashboards),
            "window_seconds": self.window_seconds,
        }
