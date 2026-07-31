---
version: alpha
name: Astra Monitoring Release Dispatch
description: Visual identity for Astra Monitoring release-notes and changelog PDFs — an ops-console dispatch.
colors:
  console: "#03122e"
  panel: "#0c1830"
  hairline: "#243553"
  ink: "#eaf0fb"
  ink-body: "#cfd6e4"
  ink-dim: "#9aa4bd"
  primary: "#009cfe"
  ok: "#43f0a8"
  alarm: "#ff5b5b"
  code-well: "#1b2a4a"
  code-ink: "#cfe6ff"
typography:
  dispatch-title:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: -0.01em
  section-flag:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: 700
    lineHeight: 1
    letterSpacing: 0.14em
  feature-head:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.55
  mono:
    fontFamily: "JetBrains Mono"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
  meta-caps:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.08em
rounded:
  none: 0
  sm: 2px
  token: 4px
spacing:
  base: 8px
  inset: 12px
  gutter: 16px
  rail: 48px
  module-gap: 14px
  page-x: 56px
  page-top: 49px
  page-bottom: 49px
components:
  dispatch-masthead:
    backgroundColor: "{colors.console}"
    textColor: "{colors.ink}"
    typography: "{typography.dispatch-title}"
  hairline-rule:
    backgroundColor: "{colors.hairline}"
    height: 1px
  section-flag:
    textColor: "{colors.primary}"
    typography: "{typography.section-flag}"
  feature-module:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-body}"
    typography: "{typography.body}"
  feature-head:
    textColor: "{colors.ink}"
    typography: "{typography.feature-head}"
  code-token:
    backgroundColor: "{colors.code-well}"
    textColor: "{colors.code-ink}"
    typography: "{typography.mono}"
    rounded: "{rounded.token}"
  status-ok:
    textColor: "{colors.ok}"
    typography: "{typography.meta-caps}"
  status-alarm:
    textColor: "{colors.alarm}"
    typography: "{typography.meta-caps}"
---

## Overview

This is the dispatch an on-call ops team prints and pins next to the console. A
release log read from the monitoring bridge itself — the product reporting its own
evolution to the operator who runs it, in the same dark register the operator
already works in.

The audience is administrators, SREs, and security officers in regulated
enterprises. They did not open this document to be sold to. They opened it to
learn what changed, where to look, and what will break on upgrade. The dispatch's
job is to deliver that with the precision and density of a watch log, not the
seduction of a launch issue.

Character: **austere, exact, self-possessed**. Dense by design — whitespace is
the remainder of a packed page, never a styling gesture. The console's deep navy
is the page, because the page is a slice of the console. Nothing glows, nothing
bounces, nothing is arranged to look impressive at first glance.

## Colors

A single-ink system with one operational accent. Color is information, not
decoration; it is spent sparingly so that where it appears, it means something.

- **Console {colors.console}** is the page. Deep navigation navy. Never pure
  black — pure black reads as a creative-coding exercise, not an instrument.
- **Panel {colors.panel}** is a tonal step up, used only where a module must read
  as a contained surface against the console.
- **Hairline {colors.hairline}** is the structural rule — the only divider
  between modules. It is the single most important visual element: the dispatch
  is built from hairlines.
- **Ink {colors.ink}** carries headings and the masthead title. **Ink-body
  {colors.ink-body}** carries prose. **Ink-dim {colors.ink-dim}** is reserved for
  metadata and labels — never running text.
- **Primary {colors.primary}** is the sole accent — in the operator's register
  it is *Signal*. It marks *structure*, not promotion: section flags, hairline
  accents, the feature-head rail. It never appears on a number to make the number
  feel bigger.
- **OK {colors.ok}** and **Alarm {colors.alarm}** are operational states, used
  only where the content is genuinely a status (resolved, fixed, security). They
  are not decorative variety.

## Typography

Two voices. **Inter** for the narrative; **JetBrains Mono** for data, commands,
and anything the operator would type or copy. If a string belongs in a terminal,
it is set in mono — this is the single most reliable signal that the document
respects its reader.

- **dispatch-title** is modest on purpose: ~22px. This is not a magazine cover;
  a title that shouts is a title that doesn't trust its content.
