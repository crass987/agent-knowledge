# Pitfalls

Things that bite.

<!--
Example entry (copy, fill, uncomment):
---
type: pitfall
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
type: pitfall
key: jira-mcp-broad-text-jql-oversize
insight: mcp__jira__search_issues with broad text JQL (summary~/description~ on common words like "документац") over a large project (MON) returns enormous results (551K chars / 10 940 lines) dumped to a file — always narrow JQL, pass a short `fields` list, and keep `max_results` ≤ 15 for exploratory pain/doc searches.
confidence: 9
source: observed
files: []
ts: 2026-07-13
scope: harness
См. также: [[jira-mcp-401-substring-issuekey]], [[jira-bulk-async-server-side-completes-after-mcp-abort]], [[jira-search-truncates-at-maxresults]], [[ref-mcp-jira-relations-got]]
---
A zero-result narrow search (e.g. `issuetype=Bug AND summary~"документац"`) is itself signal — it means there is no feedback channel for that defect class, not that the area is clean.

---
type: pitfall
key: asr-transcript-literal-grep-fails
insight: On ASR-mangled transcripts, literal grep for product/competitor names fails (Zabbix→«запикса»/«забикс», Grafana→«графиня», Пульт missed by a pattern) — read in context to QC a subagent's transcript-based output; do not grep-literal. Applies to QC of subagent drafts, not just prose; коверкалки из ASR не переносить в артефакты — имена организаций/продуктов сверять с владельцем до записи (влито из asr-mangles-org-product-names, prune 2026-11-24).
confidence: 9
source: observed
files: []
ts: 2026-07-21
См. также: [[asr-mangles-org-product-names]], [[speech-to-text-doc-summary-vs-transcript]], [[dion-vc-transcript-extraction]]
scope: harness
---
Гринатом pain-report QC: my grep for «zabbix|пульт» returned 0, yet the subagent (reading context) was right on all three. Reinforces read-don't-grep for names under ASR noise.

---
type: pitfall
key: subagent-cjk-glyph-leak
insight: A subagent drafting Russian prose can inject stray Chinese glyphs (可能是 / 监控 / 材料) — a multilingual training leak; the source transcript had 0 CJK. Always grep the draft for CJK (`grep -cP '[\x{4e00}-\x{9fff}]'`) and spot-check product/vendor names against source before accepting a subagent's artifact.
confidence: 8
source: observed
files: []
См. также: [[subagent-briefs-require-russian-explicitly]]
status: superseded
superseded_by: subagent-briefs-require-russian-explicitly
ts: 2026-07-21
scope: harness
---
Гринатом draft had 3 CJK glitches in the report's own voice (not in verbatim quotes) + 1 fabricated vendor name absent from source — subagent drafts need a fabrication/glyph QC pass, not just a style pass.

---
type: pitfall
key: zsh-glob-unquoted-url
insight: In zsh, an unquoted URL containing `?` and `=` (YouTube `?v=ID`, any query string) is parsed as a filename glob → `(eval):1: no matches found` and yt-dlp/curl exits with no output; single-quote the URL (`URL='https://...'`) before passing it to any command. The video-knowledge-extraction skill's transcript-acquisition.md shows unquoted `URL` placeholders — always quote on substitution. Same trap for grep globs: `--include=*.go` must be `--include='*.go'`, otherwise zsh aborts the command. On macOS BSD grep, `grep -r ... .` prints paths without the `./` prefix (`meta/reports/...`), so exclusion filters must match `^(meta|PM)/`, not `^\./`.
confidence: 9
source: observed
files: [~/.claude/skills/video-knowledge-extraction/references/transcript-acquisition.md]
ts: 2026-11-23
scope: harness
---
Matt Pocock video run: `yt-dlp --list-subs https://www.youtube.com/watch?v=n0VhIVtviC0` → `(eval):1: no matches found: https://...`; assigning to `URL='...'` fixed it instantly.
Astra grill run 23.11: `grep -rl ... --include=*.go` → `(eval):1: no matches found` (three wasted calls); then `grep -v '^\./meta/'` excluded nothing because BSD grep printed `meta/...` without `./`.

---
type: pitfall
key: srt-clean-fails-on-sequential-subs
insight: The skill's `srt-clean.py` assumes classic YouTube progressive-reveal auto-subs (each block = cumulative text, only last line is new). Some auto-caption tracks (observed: `ru-ru` on J6QqWkLFV-4) are clean, sequential, NON-overlapping blocks whose only artifact is `\h` word-join markers — running srt-clean.py there keeps only sentence-tails and fragments the transcript. Fix: inspect raw SRT structure first; if blocks are already sequential, skip the script and just strip `\h` + index/timestamp lines (5-line python). Always sanity-check the FIRST phrase of cleaned output.
confidence: 9
source: observed
files: [~/.claude/skills/video-knowledge-extraction/scripts/srt-clean.py]
См. также: [[yt-vtt-to-srt-before-clean]], [[srt-clean-strips-timestamps]], [[srt-anchor-timestamps]], [[srt-timestamps-before-clean]]
ts: 2026-08-06
scope: harness
---
Also: YouTube can misdetect the base caption language (reported `en-en` "English from English" for a Russian-speech video; the `en-en` track was a silent auto-TRANSLATION, true original was `ru-ru`). Always cross-check the detected base language against channel/title language and prefer `<lang>-<lang>` original over `-en` translation for faithful quotes.

