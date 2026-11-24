# Patterns

Repeatable ways that work.

<!--
Example entry (copy, fill, uncomment):
---
type: pattern
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
type: pattern
key: screencast-audio-only-fetch-tool-repo
insight: For an audio-only extraction of a screencast Tutorial/Demo, the precise commands/UI/file-structure live only in the visual channel — fetch the covered tool's canonical repo/README to recover them, and mark every fact by source (🗣 video vs 📄 repo) so the reader knows provenance.
confidence: 9
source: observed
files: []
ts: 2026-08-09
scope: harness
---
Chase AI «Graphify+Obsidian+Claude Code»: video covered only the `--obsidian` flag; the README yielded the always-on PreToolUse hook, `--strict`, global/merge-graphs, `reflect`→LESSONS.md — none in the video.

---
type: pattern
key: pain-mining-post-sale
insight: am-pain-mining работает и на пост-продажной разборке: §12 читается как удержание (готовность продукта честно 1/3), Aha-секция почти пуста — её место занимает «что продаёт: конкретика с датами»
confidence: 7
source: observed
files: ["PM/customers/СОГАЗ/pain-report-2026-09-18-post-sale.md"]
ts: 2026-09-18
scope: harness
---
COГАЗ 18.09: встреча-разборка недоработок против ТЗ вместо демо. Jobs от уже заплатившего заказчика весят больше пресейл-гипотез — в сверку с ресёрчем добавлять столбец «что меняем».
---
type: pattern
key: am-dex-token-ttl
insight: access-токен Dex выпускается тем же кодом, что id-токен (newAccessToken→newIDToken) — TTL управляется dex.expiry.id_tokens в конфиге identity-provider; в поставке секция не задана = 24h + бессрочный refresh. admin-backend JWT не валидирует вовсе (go-lib amecho ParseUnverified, RBAC по claims) — серверно отозвать токен нельзя, работает только browser-side silent renew
confidence: 9
source: observed
files: ["identity-provider/dex/server/oauth2.go", "identity-provider/internal/config/entity.go", "go-lib/amecho/utils.go", "PM/sessions/dex-token-slo/token-lifetime-research.md"]
ts: 2026-09-22
scope: project
status: superseded
superseded_by: project-dex-token-slo-acp
---
Любой вопрос про SSO/SLO/жизнь сессии в АМ начинать с этой цепочки: браузер (oidc-react silent renew) → identity-provider (Dex 2.38, upstream refresh к IAM) → admin-backend (claims без проверки). Pull-сценарий заказчика работает без доработок, задержка = expiry.id_tokens.

---
type: pattern
key: srt-timestamps-before-clean
insight: Таймкоды для меток доставай из SRT до/вместо очистки — в очищенном transcript.txt координат нет.
confidence: 7
source: observed
ts: 2026-11-01
scope: harness
tags: [video-knowledge-extraction, transcript, srt]
См. также: [[srt-anchor-timestamps]]
status: superseded
superseded_by: srt-anchor-timestamps
---

srt-clean.py выбрасывает таймкоды вместе с rolling-шумом. Если документу знаний нужны временные метки идей, вытаскивай их grep'ом/скриптом по subs.ru.srt до очистки (или параллельно): искать фразу в очищенном transcript.txt бесполезно — координат там нет. Мини-скрипт: парс SRT → (start_sec, text) → find(phrase) по ключевым фразам списка.

**Why:** на извлечении таймкодов по уже очищенному файлу теряется шаг — приходится парсить SRT заново.
**How to apply:** в video-knowledge-extraction после скачивания subs.ru.srt сразу снимать метки ключевых фраз, потом чистить.

---
type: pattern
key: srt-anchor-timestamps
insight: Таймкоды для очищенного транскрипта вынимаются из SRT обратным проходом по якорным фразам — 30-40 якорей дают точную сетку меток за один прогон.
confidence: 7
source: observed
ts: 2026-11-24
scope: harness
См. также: [[srt-timestamps-before-clean]]
skill: video-knowledge-extraction
---

