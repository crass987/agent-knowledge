# decisions.active

Settled calls with rationale. Append-only — reverse by superseding (see `README.md`).

<!--
Example:
---
id: D-0001
title: Harness stays agent/LLM-independent (approach A+C)
status: active
decided: 2026-06-18
rationale: Portability across Claude Code/Codex/etc. + LLM-independence via eval-the-harness; reject per-LLM adapters as over-engineering.
supersedes: []
superseded_by: []
scope: harness
---
-->

---
id: D-0001
title: Graphify (and graph-RAG-over-files tools) NOT adopted in the Astra harness
status: active
decided: 2026-08-09
rationale: Graphify solves concept-discovery in an unfamiliar codebase, but the Astra harness's pain is consistency/governance (AGENTS.md ownership, capability-registry, am-update, am-docs-audit) — not discovery; an auto-generated knowledge graph would become a third source of truth that drifts, and its always-on --strict hook contradicts the measured "more context = worse" finding (Nick Nisi, 77% vs 97%).
supersedes: []
superseded_by: []
scope: harness
---
**Alternatives considered:** cross-project global graph + merge-graphs under our meta-repo structure; free/private tree-sitter code parsing; god-nodes map as input to capability-audit; `graphify reflect`→LESSONS.md as a lighter retro. All real capabilities — none closes the consistency pain, and each adds a drift surface.

**Reasons (decisive):**
1. Wrong problem — discovery tool for a consistency/governance harness.
2. Third source of truth → drift (we already battle C2 §2-5, capability-registry validator gaps).
3. Always-on strict hook violates the empirically-verified "more context = worse."
4. Token cost on our docs-heavy layers (PM/, meta/, CONTEXT.md, canon); free path only covers code.
5. Obsidian-vault export (the video's core flow) is not our scenario at all.

**Re-open trigger:** if the harness pain genuinely shifts from consistency to discovery across many unfamiliar repos, or if an always-on hook is proven (measured pass-rate) to help rather than hurt.

**Note:** This decision was discussed in an earlier session but never persisted — it was re-derived from scratch on 2026-08-09 (graphify-obsidian video extraction) before the user corrected it. Recorded now to prevent a third re-litigation. See KB doc `videos/graphify-obsidian-claude-code-cheat-code/` and `videos/wiki-llm-na-maksimalkah/`.

---
id: D-0002
title: BI-слой поверх ClickHouse строим свой (UI/UX-референс — Metabase); компонент/форк Metabase не берём
status: active
decided: 2026-11-19
rationale: Metabase как компонент/форк блокируется лицензией (AGPL §13 — закрытый форк невозможен; всё нужное для white-label/SSO/air-gap — платная MCL с audit/true-up) и нацрежимом для гос-заказчиков. При этом RUM/продуктовая аналитика поверх CH требует Metabase-класса конструктора и дашбордов: UI/UX-механики берём как поведенческий референс (в их код можно подсматривать, копипастить нельзя — реализация наша), их e2e-набор — спецификация поведения. RUM-сессии — позже, вне первого скоупа.
supersedes: []
superseded_by: []
scope: project
---
**Контекст решения:** ресёрч PM/sessions/metabase-embed-research.md (2026-11-19, воркфлоу 7 агентов, адверсариальная верификация лицензии 27 клеймов). Вердикт отчёта — вариант D «не брать, взять идеи»; владелец уточнил направление 19.11: целиться в максимум возможностей Metabase в собственном движке дашбордов поверх CH (трейсы/логи → потом RUM).

**Скоуп (этапы):** 1) SQL-панели поверх CH (трейсы/логи) — недели; 2) GUI-конструктор + IR→SQL компилятор (только CH-диалект) — 2–3 квартала (оценка); 3) click behaviors/drill-through, экспорт; 4) семантический слой (каталог метрик) → заодно вход в SLO-движок U6.1. RUM-сессии/path exploration — отдельный хвост.

**Вне скоупа:** 18 драйверов, admin-панель Metabase, embedded SDK, sandboxing, sync чужих БД, копирование их кода (включая TS-frontend — тоже AGPL).

**Re-open trigger:** если появится срочная потребность в embedded-аналитике под нашим брендом в поставке заказчику — переоткрыть развилку «платить MCL (Enterprise, air-gap за доплату) vs свой слой»; если CH перестанет быть единственным целевым хранилищем BI — пересмотреть IR.