---
type: pitfall
key: jira-mcp-401-substring-issuekey
status: superseded
insight: jira-mcp's format_error_message matches HTTP statuses by substring, so any issue key containing "401"/"403"/"404" (e.g. MON-4013) masks the real response — a 400 Bad Request on such keys is reported as «Ошибка аутентификации: проверьте JIRA_EMAIL/JIRA_API_TOKEN», sending you chasing creds that are fine.
confidence: 10
source: observed
files: [/Users/CraSS/Documents/Code_projects/jira-mcp/mcp_server.py]
ts: 2026-08-13
См. также: [[jira-mcp-broad-text-jql-oversize]], [[jira-bulk-async-server-side-completes-after-mcp-abort]], [[jira-search-truncates-at-maxresults]]
scope: harness
---
Real status/message lives in ~/.cache/jira-mcp/logs/mcp-<date>.jsonl (per-call "error" entries) or in the Jira response body via a direct probe; the server itself discards e.response.text. Fix candidate: match "401 Client Error"/"Unauthorized for url" instead of bare "401" in mcp_server.py format_error_message (~line 328, also the resource-read mapper ~line 902).

Superseded 2026-11-24 (prune): факт впитан в skills/vid-rabot/SKILL.md — ловушка 401-подстроки (MON-4013)
---
type: pitfall
key: jira-worklogdate-retro-backfill-delta
insight: JQL `worklogDate` is a snapshot of the Jira worklog INDEX at query time, but teams backfill timesheets retroactively (observed on MON 2026-08-13: bulk imports created 18:56–19:00 with July `started` dates, comment-stamp «Работа над запросом MON-X», landed ~40 min AFTER a vid-rabot marking run finished → 13 tickets escaped classification). Symptom: a Tempo report shows «Не указан аккаунт и вид работ» for tickets your run's post-write JQL check counted as clean — both sides were honest, the worklogs simply arrived later. After any worklog-scoped marking run, expect a delta; before reconciling against a Tempo export, re-run the scope JQL and diff the totals (154→167 = +13 caught it here). Cancelled tickets with logged time (MON-45/46) stay out of scope by design — they need a manual management decision, not automation.
confidence: 8
source: observed
files: [~/.claude/skills/vid-rabot/SKILL.md]
ts: 2026-08-14
scope: harness

---
type: pitfall
key: gatekeeper-10s-default-timeouts
insight: gogatekeeper 4.7.1 (образ AM gatekeeper) по умолчанию рвёт запросы к upstream через 10s: `UpstreamResponseHeaderTimeout=10s` (Transport) и `ServerWriteTimeout=10s` (http.Server); флаг `--upstream-timeout` — только dial-таймаут и длинные запросы НЕ спасает. В цепочке браузер→admin-ui nginx→gatekeeper→admin-backend обрыв на ровно 10.00s с «http: proxy error: context canceled» в admin-backend и 499 у нижестоящего nginx = дефолты gatekeeper, а не nginx (60s там ни при чём). K8s/helm уже лечит (50s: admin-ui-deployment.yaml:63-66), docker-compose — нет (gatekeeper-idp без флагов). Фикс: `--upstream-response-header-timeout=120s --server-write-timeout=120s` + пересоздать контейнер.
confidence: 9
source: observed
files: [monitoring-astra-icl/docker-compose/docker-compose.yml, monitoring-astra-icl/helm/templates/admin-ui-deployment.yaml, admin-backend/internal/entities/settings/handler.go]
ts: 2026-08-19
scope: project
status: superseded

---
Superseded 2026-11-24 (traverse): gogatekeeper вышел из поставки AM — 10s-дефолты не актуальны для текущих стендов.

type: pitfall
key: amctl-fake-ip-dns-epERM
insight: amctl (и любой Go-бинарь) на маке с прокси-клиентами (V2Box/sing-box) может получить от DNS fake-IP 198.18.x–198.19.x → connect падает с «operation not permitted» (туннель выключен), при этом curl работает (системный scoped-резолвер даёт верный IP). Диагноз: `dscacheutil -q host -a name <host>`; лечение: `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` или перезапуск VPN-клиента. Может пройти само по истечении кэша (наблюдалось 2026-08-20: сбой в 16:14, чисто в 17:51 без изменений).
confidence: 7
source: observed
files: [~/.amctl.yaml, /etc/resolv.conf]
ts: 2026-08-20
scope: harness
---

