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
ts: 2026-11-04
scope: harness
См. также: [[srt-timestamps-before-clean]]
skill: video-knowledge-extraction
---

**Таймкоды для очищенного транскрипта из SRT.** srt-clean.py убирает таймкоды; для документа знаний нужны метки. Работает обратный проход: python-скрипт разбивает SRT на блоки, ищет якорные фразы из транскрипта (lowercase-сравнение, `' '.join(parts[2:])`) и печатает `fmt(начало блока)  фраза`. 30-40 якорей дают точную сетку меток за один прогон вместо пересчёта на глаз по пропорции текста. Экономит ~10 минут на видео.
