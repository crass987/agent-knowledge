#!/usr/bin/env bash
# rotate-skill-runs.sh [N=500]
# Keep the header + last N data rows of state/skill-runs.md.
# Older rows move to state/skill-runs.archive-<date>.md (gitignored).
# Run periodically so the telemetry log doesn't grow without bound.
set -euo pipefail
N="${1:-500}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
F="$ROOT/state/skill-runs.md"
[ -f "$F" ] || { echo "no $F" >&2; exit 0; }

sep=$(grep -n '^|---' "$F" | head -1 | cut -d: -f1 || true)
[ -n "$sep" ] || { echo "no table separator; nothing to rotate" >&2; exit 0; }

total=$(wc -l < "$F" | tr -d ' ')
data=$(( total - sep ))
if [ "$data" -le "$N" ]; then
  echo "only $data data rows (<= $N); nothing to rotate"
  exit 0
fi

drop=$(( data - N ))
first_drop=$(( sep + 1 ))
last_drop=$(( sep + drop ))
archive="$ROOT/state/skill-runs.archive-$(date +%Y%m%d).md"

{
  echo "<!-- archived $(date +%Y-%m-%d): $drop rows rotated out of skill-runs.md -->"
  sed -n "1,${sep}p" "$F"
  sed -n "${first_drop},${last_drop}p" "$F"
} > "$archive"

{
  sed -n "1,${sep}p" "$F"
  sed -n "$(( last_drop + 1 )),\$p" "$F"
} > "$F.new"
mv "$F.new" "$F"

echo "rotated: kept last $N data rows; archived $drop rows -> $(basename "$archive")"
