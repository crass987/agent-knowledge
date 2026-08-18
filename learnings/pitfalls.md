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
