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

---
type: operational
key: am-update-drift-vs-profile-date
insight: В facts-отчёте drift (collect-repo-facts.sh) считается относительно даты repo-AGENTS.md, а не штампа «Last refreshed» в meta/repos/*.md — пересчитывай commits-since относительно даты профиля, иначе Stage 1 work-list раздувается (пример 2026-07-28: event-processing 418c→8c реально, agent/identity-provider/license-service/amctl/docs → 0c).
confidence: 9
source: observed
files: [meta/scripts/collect-repo-facts.sh, meta/repos/*.md]
ts: 2026-07-28
scope: project
---
am-update Stage 1: `git log --since=<profile-refresh-date> --no-merges | wc -l` per repo — реальная дельта, а не число из Drift-блока facts.

---
name: am-seeding-two-docsets
description: AM сидирование — два параллельных док-сета (master_docs=AS-IS, improvements=TO-BE design), дрейфуют
metadata:
  type: operational
---
По сидированию AM есть два док-сета, которые надо различать при аудите:
- `analytics-hub/master_docs/docs/Установка и обновление/Сидирование/seeding.md` = **AS-IS**, описывает текущий код (`admin-backend/internal/seed/`, `cmd/seed.go`). Trust для текущего механизма, но отстаёт на релиз (на 2026-08-03 не хватает snmp/vector_configs, неверный exit code).
- `analytics-hub/improvements/docs/Установка и обновление/Сидирование/` = **TO-BE design-спека** (README + Seeding_Specification + 01–06_task), описывает целевой единый механизм (`--profile`, `SourceProvider`, `ApplyRecords`) — НЕ реализован в runner.go, но не помечен как TO-BE.
При любом вопросе по сиду читать оба; код-истина = `admin-backend/cmd/seed.go` (флаги/регистрация) + `internal/seed/*` (поведение по-сидерно). changeable/remove_absent есть только в ns/*, не в обобщённом Runner.

---
type: operational
key: c2-canonical-copy
insight: Канонический C2-контейнеры.md живёт в analytics-hub; rag-agent/Notes — устаревшее зеркало.
confidence: 9
source: observed
---
Две копии C2-контейнеры.md:
- `analytics-hub/master_docs/docs/Архитектура/C2-контейнеры.md` = **канон** (vmalert уже «НЕ ИСПОЛЬЗУЕТСЯ, Сальников 2026-07-06»; modern-traps «подключён к runtime»).
- `rag-agent/Notes/master_docs/Архитектура/C2-контейнеры.md` = **устаревшее зеркало** для RAG (старая vmalert-формулировка «legacy, планируется удаление»; modern-traps «не подключён»).

Маркер свежести: формулировка vmalert (analytics-hub новее). Править ТОЛЬКО analytics-hub. (замечено при snmp-traps research 2026-08-04)

---
type: operational
key: cross-repo-context-header-canonical
insight: collect-repo-facts.sh:488 парсит Profile Connections по заголовку РОВНО «## Cross-Repo Context» (sed range). Неканоничные заголовки («Cross-Repo Dependencies»/«Communication»/«Connections») молча выпадают из facts → C2-audit получает неполные evidence для этих сервисов. На запуске 2026-08-11 так терялись core-сервисы config-api/incident-service/notification-service/clickhouse-adapter/agent. Лечение: normalize всех meta/repos/*.md заголовков на «## Cross-Repo Context» (TEMPLATE требует ровно это имя). Чек: `for f in meta/repos/*.md; do grep -qE "^## Cross-Repo Context" "$f" || echo "MISS $f"; done`.
confidence: 9
source: observed
files: [meta/scripts/collect-repo-facts.sh, meta/repos/TEMPLATE.md]
ts: 2026-08-11
scope: skill:am-update
---

---
type: operational
key: confluence-content-file-sandbox
insight: MCP `confluence_update_page` `content_file` сэндбокшен до cwd (Path traversal detected на /tmp). Для больших md (registry view и т.п.) пиши файл в gitignored-путь ВНУТРИ cwd (PM/tmp/ — gitignored по PM/CLAUDE.md) и передавай относительный path. Не пытаться /tmp или абсолютные пути вне репо.
confidence: 9
source: observed
files: []
ts: 2026-08-11
scope: harness
---

---
type: operational
key: analytics-hub-pm-push-writable
insight: analytics-hub (dev) и PM (main) пушатся из meta-repo штатно — remote содержит write-capable PAT (asalnikov:glpat-…), `git push origin <branch>` работает (наблюдалось 2026-08-11: analytics-hub aa27f34..bd0fd64, PM 846f3fb..91de510). Уточняет/противоречит CLAUDE.md «read-only token» — для клонов пользователя токен write-capable. am-update Stage 1/3/4 right-push в analytics-hub dev / PM main — нормальный flow (так живут C2-коммиты из истории).
confidence: 8
source: observed
files: []
ts: 2026-08-11
scope: project
---

---
type: operational
key: meta-clone-single-branch-refspec
insight: Клоны суб-репо в meta-repo (monitoring-astra-icl и др.) имеют refspec, пиненый к ОДНОЙ ветке (dev) — `git branch -r` показывает только dev. Чтобы увидеть feature-ветки, на которых стоят ArgoCD-стенды (напр. `sharding` → стенд am-sharding), юзай `git ls-remote origin 'refs/heads/*'` или `git fetch origin <branch>`; дефолтный fetch их не приносит.
confidence: 9
source: observed
files: ["clone-repos.sh", "repos.yml"]
ts: 2026-08-11
scope: harness
---
