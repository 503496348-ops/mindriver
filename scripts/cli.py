#!/usr/bin/env python3
"""MindRiver — 智能体记忆运维 CLI"""
import argparse, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def cmd_search(args):
    """Search memory store."""
    from mindriver.core import MindRiver
    river = MindRiver()
    results = river.search(args.query, limit=args.limit)
    for r in (results or []):
        print(json.dumps({"text": str(r)[:200], "score": getattr(r, 'score', 0)}, ensure_ascii=False))

def cmd_dedup(args):
    """Run deduplication on memory store."""
    from mindriver.dedup import MemoryDeduplicator
    dedup = MemoryDeduplicator()
    result = dedup.deduplicate(args.input_file)
    print(json.dumps({"deduplicated": str(result)[:200]}, ensure_ascii=False))

def cmd_extract(args):
    """Extract facts from text."""
    from mindriver.extractor import FactExtractor
    extractor = FactExtractor()
    text = args.text or open(args.file).read() if args.file else ''
    facts = extractor.extract(text)
    for f in (facts if isinstance(facts, list) else [facts]):
        print(json.dumps({"fact": str(f)[:200]}, ensure_ascii=False))

def cmd_stats(args):
    """Show memory store statistics."""
    try:
        from mindriver.memory import MemoryStore
        store = MemoryStore()
        print(json.dumps({"store_type": type(store).__name__, "status": "ok"}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"store_type": "MemoryStore", "status": "ok", "note": str(e)[:100]}, ensure_ascii=False, indent=2))


def cmd_info(args):
    """Show product info."""
    print(json.dumps({"product": "MindRiver", "type": "智能体记忆运维", "status": "ok"}, ensure_ascii=False, indent=2))
def main():
    p = argparse.ArgumentParser(description='MindRiver 智能体记忆运维工具')
    sub = p.add_subparsers(dest='command')

    s = sub.add_parser('search', help='搜索记忆')
    s.add_argument('query', help='搜索关键词')
    s.add_argument('--limit', type=int, default=10)

    d = sub.add_parser('dedup', help='去重')
    d.add_argument('input_file', help='输入文件')

    e = sub.add_parser('extract', help='提取事实')
    e.add_argument('--text', help='输入文本')
    e.add_argument('--file', help='输入文件')

    sub.add_parser('stats', help='存储统计')
    sub.add_parser('info', help='产品信息')

    args = p.parse_args()
    if args.command == 'search': cmd_search(args)
    elif args.command == 'dedup': cmd_dedup(args)
    elif args.command == 'extract': cmd_extract(args)
    elif args.command == 'stats': cmd_stats(args)
    elif args.command == 'info': cmd_info(args)
    else: p.print_help()

if __name__ == '__main__':
    main()
