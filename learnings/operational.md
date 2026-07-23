# Operational

Commands, tool quirks, environment facts.

<!--
Example entry (copy, fill, uncomment):
---
type: operational
key: short-kebab-key
insight: one sentence, fact not opinion
confidence: 8
source: observed
files: []
ts: 2026-06-18
scope: harness
---
-->

---
type: operational
key: new-skill-needs-link-sh
insight: Навык, добавленный в agent-knowledge/skills/, невидим в Claude Code, пока не запущен link.sh — он симлинкает skills/* в ~/.claude/skills/. Запускать ./link.sh после каждого нового навыка.
confidence: 9
source: observed
files: ["link.sh", "README.md"]
ts: 2026-06-18
scope: harness
---

---
type: operational
key: link-sh-not-executable
insight: link.sh не имеет +x — `./link.sh` падает с "permission denied". Запускать `bash link.sh` (или `chmod +x link.sh` один раз). Уточняет запись new-skill-needs-link-sh.
confidence: 9
source: observed
files: ["link.sh"]
ts: 2026-06-19
scope: harness
---

---
type: operational
key: astra-meta-push-needs-vpn
insight: Astra meta-repo remote — приватный GitLab (gitlab.158-160-60-159.sslip.io); `git push` падает с SSL_ERROR_SYSCALL без VPN/доступа. agent-knowledge (GitHub) пушится штатно.
confidence: 9
source: observed
files: []
ts: 2026-06-19
scope: harness
---

---
type: operational
key: book-rar-extraction
insight: Книги иногда приходят в `.rar` — `brew install unar`, затем `unar -f -o <dir> file.rar`. Внутри обычно текстовый PDF (сделан через виртуальный принтер типа doPDF), извлекается чисто: `pdftotext -layout book.pdf book.txt`. Bookmarks/outline недоступны (pypdf/PyPDF2/mutool/qpdf отсутствуют на машине) → структуру глав восстанавливать по печатному оглавлению: `grep -nE` заголовков частей/глав → диапазоны строк → границы для извлечения.
confidence: 8
source: observed
files: []
ts: 2026-06-24
scope: skill:book-knowledge-extraction
---

---
type: operational
key: am-update-validator-skips-repo-proofs
insight: capability_registry_check.py валидирует только `docs/…` пути под master_docs; `repo:` доказательства НЕ проверяются. Удалённые/перемещённые файлы в кодовых репо (удалённый `event-processing/seed`, перенесённый `agent/…/autoconfig/discovered.go`) невидимы валидатору → Phase 2 обязана batch-check'ать существование файлов всех `repo:` proof'ов: `grep -oE 'repo:[^|)]+' functional-registry.md | sed 's/^repo://; s/ .*//; s/:[0-9]*$//' | sort -u | while read p; do [ -e "$p" ] || echo "MISS $p"; done`. На запуске 2026-07-01 так нашлись 3 сломанных proof'а (все «переехали», код уцелел).
confidence: 9
source: observed
files: [meta/scripts/capability_registry_check.py, PM/strategy/functional-registry.md]
ts: 2026-07-01
scope: skill:am-update
---

---
type: operational
key: am-update-force-sync-protects-dirty
insight: `sync-repos.sh --force` НЕ делает `git reset --hard` для репо с незафиксированными локальными изменениями — помечает `[DIRTY]` и пропускает (даже под --force). На запуске 2026-07-01 `docs` остался на feature-ветке MON-4440 с правками. Чтобы принудительно синкнуть — закоммитьте/стэшните WIP в саб-репо вручную перед запуском.
confidence: 8
source: observed
files: [sync-repos.sh]
ts: 2026-07-01
scope: skill:am-update
---

---
type: operational
key: c2-audit-go-lib-storage-indirection
insight: C2-audit «who writes table X» даёт ложный negative, если grep'ать только сервис-репо: AM Go-сервисы персистят через общий go-lib/storage (PersistMonitor / CreateRule / upsertConfig), поэтому INSERT/UPDATE лежит в go-lib, не в сервисе. Решение: grep и сервис-репо, и go-lib/storage/ по имени таблицы и storage-методам, ИЛИ трассировать Storage/Repo-интерфейс сервиса до его реализации в go-lib. Применимо и к атрибуции db_reads/db_writes в профилях. Сэкономило ~10-15 мин maker/checker-переделок на каждом таком drift'е.
confidence: 9
source: observed
files: []
ts: 2026-07-21
scope: skill:am-update
---