---
type: pitfall
key: workflow-overlapping-edits-apply-order
insight: Пакетное применение одобренных workflow-правок падает, если old_text'ы перекрываются — перед replace задать явный порядок (большая правка первой) и проверять count==1 на каждую.
confidence: 9
source: observed
files: ["skills/am-update/prompts/c2-fix.md"]
ts: 2026-09-04
scope: harness
---
am-update 2026-09-04: cha-1 содержал old_text вложенной c2-idp-readyz-1; порядок cha-1→idp сработал, обратный сломал бы вторую правку. Правило: при ≥2 APPROVE-правках в одну область C2 строить граф вложенности old_text.
---
type: pitfall
key: am-local-config-not-in-tmp
insight: Конфиги long-lived процессов на Mac-девбоксе НЕ держать в /tmp — macOS чистит /tmp между ребутами и живой бинарь остаётся без конфига (бэк :8082, 08.09). Канон: /Users/CraSS/am-backend-local/am-local.yaml; секреты env — /tmp/backend-demo.env, команда подъёма в landscape-файле ~/.amctl.
confidence: 10
source: observed
files: ["PM/initiatives/monitoring-1c/history/HANDOFF-tj-traces.md"]
ts: 2026-09-08
scope: project
status: superseded
superseded_by: project-am-backend-local-config
---
HANDOFF-tj-traces 08.09: команда подъёма бэка из хэндофа падала «open /tmp/am-local.yaml: no such file»; живая копия нашлась в ~/am-backend-local. Стенде-чек-лист: CH docker start, бэк с конфигом из ~/am-backend-local.

---
type: pitfall
key: jira-bulk-async-server-side-completes-after-mcp-abort
status: superseded
insight: MCP-клиент может убить bulk-вызов по idle-timeout (1800s), но Jira Server продолжает выполнять операцию у себя и доводит её до конца — не дублировать bulk, а поллить прогресс прямым PAT-readback.
confidence: 9
source: observed
files: ["~/.claude/skills/vid-rabot/SKILL.md"]
См. также: [[jira-mcp-broad-text-jql-oversize]], [[jira-mcp-401-substring-issuekey]], [[jira-search-truncates-at-maxresults]]
ts: 2026-09-08
scope: harness
---
vid-rabot прогон, bulk_update_issues 265 ключей (MON спринт 3641): MCP-клиент убил bulk-вызов после 1800s idle-timeout («sent no response or progress»), но 265 updates доехали за ~45 мин (темп 2→7/мин, ускоряется). Симптом-проверка: прямой readback через PAT (`key in (...) AND "Вид работ" is EMPTY`) показывает прогресс; перезапускать bulk НЕ нужно — поллить каждые 5-7 мин, пока счётчик пустых не дойдёт до 0. Параллельные мелкие bulk-группы (2-33 ключа) в это же время тоже висят >120s в фоне — MCP-сервер насыщен одним длинным bulk'ом; одиночный update_issue проходит мгновенно. Правило: большие bulk-записи (>50 ключей) = запуск в фон и полл прямым PAT-подключением; записи — только через MCP, read-only прямые вызовы в ходе прогона — норм.

Superseded 2026-11-24 (prune): факт впитан в skills/vid-rabot/SKILL.md — bulk 50+/1800s, Jira доводит сама
---
type: pitfall
key: yt-vtt-to-srt-before-clean
insight: srt-clean.py парсит только SRT с запятыми в мс; YouTube VTT от yt-dlp (точки в мс) надо сначала конвертировать `ffmpeg -i x.vtt x.srt`, иначе скрипт молча вернёт 0 символов.
См. также: [[srt-clean-fails-on-sequential-subs]]
confidence: 9
source: observed
files: [~/.claude/skills/video-knowledge-extraction/scripts/srt-clean.py]
ts: 2026-11-24
scope: skill:video-knowledge-extraction
---
Хвост про regex-бэктрекинг влит в [[srt-anchor-timestamps]] (prune 2026-11-24).
---
type: pitfall
key: mon-sprint-vs-fixversion
insight: В MON активный спринт (=имени релиза, напр. «1.7.0») шире fixVersion: 122 открытых задачи спринта 3641 не имели fixVersion — релизный хвост считать только JQL по fixVersion, иначе скоуп раздувается втрое
confidence: 9
source: observed
files: []
ts: 2026-09-10
scope: project
status: superseded
superseded_by: project-am-release-jira-filters
---
Ревизия v.1.7.0 (10-09): fixVersion-срез 21 открытая, спринт-срез 143. Дополнительно: эпики с «(релиз 1.7.0)» в названии могут не состоять в fixVersion (MON-4663/4664) — заголовок не источник скоупа.

