# Changelog

All notable changes to `mindriver` should be documented in this file.

This repository follows a lightweight Keep-a-Changelog style and semantic versioning where applicable.

## Unreleased

- Governance baseline initialized.

## 1.4.0 - Agent fleet ops panel

- Added `mindriver/fleet_ops.py` with agent semantic readiness probes, stale event-flow detection, token-safe Codex login recovery plans, and context integrity checks.
- Added `tests/test_fleet_ops.py` covering process-vs-semantic health, event-flow staleness, login recovery safety, and duplicate/empty context detection.

## 1.3.0 - Runtime observability pack

- Added runtime observability reference for PID/cmdline/heartbeat checks, semantic readiness probes, stale event-flow detection, resource/quota panels, and context integrity audits.
- Expanded Skill triggers for agent health inspection and standing-team observability.
## 2026-07-02 融合增强

- 智脑星河新增交付证据账本：记录 artifact producer/verifier 与 SHA-256，用于运行时产物可观测和可追溯。

