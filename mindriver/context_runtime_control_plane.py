"""MindRiver context runtime control-plane model.

Summarises runtime health, pending event streams, and operator actions without
binding the product to any themed organization model.
"""
from __future__ import annotations

from dataclasses import dataclass

ACTION_STATES = {
    "pause": {"running", "queued"},
    "resume": {"blocked", "paused"},
    "retry": {"blocked", "failed"},
    "rollback": {"running", "verification", "failed"},
    "escalate": {"blocked", "failed", "pending_confirmation"},
}


@dataclass(frozen=True)
class StreamSnapshot:
    topic: str
    length: int = 0
    pending: int = 0
    stale_pending: int = 0

    @property
    def health(self) -> str:
        if self.stale_pending > 0:
            return "stalled"
        if self.pending > 0:
            return "backlog"
        return "healthy"


@dataclass(frozen=True)
class RuntimeSnapshot:
    active_items: int
    blocked_items: int
    streams: tuple[StreamSnapshot, ...]

    def summary(self) -> dict:
        stream_health = {s.topic: s.health for s in self.streams}
        return {
            "active_items": self.active_items,
            "blocked_items": self.blocked_items,
            "streams": stream_health,
            "overall": self.overall_health(),
        }

    def overall_health(self) -> str:
        if any(s.health == "stalled" for s in self.streams):
            return "attention_required"
        if self.blocked_items:
            return "degraded"
        return "healthy"


def allowed_operator_actions(state: str) -> list[str]:
    return sorted(action for action, states in ACTION_STATES.items() if state in states)


def build_operator_card(snapshot: RuntimeSnapshot) -> dict:
    summary = snapshot.summary()
    return {
        "title": "MindRiver Context Runtime",
        "status": summary["overall"],
        "metrics": {
            "active": summary["active_items"],
            "blocked": summary["blocked_items"],
        },
        "streams": summary["streams"],
    }
