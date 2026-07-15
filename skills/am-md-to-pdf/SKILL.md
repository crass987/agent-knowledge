---
name: am-md-to-pdf
description: Use when converting a Markdown document to a polished dark-theme PDF — «сделай pdf из md», «красивый pdf из документа», «convert md to pdf». Renders via headless Chrome from a .md file.
---

# Markdown → Dark-Theme PDF

## Overview

Convert a `.md` file to a polished Astra-themed PDF (dark navy `#03122E`, blue accent `#009CFE`, Inter). One command: `convert.py` reads the `.md`, generates styled HTML, headless Chrome renders the PDF. Palette matches astra-monitoring.ru.

## The Iron Rule

**NEVER hand-transcribe the markdown into HTML.** Always run `convert.py` — it reads the `.md` and generates the HTML from it. Hand-transcribing is the single biggest failure mode: within a few edits the HTML drifts from the source (forgotten lines, paraphrased text, stale snapshots), the user catches it, and trust is gone. The converter eliminates this — the text comes straight from the `.md` every run.

If the output is wrong, **fix the `.md` and re-run**, never edit the HTML by hand.

## When to Use

- User wants a polished PDF from a `.md` doc — «красивый pdf», «сделай pdf из md».
- Producing a partner/customer-facing PDF from an internal `.md`.

## When NOT to Use

- Quick plain PDF → `pandoc` or browser print.
- The `.md` needs layout the converter can't do → **extend `convert.py`**, don't hand-build HTML.

## How to Run

```bash
python3 skills/am-md-to-pdf/scripts/convert.py <input.md> <output.pdf> \
  [--logo LOGO.svg] [--title "Title"] [--chrome PATH] [--keep-html]
```

- `--logo PATH` — logo top-left on every page (page 1: logo + title; inner: logo only). Passed as `file://`, so it renders fully — no truncation.
- **Canonical Astra Monitoring logo:** `PM/roadmap/logo-BKsrVIqB.svg` (path from the Astra meta-repo root). Always pass it for AM PDFs — without `--logo`, or with a wrong/invented path, the dark header has no logo. This is the usual «logo doesn't render» failure in other sessions.
- `--title TEXT` — page-1 title (default: first `# H1` in the `.md`).
- `--chrome PATH` — Chrome/Chromium binary (default: macOS Google Chrome).
- `--keep-html` — keep the intermediate `.html` next to the `.pdf`.

Prerequisites: Python 3 (stdlib only), Google Chrome / Chromium.

Example (Astra Monitoring roadmap PDF — note the `--logo` path):

```bash
python3 skills/am-md-to-pdf/scripts/convert.py \
  PM/strategy/jtbd-roadmap-external.md PM/strategy/jtbd-roadmap-external.pdf \
  --logo PM/roadmap/logo-BKsrVIqB.svg
```

## Verify After Rendering

The converter is faithful, but verify — rendering can still drop things:

```bash
# text: check key phrases from the .md are present
pdftotext <out.pdf> - | grep "<phrase from the .md>"
# visual: render a page to PNG
pdftoppm -png -r 80 -f 1 -l 1 <out.pdf> /tmp/check
```

## Layout (what the converter does)

- **Page break before each `## `** (except the first, which shares page 1 with the title). Each section stays whole — no mid-section fragmentation.
- **Header on every page**: page 1 = logo + title + accent bar; inner pages = logo + accent bar only (no repeated title), with top padding so content isn't glued to the edge.
- Blockquotes → blue callouts, tables styled, code blocks, lists — all `break-inside: avoid`.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Hand-edit HTML to "fix" text | Edit the `.md`, re-run `convert.py`. Never the HTML. |
| Logo missing/blank in header | Pass `--logo PM/roadmap/logo-BKsrVIqB.svg` (canonical Astra Monitoring logo). Skipping `--logo` or guessing a path → dark header with no logo. |
| Section splits across pages | It's longer than one page — shorten the `.md` section, or accept the clean split. |
| PDF stale after `.md` edits | Re-run `convert.py`. The `.md` is source; the PDF is build output. |

## Regeneration

The PDF is **derived** from the `.md`. After any `.md` edit, re-run `convert.py`. Commit both if you want the PDF tracked alongside the source.
