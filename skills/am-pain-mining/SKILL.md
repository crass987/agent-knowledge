---
name: am-pain-mining
description: Use when analyzing a customer meeting transcript or demo recording — extract pains, Jobs To Be Done, objections, buying signals, and competitive context. Triggers on "проанализируй встречу", "demo analysis", "pains from transcript", "extract pains", "customer meeting".
---

# Pain Pattern Mining

## Overview

Extract structured customer intelligence from demo/meeting transcripts. Produces a `pain-report` artifact with JTBD, objections, buying triggers, misalignment detection, and actionable next steps.

Grounded in Geoffrey Moore's Bowling Alley framework: the goal is to identify patterns that reveal the **headpin niche** — the segment with the strongest compelling reason to buy.

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
| **Video/Audio** | User should provide transcript. If video given, suggest manual transcription or use video-knowledge-extraction skill. |

**Speaker identification:** If transcript has speaker labels, preserve them. If not, infer roles from context (presenter vs. customer), flag with [INFERRED].

## Process

### 1. Parse and segment

- Read the full transcript
- Identify speaker roles (our team vs. customer)
- Mark major sections: intro, demo, Q&A, pricing, closing
- Note timestamps for key moments

### 2. Extract raw signals

Go through the transcript and extract:

- **Pains:** Complaints, frustrations, problems. Tag as "явная" (explicitly stated) or "вероятная" (implied from tone, context, hesitation)
- **Feature requests:** Specific asks — separate from the underlying need
- **Objections:** Pushback, skepticism, comparison with alternatives
- **Buying triggers:** Moments of genuine interest, excitement, forward-looking questions
- **Competitive references:** Mentions of other tools, past solutions, competitors
- **Decision signals:** Who decides, how they buy, budget hints, deadline mentions

### 3. Convert pains to Jobs To Be Done

For each significant pain, formulate a JTBD statement:

> "Когда [ситуация], я хочу [мотивация], чтобы [результат]"

Classify each job:
- **Functional** — get something done
- **Emotional** — feel something (confidence, control, safety)
- **Social** — be perceived a certain way by others (compliance, modern team)

Prioritize jobs by: frequency × intensity × connection to buying decision.

**Important:** JTBD is the PRIMARY section. Pains are secondary — short list, linked to jobs. Don't duplicate the same content in both sections.

### 4. Detect misalignment

Watch for moments where our team misunderstood what the customer meant. Common patterns:
- Customer uses a term → our team interprets it differently → demo goes off-track
- Customer describes a need → our team shows an unrelated feature
- Customer's silence or lukewarm reaction → we're showing the wrong thing

This is often the most valuable finding. Flag every instance.

### 5. Map competitive context

For every mention of another tool (Zabbix, Datadog, Icinga, PRTG, homemade):
- Why did they bring it up? (comparison, nostalgia, justification, alternative)
- What does that tool do well that we don't?
- What do we do well that it doesn't?
- Who brought it up? (champion vs. blocker)

### 6. Map decision dynamics

Identify each customer participant's role and stance:
- **Champion** — wants our product, will advocate internally
- **Blocker** — opposes, has alternative preference
- **Neutral** — watching, not committed either way
- **User** — will use the product but doesn't decide

### 7. Build emotional timeline

Map energy/engagement across the meeting. Note where it spiked (what sells) and where it dropped (what blocks). This directly feeds sales strategy.

### 8. Оценка перспективности ("Стоит ли вкладываться")

Четыре критерия, каждый 0-3. Сумма = итог X/12.

| Критерий | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **Внутренний advocate** | Никто не поддерживает | Кто-то проявил интерес | Есть явный сторонник | Сторонник = ЛПР |
| **Сила боли** | Не озвучена | "Было бы неплохо" | Реальная проблема | "Надо срочно решить" |
| **Готовность продукта** | Не решает их задачу | Частично, есть gaps | Почти готов, мелкие gaps | Решает main ask |
| **Угроза конкурентов** | Есть сильная бесплатная замена | Конкурент уже в оценке | "У нас и так работает" | Нет реальной альтернативы |

Интерпретация: 0-4 = не тратить время, 5-7 = доработать и follow-up, 8-9 = активно двигать, 10-12 = закрывать.

Каждый балл сопровождается комментарием "почему."

### 9. Produce the report

Use the template in `report-template.md`. Fill every section. If information is missing, mark explicitly — don't skip.

### 10. Generate next steps

Each next step must have: priority, action, effort estimate, owner, target date. No generic advice.

## Rules

- **Quote verbatim** — use exact customer words, with speaker and timestamp
- **Don't guess** — mark ambiguity as [AMBIGUOUS] with your best interpretation
- **Distinguish observed vs. inferred** — "Client said X" vs. "Client likely feels Y because..."
- **Prioritize ruthlessly** — score by frequency × intensity × buying connection
- **No generic advice** — next steps must be specific to THIS customer
- **Keep JTBD grounded** — jobs come from customer words, not your interpretation
- **Write in the language of the transcript** — Russian transcript = Russian report, English = English
- **No mixed scripts** — if writing in Russian, use only Cyrillic/Latin characters. No CJK, no Arabic, etc.
