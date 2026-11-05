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
key: am-seeding-two-docsets
insight: AM сидирование — два параллельных док-сета (AMP-013/seeding.md = AS-IS, improvements = TO-BE design), при аудите читать оба; код-истина = amctl/cmd/seed.go + internal/seed/*.
confidence: 9
source: observed
files: [analytics-hub/amps/docs/AMP-013/seeding.md, analytics-hub/improvements/docs/Установка и обновление/Сидирование/, amctl/cmd/seed.go]
ts: 2026-08-03
scope: skill:am-docs-audit
---
По сидированию AM есть два док-сета, которые надо различать при аудите (пути после AMP-реструктуризации 2026-10):
- `analytics-hub/amps/docs/AMP-013/seeding.md` = **AS-IS**, описывает текущий код (`admin-backend/internal/seed/`, `cmd/seed.go`). Trust для текущего механизма, но отстаёт на релиз (на 2026-08-03 не хватает snmp/vector_configs, неверный exit code).
- `analytics-hub/improvements/docs/Установка и обновление/Сидирование/` = **TO-BE design-спека** (README + Seeding_Specification + 01–06_task), описывает целевой единый механизм (`--profile`, `SourceProvider`, `ApplyRecords`) — НЕ реализован в runner.go, но не помечен как TO-BE.
При любом вопросе по сиду читать оба; код-истина = `amctl/cmd/seed.go` (флаги/регистрация) + `internal/seed/*` (поведение по-сидерно). changeable/remove_absent есть только в ns/*, не в обобщённом Runner.

---
type: operational
key: c2-canonical-copy
insight: Канонический C2-контейнеры.md живёт в analytics-hub/internal_docs/docs/Архитектура/ (переехал из master_docs при AMP-реструктуризации 2026-10); rag-agent/Notes — устаревшее зеркало. Править только analytics-hub.
confidence: 9
source: observed
files: [analytics-hub/internal_docs/docs/Архитектура/C2-контейнеры.md]
ts: 2026-08-04
scope: skill:am-update
---
Канон C1/C2/C3 = `analytics-hub/internal_docs/docs/Архитектура/` (до AMP-реструктуризации октября 2026 — `master_docs/docs/Архитектура/`). Править ТОЛЬКО analytics-hub; rag-agent/Notes — зеркало для RAG, не канон. (замечено при snmp-traps research 2026-08-04; путь обновлён 2026-10-08)

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
См. также: [[confluence-update-content-placeholder]]
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

---
type: operational
key: cc-logs-dir-underscore-flattening
insight: Каталог логов Claude Code = путь проекта в ~/.claude/projects с заменой на дефисы и слэшей, и подчёркиваний (Code_projects → Code-projects).
confidence: 9
source: observed
files: [agent-knowledge/scripts/measure-run.py]
ts: 2026-08-21
scope: harness
---
Оригинальный measure-run.py от nick-vels делал только replace("/", "-") и молча не находил каталог; фикс — добавить .replace("_", "-").

---
type: operational
key: req-spec-path-amps
insight: REQ/SPEC в analytics-hub переехали в фичевые папки amps/docs/AMP-0XX/ (коммиты «merge REQ => AMP», «merge ADR, SPEC to AMP», октябрь 2026) — старые пути analytics-hub/docs/requirements/, internal_docs/docs/{requirements,specifications}, improvements/docs пусты
confidence: 9
source: observed
files: [analytics-hub/amps/docs, PM.md]
ts: 2026-10-08
scope: skill:am-write-specs
---
Скилл am-write-specs и PM.md ещё указывают старые расположения. Референс искать `find analytics-hub -name "REQ-*" -o -name "SPEC-*"` (сейчас десятки в amps/docs/AMP-003/006/009/011/016…). PM.md в метарепе показывает мёртвый analytics-hub/docs/requirements/ — править вне скоупа prune.

---
type: operational
key: git-diff-quotepath-cyrillic
insight: git diff --name-only экранирует кириллицу в путях (core.quotepath=true по умолчанию) — grep по литеральному русскому имени файла молча даёт 0 совпадений; для сверок путей использовать git -c core.quotepath=false
confidence: 9
source: observed
files: []
ts: 2026-10-08
scope: harness
---
Проявилось при prune 2026-10-08: проверка пересечения локально-грязного файла analytics-hub (…/Ролевая модель/RBAC/rbac-feature-DRAFT.md) с входящим диффом дала ложное «0 пересечений», а git pull честно абортился — проверка была сломана экранированием. Правило: в репо с кириллическими путями все сверки имён — только с `-c core.quotepath=false`.
---
type: operational
key: facts-drift-counter-profile-date
insight: Дрейф в facts-репорте считается от даты Last-refreshed в шапке профиля, а не от последнего C2-аудита — для аудита C2 брать окно «с даты последнего c2-audit» (git log --since), не число из facts.
confidence: 9
source: observed
files: ["meta/scripts/collect-repo-facts.sh"]
ts: 2026-09-04
scope: project
---
admin-console: facts показал 16 коммитов с 2026-09-03, фактическое окно после аудита 08-11 — ~230. Отдельный дефект: секция Dirs go-lib в facts обрезана на 30 записях (поднять лимит листинга в collect-repo-facts.sh).

---
type: operational
key: srt-clean-strips-timestamps
insight: srt-clean.py выдаёт transcript.txt без таймкодов, а шаблон документа знаний требует MM:SS для каждой единицы — якоря восстанавливаются перепарсингом исходного SRT из source/ (python: regex по блокам, поиск фразы → первый таймкод).
confidence: 9
source: observed
files: ["~/.claude/skills/video-knowledge-extraction/scripts/srt-clean.py"]
ts: 2026-09-14
scope: harness
См. также: [[srt-clean-fails-on-sequential-subs]], [[srt-anchor-timestamps]]
---
SRT парсится одним python-скриптом: split по \n\n, блок с '-->' в строке 1, timestamp из start, текст после тегов. Оригинал SRT сохраняйте в source/ до очистки.
---
type: operational
key: release-notes-infra-by-code
insight: Инфровые изменения релиза AM не видны по summaries Jira — проверять по коду platformctl/monitoring-astra-icl/infra-releases; release.yaml запаздывает
confidence: 9
source: observed
files: [monitoring-astra-icl/scripts/build_airgap.sh, infra-releases/release.yaml]
См. также: [[mon-sprint-vs-fixversion]], [[project-am-release-jira-filters]]
ts: 2026-09-21
scope: harness
---
Инфровая часть релиза (закрытый контур, airgap, установка, шлюзы) почти не тикетируется в MON или прячется в сабмитах — по сводке fixVersion её не собрать. Прогон v.1.7.0 (2026-09-21): «мониторинг куба из закрытого контура» в Jira дал только airgap-очистку (MON-4561), а по коду — platformctl install из офлайн-бандла + helm-чарт agent-k8s в бандле (monitoring-astra-icl/scripts/build_airgap.sh, --set upstreamAddr=airgap), Envoy вместо vmauth/gatekeeper, externalDB. Владелец ждёт инфра-раздел в нотсах; без ресерча по репам он получается пустым или выдуманным. Для инфра-части диспачить Explore по platformctl, monitoring-astra-icl (build_airgap.sh, docker-compose), infra-releases, amctl/config-api/go-lib; cross-check: infra-releases/release.yaml часто ещё на прошлой версии, airgap-бандл собирает amctl/platformctl с тегом dev — перед релизом это точки проверки, не факты нотсов.

---
type: operational
key: am-vector-version-artifactory
insight: Версию Vector в поставке АМ проверять по бинарнику из Artifactory am-generic/exporters/vector — листинг папок врёт про свежесть (latest перепаковывается старым бинарником), embedded build_info в `strings vector | grep 0\.` — источник истины
confidence: 9
source: observed
files: ["PM/sessions/vector-log-sources/vector-log-sources.md"]
ts: 2026-10-06
scope: harness
---
`latest` в Artifactory перезаливали 2026-09-28, но внутри всё ещё 0.41.1 (build_info: 2024-09-11); версия апстрим-репака = имя папки + строки в бинарнике. Бонус: /releases/latest у vectordotdev/vector отдаёт vdev-* тег — реальные релизы фильтровать из списка /releases по префиксу v0.

---
type: operational
key: dion-vc-transcript-extraction
insight: Записи dion.vc не скачиваются без логина и не поддерживаются yt-dlp. Рабочий путь: Playwright (профиль mcp-chrome, разовый логин сохраняется) → страница /video/<id> → кнопка «Расшифровка видео Текст видео и протокол» → кнопка download отдаёт speech-to-text.doc (это HTML, не Word) → textutil -convert txt → чистый текст со спикерами и таймкодами. Название записи брать из последнего пункта хлебных крошек (nav p:last).
confidence: 9
source: observed
files: []
ts: 2026-10-08
scope: harness
См. также: [[asr-transcript-literal-grep-fails]]
---

---
type: operational
key: workflow-verdicts-match-by-index
insight: В workflow-пайплайнах maker→checker сопоставляйте вердикты чекеров по индексу элемента, не по slug/item-названию — LLM-чекеры переформулируют названия, и slug-матчинг молча теряет вердикты («checker missing»), убивая одобренные правки.
confidence: 10
source: observed (am-update 2026-11-01: 8 из 9 правок реестра отклонены из-за mismatch, полный перегон чекеров)
ts: 2026-11-01
scope: harness
---

Схема чекера: массив verdicts с полем i (0-based индекс) + инструкция «в том же порядке, что и вход». Сопоставление строго по позиции. Slug-названия годятся только для логов/лейблов.

---
type: operational
key: workflow-bulk-data-via-tmp-files
insight: Массовые данные для агентов workflow (списки правок, JSON-выжимки) кладите в /tmp-файл и давайте агентам путь — «прочитай элемент i из файла», а не прокачивайте через args/workflow-скрипт: меньше транскрипционных ошибок и дешёвый resume.
confidence: 9
source: observed (am-update 2026-11-01: args без полей уронил запуск за 24 мс; /tmp-вариант отработал чисто)
ts: 2026-11-01
scope: harness
---

Годится для промптов вида «возьми элемент i массива из file.json». Скрипт workflow не имеет доступа к ФС — но агенты имеют.

---
type: operational
key: am-registry-validator-root-internal-docs
insight: capability_registry_check.py для Astra запускать с корнем analytics-hub/internal_docs — доки переехали туда из master_docs в 2026-10; против master_docs валидатор даёт 9 ложных broken_link (промпты capability-registry-*.md пока говорят master_docs).
confidence: 10
source: observed (am-update 2026-11-01, Stage 4)
ts: 2026-11-01
scope: project
---

Команда: `python3 meta/scripts/capability_registry_check.py PM/strategy/functional-registry.md analytics-hub/internal_docs`.
