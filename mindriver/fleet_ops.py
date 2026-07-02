from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
from typing import Optional


class ProbeStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass(frozen=True)
class AgentProbe:
    name: str
    pid_alive: bool
    cmdline_matches: bool
    heartbeat_age_seconds: Optional[float]
    semantic_state: str = "ready"
    quota_remaining: Optional[int] = None
    max_heartbeat_age_seconds: float = 60

    def evaluate(self) -> dict:
        reasons: list[str] = []
        if not self.pid_alive:
            reasons.append("pid_dead")
        if not self.cmdline_matches:
            reasons.append("cmdline_mismatch")
        if self.heartbeat_age_seconds is None:
            reasons.append("heartbeat_unknown")
        elif self.heartbeat_age_seconds > self.max_heartbeat_age_seconds:
            reasons.append("heartbeat_stale")
        if self.semantic_state not in {"ready", "idle", "working"}:
            reasons.append(f"semantic_{self.semantic_state}")
        status = ProbeStatus.HEALTHY
        if "pid_dead" in reasons:
            status = ProbeStatus.DOWN
        elif reasons:
            status = ProbeStatus.DEGRADED
        return {
            "status": status.value,
            "reasons": reasons,
            "pid_alive": self.pid_alive,
            "cmdline_matches": self.cmdline_matches,
            "heartbeat_age_seconds": self.heartbeat_age_seconds,
            "semantic_state": self.semantic_state,
            "quota_remaining": self.quota_remaining if self.quota_remaining is not None else "unknown",
        }


@dataclass(frozen=True)
class EventFlowProbe:
    name: str
    process_alive: bool
    last_event_at: Optional[float]
    max_silence_seconds: float = 60

    def evaluate(self, now: float) -> dict:
        reasons: list[str] = []
        if not self.process_alive:
            reasons.append("event_process_dead")
        if self.last_event_at is None:
            reasons.append("event_flow_unknown")
        elif now - self.last_event_at > self.max_silence_seconds:
            reasons.append("event_flow_stale")
        status = ProbeStatus.HEALTHY
        if "event_process_dead" in reasons:
            status = ProbeStatus.DOWN
        elif reasons:
            status = ProbeStatus.DEGRADED
        return {"status": status.value, "reasons": reasons, "last_event_at": self.last_event_at}


@dataclass(frozen=True)
class LoginRecoveryRequest:
    agent: str
    cli: str
    cred_home: str

    def to_plan(self) -> dict:
        normalized = self.cli.lower().replace("_", "-")
        if normalized not in {"codex", "codex-cli"}:
            raise ValueError(f"unsupported cli for recovery: {self.cli}")
        return {
            "agent": self.agent,
            "handled_by": "router",
            "command": ["codex", "login", "--device-auth"],
            "env": {"CODEX_HOME": str(PurePosixPath(self.cred_home) / ".codex")},
            "user_visible": "Open the verification URL and enter the device code. Raw credentials stay private.",
        }


@dataclass(frozen=True)
class ContextNode:
    path: str
    content: str
    tier: str


@dataclass
class FleetOpsPanel:
    now: float = 0
    _agents: list[AgentProbe] = field(default_factory=list)
    _flows: list[EventFlowProbe] = field(default_factory=list)
    _context_nodes: list[ContextNode] = field(default_factory=list)

    def add_agent(self, probe: AgentProbe) -> None:
        self._agents.append(probe)

    def add_event_flow(self, probe: EventFlowProbe) -> None:
        self._flows.append(probe)

    def add_context_node(self, path: str, content: str, tier: str) -> None:
        self._context_nodes.append(ContextNode(path=path, content=content, tier=tier))

    def evaluate(self) -> dict:
        now = self.now or 0
        agents = {probe.name: probe.evaluate() for probe in self._agents}
        event_flows = {probe.name: probe.evaluate(now) for probe in self._flows}
        return {
            "agents": agents,
            "event_flows": event_flows,
            "context_integrity": self._context_integrity(),
        }

    def _context_integrity(self) -> dict:
        reasons: list[str] = []
        seen: set[str] = set()
        tier_counts: dict[str, int] = {}
        for node in self._context_nodes:
            tier_counts[node.tier] = tier_counts.get(node.tier, 0) + 1
            normalized = " ".join(node.content.split())
            if not normalized:
                reasons.append("empty_context")
            elif normalized in seen:
                reasons.append("duplicate_context")
            seen.add(normalized)
        unique_reasons = sorted(set(reasons))
        status = ProbeStatus.DEGRADED if unique_reasons else ProbeStatus.HEALTHY
        return {"status": status.value, "reasons": unique_reasons, "tier_counts": tier_counts}
