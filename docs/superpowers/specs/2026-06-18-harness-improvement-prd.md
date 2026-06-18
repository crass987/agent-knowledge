# PRD: Улучшение харнесса — operational learning loop, governance и независимость от агента/LLM

| | |
|---|---|
| **Version** | 0.1 (draft) |
| **Date** | 2026-06-18 |
| **Status** | Draft, ожидает review |
| **Scope variant** | Средний — loop + governance + light telemetry |
| **Approach** | A + C (agent-portability + eval-the-harness) |
| **Target** | Личный Claude Code харнесс: am-* навыки (этот репо) + `memory/` + `CONTEXT.md` + MCP |

---

## 1. Problem & Context

### 1.1 Что есть сегодня

Харнесс состоит из: upstream-пакета **superpowers** (read-only), собственных **am-*** навыков (этот репо `agent-knowledge`), рефлексивной **`memory/`** (кто пользователь, какой фидбек), горячего канала **`CONTEXT.md`**, реестра исследований **research-index**, и набора **MCP**-серверов (searxng, context7, jira, confluence, zread, playwright).

Сильная сторона, которую **сохраняем**: продуктовая и стратегийная дисциплина — JBTD, Minto, инфостиль Ильяхова, grill-навыки. Этого нет ни у gstack, ни у большинства пэров.

### 1.2 Gap

1. Память **рефлексивная**, но не **операционная**: факты о кодбейзе/командах, экономящие время, не захватываются и не переиспользуются систематически.
2. Нет **петли компаундинга**: навык_N не подгружает уроки навыка_(N−1).
3. Нет **governance**: память гниёт вручную (пометки `DECOMPOSED/SUPERSEDED` от руки), нет авто-чистки устаревших и конфликтных записей.
4. Нет **лёгкой телеметрии**: непонятно, какие навыки реально используются, какие падают, какие мертвы.
5. **Зависимость от Claude Code**: hooks, пути `~/.claude/`, хардкод tool-неймов (`mcp__jira__*`) внутри текстов навыков.

### 1.3 Уроки из анализа пэров и источников

| Источник | Забираем | Чего избегаем |
|---|---|---|
| **gstack** | 4-слойная петля (store→capture→retrieve→govern); `decisions.active`; регрессионные тесты как память харнесса | bash-преамбула на сотни строк; пути `~/.claude`; бинарники; vendor-телеметрия в Supabase — **всё это anti-pattern для независимости** |
| **Addy Osmani** (Loop Eng., Self-Improving Agents) | 4 канала памяти (git / progress / task-state / knowledge); AGENTS.md self-append; maker≠checker; stateless-loop | — |
| **Anthropic** (Demystifying Evals) | eval-the-harness; capability vs regression; grade **output not path**; pass@k / pass^k | — |
| **Arize** (Closing the Loop) | harness > model; **traces as ground truth**; skills = **map, not encyclopedia** | full observability stack (Phoenix) — тяжело, vendor-lock |
| **Willison** (Agentic Patterns) | канон паттернов; lead-by-example; «code is cheap now» | — |

---

## 2. Goals / Non-goals

### Goals

- **G1. Operational learning loop.** Навыки захватывают операционные уроки и подгружают релевантные на следующем запуске — знания компаундируются между сессиями.
- **G2. Governance.** Память и learnings не гниют: auto-prune (устаревшие/конфликтные), `decisions.active` (не переподнимать settled-calls), опциональный decay, регрессионные эвалы.
- **G3. Лёгкая локальная телеметрия.** `skill-runs` лог (навык/длительность/исход), local-only, переносимый формат.
- **G4. Независимость (сквозной принцип).** Артефакты переносимы (`AGENTS.md`/`SKILL.md`/MCP/markdown); убираем Claude-only-механизмы; LLM-независимость через model-agnostic промпты + eval-the-harness (не через per-LLM адаптеры).

### Non-goals

- Upstream **superpowers** — read-only, не форкаем.
- **Внешняя телеметрия** и **vendor-SDK** (Phoenix / LangSmith / Braintrust / Supabase).
- **per-LLM adapter** (подход B отвергнут).
- Тяжёлые рантайм-зависимости (Bun / Playwright как у gstack).
- Eng-цепочка gstack (`/qa`→`/ship`→`/cso`→`/browse`) — не наша высота.

---

## 3. Принципы (сквозная независимость)

Применяются к **каждому** компоненту, не отдельным эпиком.

