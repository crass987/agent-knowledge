#!/usr/bin/env python3
"""
Clean YouTube auto-generated SRT subtitles.

YouTube auto-captions use rolling captions: each block contains
the previous text + a new phrase. Transition blocks (~10ms duration)
sit between real blocks. This script extracts only the unique text.

Usage:
    python3 srt-clean.py input.srt [output.txt]

    If output is omitted, prints to stdout.
    Output is plain text (no timestamps).
"""

import re
import sys


def parse_timestamp(ts_line):
    """Parse SRT timestamp line, return (start_ms, end_ms) or None."""
    m = re.match(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})",
        ts_line,
    )
    if not m:
        return None
    g = [int(x) for x in m.groups()]
    start = g[0] * 3600000 + g[1] * 60000 + g[2] * 1000 + g[3]
    end = g[4] * 3600000 + g[5] * 60000 + g[6] * 1000 + g[7]
    return start, end


def _is_text(line):
    """Check if a line is plain text (not index, timestamp, or empty)."""
    if not line.strip():
        return False
    if re.match(r"^\d+$", line.strip()):
        return False
    if re.match(r"\d{2}:\d{2}:\d{2}", line.strip()):
        return False
    return True


def clean_srt(srt_text):
    """Extract unique text from rolling captions SRT.

    Handles the edge case where yt-dlp inserts a blank line between
    the timestamp and text in the first subtitle block, causing
    \\n\\n+ split to break it into orphan fragments.
    """
    # Phase 1: re-join orphan text fragments into their preceding block.
    # When a blank line appears between timestamp and text, \n\n+ split
    # produces fragments like ["1\n00:00:00,000 --> 00:00:02,230", "text here"].
    raw_blocks = re.split(r"\n\n+", srt_text.strip())
    merged = []
    for block in raw_blocks:
        lines = block.strip().split("\n")
        # Orphan: a block that is pure text (no index/timestamp)
        if all(_is_text(l) for l in lines) and merged:
            merged[-1] += "\n" + block.strip()
        else:
            merged.append(block)

    # Phase 2: parse rolling captions from merged blocks
    result = []
    for block in merged:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        ts = parse_timestamp(lines[1])
        if ts is None:
            continue

        duration = ts[1] - ts[0]
        if duration < 100:
            # Transition frame — skip
            continue

        text_lines = [l.strip() for l in lines[2:] if l.strip()]
        if text_lines:
            # Last line = the new/unique content
            result.append(text_lines[-1])

    return " ".join(result)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        text = f.read()

    cleaned = clean_srt(text)

    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w") as f:
            f.write(cleaned)
        print(f"Wrote {len(cleaned)} chars to {sys.argv[2]}", file=sys.stderr)
    else:
        print(cleaned)


if __name__ == "__main__":
    main()
