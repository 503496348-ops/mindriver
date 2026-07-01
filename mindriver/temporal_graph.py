"""Temporal entity graph for agent memory consolidation."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json, re
from pathlib import Path
from typing import Dict, Iterable, List
ENTITY_RE = re.compile(r'[#@]?[A-Z][A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,12}')
@dataclass(frozen=True)
class MemoryEdge:
    source: str; relation: str; target: str; evidence: str; confidence: float; timestamp: str
    def to_dict(self) -> dict: return asdict(self)
class TemporalGraph:
    def __init__(self, edges: Iterable[MemoryEdge] | None = None): self.edges=list(edges or [])
    def add(self, source: str, relation: str, target: str, evidence: str='', confidence: float=0.7) -> MemoryEdge:
        edge=MemoryEdge(source.strip(), relation.strip() or 'related_to', target.strip(), evidence.strip()[:300], max(0.0,min(1.0,float(confidence))), datetime.now(timezone.utc).isoformat())
        if edge.source and edge.target: self.edges.append(edge)
        return edge
    def probe(self, entity: str) -> List[MemoryEdge]:
        q=entity.lower(); return [e for e in self.edges if e.source.lower()==q or e.target.lower()==q]
    def reason(self, entities: Iterable[str]) -> List[MemoryEdge]:
        qs={e.lower() for e in entities}; return [e for e in self.edges if e.source.lower() in qs or e.target.lower() in qs]
    def related(self, entity: str) -> Dict[str, float]:
        scores={}
        for e in self.probe(entity):
            other=e.target if e.source.lower()==entity.lower() else e.source; scores[other]=max(scores.get(other,0), e.confidence)
        return dict(sorted(scores.items(), key=lambda kv: -kv[1]))
    def save(self, path: str | Path) -> Path:
        p=Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps([e.to_dict() for e in self.edges], ensure_ascii=False, indent=2), encoding='utf-8'); return p
    @classmethod
    def load(cls, path: str | Path) -> 'TemporalGraph':
        p=Path(path)
        if not p.exists(): return cls()
        return cls(MemoryEdge(**item) for item in json.loads(p.read_text(encoding='utf-8')))
def extract_entities(text: str) -> List[str]: return sorted(set(m.group(0).strip('#@') for m in ENTITY_RE.finditer(text or '') if len(m.group(0).strip('#@')) >= 2))
def edges_from_fact(fact: str, *, relation: str='mentions') -> List[MemoryEdge]:
    entities=extract_entities(fact)
    if len(entities) < 2: return []
    src=entities[0]; now=datetime.now(timezone.utc).isoformat()
    return [MemoryEdge(src, relation, dst, fact[:300], 0.55, now) for dst in entities[1:]]
