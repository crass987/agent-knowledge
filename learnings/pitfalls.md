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
---
A zero-result narrow search (e.g. `issuetype=Bug AND summary~"документац"`) is itself signal — it means there is no feedback channel for that defect class, not that the area is clean.

---
type: pitfall
key: asr-transcript-literal-grep-fails
insight: On ASR-mangled transcripts, literal grep for product/competitor names fails (Zabbix→«запикса»/«забикс», Grafana→«графиня», Пульт missed by a pattern) — read in context to QC a subagent's transcript-based output; do not grep-literal. Applies to QC of subagent drafts, not just prose.
confidence: 9
source: observed
files: []
ts: 2026-07-21
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
ts: 2026-07-21
scope: harness
---
Гринатом draft had 3 CJK glitches in the report's own voice (not in verbatim quotes) + 1 fabricated vendor name absent from source — subagent drafts need a fabrication/glyph QC pass, not just a style pass.

---
type: pitfall
key: zsh-glob-unquoted-url
insight: In zsh, an unquoted URL containing `?` and `=` (YouTube `?v=ID`, any query string) is parsed as a filename glob → `(eval):1: no matches found` and yt-dlp/curl exits with no output; single-quote the URL (`URL='https://...'`) before passing it to any command. The video-knowledge-extraction skill's transcript-acquisition.md shows unquoted `URL` placeholders — always quote on substitution.
confidence: 9
source: observed
files: [~/.claude/skills/video-knowledge-extraction/references/transcript-acquisition.md]
ts: 2026-07-23
scope: harness
---
Matt Pocock video run: `yt-dlp --list-subs https://www.youtube.com/watch?v=n0VhIVtviC0` → `(eval):1: no matches found: https://...`; assigning to `URL='...'` fixed it instantly.

---
type: pitfall
key: srt-clean-fails-on-sequential-subs
insight: The skill's `srt-clean.py` assumes classic YouTube progressive-reveal auto-subs (each block = cumulative text, only last line is new). Some auto-caption tracks (observed: `ru-ru` on J6QqWkLFV-4) are clean, sequential, NON-overlapping blocks whose only artifact is `\h` word-join markers — running srt-clean.py there keeps only sentence-tails and fragments the transcript. Fix: inspect raw SRT structure first; if blocks are already sequential, skip the script and just strip `\h` + index/timestamp lines (5-line python). Always sanity-check the FIRST phrase of cleaned output.
confidence: 9
source: observed
files: [~/.claude/skills/video-knowledge-extraction/scripts/srt-clean.py]
ts: 2026-08-06
scope: harness
---
Also: YouTube can misdetect the base caption language (reported `en-en` "English from English" for a Russian-speech video; the `en-en` track was a silent auto-TRANSLATION, true original was `ru-ru`). Always cross-check the detected base language against channel/title language and prefer `<lang>-<lang>` original over `-en` translation for faithful quotes.

---
type: pitfall
key: jira-mcp-401-substring-issuekey
insight: jira-mcp's format_error_message matches HTTP statuses by substring, so any issue key containing "401"/"403"/"404" (e.g. MON-4013) masks the real response — a 400 Bad Request on such keys is reported as «Ошибка аутентификации: проверьте JIRA_EMAIL/JIRA_API_TOKEN», sending you chasing creds that are fine.
confidence: 10
source: observed
files: [/Users/CraSS/Documents/Code_projects/jira-mcp/mcp_server.py]
ts: 2026-08-13
scope: harness
---
Real status/message lives in ~/.cache/jira-mcp/logs/mcp-<date>.jsonl (per-call "error" entries) or in the Jira response body via a direct probe; the server itself discards e.response.text. Fix candidate: match "401 Client Error"/"Unauthorized for url" instead of bare "401" in mcp_server.py format_error_message (~line 328, also the resource-read mapper ~line 902).

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

