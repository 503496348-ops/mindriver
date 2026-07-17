#!/usr/bin/env python3
"""Smoke runner for mindriver Wave-7 memory bridge."""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path

from memory_bridge import make_backend


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--repo', default=str(Path.cwd()))
    p.add_argument('--input', default='')
    args=p.parse_args()
    root=Path(args.repo).resolve()

    async def run() -> int:
        backend = make_backend(root)
        await backend.start()
        try:
            await backend.store('memory-smoke', [{'role':'user','content':'mindriver smoke'}], user_id='mindriver-user')
            await backend.feedback({'kind':'smoke-run'})
            hits = await backend.recall('mindriver', user_id='mindriver-user', top_k=3)
            print(json.dumps({'status':'ok','repo':root.name,'hits':[{'text':h.text,'score':h.score,'metadata':h.metadata} for h in hits]}, ensure_ascii=False, indent=2))
            return 0
        finally:
            await backend.stop()

    return asyncio.run(run())


if __name__ == '__main__':
    raise SystemExit(main())
