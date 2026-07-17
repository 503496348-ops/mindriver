#!/usr/bin/env python3
"""Mindriver Raven-like memory bridge PoC (additive)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import uuid
from datetime import datetime, timezone


@dataclass(frozen=True)
class Memory:
    text: str
    score: float = 0.0
    metadata: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


class FileMemoryBackend:
    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    def _read_lines(self):
        if not self.store_path.exists():
            return []
        out = []
        for line in self.store_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                out.append({'text': 'invalid json line', 'score': 0.0, 'metadata': {}})
        return out

    def _append(self, rec: dict[str, Any]):
        with self.store_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    async def recall(self, query: str, *, user_id: str | None = None, agent_id: str | None = None, top_k: int = 5):
        q = (query or '').lower()
        rows = self._read_lines()
        hits = []
        for row in rows:
            if user_id and row.get('user_id') and row.get('user_id') != user_id:
                continue
            if agent_id and row.get('agent_id') and row.get('agent_id') != agent_id:
                continue
            text = str(row.get('text', ''))
            s = float(row.get('score', 0.0) or 0.0)
            if q and q in text.lower():
                s += 1.0
            hits.append((s, text, row.get('metadata', {})))
        hits.sort(key=lambda x: x[0], reverse=True)
        return [Memory(text=h[1], score=h[0], metadata=h[2]) for h in hits[:top_k]]

    async def store(self, session_id: str, messages: list[dict[str, Any]], *, user_id: str | None = None, agent_id: str | None = None, top_k: int | None = None) -> None:
        del top_k
        self._append({
            'id': str(uuid.uuid4()),
            'ts': datetime.now(timezone.utc).isoformat(),
            'session_id': session_id,
            'user_id': user_id,
            'agent_id': agent_id,
            'messages': messages,
            'text': 'mindriver memory snapshot',
            'type': 'store',
        })

    async def feedback(self, payload: dict[str, Any]) -> None:
        self._append({'id': str(uuid.uuid4()), 'ts': datetime.now(timezone.utc).isoformat(), 'type': 'feedback', 'payload': payload})


def make_backend(repo_root: Path) -> FileMemoryBackend:
    return FileMemoryBackend(repo_root / 'references' / 'wave7_raven_memory_store.jsonl')
