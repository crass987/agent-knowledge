---
name: am-pain-mining
description: Use when analyzing a customer meeting transcript, demo recording, or pre-sale call. Triggers on "analyze meeting", "demo analysis", "pains from transcript", "extract pains", "customer meeting", "проанализируй встречу".
---

# Pain Pattern Mining

## Overview

Extract structured customer intelligence from demo/meeting transcripts. Produces a `pain-report` artifact using the template in `report-template.md`.

Grounded in Geoffrey Moore's Bowling Alley framework: identify patterns that reveal the **headpin niche** — the segment with the strongest compelling reason to buy.

## When to Use

- Have a transcript of a demo, pre-sale meeting, or pilot review
- User asks to extract pains or customer needs from a meeting
- Building up data for cross-meeting pattern analysis
- Evaluating product-market fit for a specific customer segment

## When NOT to Use

- Cross-meeting pattern analysis (multiple meetings) — use pain-reports as input for separate analysis
- Feature research — use `am-research`
- Competitive analysis without customer data — use `competitive-analysis`

## Input Formats

| Format | Handling |
|--------|----------|
| **TXT** | Plain text. Read as-is. Infer timestamps if not present. |
| **SRT** | Subtitle format with timestamps. Parse time markers for emotional map and quote references. |
| **Video/Audio** | User should provide transcript. If video given, suggest manual transcription or use `video-knowledge-extraction` skill. |

**Speaker identification:** If transcript has speaker labels, preserve them. If not, infer roles from context (presenter vs. customer), flag with `[INFERRED]`.

## Quick Reference

| Step | Action | Key Output |
|------|--------|------------|
| 1 | Parse & segment | Speaker roles, sections, timestamps |
| 2 | Extract raw signals | Pains (явная/вероятная), feature requests, objections, buying triggers, competitive refs, decision signals |
| 3 | Convert → JTBD | "Когда [ситуация], я хочу [мотивация], чтобы [результат]" — Functional / Emotional / Social |
| 4 | Detect misalignment | Where our team misunderstood what the customer meant |
| 5 | Map competitive context | For each competitor: why mentioned, strengths, gaps, who brought it up |
| 6 | Map decision dynamics | Champion / Blocker / Neutral / User for each participant |
| 7 | Build emotional timeline | Energy spikes (what sells) and drops (what blocks) |
| 8 | Score opportunity | X/12 viability (see `report-template.md` §10 for criteria) |
| 9–10 | Produce report + next steps | Filled template with specific, actionable next steps |

## Process Details

### JTBD Prioritization

Score each job by: **frequency × intensity × connection to buying decision**.

JTBD is the PRIMARY section. Pains are secondary — short list, linked to jobs. Don't duplicate content across sections.

### Misalignment Detection

Often the most valuable finding. Common patterns:

- Customer uses a term → our team interprets differently → demo goes off-track
- Customer describes a need → our team shows unrelated feature
- Customer's silence or lukewarm reaction → we're showing the wrong thing

Flag every instance with consequences (lost time, wrong feature shown).

### Next Steps

Each must have: **priority, action, effort estimate, owner, target date**. No generic advice — specific to THIS customer.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Mixing pains with feature requests | Always separate; feature request = surface, pain = underlying need |
| Inferring too much | Mark everything inferred as `[INFERRED]` or `[AMBIGUOUS]` |
| Generic next steps | "Follow up" is useless — specific action with owner and deadline |
| Duplicating across sections | Pain in §4 links to JTBD in §3, never repeats the same content |
| Wrong report language | Match the transcript language (Russian → Russian, English → English) |

## Rules

- **Quote verbatim** — use exact customer words, with speaker and timestamp
- **Don't guess** — mark ambiguity as `[AMBIGUOUS]` with your best interpretation
- **Distinguish observed vs. inferred** — "Client said X" vs. "Client likely feels Y because..."
- **Prioritize ruthlessly** — score by frequency × intensity × buying connection
- **No generic advice** — next steps must be specific to THIS customer
- **Keep JTBD grounded** — jobs come from customer words, not your interpretation
- **Write in the language of the transcript** — Russian transcript = Russian report, English = English
- **Output location.** Save product output under `PM/` per the routing test in `PM/CLAUDE.md` (theme-specific → `PM/initiatives/<theme>/`; competitive → `PM/competitive/`; untethered one-off → `PM/sessions/`; disposable → `PM/tmp/`). Client-conversation output usually belongs in `PM/customers/<client>/`. Never write product artifacts into `meta/` — `meta/` is meta-repo infrastructure only.
- **Стиль отчёта.** Текст `pain-report` читают люди — пишите по инфостилю (`infostyle` + `_shared/infostyle-core.md`): факт вместо оценки, сильная позиция, одна мысль на абзац. JTBD-формулировки внутри отчёта — по `jtbd`.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
