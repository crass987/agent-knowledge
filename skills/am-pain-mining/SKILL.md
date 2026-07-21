---
name: am-pain-mining
description: Use when analyzing a customer meeting transcript, demo recording, or pre-sale call. Triggers on "analyze meeting", "demo analysis", "pains from transcript", "extract pains", "customer meeting", "проанализируй встречу".
---

# Pain Pattern Mining

## Overview

Extract structured customer intelligence from a single demo/meeting transcript. Produces a `pain-report` artifact (`report-template.md`) with **two readers**:

- **Sales / pre-sale** — deal tactics: decision map, misalignments, emotional map, deal viability, next steps.
- **Product / `am-gap-analysis`** — a **Zamesin payload**: Core Jobs with success criteria, Current Chain, classified pains, typed Gap map. This is the feed for cross-meeting product-gap analysis.

**Methodology base = AJTBD / Next Move Theory (Zamesin).** Geoffrey Moore's headpin + deal-viability enter only as a **presale overlay** (§§8, 12 of the template) — not as the segmentation root. The canon lives in `Next-Move-Theory-Canon/Advanced-Jobs-To-Be-Done/` (read `job-structure.md`, `value-creation.md`, `barrier-removal.md` before heavy runs). Apply canon in your own words; do not copy canon text.

## When to Use

- Have a transcript of a demo, pre-sale meeting, or pilot review
- User asks to extract pains or customer needs from a meeting
- Building up data for cross-meeting pattern analysis (this skill = the atom; `am-gap-analysis` aggregates)
- Evaluating product-market fit signal for a specific customer

## When NOT to Use

- **Product go/no-go across deals** (coverage map, RICE ranking, «надо ли автоматизировать в принципе») → `am-gap-analysis`. This skill answers *pursue this deal?* and *what's the Job/pain structure here?* — not *should we invest in automating X?*
- Feature research → `am-research`
- Competitive analysis without customer data → `competitive-analysis`

## Input Formats

| Format | Handling |
|--------|----------|
| **TXT** | Plain text. Read as-is. Infer timestamps if not present. |
| **SRT** | Subtitle format with timestamps. Parse time markers for quotes and emotional map. |
| **Video/Audio** | User should provide transcript. If video given, suggest manual transcription or use `video-knowledge-extraction`. |

**Speaker identification:** Preserve labels if present. Infer roles from context (presenter vs. customer), flag with `[INFERRED]`.

## Quick Reference

| Step | Action | Key Output |
|------|--------|------------|
| 1 | Parse & segment | Speaker roles, sections, timestamps |
| 2 | Extract raw signals | Pains, feature requests, objections, Aha-moments, competitive refs, decision signals |
| 3 | **Core Jobs with criteria** | «Когда [контекст], я хочу [результат] **с [критериями]**, чтобы [Big Job]» + Big Job parent + confidence |
| 4 | **Current Chain** | How the customer walks the Big Job today; Tax Jobs marked |
| 5 | **Classify pains** | Each pain → Problem / Barrier / Tax Job / State-A emotion / fear |
| 6 | **Type the gaps** | Each gap → Core-Job / Barrier / chain-break / value + candidate mechanic |
| 7 | Tag confidence | Every Job/pain/gap → 🟢 observed / 🟡 inferred / 🔴 hypothesis |
| 8 | Detect misalignment | Where our team misunderstood the customer (sales gold) |
| 9 | Map decision dynamics | Champion / Blocker / Neutral / User + levers |
| 10 | Build emotional timeline | Energy spikes (Aha) and drops (Problems) |
| 11 | Score deal viability | X/12 (template §12) — *deal*, not product |
| 12 | Next steps + report | Specific actions; filled template |
| 13 | **Finishing gate** | Run `/jtbd` (Job headlines) + `/infostyle` (prose) on the finished report |

## Process Details

### Core Jobs (the primary unit)

A Job is `I want to {outcome} with {success criteria}` — verb-phrase plus **criteria**. Criteria are mandatory: without them you cannot judge coverage, design value, or detect a Problem. Format in the report: «Когда [контекст/триггер], я хочу [результат] с [критериями], чтобы [Big Job]».

- **Each verb is a separate Job.** Multi-verb statements («собирать логи И алертить») parse into levels: Core Job → Big Job above.
- **Orphan pain → raise the Job.** If a pain has no Job above its verb, the real Job is higher («собирает логи, но алертинг в следующем релизе» → Job is «действовать по логам», not «собирать»).
- **Ladder to the Big Job** — the motivational level above the Core Job («держать наблюдаемость без раздувания штата»). Record it per Job.
- Jobs come from customer words, not your interpretation. Criteria come from customer words too.

### Classify every pain (the fix depends on the class)

A flat «боль» is unusable downstream — different classes need different fixes. Classify each (legend in template §«Легенды»):

- **Problem** — a hired Solution performs the Job below criteria (complaint / negative emotion present). Fix: value or chain repair.
- **Barrier** — an objective fact makes the Job Graph non-executable (no SSO, region/registry unsupported, data format, missing integration). Fix: **reality work** — build it. A testimonial won't help.
- **Tax Job** — forced manual work the customer didn't choose (alert storms, manual dedup). Fix: kill the Job or take it off the customer.
- **State-A emotion** — anxiety / irritation *before* the result. Fix: remove the negative emotion.
- **fear** — prediction of a Barrier/Problem/loss. If accurate → it's a Barrier (§6). If not → messaging work.

### Current Chain

Reconstruct how the customer walks the Big Job **today**, step by step. Mark Tax Jobs — they are your kill-a-Job / take-the-Job-off-customer candidates (the «unautomated work»). A demo transcript often under-supplies this — mark `[INSUFFICIENT DATA]` rather than fabricate, and note what a depth-interview must recover.

