# Grill: am-wiki (LLM Wiki как слой харнесса)

| | |
|---|---|
| Дата | 2026-06-19 |
| Verdict | **DO (trial-scoped)** |
| Target | Личный харнесс (не продукт Astra) |

## Что прожариваем

**am-wiki** — навык харнесса: агент инкрементально строит и поддерживает связанный markdown-wiki из источников (`add` / `gather` / `query` / `lint`). Не продукт Astra — слой личного knowledge-base поверх существующих навыков. Паттерн — [LLM Wiki Карпати](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Product Assessment (под пользователя)

| Критерий | Оценка | Заметки |
|---|---|---|
| Польза | High | Закрывает «налог вспомнить-перечитать»; соединяет 5+ разрозненных механизмов знаний |
| Срочность | Medium | Боль реальна, но не блокирует — можно жить и так |
| Риск | Medium | Главный — стать «ещё одним силосом» без дисциплины; синтез-когерентность на масштабе |

**Проблема.** Сейчас знания рассыпаны по one-shot артефактам: выводы `am-research`, выжимки `book/video-knowledge-extraction`, `research-index` (реестр), `learnings/`/`decisions/`/`memory/`. Каждый возврат к теме — перечитывание/перепоиск. am-wiki делает знание **компаундингом**: скомпилировано один раз, поддерживается агентом.

**Целевой пользователь.** N=1 (автор харнесса). Высокий объём чтения/исследований: книги, видео, конкурентка, JTBD, security-исследования, клиентские звонки.

**Альтернативы (как сейчас).** One-shot extraction, one-shot `am-research`, ручной `research-index`, `memory/`, заметки. Внешнее: gstack/**gbrain** (graph DB, тяжелее), **Graphify** (структура кода — другой слой), Obsidian+ручное.

**Метрики успеха.** time-to-answer на рекуррентный вопрос; reuse-rate (% ответа из wiki без перечитывания источников); покрытие wiki; число пойманных конфликтов/stale.

**Зависимости.** `last30days`, `searxng`/`web-reader` MCP, `book/video-knowledge-extraction` (backend), `am-prune` (lint). Всё есть.

**Риски.** (a) Каннибализация/путаница с существующими навыками; (b) adoption — надо кормить источники / гонять gather; (c) agent-gathered требует верификации (provenance/confidence); (d) scope creep («завикировать всё»); (e) когерентность синтеза на масштабе — главный технический риск; (f) N=1 — вся поддержка на агенте+пользователе.

## Technical Assessment (против харнесса)

| Критерий | Оценка | Заметки |
|---|---|---|
| Сложность | Low–Medium | В основном оркестрация существующих кусков + слой integrate/synthesize |
| Затронуто | 1 репо (`agent-knowledge`) + per-project `wiki/` dirs | новых сервисов Astra нет |
| Координация | No | один пользователь, один репо |
| Миграция данных | No | новый слой, ничего не ломает |

**Сложность.** Plumbing низкая: переиспользуем `book/video-knowledge-extraction` (ingest), `last30days` + `web-reader` (gather), `am-prune` (lint), паттерн `auto-retrieve` (selective query). Новое = **интеграция/синтез** (агент поддерживает связанный wiki + флагает конфликты) + provenance + query. Трудная часть — качество синтеза на масштабе, не plumbing.

**Существующий фундамент — сильный, ~60–70% reuse:** extraction-skills, `am-prune`, `auto-retrieve`-паттерн, `research-index`, футер-паттерн. am-wiki = оркестрация + integrate-слой поверх.

**Технические риски.** (a) Когерентность синтеза при росте (главный); (b) provenance-дисциплина; (c) бюджет контекста — wiki растёт → держать гардраил «query выборочно, никогда целиком» (как `auto-retrieve`); (d) портабельность — markdown/agent, без хуков (A+C).

## Redundancy-проверка (главный вопрос)

| Существующее | Отношение к am-wiki |
|---|---|
| `book/video-knowledge-extraction` | **Backend** (не дубль) — становятся extraction-движком wiki; one-shot-режим остаётся |
| `am-research` | **Потребитель** — am-wiki копит его выводы в продуктовый wiki (investigate vs accumulate) |
| `am-research-index` | **Комплемент** — index = реестр, wiki = содержание |
| `learnings/` | **Другой тип** — agent-generated operational facts vs source-derived synthesis |
| `decisions/` | **Другое** — settled calls, не source-synthesis |
| `memory/` | **Другое** — reflexive about user |

**Вердикт по дублям:** НЕ дублирует. am-wiki = недостающий «integrate + maintain + query across sources»-слой, связывающий one-shot навыки в компаундинг. Риск — не дубль, а путаница границ; лечится чётким разделением (extraction = backend, am-wiki = maintained layer).

**Overkill?** Для объёма этого пользователя (много чтения/исследований) — нет. Для случайного — да.

## Competitive Context

- **Карпати LLM Wiki** — паттерн-основа ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)); community-реализации на Claude Code + Obsidian.
- **gstack/gbrain** — persistent knowledge graph (graph DB, тяжелее; anti-образец для независимости — см. наш gstack-анализ).
- **Graphify** ([repo](https://github.com/safishamsi/graphify)) — структура кодбейза; другой слой (код, не документы).
- Отличие am-wiki: markdown + agent (легче, соответствует A+C), переиспользует существующие навыки пользователя.

## Verdict: DO (trial-scoped)

Паттерн здрав; ценность реальна для этого пользователя; ~60–70% переиспользования; риск — исполнение/дисциплина, не концепция. Но не big-bang: **минимальный триал на одном сценарии** → kill-or-expand через ~2 недели реального использования.

## Conditions (DO)

- [ ] Триал на ОДНОМ сценарии (конкурентка через `last30days` — высшая felt-value, инструменты готовы), не 5 сразу.
- [ ] Переиспользовать существующие навыки как backends (не переизобретать extraction/lint/query).
- [ ] Provenance + confidence-теги с первого дня.
- [ ] Гардраил: query выборочно (≤топ), никогда не грузить wiki целиком (как `auto-retrieve`).
- [ ] Markdown/agent, без хуков (A+C).
- [ ] **Kill-criterion:** если за 2 недели триал-вики не используется / не даёт felt-value — выкинуть; существующих навыков хватает.

## Open Questions

- Где живут wiki? per-project (`Astra/PM/competitive/wiki/`) или личный KB-root?
- Один connected wiki или по одному на тему (конкурентка / книги / ФСТЭК)?
- gather-heavy vs add-heavy — сколько пользователь хочет кормить сам?
- Каденция maintenance — кто триггерит lint?