---
type: pitfall
key: playwright-mcp-profile-lock
insight: «Browser is already in use» в Playwright MCP = зависший chrome прошлой сессии держит профиль — все browser_* вызовы падают сразу; лечится убийством главного PID процесса с user-data-dir профиля
confidence: 9
source: observed
files: []
ts: 2026-09-15
scope: harness
---
Лечится за один шаг: `pgrep -f "user-data-dir=/Users/CraSS/Library/Caches/ms-playwright-mcp/<профиль>"` → `kill <главный PID>` (процесс с `Google Chrome.app/Contents/MacOS/Google Chrome` в команде, не Helper) → подождать 2–3 с → navigate снова работает. Проверять `pgrep | wc -l` = 0 перед повтором.

---
type: pitfall
key: confluence-update-content-placeholder
См. также: [[confluence-content-file-sandbox]]
insight: mcp confluence_update_page публикует ЛЮБОЙ переданный content немедленно — accidental placeholder уходит на живую страницу; для больших тел использовать content_file, но путь обязан быть внутри workspace (path traversal guard режет /tmp)
confidence: 10
source: observed
files: []
ts: 2026-09-16
scope: harness
---
am-update 2026-09-16: в content утекла строка-заглушка → Confluence v15 опубликован мусором; лечится немедленным повторным update с реальным телом (v16) + верификацией get_page. content_file принимает только пути внутри cwd сессии — сначала скопировать файл из /tmp в workspace.

---
type: pitfall
key: speech-to-text-doc-summary-vs-transcript
insight: Файлы speech_to_text*.doc и презентационные .doc из Downloads — это HTML под маской .doc; конверт может оказаться кратким AI-саммари встречи (Заголовок/ОПИСАНИЕ/ДАЛЬНЕЙШИЕ ШАГИ/Концепции-SWOT), а не полным транскриптом — проверять объём конвертата (self-summary ~5–7 КБ vs транскрипт ~100+ КБ) и просить у пользователя полный speech_to_text файл
confidence: 9
source: observed
files: []
ts: 2026-09-17
scope: harness
См. также: [[asr-transcript-literal-grep-fails]], [[asr-mangles-org-product-names]]
---
textutil -convert txt работает; признак саммари: структура «Заголовок: НАИМЕНОВАНИЕ… Содержимое: <таймкоды-оглавление> Концепции: SWOT».

---
type: pitfall
key: jql-worklogdate-date-only
insight: worklogDate в JQL MON не принимает время — только YYYY-MM-DD; ISO-время из vid-rabot last-run.txt обрезать до даты
confidence: 9
source: observed
files: []
ts: 2026-09-21
scope: harness
---
Jira Server MON отклоняет `worklogDate >= "2026-09-08 15:50"` (400 «Date value is invalid»; валидные форматы YYYY/MM/DD, YYYY-MM-DD, периоды вроде -5d). Для vid-rabot в режиме since-last: ISO-время из last-run.txt обрезать до даты (прогон 2026-09-21 потерял вызов на этой ошибке до первого результата). Перепокрытие (работлоги с 00:00 дня прошлого прогона) безвредно — фильтр `"Вид работ" is EMPTY` отсекает уже размеченное.
---
type: pitfall
key: jira-search-truncates-at-maxresults
insight: search_issues молча режет issues до max_results — при total>limit агрегаты и списки врут; сверять .total с .issues|length
confidence: 9
source: observed
См. также: [[jira-mcp-broad-text-jql-oversize]], [[jira-mcp-401-substring-issuekey]], [[jira-bulk-async-server-side-completes-after-mcp-abort]]
files: []
ts: 2026-09-21
scope: harness
---
mcp__jira__search_issues при total > max_results сохраняет в файл только первую страницу (224 total → 200 issues, isLast:false), без предупреждения в тексте результата. Прогон am-release-notes v.1.7.0 (2026-09-21): скилл-рецепт с max_results=200 потерял 24 задачи — поймано по расхождению `.total` vs `jq '.issues|length'`. Потерянные задачи = дыры в dev-файле релиз-нотсов; coverage-проверка ловит их не всегда — expected-набор может быть собран из той же обрезанной выдачи (оба неполны, проверка зелёная при дыре). Лечение: после выдачи всегда `jq '{total, have: (.issues|length), isLast}' $F`; если have < total — дотягивать страницами start_at, слить `jq -s '{total: .[0].total, issues: (.[0].issues + .[1].issues)}'`.

