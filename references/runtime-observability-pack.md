# Runtime Observability Pack

MindRiver adds an observability layer for agent context systems and standing teams. Its job is to distinguish **process alive** from **semantically ready**.

## Health Dimensions

| Dimension | Signal | Bad Smell |
|---|---|---|
| Process | PID exists and cmdline matches expected daemon. | PID file points to another process or stale pid. |
| Heartbeat | Agent writes fresh heartbeat or status row. | Heartbeat older than threshold while process is alive. |
| Semantic readiness | Latest pane/log/transcript confirms identity and readiness. | Agent is on login screen, crashed shell, or wrong identity. |
| Event flow | Router sees inbound events or keepalive within threshold. | WebSocket/subscriber alive but no events flow. |
| Resource load | CPU, memory, disk, queue depth, provider quota. | Green process status hides exhausted disk/quota. |
| Memory integrity | Context layer counts, tier distribution, duplicate/empty facts. | Context DB exists but retrieval is empty or polluted. |
| Login recovery | Router-owned device-auth plan with isolated credential home. | Worker pane is stuck on auth prompt or wrong account. |

## Inspection Algorithm

1. Load expected agents/services from config, not from local `ps` alone.
2. For each daemon, verify pid file, process existence, and cmdline markers.
3. For each agent, inspect heartbeat age and latest semantic output.
4. If state is ambiguous, send one low-risk liveness probe and wait for a bounded reply.
5. Collect resource metrics: CPU, memory, disk, queue depth, and quota where available.
6. Classify health as `ready`, `degraded`, `stalled`, `auth_required`, `unknown`, or `down`.
7. Emit evidence, not vibes: exact check, observed value, threshold, and next action.

## Report Shape

```json
{
  "service": "agent-team",
  "status": "degraded",
  "checks": [
    {"name": "router_pid", "status": "pass", "evidence": "pid and cmdline match"},
    {"name": "worker_semantic_ready", "status": "fail", "evidence": "latest pane shows login prompt"}
  ],
  "next_actions": ["refresh worker login", "re-run semantic probe"]
}
```

## Guardrails

- Never equate “green process” with “ready to work”.
- Missing metrics are `unknown`, not zero.
- Do not auto-restart gateway or external services without explicit approval.
- Keep credentials and raw ids redacted in health reports.
- Health probes must be low-risk and must not trigger destructive work.

## Integration Targets

- Team runtime health cards
- Context database integrity checks
- Memory tier/duplicate audits
- Provider usage and quota panels
- Router stale-event recovery runbooks

## Fleet Ops Panel Contract

`mindriver/fleet_ops.py` provides a small deterministic contract:

- `AgentProbe.evaluate()` reports `healthy/degraded/down` with reason codes such as `semantic_wedged`, `heartbeat_stale`, or `cmdline_mismatch`.
- `EventFlowProbe.evaluate()` reports subscriber/event silence separately from process liveness.
- `LoginRecoveryRequest.to_plan()` returns a router-owned `codex login --device-auth` command and isolated `CODEX_HOME`, while user-visible text stays token-safe.
- `FleetOpsPanel.evaluate()` combines agent health, event-flow health, and context integrity into one report.
