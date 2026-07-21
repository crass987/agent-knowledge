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