См. также: [[project-ai-sre-stand-token-cadence]]
---
type: pitfall
key: am-dev-jwt-24h-and-split-dns
insight: Токены am-dev живут 24ч и протухают молча (amctl отдаёт 403/401); split-DNS VPN может давать трафик без системного DNS — браузер спасает DoH
confidence: 9
source: observed
files: ["~/.amctl-dev-live.yaml"]
ts: 2026-09-25
scope: project
status: superseded
superseded_by: project-ai-sre-stand-token-cadence
---
JWT am-dev живёт ~24 часа (exp = iat + 86400). Протухание молчаливое: amctl отдаёт 403/401, сервисы-обёртки (полигон ai-agent) — «инструмент не работает», стек прототипа остаётся без рук. Свежий токен — в `~/.amctl-dev-live.yaml` (обновляется перелогином владельца); конфиг полигона на ВМ — `astra@10.205.142.219:/home/astra/.amctl.yaml` (ro-mount, заменять файл на хосте, контейнер перезапускать не надо). Дата-чек: `python3 -c` base64-decode payload.

Split-DNS VPN: туннель поднят (ВМ по IP отвечает), но системный DNS macOS не получает записи `*.dev.astra-monitoring.astralinux.ru` — curl/amctl/vite-прокси падают NXDOMAIN, а браузер владельца работает (браузерный DoH). Диагностика: `host <имя>` против `curl http://<ВМ-IP>:порт/health`; если ВМ жива, а имя нет — просить IP или перезапуск туннеля, не гадать про «сеть мертва».

См. также: [[subagent-cjk-glyph-leak]]
---
type: pitfall
key: subagent-briefs-require-russian-explicitly
insight: Брифы саб-агентов на GLM обязаны содержать явное требование «работай только по-русски» — без него агент скатывается на китайский в рассуждениях и правках
confidence: 9
source: observed
files: []
ts: 2026-09-25
scope: harness
---
Наблюдение 25.09 (верификатор демо-сцен AI-SRE). В каждый бриф — строка «работай и пиши ТОЛЬКО на русском, без китайских иероглифов», плюс при приёмке — проверка внесённых правок на иероглифы (grep по файлу правок, CJK-диапазоны U+3400–U+9FFF; глифы протекают и в русский текст — [[subagent-cjk-glyph-leak]]). Дополнение из memory (workflow-args, 27.07): после генерации md/text — обязательный CJK-скан `grep -P '[\x{3400}-\x{9fff}\x{f900}-\x{faff}]'` с целевыми заменами; артефакты вероятны в любой длинной генерации на GLM (роутер → z.ai).
---
type: pitfall
key: sandbox-tcc-documents-ephemeral
insight: Bash-песочница может внезапно потерять TCC-доступ к ~/Documents (EPERM на ls/Read) — перепроверить stat'ом и перезапустить вызов с dangerouslyDisableSandbox
confidence: 9
source: observed
files: []
ts: 2026-09-25
scope: harness
---
В одной сессии Bash-вызовы свободно читали ~/Documents/..., затем новые вызовы стали получать `Operation not permitted` на ls/open (и Read tool EPERM) — macOS TCC-гейт для sandboxed-процессов; файл при этом нормальный (`stat` показывает обычные права). Песочница Bash-инструмента изолируется, а TCC-разрешение на Documents у неё своего нет — ранее выданный доступ не гарантирован для последующих вызовов. При неожиданном `Operation not permitted` на файлы проекта — сначала `stat` (отличить sandbox от реальных прав), затем перезапустить тот же вызов с `dangerouslyDisableSandbox: true` (легитимно для файлов проекта). Пользователю о сбое доступа сказать прямо — он может поднять разрешение.

---
type: pitfall
key: facts-scanner-make-slash-targets
insight: collect-repo-facts.sh не видит Make-цели со слэшем (regexp без /) — «отсутствие цели» в facts-отчёте неподтверждено, сверять с Makefile репо
confidence: 9
source: observed
files: [Astra/meta/scripts/collect-repo-facts.sh]
ts: 2026-10-01
scope: project
status: superseded
superseded_by: ref-collect-repo-facts-quirks
---
am-update 2026-10-01: сканер не показал `swagger/doc` в agent (цель существует, Makefile:129) и feeder; профиль agent чуть не починили «по фактам». Вторая ловушка того же запуска: счёт top-level каталогов go-lib — аудит дал 34, двойной пересчёт 35 (8 удалённых подкаталогов под ОДНИМ top-level). Счётчики пересчитывать двумя способами перед правкой C2.

