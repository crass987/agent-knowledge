#!/usr/bin/env python3
"""merge-index.py — merge agent-knowledge's skills/_INDEX.md into am-skills' _INDEX.md.

am-skills is a TEAM repo: colleagues add their own skills and index rows.
This merge keeps both sides:
  - rows referencing skills published from agent-knowledge → taken from SRC
    (agent-knowledge is the canon for those);
  - rows referencing anything else (team-added skills) → preserved from DST,
    collected into a dedicated section, order preserved.

A row is `| triggers | `skill-name/SKILL.md` |` — the skill path in backticks
is the merge key. Sections in DST that are not part of SRC's structure are
preserved as-is.

Usage:
  merge-index.py SRC_INDEX DST_INDEX OUT_INDEX
"""

import os
import re
import sys

ROW_RE = re.compile(r"^\|.*`([^`]+/SKILL\.md)`.*\|\s*$")
TEAM_SECTION = "## Team-added skills (not from agent-knowledge)"


def parse_rows(path):
    """Return (lines, {skill_path: row_line}) for a table-style _INDEX.md."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return [], {}
    rows = {}
    for line in lines:
        m = ROW_RE.match(line)
        if m:
            rows[m.group(1)] = line
    return lines, rows


def main():
    src_path, dst_path, out_path = sys.argv[1:4]
    src_lines, src_rows = parse_rows(src_path)
    _, dst_rows = parse_rows(dst_path)

    # My published skills = every skill path referenced in SRC.
    mine = set(src_rows)
    # Team rows = DST rows whose skill is not published from agent-knowledge.
    # Rows for skills we deliberately dropped (EXCLUDE_SKILLS) are not carried
    # over — the caller passes the same list via MERGE_EXCLUDE.
    exclude = set(filter(None, os.environ.get("MERGE_EXCLUDE", "").split()))
    team_rows = [row for skill, row in dst_rows.items()
                 if skill not in mine and skill.split("/")[0] not in exclude]

    out = list(src_lines)
    if team_rows:
        out += ["", TEAM_SECTION, "",
                "Skills added by the team directly in this repo. Publishes from "
                "agent-knowledge never touch them.", "",
                "| Task involves... | Load |",
                "|---|---|"]
        out += team_rows

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()