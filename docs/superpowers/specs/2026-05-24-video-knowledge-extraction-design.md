# Video Knowledge Extraction — Design Spec

**Date:** 2026-05-24
**Status:** Draft
**Based on:** `skills/book-knowledge-extraction/SKILL.md`

---

## Overview

A standalone skill for extracting structured knowledge from YouTube videos and local video files. Reuses the cognitive quality framework from the book skill, but rebuilds the pipeline around video's unique characteristics: dual-channel content (audio + visual), lower information density, and temporal structure (timestamps instead of pages).

## Scope

- **Input:** YouTube URL, local video file (.mp4, .mkv, .mov), audio file (.mp3, .m4a), or pre-existing transcript (.srt, .vtt, .txt)
- **Output:** Russian-language knowledge document with original-language quotes and timestamps
- **Unit of work:** Single video (no playlists or channels)
- **Video types:** All formats — educational, interviews, reviews, tutorials, vlogs, shorts

---

## Architecture: 4-Phase Pipeline

```
Phase 0: Source Acquisition  ← Video-specific (dual-channel extraction)
Phase 1: Content Mapping     ← Adapted (infers structure instead of reading TOC)
Phase 2: Knowledge Extraction ← Same intellectual framework, adapted for video
Phase 3: Output              ← Adapted (timestamps, compression, visual references)
```

---

## Phase 0: Source Acquisition

### Input Matrix

| Source | Audio channel | Visual channel | Tools |
|--------|--------------|----------------|-------|
| YouTube URL | yt-dlp subtitles → Whisper fallback | yt-dlp thumbnails + keyframe extraction | yt-dlp, ffmpeg |
| Local video (.mp4, .mkv, .mov) | Whisper transcription | Keyframe extraction via ffmpeg | Whisper, ffmpeg |
| Transcript (.srt, .vtt, .txt) | Direct read | Not available (unless video also provided) | Read tool, MCP vision |
| Audio only (.mp3, .m4a) | Whisper transcription | Not available | Whisper |

### Audio Channel Pipeline

1. Check for existing subtitles first (yt-dlp `--list-subs`)
2. If available: download `.vtt`/`.srt`, clean HTML timestamp artifacts
3. If not: extract audio → Whisper (`base` for speed, `large` for technical/multilingual)
4. Output: clean timestamped transcript (sentence-level granularity)

### Visual Channel Pipeline

1. Extract keyframes: every 60 seconds + on scene change detection (ffmpeg `scene=0.3`)
2. Analyze keyframes with MCP vision tools (`analyze_image`, `extract_text_from_screenshot`)
3. Classify each visual frame: diagram/chart, code on screen, slide presentation, demo, talking head (ignore)
4. Output: Visual moment index `{timestamp} → {type} → {description}`

### Quality Gate (before Phase 1)

- Transcript is clean (no HTML subtitle artifacts, no Whisper repeats)
- Visual index classifies each extracted frame (no empty entries)
- Duration and estimated speaker count determined

---

## Phase 1: Content Mapping

Unlike books, videos lack a table of contents. The skill must *infer* structure.

### 1.1 Video Type Classification

| Type | Description | Extraction strategy |
|------|-------------|---------------------|
| **Lecture/Educational** | Single speaker teaches a topic | Temporal topics, slides as structural markers |
| **Interview/Podcast** | Two or more speakers in conversation | Topic turns, agreement/disagreement points, questions |
| **Review/Analysis** | Evaluating a product/idea/event | Evaluation criteria, conclusions, recommendations |
| **Tutorial/Demo** | Step-by-step demonstration | Action sequence, visual demonstrations as primary knowledge |
| **Vlog/Narrative** | Personal story, experience | Timeline, key turning points, lessons learned |
| **Short/Clip** | Under 3 minutes, high density | Single topic, quick extraction |

### 1.2 Structure Inference (Virtual Chapters)

From the transcript, identify topical segments:
- Look for transition phrases ("Now let's talk about...", "Moving on to...")
- Visual changes (new slide, demo switch) as segment boundaries
- For interviews: speaker changes as potential boundaries
- Output: List of topical segments with start/end timestamps

Format:

```markdown
## Virtual Chapters

- [00:00–02:30] Introduction and context
- [02:30–08:15] Core concept: X
- [08:15–12:00] Case study: Y
- [12:00–15:00] Practical application
- [15:00–18:30] Q&A / Discussion
```

### 1.3 Information Density Assessment

Evaluate what portion of the video is actual content vs. filler:
- Signal-to-noise ratio: how much transcript contains novel knowledge vs. repetition/filler
- This drives the *compression level* for Phase 2 — low-density videos are compressed more aggressively

---

## Phase 2: Knowledge Extraction

### 2.1 Cognitive Quality Checks (reused from book skill)

The same 4 principles, applied to video content:

| Principle | Application |
|-----------|-------------|
| **Context & Applicability** | Who is this for, in what situation, for what purpose |
| **Utility Taxonomy** | Functional / Social / Psychological |
| **Actionable Syntax** | Concrete, visualizable, "subject + verb + object" grammar |
| **Armament Test** | Can this be used as an argument in a discussion? |

No changes — these are medium-independent.

### 2.2 Extraction Categories (video-adapted)

| Category | Video adaptation |
|----------|-----------------|
| **Main ideas** | Compress repetitions — speakers repeat key points 2-3 times. Extract once. |
| **Problems** | Note where in the video the problem is visually demonstrated (demo, example) |
| **Assumptions** | In video, assumptions are often implicit — speaker takes them for granted without stating |
| **Consequences** | Same |
| **Methodology** | For tutorials/demos: the visual sequence IS the methodology. Extract steps from visual channel, not just speech. |
| **Insights** | Tag whether the insight was verbal (spoken) or visual (shown) |