---
type: pitfall
key: searxng-russian-queries-degraded
insight: SearXNG-инстанс деградирует на русскоязычных запросах (google/yandex/ddg пусто, bing — мусор) — RU-ресёрч вести через WebSearch, RU-сайты читать web_url_read/curl с перекодировкой
confidence: 9
source: observed
files: []
ts: 2026-09-28
scope: harness
---
Подтверждено независимо 4 саб-агентами в одном прогоне (pain research мониторинга 1С, 2026-09-17) и B2B-ресёрчем ЦИФРА (2026-09-28): каждый ресёрчер терял 10–20 минут на диагностику «сломанного поиска». В брифах RU-ресёрч-агентов сразу указывать основной поиск = WebSearch, searxng — запасной для латиницы. Нюансы обхода: infostart.ru режет кириллицу из HTML при скачивании (анти-скрейп) — тексты брать через README-ссылки/конспекты; habr-комментарии — через kek API; mista.ru в cp1251 (curl + перекодировка). Для длинных нормативных запросов («класс защищённости К2 ЕМИАС приказ ФСТЭК 17») searxng дробит запрос → словарные статьи вместо регуляторики; прицельный WebFetch на канонические страницы (fstec.ru и профильные порталы) результативнее трёх пустых поисков. Русская B2B-выдача тоже слабо покрыта (запросы вида «ЦИФРА Диспетчер отзывы внедрение» → авторемонт/Steam); вендорские PDF (презентации ЦИФРА) лежат на intechnology.ru/files/, где все читалки (web_url_read/webReader) падают по SSL — качать голым curl, href искать grep'ом по HTML страницам вендора.


---
type: pitfall
key: asr-mangles-org-product-names
insight: ASR-транскрипты звонков (SRT) коверкают имена организаций, продуктов и должностей — не переносить их в артефакты, сверять с владельцем до записи
См. также: [[asr-transcript-literal-grep-fails]]
confidence: 8
source: observed
files: [PM/customers/ВСМПО-АВИСМА/pain-report-2026-10-15.md]
ts: 2026-10-15
status: superseded
superseded_by: asr-transcript-literal-grep-fails
scope: harness
---
Примеры с одного файла: «клинический директор» ← «клиентский», «Sub-Danter под 1С» ← нераспознанный продукт, «решение инфробейс»/«стрем-мониторинг» — не восстановлены. Название клиента при этом отсутствовало в транскрипте вовсе. Порядок: до записи заголовка/папки артефакта спросить владельца (AskUserQuestion) — имя и манглы он называет сразу; в артефакте манглы фиксировать как «X [искажение распознавания]», не как факт. Спикеров без имён различать по перекрёстным упоминаниям в репликах (кто кого назвал), не по порядку.

---
type: pitfall
key: chunk-slicing-drops-keys
insight: при ручной нарезке длинного списка ключей на чанки для субагентов один ключ выпадает — нарезать программно и сверять объединение через comm до диспэтча
confidence: 8
source: observed
files: []
ts: 2026-10-16
scope: harness
---
vid-rabot 2026-10-16: 99 ключей Jira разрезал вручную на 4 чанка «на глаз» — выронил MON-5526 (сосед 5525/5560); субагенты честно отработали свои 98, расхождение нашлось только сверкой (коммутатор чанков 98 vs total 99 → comm -23 по спискам). Правило: ключи из jq писать в файл, чанки резать awk/sed, перед диспэтчем `comm` объединения с исходником; после сбора результатов — обратная comm-сверка. Пропущенный ключ доводится одним solo-вызовом, без перезапуска чанка.

---
type: pitfall
key: release-notes-file-naming
insight: am-release-notes — релиз живёт папкой release-notes/<версия>/{dev,changelog,marketing}.md (имена без версии и без даты); SKILL.md обновлён 2026-10-22, при расхождении — следуй последней папке релиза
confidence: 9
source: observed
files: [analytics-hub/internal_docs/docs/release-notes/]
ts: 2026-10-22
scope: harness
---
SKILL.md am-release-notes требует `YYYY-MM-DD-*`, README папки — `vX.Y.Z-release-notes.md`, фактика папки — `1.7.0-release-notes-dev.md` / `1.7.0-changelog.md` / `1.7.0-release-notes-marketing.md` (три файла, префикс = версия без «v»). Название по версии устойчивее к переносу даты релиза. Перед следующей генерацией: ls -t папки решает.

