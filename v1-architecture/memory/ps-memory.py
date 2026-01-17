#!/usr/bin/env python3
"""
Pattern Space Memory CLI - mem0 wrapper for shell hooks

Usage:
    ps-memory.py add --content "..." [--user USER] [--agent AGENT] [--metadata '{}']
    ps-memory.py search --query "..." [--user USER] [--limit N]
    ps-memory.py get-all [--user USER]
    ps-memory.py bridge [--user USER] [--limit N]

Requires: pip install "mem0ai[graph]"
"""

import argparse
import json
import os
import sys

def get_config():
    """Load mem0 configuration from file or environment."""
    config_paths = [
        os.environ.get('MEM0_CONFIG'),
        os.path.expanduser('~/.pattern-space/memory/mem0-config.json'),
        os.path.join(os.path.dirname(__file__), 'mem0-config.json'),
    ]

    for path in config_paths:
        if path and os.path.exists(path):
            with open(path) as f:
                return json.load(f)

    # Return empty config (use mem0 defaults)
    return {}

def get_memory():
    """Initialize mem0 Memory instance."""
    try:
        from mem0 import Memory
    except ImportError:
        print(json.dumps({"error": "mem0 not installed. Run: pip install 'mem0ai[graph]'"}))
        sys.exit(1)

    config = get_config()
    try:
        return Memory.from_config(config) if config else Memory()
    except Exception as e:
        print(json.dumps({"error": f"mem0 init failed: {str(e)}"}))
        sys.exit(1)

def cmd_add(args):
    """Add a memory."""
    m = get_memory()

    messages = [{"role": "user", "content": args.content}]

    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            metadata = {"raw": args.metadata}

    if args.type:
        metadata["type"] = args.type
    if args.confidence:
        metadata["confidence"] = args.confidence

    result = m.add(
        messages=messages,
        user_id=args.user,
        agent_id=args.agent,
        metadata=metadata
    )

    print(json.dumps(result, default=str))

def cmd_search(args):
    """Search memories."""
    m = get_memory()

    results = m.search(
        query=args.query,
        user_id=args.user,
        limit=args.limit
    )

    print(json.dumps(results, default=str))

def cmd_get_all(args):
    """Get all memories for user."""
    m = get_memory()

    results = m.get_all(user_id=args.user)

    print(json.dumps(results, default=str))

def cmd_bridge(args):
    """Get session bridge context (recent memories)."""
    m = get_memory()

    # Search for patterns, breakthroughs, trajectories
    results = m.search(
        query="pattern breakthrough trajectory evolution session",
        user_id=args.user,
        limit=args.limit
    )

    # Categorize results
    bridge = {
        "patterns": [],
        "breakthroughs": [],
        "trajectories": [],
        "evolutions": [],
        "other": []
    }

    if isinstance(results, list):
        for mem in results:
            content = mem.get('memory', mem.get('content', ''))
            if '[PATTERN]' in content:
                bridge["patterns"].append(mem)
            elif '[BREAKTHROUGH]' in content:
                bridge["breakthroughs"].append(mem)
            elif '[TRAJECTORY]' in content:
                bridge["trajectories"].append(mem)
            elif '[EVOLUTION]' in content:
                bridge["evolutions"].append(mem)
            else:
                bridge["other"].append(mem)

    print(json.dumps(bridge, default=str))

def main():
    parser = argparse.ArgumentParser(
        description='Pattern Space Memory CLI - mem0 wrapper'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Default user
    default_user = os.environ.get('PATTERN_SPACE_USER_ID', 'pattern-space-user')

    # add command
    add_parser = subparsers.add_parser('add', help='Add a memory')
    add_parser.add_argument('--content', '-c', required=True, help='Memory content')
    add_parser.add_argument('--user', '-u', default=default_user, help='User ID')
    add_parser.add_argument('--agent', '-a', help='Agent/perspective ID')
    add_parser.add_argument('--metadata', '-m', help='JSON metadata')
    add_parser.add_argument('--type', '-t', help='Memory type (pattern, breakthrough, etc.)')
    add_parser.add_argument('--confidence', type=float, help='Confidence score')

    # search command
    search_parser = subparsers.add_parser('search', help='Search memories')
    search_parser.add_argument('--query', '-q', required=True, help='Search query')
    search_parser.add_argument('--user', '-u', default=default_user, help='User ID')
    search_parser.add_argument('--limit', '-l', type=int, default=10, help='Max results')

    # get-all command
    getall_parser = subparsers.add_parser('get-all', help='Get all memories')
    getall_parser.add_argument('--user', '-u', default=default_user, help='User ID')

    # bridge command
    bridge_parser = subparsers.add_parser('bridge', help='Get session bridge context')
    bridge_parser.add_argument('--user', '-u', default=default_user, help='User ID')
    bridge_parser.add_argument('--limit', '-l', type=int, default=10, help='Max results')

    args = parser.parse_args()

    if args.command == 'add':
        cmd_add(args)
    elif args.command == 'search':
        cmd_search(args)
    elif args.command == 'get-all':
        cmd_get_all(args)
    elif args.command == 'bridge':
        cmd_bridge(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
