#!/usr/bin/env python3
"""Flag hardcoded mcp__* tool-names in skill texts.

Enforces portability principle P3: skills reference capabilities, concrete
tools live in the AGENTS.md tool-registry. Exits 1 if any found, 0 if clean.
"""
import re
import sys
from pathlib import Path

TOOLNAME = re.compile(r"\bmcp__[A-Za-z0-9_]+__[A-Za-z0-9_]+")


def scan_dir(root):
    """Return list of '<file>:<line>: ...' findings for hardcoded tool-names."""
    findings = []
    for md in Path(root).rglob("SKILL.md"):
        for lineno, line in enumerate(
            md.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for hit in TOOLNAME.findall(line):
                findings.append(
                    f"{md}:{lineno}: hardcoded tool-name '{hit}' "
                    f"— reference by capability in the AGENTS.md tool-registry"
                )
    return findings


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path("skills")
    findings = scan_dir(root)
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
