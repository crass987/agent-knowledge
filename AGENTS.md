# Agent Knowledge Router

This file routes the AI agent to the right standards and skills based on context.

## How to use

Before writing code or performing a task, check the relevant category index.
Load ONLY the skills that match the current file or task — do not load everything.

## Standards

| Editing... | Read index |
|---|---|
| `*.py`, `requirements.txt`, `pip`, `pytest` | `standards/python/_INDEX.md` |
| `*.ts`, `*.tsx`, `tsconfig.json`, `package.json` | `standards/typescript/_INDEX.md` |
| `*.go`, `go.mod`, `go.sum` | `standards/go/_INDEX.md` |
| `Dockerfile`, `docker-compose*`, `*.yml`, `*.yaml` | `standards/devops/_INDEX.md` |
| Keywords: roadmap, metrics, research, product, KPI | `standards/product/_INDEX.md` |
| Keywords: sprint, stakeholder, planning, backlog | `standards/management/_INDEX.md` |

## Skills

| Task involves... | Read index |
|---|---|
| testing, TDD, red-green-refactor | `skills/tdd/SKILL.md` |
| debugging, investigating bugs, errors | `skills/debugging/SKILL.md` |
| code review, PR review, pull request | `skills/code-review/SKILL.md` |
| deploy, release, production, rollout | `skills/deploy-checklist/SKILL.md` |
| incident, outage, postmortem, SEV | `skills/incident-response/SKILL.md` |
| spec, PRD, requirements, feature design | `skills/spec-writing/SKILL.md` |
| competitor, market, analysis, benchmark | `skills/competitive-analysis/SKILL.md` |
| book, knowledge, extraction, convert, OCR, Pandoc | `skills/book-knowledge-extraction/SKILL.md` |
| video, YouTube, transcript, whisper, lecture, podcast, knowledge extraction | `skills/video-knowledge-extraction/SKILL.md` |
| investigate, research, feature, как работает, изучи | `skills/am-research/SKILL.md` |
| research index, did we research, зарегистрируй исследование, проверь research index, что из исследований устарело | `skills/am-research-index/SKILL.md` |
| evaluate, grill, assess, оцени фичу, прожарь, стоит ли делать | `skills/am-grill-feature/SKILL.md` |
| requirements, specs, аналитика, напиши требования, write specs | `skills/am-write-specs/SKILL.md` |
| audit, docs, documentation, неточности, проверь доки, прожарь документацию | `skills/am-grill-docs/SKILL.md` |
| jbtd, jobs-to-be-done, job story, JTBD, формулировка задачи, напиши jbdt, сформулируй задачу, заголовок, придумай заголовок, переделай заголовок | `skills/jbtd/SKILL.md` |
| decision, что решили, напиши решение, supersede решение, почему решили, архитектурное решение | `skills/decisions/SKILL.md` |
| prune, чистка памяти, почисти learnings, устаревшие записи, conflicting entries, почисти память | `skills/prune/SKILL.md` |
| grill plan, прожарь план, прожарь меня, grill my design, стресс-тест плана, решить с агентом что делать | `skills/grill-plan/SKILL.md` |

## Tool registry (capability → tool)

Skills reference tools by **capability**, not by vendor tool-name. Concrete tools are resolved here. (Portability principle P3: the neutral instrument layer is MCP; keep skill text tool-agnostic.) The portability linter (`scripts/lint-portability.py`) rejects hardcoded `mcp__*` names inside `SKILL.md` files — this registry is their only legitimate home.

| Capability | Tool | Notes |
|---|---|---|
| jira | `mcp__jira__*` | no raw REST, no stored creds |
| confluence | `mcp__confluence__*` | |
| web-search | `mcp__searxng__searxng_web_search` | preferred over built-in WebSearch |
| web-read | `mcp__web-reader__webReader` | url → markdown |
| repo-read (github) | `mcp__zread__*` | structure / read_file / search_doc |
| browser automation | `mcp__plugin_playwright_playwright__*` | |
| lib docs | `mcp__context7__*` | resolve-library-id → query-docs |
