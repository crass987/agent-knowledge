#!/bin/sh
# estate-sweep.sh — сверка поместья с meta/ESTATE.md.
# Сам удаляет ТОЛЬКО tmp-класс (владелец зафиксировал TTL 7 дней в реестре).
# Остальные классы — только кандидат-лист, решение за владельцем.
# Использование: estate-sweep.sh [путь-к-Astra] [путь-к-агент-ноутбук tmp-каталогу]

ASTRA="${1:-$HOME/Documents/Code_projects/Astra}"
DRY="${DRY:-0}"   # DRY=1 — ничего не удалять, только показать

echo "== tmp-класс (TTL 7 дней, удаление разрешено реестром) =="
found=0
for f in "$ASTRA"/.claude/tmp-*; do
  [ -e "$f" ] || continue
  found=1
  if [ -n "$(find "$f" -mtime +7 2>/dev/null)" ]; then
    if [ "$DRY" = "1" ]; then
      echo "ПРОСРОЧЕН (не удалён, DRY): $f"
    else
      rm -rf "$f" && echo "удалён: $f"
    fi
  else
    echo "свежий: $f"
  fi
done
[ "$found" = "0" ] && echo "пусто"

echo
echo "== кандидаты 30 дней (только список, решает владелец) =="
find "$ASTRA" -maxdepth 1 -name "*.tgz" -mtime +30 2>/dev/null | sed 's/^/бандл: /'
find "$ASTRA"/.claude -maxdepth 1 \( -name "HANDOFF-*" -o -name "PILOT-*" \) -mtime +30 2>/dev/null | sed 's/^/handoff: /'
find "$ASTRA" -maxdepth 1 -name "*.yml" ! -name "repos.yml" ! -name "1c-infra-dom.yml" -mtime +30 2>/dev/null | sed 's/^/корень yml: /'
echo "== конец сверки =="