---
type: pitfall
key: draft-release-notes-future-release
insight: релиз-ноуты будущего (невыпущенного) релиза — драфт по MUST-скоупу допустим, но честно: статусы тикетов не Done, плашка «ЧЕРНОВИК», Testing/Known Issues — заглушки до полного прогона по fixVersion
confidence: 8
source: observed
files: [analytics-hub/internal_docs/docs/release-notes/1.8.0/dev.md]
ts: 2026-10-22
scope: product
---
Кейс v.1.8.0 (план 03.11.2026): юзер попросил драфт по MUST-скоупу (интеграции + RBAC по данным). Паттерн: в dev-файле ключи не-Done тикетов включаются как плановый скоуп, в шапке — статусная оговорка и ссылка на живую релизную страницу Confluence; номера тикетов НЕ упоминать вне буллетов, иначе key-coverage check (exact-once) ложно краснеет. Коммит только после апрува владельца.
---
type: pitfall
key: complaint-vs-requirement-ticket-reading
insight: Фразы «может только X» / «Y недоступны» в жалобных тикетах заказчика — это констатация текущего как проблемы, не требование ограничить; прежде чем резать скоуп, определи прочтение у владельца явно.
confidence: 8
source: observed
files: []
ts: 2026-11-03
scope: harness
---
Кейс KIM-538: «Администратор может исправить только ИНН… ОКПО/КПП/р/сч недоступны» — сначала прочитали как требование отобрать у админа поля (полгода лишней работы по ограничению), по факту это была жалоба «недостаёт поверхностей» + часть объяснялась карточкой физлица, где КПП/ОГРН/ОКПО не существуют по замыслу. Маркер: в тикете рядом есть явное «должно быть доступно только для…» — жалоба-абзац зеркалит его структуру. Сверяй оба прочтения с кодом до скоупа: код часто снимает одну из версий сразу.
---
type: pitfall
key: mon-jira-done-filter-and-transition-dates
insight: в Jira MON statusCategory=Done врёт (возвращает подмножество), resolutiondate пуст у «To Release»/«Finished», а updated переклеивается массово при спринт-мерже — границы релизов резать по status = <числовой ID> + status CHANGED TO <ID> AFTER/BEFORE <дата тега>.
confidence: 9
source: observed
files: []
ts: 2026-11-23
scope: harness
---
Кейс 1.7.2: statusCategory=Done дал 200 тикетов вместо 505 реальных «To Release»; по именам статусов («To Release») JQL отклоняется — только числовые ID (список через list_statuses). updated 173 тикетов был одинаковым днём (11-13, спринт-мерж). Рабочий паттерн: fixVersion = "v.X" AND status = 11402 AND status CHANGED TO 11402 AFTER "<дата тега предыдущего релиза>" → чистый когорт релиза (389 до / 116 после, пересечений ноль). Cross-references в summaries чужих тикетов («Настройки таблиц (MON-5684): …») дают ложные дубли в key-coverage — чекать только буллет-строки `- [MON-X](https://...)`.
---
type: pitfall
key: amctl-login-fresh-config-needs-insecure
insight: amctl login в новый конфиг на am-dev падает «сервер не доступен … x509: certificate is not trusted» — в конфиге заранее должно быть insecure: true, как в рабочих конфигах
confidence: 9
source: observed
files: ["~/.amctl-dev-live.yaml"]
ts: 2026-11-23
scope: project
---
Кейс 23.11 (восстановление контекста AI-SRE): `amctl login --login … --server … -c /tmp/new.yaml` без `insecure: true` в файле даёт ERR «сервер не доступен», хотя стенд жив; файл после этого не создаётся, и следующий `amctl … -c` паникует в MustLoad. Рабочий порядок: создать конфиг с `insecure: true` и заготовкой сервера (права 600), затем login; токен читать из конфига в переменную, не печатая; временный конфиг удалить. В --help у login есть ещё флаг --insecure — этот путь не проверялся.
---
type: pitfall
key: stale-clones-grep-origin-dev
insight: grep по рабочему дереву клонов в метарепо молчит для свежесмерженного кода — локальный dev отстаёт от origin/dev; вывод «не реализовано» делать только после `git log --all -i --grep` и `git grep <шаблон> origin/dev`.
confidence: 9
source: observed
files: ["sync-repos.sh"]
ts: 2026-11-23
scope: harness
---
Кейс 23.11 (am-research по Apdex, MON-4950): в admin-backend, admin-console, db-migration-service, monitoring-astra-icl локальный dev стоял на 05.11, а ветка mon-4950 смержена в origin/dev 20.11 — grep по дереву дал 0 файлов при готовой реализации. Читать код без правки дерева: `git show origin/dev:<путь>`, `git diff <merge>^1 <merge> --stat`. Отставание лечится sync-repos.sh, но проверка по origin-ссылкам — постоянное правило.
---
type: pitfall
key: release-notes-scope-vs-merged-dev
insight: am-release-notes — отбор «fixVersion = vX AND statusCategory = Done» пропускает фичи, смерженные в dev после тега прошлого релиза, но без fixVersion или ещё не в Done; перед сдачей сверять скоуп с мержами в origin/dev
confidence: 9
source: observed
files: ["analytics-hub/internal_docs/docs/release-notes/"]
ts: 2026-11-23
scope: project
---
Кейс 23.11 (нотсы 1.7.2): Apdex по BTM (MON-4950) — один тикет на фичу, без fixVersion, «На тестировании», код в origin/dev четырёх репо 18–20.11; в нотсах фичи не было, заметил владелец. Тот же класс: MON-5720 (platformctl update), MON-5968 (AI-ассистент: Kubernetes), MON-5871 (ушёл в To Release уже после выгрузки), MON-5822. Тег релиза в monitoring-astra-icl стоит на main и НЕ является предком dev, поэтому `<тег>..origin/dev` выдаёт тысячи старых коммитов; рабочий фильтр — по дате тега: `git log origin/dev --first-parent --since=<дата тега> -i -E --grep='mon-[0-9]+'`, ключи сверить с dev.md, кандидатов проверить в Jira (statusCategory, fixVersion).
---
type: pitfall
key: check-learnings-before-no-docs-claim
insight: Перед утверждением «публичной документации вендора нет» — искать имя вендора в agent-knowledge/learnings и в meta/research-index.md: там может уже лежать способ чтения (docsify-сырой markdown, зеркала, обходы редиректов); найденное сразу класть в бриф веб-агенту.
confidence: 9
source: observed
files: ["PM/initiatives/sla-monitoring/deep-dive-q1-2027.md"]
ts: 2026-11-23
scope: harness
---
Кейс 23.11 (am-grill-feature по фичам Q1 2027): два веб-агента не нашли документацию GMONIT, в документ попало «публичной документации нет», хотя в patterns.md с утра лежал урок «Доки GMONIT = docsify, сырой md по прямому пути» (curl https://docs.gmonit.ru/<path>.md, оглавление _sidebar.md). Владелец спросил «как это реализовано в GMONIT» — модуль SLO нашёлся одним curl; ложное утверждение снято из документа, индекса и памяти.

---
type: pitfall
key: github-api-limit-shared-with-subagents
insight: An invalid `GITHUB_TOKEN` is exported from `~/.zshrc` (line 1) and overrides the valid `gh` keyring login (`crass987`), so plain `gh api` fails with 401 «Bad credentials» and everyone falls back to the unauthenticated limit (60 requests/h per IP, shared by the main session and all subagents); the token itself is fine — call GitHub as `env -u GITHUB_TOKEN -u GH_TOKEN gh api ...` (5000 requests/h) and put this exact line into the brief of every web-research subagent. Without it, agents read tagged sources via `raw.githubusercontent.com`, issue/PR state via GitHub HTML pages and Wayback — workable, but slower and no fresher than the page.
confidence: 9
source: observed
files: ["meta/research/vector-otlp-logs-pipeline.md"]
ts: 2026-11-23
scope: harness
status: superseded
superseded_by: ref-github-api-gh-token
---
Superseded 2026-11-24 (traverse): GitHub-часть канонизована в memory ref-github-api-gh-token; не-GitHub факты вынесены в webreader-github-pages-500-fallback.

Vector OTLP research run 23.11: the subagent reported «GitHub API исчерпал лимит (60/ч без токена, gh-токен невалиден)» mid-run and burned an hour on HTML scraping; the main session hit the same 401 and repeated the mistake. The owner corrected it («у нас есть токен на gh»); `gh auth status` showed both facts at once (GITHUB_TOKEN invalid + keyring login valid). The fix was already in memory ([[ref-knowledge-base]], line about `unset GITHUB_TOKEN`) but hidden under an unrelated index hook — not found because the brief for the agent was written without grepping memory for the tool name. `mcp__web_reader__webReader` intermittently returned 500 «Network error» on github.com pages — `curl` + a short `python3 -I` extraction worked; plain `grep -oE '.{0,160}(a|b).{0,200}'` over a 280 KB page fails in ugrep with «exceeds complexity limits».

---
type: pitfall
key: webreader-github-pages-500-fallback
insight: mcp web_reader на страницах github.com периодически отдаёт 500 «Network error» — сырой контент вытягивать curl'ом + коротким python3 -I, по репозиториям — zread; обычный grep по HTML тоже работает
confidence: 8
source: observed
files: []
ts: 2026-11-24
scope: harness
---
Vector OTLP research run 23.11: the subagent reported «GitHub API исчерпал лимит (60/ч без токена, gh-токен невалиден)» mid-run and burned an hour on HTML scraping; the main session hit the same 401 and repeated the mistake. The owner corrected it («у нас есть токен на gh»); `gh auth status` showed both facts at once (GITHUB_TOKEN invalid + keyring login valid). The fix was already in memory ([[ref-knowledge-base]], line about `unset GITHUB_TOKEN`) but hidden under an unrelated index hook — not found because the brief for the agent was written without grepping memory for the tool name. `mcp__web_reader__webReader` intermittently returned 500 «Network error» on github.com pages — `curl` + a short `python3 -I` extraction worked; plain `grep -oE '.{0,160}(a|b).{0,200}'` over a 280 KB page fails in ugrep with «exceeds complexity limits».
