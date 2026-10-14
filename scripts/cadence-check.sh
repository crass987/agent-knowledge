#!/bin/sh
# cadence-check.sh — печатает просроченные active-задачи из state/cadence.md, молчит если нет.
# Использование: cadence-check.sh [путь-к-cadence.md]  (по умолчанию state/cadence.md рядом со скриптом)
# Exit: 0 всегда (hook-безопасно).

CADENCE="${1:-$(dirname "$0")/../state/cadence.md}"
[ -f "$CADENCE" ] || exit 0

TODAY=$(date +%Y-%m-%d)

awk -F'|' -v today="$TODAY" '
{
  gsub(/^[ \t]+|[ \t]+$/, "", $1); gsub(/^[ \t]+|[ \t]+$/, "", $2)
  gsub(/^[ \t]+|[ \t]+$/, "", $3); gsub(/^[ \t]+|[ \t]+$/, "", $4)
  # пропуск заголовка, пустых и комментарий-строк
  if ($1 == "" || $1 ~ /^#/ || $4 != "active" || $2 !~ /^[0-9]+$/) next
  if ($3 == "never" || $3 == "") { printf "ПРОСРОЧЕНО: %s — ни разу не запускалась\n", $1; next }
  cmd = "date -j -f \"%Y-%m-%d\" \"" $3 "\" +%s"
  cmd | getline last; close(cmd)
  cmd = "date -j -f \"%Y-%m-%d\" \"" today "\" +%s"
  cmd | getline now; close(cmd)
  if (last == "" || now == "") next
  if (now - last >= $2 * 86400) printf "ПРОСРОЧЕНО: %s — период %s дн., последний %s\n", $1, $2, $3
}' "$CADENCE"

exit 0
