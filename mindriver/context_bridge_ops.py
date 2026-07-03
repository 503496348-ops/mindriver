"""Operational control-plane probes for Lark coding-agent bridges."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

HealthStatus = Literal["ok", "warn", "fail"]

@dataclass(frozen=True)
class ProbeResult:
    name: str
    status: HealthStatus
    detail: str

@dataclass(frozen=True)
class BridgeProcess:
    profile: str
    agent: str
    pid: int | None
    workspace: str
    active_runs: int = 0

class BridgeOpsPanel:
    def summarize(self, processes: Iterable[BridgeProcess]) -> dict:
        rows = list(processes)
        return {
            "processes": len(rows),
            "active_runs": sum(p.active_runs for p in rows),
            "profiles": sorted({p.profile for p in rows}),
            "agents": sorted({p.agent for p in rows}),
        }

class BridgeHealthProbe:
    def __init__(self, lark_cli_config_dir: str | None = None) -> None:
        self.lark_cli_config_dir = lark_cli_config_dir

    def probe_workspace(self, workspace: str) -> ProbeResult:
        path = Path(workspace).expanduser()
        if not path.exists():
            return ProbeResult("workspace", "fail", f"missing: {path}")
        if not path.is_dir():
            return ProbeResult("workspace", "fail", f"not-directory: {path}")
        return ProbeResult("workspace", "ok", str(path.resolve()))

    def probe_profile_identity(self) -> ProbeResult:
        if not self.lark_cli_config_dir:
            return ProbeResult("lark-cli-profile", "warn", "LARKSUITE_CLI_CONFIG_DIR not set")
        path = Path(self.lark_cli_config_dir).expanduser()
        return ProbeResult("lark-cli-profile", "ok" if path.exists() else "warn", str(path))

def recommend_action(results: Iterable[ProbeResult]) -> str:
    statuses = {r.status for r in results}
    if "fail" in statuses:
        return "block-run-and-repair"
    if "warn" in statuses:
        return "allow-readonly-with-warning"
    return "allow-normal-run"