---
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
key: srt-clean-drops-timestamps
insight: scripts/srt-clean.py (video-knowledge-extraction) выкидывает тайминги при очистке rolling captions, а шаблон knowledge-дока требует временные метки MM:SS на каждой единице.
confidence: 9
source: observed
files: [~/.claude/skills/video-knowledge-extraction/scripts/srt-clean.py]
ts: 2026-08-21
scope: harness
---
После очистки метки приходится считать пропорционально позиции в тексте и честно помечать их «оценочными» в метаданных документа; если метки важны точнее — чистить vtt/srt с сохранением маркеров времени вместо srt-clean.py.
---
type: pitfall
key: workflow-overlapping-edits-apply-order
insight: Пакетное применение одобренных workflow-правок падает, если old_text'ы перекрываются — перед replace задать явный порядок (большая правка первой) и проверять count==1 на каждую.
confidence: 9
source: observed
files: ["meta/prompts/c2-fix.md"]
ts: 2026-09-04
scope: harness
---
am-update 2026-09-04: cha-1 содержал old_text вложенной c2-idp-readyz-1; порядок cha-1→idp сработал, обратный сломал бы вторую правку. Правило: при ≥2 APPROVE-правках в одну область C2 строить граф вложенности old_text.
---
type: pitfall
key: confluence-publish-placeholder-risk
insight: Большие md в Confluence публиковать одним вызовом с полным телом и сразу верифицировать результат (версия+кусок тела) — частичная публикация с placeholder уходит на сервер как новая версия.
confidence: 10
source: observed
files: []
ts: 2026-09-04
scope: harness
---
am-update 2026-09-04: страница 677878056 на ~2 минуты получила v8 с PLACEHOLDER вместо тела реестра; поймано сразу, v9 с полным телом перезаписала. Файл-посредник (/tmp/…md) → Read → полный content в один update_page.

---
type: pitfall
key: am-local-config-not-in-tmp
insight: Конфиги long-lived процессов на Mac-девбоксе НЕ держать в /tmp — macOS чистит /tmp между ребутами и живой бинарь остаётся без конфига (бэк :8082, 08.09). Канон: /Users/CraSS/am-backend-local/am-local.yaml; секреты env — /tmp/backend-demo.env, команда подъёма в landscape-файле ~/.amctl.
confidence: 10
source: observed
files: ["PM/initiatives/monitoring-1c/HANDOFF-tj-traces.md"]
ts: 2026-09-08
scope: project
---
HANDOFF-tj-traces 08.09: команда подъёма бэка из хэндофа падала «open /tmp/am-local.yaml: no such file»; живая копия нашлась в ~/am-backend-local. Стенде-чек-лист: CH docker start, бэк с конфигом из ~/am-backend-local.

---
type: pitfall
key: jira-bulk-async-server-side-completes-after-mcp-abort
insight: MCP-клиент может убить bulk-вызов по idle-timeout (1800s), но Jira Server продолжает выполнять операцию у себя и доводит её до конца — не дублировать bulk, а поллить прогресс прямым PAT-readback.
confidence: 9
source: observed
files: ["~/.claude/skills/vid-rabot/SKILL.md"]
ts: 2026-09-08
scope: harness
---
vid-rabot прогон, bulk_update_issues 265 ключей (MON спринт 3641): MCP-клиент убил bulk-вызов после 1800s idle-timeout («sent no response or progress»), но 265 updates доехали за ~45 мин (темп 2→7/мин, ускоряется). Симптом-проверка: прямой readback через PAT (`key in (...) AND "Вид работ" is EMPTY`) показывает прогресс; перезапускать bulk НЕ нужно — поллить каждые 5-7 мин, пока счётчик пустых не дойдёт до 0. Параллельные мелкие bulk-группы (2-33 ключа) в это же время тоже висят >120s в фоне — MCP-сервер насыщен одним длинным bulk'ом; одиночный update_issue проходит мгновенно. Правило: большие bulk-записи (>50 ключей) = запуск в фон и полл прямым PAT-подключением; записи — только через MCP, read-only прямые вызовы в ходе прогона — норм.

---
type: pitfall
key: yt-vtt-to-srt-before-clean
insight: srt-clean.py парсит только SRT с запятыми в мс; YouTube VTT от yt-dlp (точки в мс) надо сначала конвертировать `ffmpeg -i x.vtt x.srt`, иначе скрипт молча вернёт 0 символов.
confidence: 9
source: observed
files: [~/.claude/skills/video-knowledge-extraction/scripts/srt-clean.py]
ts: 2026-09-08
scope: skill:video-knowledge-extraction
---
Также regex-поиск таймкодов по большому SRT — только линейным поиском по блокам (split по пустым строкам); finditer с вложенными квантификаторами по 100k+ файлу уходит в катастрофический бэктрекинг.
