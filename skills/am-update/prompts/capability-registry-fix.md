# Capability Registry Drift Fix

Apply drift fixes, regenerate views, publish. Follows `capability-registry-audit.md`.

**Part of:** `am-update` (Stage 4).
**Source of truth:** `PM/strategy/functional-registry.md` (PM sibling repo — commit there).

---

## Classify each drift finding

- **Code-wins (auto-fix):** validator or grep is unambiguous — broken proof link (page moved/removed → update path or mark `не найдено`), feature graduated (`роадмап`→`Поддерживается`). → **maker-subagent** edits `PM/strategy/functional-registry.md`, separate **checker-subagent** re-verifies against `internal_docs`/code → commit on APPROVE.
- **Judgment (→ review queue):** verdict change (AGPL/ФСТЭК status, softening/rewording a claim, status reclassification). → append to `meta/reports/review-queue.md`: `- [open] **[<fn-slug>]** <item> — source: capability-registry-drift · 📅 opened <date> · 🔎 rationale`.
- **maker ≠ checker (P9):** if the checker thinks an auto-fix is actually a judgment call, it rejects and queues it.

## After edits — re-validate, then regenerate views (gated)

1. `python3 meta/scripts/capability_registry_check.py PM/strategy/functional-registry.md analytics-hub/internal_docs` → must print `OK: реестр валиден` (exit 0). If not — fix; do not regenerate/publish a dirty registry.
2. Regenerate views (both refuse to emit if the registry is invalid):
   - `python3 meta/scripts/registry_to_xlsx.py PM/strategy/functional-registry.md <out.xlsx> analytics-hub/internal_docs`
   - `python3 meta/scripts/registry_to_md.py PM/strategy/functional-registry.md analytics-hub/internal_docs > <out.md>`

## Publish

- **Confluence model (с 2026-10-01): страница на релиз.** Дерево: родитель **«Реестр функциональности AM»** (`728802299`, space MNTR), внутри — замороженные снапшоты по релизам. Актуальный ребёнок: **«Реестр функциональности AM 1.7.0»** (`728802300`). Новый релиз → создать нового ребёнка (title: `Реестр функциональности AM <версия> — сверка ФТТ с кодом (<дата>)`), старые страницы НЕ редактировать; обновить у родителя строку «Актуальный релиз» и «История».
  - Before publishing: bump the version/date line in `PM/strategy/functional-registry.md` (`**Последняя проверка:** <дата> · версия: <релиз>`), re-run the validator.
  - `content_file` must be **inside the Astra workspace** (MCP rejects `/tmp`) — publish from `PM/strategy/registry-views/`.
- **Артефакты:** `PM/strategy/registry-views/AM-<версия>-<дата>.{md,xlsx}` — коммитятся в PM рядом с источником (не в /tmp).
- **xlsx attachment — MCP `confluence_upload_attachment` is currently BROKEN** (fails for any file, including a 16-byte .txt — likely Cloud/Server API mismatch; manual upload works). Until fixed: attach xlsx to the release page manually. The page content (tables) is self-sufficient; the xlsx is a convenience download.

## Commit

Commit registry edits in the **PM** repo (`PM/strategy/functional-registry.md`), prompt/report changes in the **Astra** repo. One status line into the summary: `Stage 4 — capability-registry: N drift, M auto-fixed, K queued; views regenerated, Confluence updated`.