### Type every gap (the `am-gap-analysis` feed)

For each Job we don't fully deliver, classify the gap (legend in template §6). The class sets the fix and the effort:

- **Core-Job gap** — we don't perform this Job at all → build.
- **Barrier** — we perform it but it's non-executable for this segment → reality (integration / cert / format / registry).
- **chain-break** — we perform the Core Job but the chain breaks before/after → repair the link.
- **value gap** — we perform it but below the customer's criteria → raise to criteria.

Attach a candidate mechanic (kill-a-Job / take-the-Job-off-customer / move-up-a-level / repair-chain / better-meet-criteria / remove-negative-emotion / exclusive-value) and an effort estimate (S/M/L).

### Confidence on every finding (epistemic governor)

Tag each Job, pain, and gap 🟢 observed / 🟡 inferred / 🔴 hypothesis. **A single demo is weak evidence** — most structural findings will be 🟡 or 🔴. Do not assert a Job structure or a product gap as settled when the data is a 50-minute demo. The downstream `am-gap-analysis` uses these tags to decide what needs a depth-interview before acting. Confident verdicts on thin data is the classic failure mode of this skill — resist it.

### Misalignment Detection

Often the most valuable *sales* finding. Common patterns:

- Customer uses a term → our team interprets differently → demo goes off-track
- Customer describes a need → our team shows an unrelated feature
- Customer's silence or lukewarm reaction → we're showing the wrong thing

Flag every instance with consequences (lost time, wrong feature shown).

### Next Steps

Each must have: **priority, action, effort estimate, owner, target date**. No generic advice — specific to THIS customer. Distinguish cheap sales-enabling actions (send link, prep reference sanitize) from expensive product actions (build RBAC) — the latter should reference the gap's confidence and usually wait for depth-interview.

### Finishing gate

Before declaring the report done, run it through two skills:

- **`/jtbd`** — on every Job-statement headline (template §3). Use it for *quality*: first-person, concrete felt scene, no stop-words (быстро/удобно/надёжно), benefit-led. **Keep the AJTBD slot semantics** — `я хочу [результат] с [критериями], чтобы [Big Job]`. Do not let `/jtbd` reformat the statement into its own `мотивация/результат` slots and drop the criteria. (`/jtbd` = Ильяхов job-story for headlines; ≠ AJTBD canon. The headline *form* comes from `/jtbd`; the criteria and 8-element structure come from canon. Don't blur them.)
- **`/infostyle`** — on all human-facing prose (§§1, 7–14). Fact over assessment, one idea per paragraph, de-anglicized, verb-first headings. For a cold independent read, dispatch the `infostyle-critic` agent on the report.

A structurally-correct but stiff or telegraphic report still fails — humans (sales, product) read this. The structural payload (§§3–6) and the prose quality are independent requirements; both must pass before the report ships.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| **Job without success criteria** | Criteria are mandatory — without them the Job can't be designed against or coverage-judged. Dig for the measurable «good enough». |
| **Flat «боль»** | Classify every pain (Problem/Barrier/Tax-Job/emotion/fear). The class decides the fix. |
| **Untyped gap** | Every gap gets a type (Core-Job/Barrier/chain-break/value) + candidate mechanic + effort. One `Gap` cell is not enough. |
| **No Current Chain** | Try to reconstruct the customer's today-process; mark Tax Jobs. Mark `[INSUFFICIENT DATA]` if the demo doesn't supply it — don't skip silently. |
| **Confident verdict on one demo** | Tag confidence honestly. Most structural findings are 🟡/🔴. Don't prioritize a build off a single presale demo. |
| Mixing pains with feature requests | Feature request = surface; pain = underlying need. Separate; the pain links to a Job. |
| Inferring too much | Mark inferred as `[INFERRED]` / `[AMBIGUOUS]` with your best interpretation. |
| Generic next steps | «Follow up» is useless — specific action with owner and deadline. |
| Duplicating across sections | Pain in §5 links to Job in §3, never repeats the same content. |
| Wrong report language | Match the transcript language (Russian → Russian, English → English). |

## Rules

- **Criteria are mandatory** on every Job — dig for the measurable «good enough» from customer words.
- **Classify every pain** and **type every gap** — the structural routing depends on it.
- **Tag confidence** on every Job/pain/gap — observed / inferred / hypothesis.
- **Quote verbatim** — exact customer words, with speaker and timestamp.
- **Don't guess** — mark ambiguity as `[AMBIGUOUS]` with your best interpretation.
- **Distinguish observed vs. inferred** — «Client said X» vs. «Client likely feels Y because…».
- **Epistemic humility** — a demo is weak evidence; don't assert structural findings as settled. Flag what needs depth-interview.
- **Keep Jobs grounded** — jobs and criteria come from customer words, not your interpretation.
- **Write in the language of the transcript** — Russian transcript = Russian report, English = English.
- **Output location.** Save product output under `PM/` per the routing test in `PM/CLAUDE.md` (theme-specific → `PM/initiatives/<theme>/`; competitive → `PM/competitive/`; untethered one-off → `PM/sessions/`; disposable → `PM/tmp/`). Client-conversation output usually belongs in `PM/customers/<client>/`. Never write product artifacts into `meta/` — `meta/` is meta-repo infrastructure only.
- **Финишный гейт.** Перед сдачей прогони артефакт по `/jtbd` (заголовки Jobs) и `/infostyle` (проза) — см. «Finishing gate» в Process Details. Структура и критерии — по AJTBD-канону; `/jtbd` отвечает только за качество формулировки, не за слот-семантику.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
