"""
MindRiver — Agent上下文数据库
文件系统范式管理记忆/资源/技能，分层加载减少token消耗。
"""

__version__ = "1.5.0"

from .core import MindRiver, ContextNode
from .layers import LayeredLoader, Layer
from .memory import MemoryStore, Memory
from .search import SearchEngine, SearchResult
from .extractor import FactExtractor, ExtractedFact
from .dedup import MemoryDeduplicator, MemoryAction, DedupDecision
from .hybrid_search import HybridSearchEngine, HybridResult
from .fleet_ops import AgentProbe, EventFlowProbe, FleetOpsPanel, LoginRecoveryRequest, ProbeStatus
from .session_contracts import SessionHop, audit_session_chain, build_hop, contract_summary

__all__ = [
    "MindRiver", "ContextNode",
    "LayeredLoader", "Layer",
    "MemoryStore", "Memory",
    "SearchEngine", "SearchResult",
    "FactExtractor", "ExtractedFact",
    "MemoryDeduplicator", "MemoryAction", "DedupDecision",
    "HybridSearchEngine", "HybridResult",
    "AgentProbe", "EventFlowProbe", "FleetOpsPanel", "LoginRecoveryRequest", "ProbeStatus",
    "SessionHop", "audit_session_chain", "build_hop", "contract_summary",
    "RuntimeSnapshot", "StreamSnapshot", "allowed_operator_actions", "build_operator_card",
    "BridgeHealthProbe", "BridgeOpsPanel", "BridgeProcess", "ProbeResult", "recommend_action",
]

from .context_runtime_control_plane import RuntimeSnapshot, StreamSnapshot, allowed_operator_actions, build_operator_card
from .context_bridge_ops import BridgeHealthProbe, BridgeOpsPanel, BridgeProcess, ProbeResult, recommend_action