**Таймкоды для очищенного транскрипта из SRT.** srt-clean.py убирает таймкоды; для документа знаний нужны метки. Работает обратный проход: python-скрипт разбивает SRT на блоки, ищет якорные фразы из транскрипта (lowercase-сравнение, `' '.join(parts[2:])`) и печатает `fmt(начало блока)  фраза`. 30-40 якорей дают точную сетку меток за один прогон вместо пересчёта на глаз по пропорции текста. Экономит ~10 минут на видео. Исходный SRT сохраняйте в source/ до очистки (якоря восстанавливаются по нему). Regex-поиск таймкодов — только линейный по блокам (split по пустым строкам): finditer с вложенными квантификаторами по 100k+ файлу уходит в катастрофический бэктрекинг. Влито из srt-clean-strips-timestamps, srt-timestamps-before-clean, srt-clean-fails-on-sequential-subs (prune 2026-11-24).

---
type: pattern
key: gmonit-docs-docsify-raw-md
insight: Доки GMONIT (docs.gmonit.ru) — docsify; сырой markdown берётся curl'ом по пути без /#/ (например /modules/mcp.md), SPA-рендер не нужен.
confidence: 8
source: observed
ts: 2026-11-06
scope: project
skill: am-research
---

**Доки GMONIT = docsify, сырой md по прямому пути.** URL вида docs.gmonit.ru/#/modules/mcp — SPA-роутинг. curl https://docs.gmonit.ru/modules/mcp.md отдаёт исходный markdown (то же для setup.md/guide.md внутри модуля); доки открыты без авторизации. GMONIT — конкурент №1 русской линзы; их агентный ход (MCP-сервер коллектора) разобран в PM/competitive/gmonit-mcp-vs-amctl-ai-agent.md. При следующем заходе на GMONIT — сразу прямые .md-пути (предыдущий ресёрч конкурентов их пропустил, вероятно, из-за SPA).

---
type: pattern
key: cold-subagent-spec-grill
insight: Независимое ревью спеки, которую писал сам — только через холодного сабагента с самодостаточным брифом и без своих оценок в брифе.
confidence: 8
source: observed
files: []
ts: 2026-11-24
scope: harness
---
Кейс 14.11: гриль спеки MON-5919 холодным general-purpose сабагентом нашёл 5 MAJOR в тексте, который автор дважды прогонял сам (маршрут пуша, таймаут-миссматч, ложная атрибуция тикета). Бриф без оценок автора обязателен — иначе якорение; код-проверку претензий сабагент делает сам (пути, Jira-ключи в бриф).

См. также: [[subagent-briefs-require-russian-explicitly]], [[feedback-worker-brief-teamlead-address]].

---
type: pattern
key: cat-assembly-blank-line-normalize
insight: При сборке большого документа из частей командой cat после Write на стыках не оказывается пустой строки — заголовок следующей части приклеивается к последней строке предыдущей; после сборки прогонять нормализацию: пустая строка перед каждой строкой, начинающейся с «## ».
confidence: 9
source: observed
files: ["PM/initiatives/sla-monitoring/deep-dive-q1-2027.md"]
ts: 2026-11-24
scope: harness
---
Кейс 23.11: 5 частей → 4 стыка, на одном «## 9» слился с абзацем и пропал из оглавления. Проверка: `grep -n '^## '` и сверка с ожидаемым списком разделов. Время агентов для планирования: Explore по коду — 22–65 мин и 180–216k токенов каждый; веб-разведка general-purpose — 72–86 мин и ~190–210k токенов; запускать их первыми и читать канон и PM-документы параллельно.

См. также: [[project-service-object-q1-deep-dive]].


---
id: tz-answers-check-registry
date: 2026-11-24
context: Пресейл-ответы на пункты ТЗ заказчика (прошу уточнить…)
pattern: Прежде чем давать ответ на пункт ТЗ, сверить его с строками PM/strategy/functional-registry.md (fn-os-exotic, fn-device-presets-10k и т.п.) — там уже вердикты 🟢/🟡/🔴 с evidence из репо. Черновики от продаж могут противоречить реестру (случай 2026-11-24: «Аврора/Стрелец подтверждаем» vs 🔴 не подтверждено).