- **section-flag** is a small uppercase caps flag with wide tracking — the
  register of a labeled switch on a control panel, not a headline.
- **feature-head** is a quiet 15px heading. Hierarchy comes from the accent rail
  beside it, not from size. Trust modest size differences.
- **body** is 13px and dense. Long line lengths are acceptable here; operators
  read for content, not comfort.
- **meta-caps** is for eyebrows, version stamps, and table-like labels — always
  uppercase, always tracked.

## Layout & Spacing

The console is the whole sheet — {colors.console} runs **full-bleed to every
edge of the page**, edge to edge. There is no white document margin around it: a
dark sheet inside a white frame reads as a screenshot pasted onto paper, not a
console. Edge-to-edge navy is non-negotiable.

Because the fill is full-bleed, the text inset is carried by a single **sheet**
wrapper, not by `@page` margins. Horizontal text inset is {spacing.page-x}
(≈15mm — the gutter of a log sheet); top and bottom insets are
{spacing.page-top} / {spacing.page-bottom}. The sheet's padding is **cloned at
every page break** so the inset holds on every page, not only the first.

A modular dispatch grid sits inside the sheet. The page is a single column;
vertical rhythm is tight, governed by {spacing.module-gap}.

- Modules (features, change groups) are separated by **hairline-rules**, not by
  blank space.
- The masthead appears **once**, at the top of the first page. It does not
  repeat. There is no running header, no page chrome, no logo on every page —
  this is a dispatch, not stationery.
- Pages may end partway down. A page that ends two-thirds of the way is correct,
  not under-filled.

## Elevation & Depth

Depth is **tonal, never shadowed**. The console sits beneath the panel sits
beneath the ink — three flat values, no blur, no glow, no drop shadow. Anything
that resembles glassmorphism or a "diamond-ring" effect is a category error for
this register and is rejected on sight.

## Shapes

**Architectural sharpness.** Corners are near-square: {rounded.sm} on tokens,
{rounded.token} on code wells, and nothing larger. There are no pills, no
generous curves, no rounded-xl surfaces. Roundness softens; an instrument does
not soften.

## Components

- **dispatch-masthead** — logo mark, a version stamp in meta-caps, a single
  hairline. One-time. Never a banner across every page.
- **section-flag** — a small caps label (KEY CHANGES / IMPROVEMENTS / FIXES /
  SECURITY) sitting on a hairline, marking a module group.
- **feature-module** — a feature-head on its accent rail, a tight body paragraph,
  and a list of capabilities. The atomic unit of the dispatch.
- **code-token** — inline mono (`amctl`, `relabel_configs`, `-f json`) on the
  code-well surface. Anything copy-pasteable lives here.
- **status-ok / status-alarm** — operational labels only, used where the content
  is a state, never as color-coding for emphasis.
- **header-mark** — the wordless AM sign (no wordmark), small, top-right of every
  inner page. Chrome, not content. Never on the first page — the masthead owns it.
- **page-number** — a centered `n / N` footer on every page when the doc has more
  than one page. Set small in ink-dim; it is wayfinding, not typography.

## Do's and Don'ts

- **Don't** build a magazine cover. No oversized display title, no hero block, no
  full-bleed title page. The first page is the first page of content.
- **Don't** use a drop cap. That is the editorial register; this is the
  operational register.
- **Don't** turn release counts (3 / 154 / 1) into big stat tiles. Numbers are
  stated in the line, in body weight. Inflating them is sales, not reporting.
- **Don't** repeat the full wordmark logo or the masthead on inner pages. Inner
  chrome is exactly two things: the small wordless **header-mark** top-right and a
  centered **page-number** bottom. No titles, no rules stamped across the top of
  every page.
- **Don't** introduce gradients, glows, glass surfaces, drop shadows, or rounded-xl
  corners. The console is flat and sharp.
- **Don't** use the accent color to make a number or a word feel important. Signal
  marks structure and status — nothing else.
- **Do** build the page from hairlines. When in doubt about how to separate two
  things, the answer is a 1px rule.
- **Do** set every command, flag, path, and label in mono. If the operator would
  type it, it is mono.
- **Do** trust dense pages and partial pages. An under-filled page is honest; a
  padded page is not.
- **Do** keep the masthead to the first page only.