| # | Принцип | Смысл |
|---|---|---|
| P1 | **AGENTS.md как канон** | Не `CLAUDE.md`. Meta-repo уже на AGENTS.md — распространить на харнесс |
| P2 | **SKILL.md формат** | Переносимо Claude Code ↔ Codex (навыки уже в нём) |
| P3 | **MCP как нейтральный инструмент-слой** | Инструменты не зашивать хардкодом в тексты навыков |
| P4 | **Markdown/JSONL память на диске** | git-friendly, переносима, читаема человеком |
| P5 | **Локальная телеметрия, portable формат** | Никаких vendor SDK; данные не покидают машину |
| P6 | **Model-agnostic промпты** | Без опоры на Claude-специфичные паттерны рассуждений |
| P7 | **Eval-the-harness** | Успех определён независимо от того, какая модель/хост бежит |
| P8 | **Maker ≠ Checker** | Навык не оценивает свой вывод; improve-skill — отдельный checker-проход |
| P9 | **Knowledge = map, not encyclopedia** | Навыки/память — указатели на правду, не монолит (Arize) |

---

## 4. Архитектура

### 4.1 Operational learning loop

Основа — 4 канала памяти (по Addy Osmani), намапленные на текущий харнесс:

| Канал | Роль | У вас |
|---|---|---|
| **Git history** | что изменилось — читается из repo | уже есть |
| **Progress-журнал** | что произошло (хронология) | `CONTEXT.md` (hot) — есть, **формализовать** как progress-канал |
| **Task-state** | статус задач/решений | **добавить** лёгкий (`decisions.active`, task-листы) |
| **Knowledge (semantic)** | долговременные уроки | `memory/` (reflexive) + **НОВЫЙ** operational learnings канал |

**Новый operational-learnings канал** — типизированные записи, **отдельно** от рефлексивной `memory/`:

```
type:    pattern | pitfall | preference | operational
key:     <2-5 слов, kebab-case>
insight: <одно предложение, факт а не оценка>
confidence: 1-10
source:  observed | user-stated | extracted
files:   [<опц. релевантные пути>]
ts:      <ISO>
scope:   harness | project
```

Формат — **markdown с frontmatter** (человекочитаемо, git-diff-friendly, переносимо; queryable через grep/навык). JSONL — резерв, если позже понадобится программный поиск в масштабе.

**Скоуп записей**: harness-level (как работают навыки, квирки инструментов) → `agent-knowledge/learnings/`; project-level (факты о кодбейзе Astra) → рядом с проектом (секция в AGENTS.md или project-state).

**Цикл**: `skill-end → capture (footer) → store → next-skill-start → retrieve top-3 → governance prune → eval-gate`

### 4.2 OIAE-цикл для improve-skill (дисциплинированное самоулучшение навыков)

Обновление существующего `improve-skill` по паттерну Observe → Inspect → Amend → Evaluate, с обязательным rollback:

| Шаг | Что делает | Источник данных |
|---|---|---|
| **Observe** | где навык падает/медленный | `skill-runs` телеметрия |
| **Inspect** | при кластере failures — смотреть `SKILL.md` + transcripts | git, логи |
| **Amend** (maker) | агент предлагает **minimal diff** к `SKILL.md` | — |
| **Evaluate** (checker) | **другая** модель/сессия: стало лучше? есть регрессия? | regression-эвалы |
| **Rollback** | если не помогло — `git revert` | git |

Принцип **maker≠checker** (P8): тот, кто правил навык, не оценивает результат. Это одновременно и контроль качества, и механизм LLM-независимости (checker может быть другой моделью).

### 4.3 Governance

- **Auto-prune** — обобщение stale-чекера из `am-research-index` на `memory/` + learnings:
  - **Stale**: ссылка на удалённый файл/навык → флаг.
  - **Contradiction**: один `key`, противоположный `insight` → флаг.
  - Append-only, latest-wins (как у gstack `/learn prune`).
- **`decisions.active`** — долговечные решения с rationale + `--supersede <id>` для реверса. Не переподнимать молча. Лечит боль из `feedback-root-jtbd` (повторно дебатировавшиеся джобы/решения).
- **Decay** (опц.) — по типу: operational-facts без decay; taste/preferences — мягкий decay (по образцу gstack taste 5%/нед).
- **Регрессионные эвалы (подход C)** — seed-набор per-навык; capability→regression graduation по Anthropic.

---

## 5. Компоненты (конкретно)

1. **`learning-footer`** — стандартный блок в конец am-* `SKILL.md`: «если нашёл операционный урок, экономящий 5+ мин — залогируй». Гейт: **не логировать очевидное и транзитное**. Применять только к операционным навыкам (tier), не к каждым.
2. **Operational-learnings store** — `agent-knowledge/learnings/{patterns,pitfalls,preferences,operational}.md` + project-level секция.
3. **`decisions.active.md`** — стор решений с supersede.
4. **OIAE-wrapper** — обновить `improve-skill` до Observe→Inspect→Amend→Evaluate→rollback, с maker≠checker.
5. **`auto-prune`-навык** — новый (или расширение `am-research-index`): stale + contradiction чеки над memory + learnings.
6. **Light local telemetry** — `agent-knowledge/state/skill-runs.{md,jsonl}` (harness-level), local-only.
7. **Regression eval seed** — минимальный набор per am-* навык.

---

## 6. Data flow

