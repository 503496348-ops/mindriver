"""Session-chain contract checks for retrieval and tool execution paths."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class SessionHop:
    name: str
    session_id: str | None
    trace_id: str | None
    payload_keys: tuple[str, ...]


def build_hop(name: str, event: Mapping[str, object]) -> SessionHop:
    payload = event.get("payload", {})
    keys = tuple(sorted(payload.keys())) if isinstance(payload, Mapping) else ()
    return SessionHop(
        name=name,
        session_id=str(event.get("session_id")) if event.get("session_id") else None,
        trace_id=str(event.get("trace_id")) if event.get("trace_id") else None,
        payload_keys=keys,
    )


def audit_session_chain(hops: Iterable[SessionHop]) -> list[str]:
    hops = list(hops)
    errors: list[str] = []
    if not hops:
        return ["empty session chain"]
    expected_session = hops[0].session_id
    expected_trace = hops[0].trace_id
    for hop in hops:
        if not hop.session_id:
            errors.append(f"{hop.name}: missing session_id")
        elif expected_session and hop.session_id != expected_session:
            errors.append(f"{hop.name}: session_id drift {hop.session_id} != {expected_session}")
        if not hop.trace_id:
            errors.append(f"{hop.name}: missing trace_id")
        elif expected_trace and hop.trace_id != expected_trace:
            errors.append(f"{hop.name}: trace_id drift {hop.trace_id} != {expected_trace}")
    return errors


def contract_summary(hops: Iterable[SessionHop]) -> dict[str, object]:
    hops = list(hops)
    errors = audit_session_chain(hops)
    return {"hops": len(hops), "ok": not errors, "errors": errors}
