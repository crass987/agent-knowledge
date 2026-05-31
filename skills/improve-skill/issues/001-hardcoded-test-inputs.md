---
id: 001
title: eval_generator.py uses hardcoded test inputs unrelated to skill type
severity: high
status: open
discovered: 2026-05-31
skill-affected: am-pain-mining (and all file-based skills)
component: lib/eval_generator.py
---

# Bug: Hardcoded test inputs from video-knowledge-extraction

## Description

`eval_generator.py` generates wrong test inputs for file-based skills. Instead of finding files relevant to the skill's domain, it uses a hardcoded default path pointing to the video-knowledge-extraction skill's directory, and falls back to searching the entire `knowledge-base` for any `.txt/.md` file regardless of content type.

## Root cause

Two functions in `lib/eval_generator.py`:

### 1. `DEFAULT_TEST_FILE` constant (line 36-39)

```python
DEFAULT_TEST_FILE = (
    "/Users/CraSS/Documents/knowledge-base/videos/"
    "5-claude-code-skills-every-day/transcript.txt"
)
```

This is a video transcript file from the video-knowledge-extraction domain. It is used as the primary test input for **every** file-based skill.

### 2. `_build_test_inputs()` (line 259-291)

For `archetype == "file"`:
- Primary input: uses `DEFAULT_TEST_FILE` (or `_find_shortest_test_file()` if missing)
- Secondary input: `_find_second_test_file()` picks the file closest to 2× the primary's size

Neither function considers **what kind of file the skill actually processes**.

### 3. `_find_shortest_test_file()` (line 294-313)

Falls back to finding the **shortest** `.txt/.md/.srt/.vtt` file in the entire `knowledge-base` directory, with no filtering by skill domain or content type.

## Impact

When running `improve-skill` on `am-pain-mining` (a meeting/demo transcript analysis skill), the auto-generated `evals.json` contained:

| What happened | Value |
|---|---|
| Primary test input | `knowledge-base/videos/software-fundamentals-matter-more-than-ever/source/URL-reference.md` — a 162-byte URL reference card |
| Secondary test input | `knowledge-base/videos/5-claude-code-skills-matt-pocock/source/URL-reference.md` — another URL reference card |
| Both files | From video-knowledge-extraction domain, **not meeting transcripts** |

The assertions generated from these inputs were equally useless:
- `a01`: checks if output contains the word "Write" (from rule "Write in the language of the transcript")
- `a02`: checks if output does NOT contain the word "guess"
- `a04`: checks if output has markdown headers (regex `^#{1,3}\s+\S+`)

None of these test whether the skill actually produces a quality pain report.

## Evidence

The generated evals.json (before manual fix):

```json
{
  "test_inputs": [
    {
      "type": "file",
      "path": "/Users/CraSS/Documents/knowledge-base/videos/software-fundamentals-matter-more-than-ever/source/URL-reference.md",
      "label": "am-pain-mining primary file"
    },
    {
      "type": "file",
      "path": "/Users/CraSS/Documents/knowledge-base/videos/5-claude-code-skills-matt-pocock/source/URL-reference.md",
      "label": "am-pain-mining secondary file"
    }
  ]
}
```

## Fix suggestions

### Option A: Skill-specific test input hints (minimal change)

Add a `test_input_dir` or `test_input_paths` field to SKILL.md frontmatter that `eval_generator.py` reads:

```yaml
---
name: am-pain-mining
description: ...
test_inputs:
  - path: /path/to/meeting-transcripts/
  - pattern: "*.txt"
---
```

The generator would look for files matching these paths/patterns first, and only fall back to the current behavior if no hints are provided.

### Option B: Content-type-aware search (medium change)

Instead of searching the entire `knowledge-base`, correlate the skill's description and keywords with directory names in `knowledge-base`:

1. Extract key nouns from skill description ("meeting", "demo", "transcript", "pain", "customer")
2. Match against directory/file names in `knowledge-base`
3. Pick files whose content matches the skill's input format

### Option C: Interactive fallback (safe default)

When `_build_test_inputs()` can't find a clearly relevant file, print a warning to stderr:

```
WARNING: No skill-specific test input found. Using generic file.
Consider adding test_inputs to SKILL.md frontmatter or providing a --test-input flag.
```

## Workaround

Hand-write `evals.json` with correct `test_inputs.path` pointing to a real meeting transcript. This is what was done for the am-pain-mining run on 2026-05-31.

## Affected skills

Any skill classified as `archetype == "file"` by `detect_archetype()` is affected. The function triggers on these keywords in the skill description:

```python
FILE_PROCESSING_KEYWORDS = [
    "file", "url", "transcript", "video", "audio", "book", "document",
]
```

Skills whose descriptions contain "transcript", "video", "audio", "file", or "document" will all get test inputs from `knowledge-base/videos/` regardless of their actual domain.