```
[skill invoked]
   │
   ├─ preamble: load top-3 релевантных learnings + active decisions
   │
   ▼
[skill runs]
   │
   ├─ at end:
   │    ├─ learning-footer → capture (если 5+ мин saver)
   │    └─ telemetry → log skill-run {skill, ts, duration, outcome}
   ▼
[store append]  (learnings / decisions / skill-runs)
   │
   ▼
[next session: context-recovery]
   └─ читает recent learnings + decisions → «welcome back» summary
   │
   ▼
[governance: периодически]
   └─ auto-prune: stale / contradiction / decay
   │
   ▼
[eval-gate on skill changes]
   └─ OIAE Evaluate: regression-эвал решает принять/откатить
```

---

## 7. Портабельность (подход A)

**Уже переносимо:** `AGENTS.md` (meta-repo), `SKILL.md` (am-*), MCP-серверы, markdown `memory/`.

**Деклоджить (P0 mini-audit + каждая фаза):**

| Claude-only | → Переносимое решение |
|---|---|
| Хардкод tool-неймов (`mcp__jira__*`) в текстах навыков | Вынести в `AGENTS.md` / tool-registry; навыки ссылаются на инструмент **абстрактно** (по capability, не по имени) |
| Hooks (Claude-only) | Документировать как **optional enhancement**, не критичный путь; критичная логика — в самом `SKILL.md` |
| Пути `~/.claude/...` | Относительные / конфигурируемые через env |
| Директивы только в `CLAUDE.md` | Дублировать в `AGENTS.md` (канон) |

Критерий приёмки независимости: am-* навык запускается на Claude Code **и** Codex без правок `SKILL.md`.

---

## 8. Фазинг

| Фаза | Что | Эффект |
|---|---|---|
| **P0** | `learning-footer` + operational-learnings канал + `skill-runs` телеметрия + portability mini-audit | Компаундинг начинается; видны dead/failing навыки |
| **P1** | `decisions.active` + OIAE-upgrade `improve-skill` (maker≠checker) | Не переподнимаем решения; навыки самоулучшаются с rollback |
| **P2** | `auto-prune` governance + регрессионные эвалы + decay | Память не гниёт; регрессии ловятся |

Принцип P1–P9 (независимость) применяется **в каждой фазе**, не отдельным этапом.

---

## 9. Success metrics

- **Компаундинг**: # операционных learnings за N сессий; % сессий, где retrieved-learning повлиял на действие.
- **Governance**: # stale/conflicting, удалённых auto-prune; # переподнятых решений (цель → 0).
- **Телеметрия**: покрытие `skill-runs` логом; # выявленных dead/failing навыков.
- **Эвалы**: # навыков с regression-эвалом; regression catch rate.
- **Независимость**: am-* навыки запускаются на ≥2 хостах без правок; # Claude-only-зависимостей (цель → min).
- **OIAE**: % изменений `improve-skill`, прошедших Evaluate (не откатанных).

---

## 10. Risks & Open questions

### Risks

- **Capture-noise**: агенты логируют мусор → митигируется гейтом footer'а + auto-prune.
- **LLM-independence иллюзорна** → честно идём через эвалы (P7), не через адаптеры.
- **Оверхед footer'а** на каждый навык → tier: только операционные навыки, не все.
- **Путаница `memory/` vs `learnings/`** → жёсткое разделение: `memory/` = reflexive (о пользователе/проекте), `learnings/` = operational (факты экономящие время).

### Open questions (с рекомендацией)

- **Формат learnings: md vs JSONL?** → **md с frontmatter** (человекочитаемо, git-friendly, переносимо). JSONL — если позже нужен масштабный программный поиск.
- **Где live `skill-runs` лог: per-project vs global?** → **global harness-level** (`agent-knowledge/state/`), т.к. это про харнесс, не про конкретный проект Astra. Project-specific контекст остаётся в `CONTEXT.md`/AGENTS.md проекта.
- **`decisions.active` поверх существующих `project-`/`feedback-` памятей или отдельно?** → **отдельно**. Существующие памяти reflexive; decisions — авторитетные «settled calls» с supersede-семантикой, их не смешивать.

---

## Ссылки (источники)

- gstack — https://github.com/garrytan/gstack
- Addy Osmani — Loop Engineering — https://addyosmani.com/blog/loop-engineering/
- Addy Osmani — Self-Improving Coding Agents — https://addyosmani.com/blog/self-improving-agents/
- Anthropic — Demystifying Evals for AI Agents — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Arize — Closing the Loop — https://arize.com/blog/closing-the-loop-coding-agents-telemetry-and-the-path-to-self-improving-software/
- Simon Willison — Agentic Engineering Patterns — https://simonw.substack.com/p/agentic-engineering-patterns
- BerriAI/self-improving-agent — https://github.com/BerriAI/self-improving-agent
- OIAE-loop MCP (Observe→Inspect→Amend→Evaluate) — https://github.com/topics/self-improving