### 2.3 Compression Principle

**Rule:** The knowledge document must be denser than the source video. A 30-minute video should produce a knowledge document readable in 3-5 minutes.

This is the key differentiator from the book skill, where the knowledge document is ~1:10 the size of the book. Video's lower information density means the compression ratio must be higher (~1:6 to 1:10 of reading time).

Apply compression by:
- Removing verbal filler, tangents, repetitions
- Converting spoken-word phrasing into written-form precision
- Consolidating the same idea expressed multiple times into one clear statement
- Preserving only unique, actionable knowledge

---

## Phase 3: Output

### Knowledge Document Template

```markdown
# {Video Title} — Knowledge Document

## Metadata
- **Source:** YouTube URL / local file path
- **Channel:** Channel name
- **Published:** Date
- **Duration:** XX:XX
- **Type:** Lecture / Interview / Review / Tutorial / Vlog / Short
- **Density:** High / Medium / Low
- **Language:** Original language

## Summary (3-5 sentences)
[Concise overview of what knowledge the video delivers]

## Virtual Chapters
- [MM:SS–MM:SS] Topic 1
- [MM:SS–MM:SS] Topic 2
...

## Main Ideas
[Extracted, compressed, with source labels: 🗣 verbal / 👁 visual]

## Problems and Solutions

## Methodology in Action
[For tutorials/demos: step sequence from visual + audio channel]

## Key Insights

## Visual Knowledge
[Diagrams, schemas, demos — described or linked to extracted keyframe files]

## Applicability
[Who, in what situation, for what purpose]
```

### Key Differences from Book Template

1. **Timestamps instead of page numbers** — every piece of knowledge traces back to when it appeared
2. **Visual Knowledge section** — visual content is first-class knowledge, not just "images"
3. **Source labels (🗣/👁)** — distinguish whether something was said or shown
4. **Summary upfront** — due to compression, reader needs a quick overview before diving into details
5. **No "narrative arc"** — most videos don't have the architectural narrative structure of books

### File Naming Convention

```
knowledge-base/
└── videos/
    └── {video-title}/
        ├── source/
        │   └── {video-file or URL-reference.md}
        ├── transcript.txt
        ├── keyframes/                # Extracted frames (if visual content matters)
        │   ├── 00-02-30_diagram.png
        │   └── 00-15-00_demo.png
        └── {video-title}_knowledge.md
```

Flat structure: `videos/{video-title}/`. Channel name, publish date, URL and other metadata live in the knowledge document metadata, not in the path. The video title is the primary organizer — what matters is *what* the video is about, not *who* uploaded it.

---

## Quality Checklist

### Before Extraction
- [ ] Source acquired (transcript + visual index if video available)
- [ ] Video type classified
- [ ] Virtual chapters identified
- [ ] Information density assessed
- [ ] Original video saved in `source/`

### After Extraction
- [ ] Every knowledge item passes Armament Test
- [ ] Context defined (for whom, in what situation)
- [ ] Utility type defined (Functional/Social/Psychological)
- [ ] Compression principle applied (document is significantly denser than the video)

### After Structuring
- [ ] Knowledge document follows the template
- [ ] All categories filled (where applicable to video type)
- [ ] Metadata complete
- [ ] Practical applicability defined
- [ ] Document is readable and understandable without watching the video
- [ ] Original video/transcript preserved in `source/`

---

## Output Artifact

**Language:** Russian for the knowledge document, original-language quotes preserved as-is. Video titles and key terms in original language with Russian explanation.

**Files (in video folder):**
1. `{video-title}_knowledge.md` — extracted knowledge
2. `source/{original-file or URL-reference}` — source archive
3. `transcript.txt` — clean transcript (for reference/re-extraction)
4. `keyframes/` — extracted visual frames (if applicable)

**Readiness criteria:**
- Knowledge structured by categories
- Compression applied (3-5 min read for a 30-min video)
- Applicability conditions described
- Connections between ideas noted
- Document readable without the source video
- Original video/transcript preserved

---

## Tools

```bash
# YouTube: download subtitles and video info
yt-dlp --list-subs URL                    # check available subtitles
yt-dlp --write-sub --sub-lang en,ru URL   # download subtitles
yt-dlp --write-thumbnail URL              # download thumbnail

# Audio extraction
yt-dlp -x --audio-format mp3 URL          # extract audio
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3  # from local video

# Whisper transcription
whisper audio.mp3 --model base --language en --output_format txt
whisper audio.mp3 --model large --language en --output_format srt  # for timestamps

# Keyframe extraction
ffmpeg -i video.mp4 -vf "fps=1/60" keyframes/frame_%04d.png           # every 60s
ffmpeg -i video.mp4 -vf "select=gt(scene\,0.3)" keyframes/scene_%04d.png  # scene changes

# Transcript cleanup
sed 's/<[^>]*>//g' subtitles.vtt > clean.txt  # strip HTML tags from VTT
```

---

## Relationship to Book Skill

| Aspect | Book skill | Video skill |
|--------|-----------|-------------|
| Structure source | Provided by author (TOC) | Inferred by skill (virtual chapters) |
| Information density | High (written word) | Low (spoken word) → requires compression |
| Channels | Text only | Dual: audio + visual |
| Compression ratio | ~1:10 (pages) | ~1:6-1:10 (reading time) |
| Quality checks | Identical | Identical (medium-independent) |
| Output language | Russian + original | Russian + original |
| Naming hierarchy | author/title/ | title/ (flat) |
