"""MindRiver CLI"""
import sys, time, argparse
from .core import MindRiver
from .memory import MemoryStore
from .search import SearchEngine

def main():
    parser = argparse.ArgumentParser(prog="ov", description="MindRiver — Agent上下文数据库")
    parser.add_argument("--data-dir", default="./mindriver_data")
    sub = parser.add_subparsers(dest="cmd")

    mem = sub.add_parser("memory"); mem_sub = mem.add_subparsers(dest="action")
    add = mem_sub.add_parser("add"); add.add_argument("value"); add.add_argument("--key"); add.add_argument("--user", default="default")
    srch = mem_sub.add_parser("search"); srch.add_argument("query"); srch.add_argument("--user", default="default")
    lst = mem_sub.add_parser("list"); lst.add_argument("--user", default="default")

    ls_p = sub.add_parser("ls"); ls_p.add_argument("path", nargs="?", default="viking://")
    tree_p = sub.add_parser("tree"); tree_p.add_argument("path", nargs="?", default="viking://"); tree_p.add_argument("--depth", type=int, default=3)
    gs = sub.add_parser("search"); gs.add_argument("query"); gs.add_argument("--limit", type=int, default=10)
    sub.add_parser("stats")
    sub.add_parser("runtime-status", help="print a minimal context runtime status card")
    put_p = sub.add_parser("put"); put_p.add_argument("path"); put_p.add_argument("content"); put_p.add_argument("--type", default="file")
    get_p = sub.add_parser("get"); get_p.add_argument("path"); get_p.add_argument("--layer", default="full", choices=["L0","L1","full"])

    args = parser.parse_args()
    mr = MindRiver(args.data_dir)

    if args.cmd == "memory":
        store = MemoryStore(mr, user_id=getattr(args, "user", "default"))
        if args.action == "add":
            key = getattr(args, "key", None) or f"mem_{int(time.time())}"
            print(f"✅ {store.remember(key, args.value)}")
        elif args.action == "search":
            for r in store.recall(args.query): print(f"  [{r['score']:.1f}] {r['key']}: {r['value'][:100]}")
        elif args.action == "list":
            for m in store.get_all(): print(f"  {m['key']}: {m['value'][:100]}")
    elif args.cmd == "ls":
        for n in mr.ls(args.path):
            icon = {"dir":"📁","file":"📄","memory":"🧠","resource":"📚","skill":"🔧"}.get(n.node_type,"❓")
            print(f"  {icon} {n.name} ({n.token_count}tok)")
    elif args.cmd == "tree": print(mr.tree(args.path, args.depth))
    elif args.cmd == "search":
        for r in SearchEngine(mr).search(args.query, args.limit): print(f"  [{r.score:.1f}] {r.path} ({r.node_type})")
    elif args.cmd == "stats":
        s = mr.stats(); print(f"📊 节点:{s['total_nodes']} Token:{s['total_tokens']} 类型:{s['type_distribution']}")
    elif args.cmd == "runtime-status":
        from .context_runtime_control_plane import RuntimeSnapshot
        print(RuntimeSnapshot(active_items=0, blocked_items=0, streams=()).summary())
    elif args.cmd == "put": n = mr.put(args.path, args.content, node_type=args.type); print(f"✅ {n.path} ({n.token_count}tok)")
    elif args.cmd == "get":
        n = mr.get(args.path); 
        if n: print(n.summary if args.layer=="L0" else n.overview if args.layer=="L1" else n.content)
        else: print(f"❌ 未找到: {args.path}"); sys.exit(1)
    else: parser.print_help()
