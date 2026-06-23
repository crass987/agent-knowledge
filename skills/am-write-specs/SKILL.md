---
name: am-write-specs
description: Use when writing requirements or specs for Astra Monitoring — "напиши требования", "подготовь аналитику", "write specs for X", "напиши требования". Triggers on spec/requirement authoring requests.
---

# Write Requirements / Specs

## Overview

Write structured requirements or specifications for a feature, ready for commit to analytics-hub. Combines research, architecture analysis, and Jira context.

## When to Use

- User asks to write requirements or specs for a feature
- User needs to prepare product analytics for development
- User wants to create a REQ or SPEC document in analytics-hub

## When NOT to Use

- Just researching a feature → use `am-research`
- Evaluating whether to build → use `am-grill-feature`
- Checking existing docs for accuracy → use `am-grill-docs`

**REQUIRED:** Read `am-research` output or follow its process first — you must understand the feature before writing specs.

## Стиль

Текст требований и спецификаций читают люди — пишите по инфостилю Ильяхова. Базис
(стоп-слова, факт-вместо-оценки, чувственная конкретика) — в
`_shared/infostyle-core.md`; полный референс для прозы — скилл `infostyle`. Заголовок
REQ/SPEC называет **работу** (как `jtbd` для task title), а не пользу читателю.

## Process

### 1. Research the feature

Follow `am-research` process to understand the feature fully. You must know:
- What the feature does and why
- Which services are involved
- Current implementation state
- Existing requirements/specs (if any)

### 2. Understand the target format

Check analytics-hub conventions:

- **Requirements**: `analytics-hub/docs/requirements/REQ-mon-XXXX-<title>.md`
- **Specifications**: `analytics-hub/docs/specifications/SPEC-XXXX-<title>/`
- **Architecture decisions**: `analytics-hub/docs/architecture/ADR-XXX-<title>.md`

Read 1-2 existing files in the target format for structure reference.

### 3. Check architecture constraints

Read relevant architecture docs:
- `analytics-hub/master_docs/Архитектура/C2-контейнеры.md` — system boundaries
- `analytics-hub/docs/architecture/ADR-*.md` — existing decisions
- `meta/repos/<service>.md` — service capabilities and limits

### 4. Write the document

Structure for a **requirement** (REQ):

```markdown
# REQ-mon-XXXX — [Feature Title]

## Контекст
[Why this feature is needed. User pain points. Business context.]

## Цели
[What we want to achieve. Measurable if possible.]

## Пользовательские сценарии
### Сценарий 1: [name]
- **Как** [роль]
- **Я хочу** [действие]
- **Чтобы** [результат]

## Функциональные требования
1. [requirement]
2. [requirement]

## Нефункциональные требования
- Производительность: [...]
- Безопасность: [...]
- Масштабируемость: [...]

## Критерии приемки
- [ ] [criterion]
- [ ] [criterion]

## Зависимости
- Сервисы: [...]
- API: [...]
- Данные: [...]

## Открытые вопросы
- [question]
```

Structure for a **specification** (SPEC) — more detailed, includes technical design.

### 5. Self-review

Before presenting, check:
- [ ] No contradictions with existing architecture
- [ ] All affected services are listed in dependencies
- [ ] Acceptance criteria are testable
- [ ] No TBD/TODO placeholders
- [ ] References to Jira epics/stories if they exist

## Rules

- Write in Russian (matching existing analytics-hub conventions)
- Reference Jira tickets where applicable (MON-XXXX)
- If the feature requires go-lib changes — explicitly flag it (affects all services)
- If the feature requires schema changes — note migration needs
- Include the PM in open questions — don't decide product details yourself
- The output should be ready to commit to analytics-hub after PM review
- **Output location.** The final spec goes to `analytics-hub` (already the convention). A WIP/draft before PM review goes to `PM/initiatives/<theme>/`. Never write product drafts into `meta/` — `meta/` is meta-repo infrastructure only. Routing test: see `PM/CLAUDE.md`.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
