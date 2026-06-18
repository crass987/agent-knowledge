#!/usr/bin/env python3
"""Selective learnings retrieval. Prints <=3 entries matching the query.

Load-bearing guardrail (user-confirmed 2026-06-18): NEVER prints a whole
file — only matched frontmatter blocks, hard-capped. Keeps agent context
clean as the stores grow.

Usage:
    python3 scripts/auto-retrieve.py <query> [max]
"""
import sys
from pathlib import Path

MAX = 3


def blocks(text):
    """Yield each frontmatter block (list of lines) from text.

    Skips HTML-commented blocks (the seed examples live inside <!-- -->).
    """
    in_comment = False
    cur = None
    for line in text.splitlines():
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if line.strip() == "---":
            if cur is not None:
                yield cur
            cur = ["---"]
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        yield cur


def main(argv):
    if len(argv) < 2:
        print("usage: auto-retrieve.py <query> [max]", file=sys.stderr)
        return 2
    query = argv[1].lower()
    max_n = int(argv[2]) if len(argv) > 2 else MAX
    root = Path(__file__).resolve().parent.parent / "learnings"
    if not root.is_dir():
        print("no learnings/ found", file=sys.stderr)
        return 0
    shown = 0
    for md in sorted(root.glob("*.md")):
        if md.name.upper() == "README.MD":
            continue
        for cur in blocks(md.read_text(encoding="utf-8")):
            body = "\n".join(cur)
            if query in body.lower():
                print(body)
                print("---")
                shown += 1
                if shown >= max_n:
                    return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
