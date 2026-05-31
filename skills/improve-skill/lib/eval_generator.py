"""
eval_generator — hybrid eval generation for improve-skill v2.

Reads a skill directory, extracts rules from SKILL.md (and reference .md files),
converts extractable rules into binary assertions, and returns a valid v2
evals.json dict.

Hybrid generation:
  Phase 1 (Heuristic): deterministic regex-based extraction of structural rules.
    Each assertion carries source_file (which file the rule came from) and
    generator="heuristic".
  Phase 2 (LLM): semantic extraction via _run_llm_extraction seam.
    Returns empty by default; SKILL.md handles the actual LLM call.

v2 schema changes from v1:
  - test_input (singular) → test_inputs (array, 2-3 per skill)
  - New field: source_file on each assertion (traces rule to originating file)
  - New field: generator on each assertion ("heuristic" or "llm")
  - New field: label on each test_input
  - version bumped to 2
  - Assertion deduplication by exact (type, check, value) pattern
"""

import json
import os
import re
from datetime import datetime, timezone


# ── Constants ─────────────────────────────────────────────────────────

FILE_PROCESSING_KEYWORDS = [
    "file", "url", "transcript", "video", "audio", "book", "document",
]

DEFAULT_TEST_FILE = (
    "/Users/CraSS/Documents/knowledge-base/videos/"
    "5-claude-code-skills-every-day/transcript.txt"
)

VALID_CHECK_TYPES = {"regex", "not_regex", "contains", "not_contains", "max_words", "min_words"}


# ── Public API ────────────────────────────────────────────────────────

def detect_archetype(skill_dir: str) -> str:
    """
    Classify a skill as 'file' (file-processing) or 'prompt' (prompt-based).

    Detection logic:
    - Read SKILL.md's YAML frontmatter 'description' field
    - If description mentions file-processing keywords → 'file'
    - Otherwise → 'prompt'
    """
    skill_md = _read_skill_md(skill_dir)
    if not skill_md:
        return "prompt"

    description = _extract_frontmatter_field(skill_md, "description") or ""
    full_text = skill_md.lower()

    # Check description first (most reliable signal)
    desc_lower = description.lower()
    for keyword in FILE_PROCESSING_KEYWORDS:
        if keyword in desc_lower:
            return "file"

    # Fallback: check if decision tree mentions file input branches
    if "file" in full_text and ("decision tree" in full_text or "input" in full_text):
        return "file"

    return "prompt"


def generate_evals(skill_dir: str) -> dict:
    """
    Generate a complete evals.json dict for the given skill directory.

    Steps:
    1. Read SKILL.md + reference .md files individually (for source_file tracing)
    2. Detect archetype (file vs prompt)
    3. Extract rules from each file (tracing source_file)
    4. Convert extractable rules to binary assertions (with source_file + generator)
    5. Build and return the evals.json structure
    """
    skill_md = _read_skill_md(skill_dir)
    # Prefer the name from SKILL.md frontmatter, fall back to directory name
    skill_name = _extract_frontmatter_field(skill_md or "", "name") or os.path.basename(os.path.normpath(skill_dir))

    # Read files individually for source_file tracing
    file_sources = _read_files_with_sources(skill_dir)

    archetype = detect_archetype(skill_dir)
    test_inputs = _build_test_inputs(archetype, skill_dir, skill_md or "")

    # Extract rules from each file, carrying source_file
    all_rules = []
    for source_file, content in file_sources:
        rules = _extract_rules(content)
        for r in rules:
            r["source_file"] = source_file
        all_rules.extend(rules)

    heuristic_assertions = _rules_to_assertions(all_rules)

    # LLM phase: semantic extraction for rules the heuristics missed
    llm_assertions = _run_llm_extraction(
        file_sources=file_sources,
        heuristic_assertions=heuristic_assertions,
        skill_name=skill_name,
    )
    # Ensure LLM assertions have generator="llm"
    for a in llm_assertions:
        a["generator"] = "llm"
        if "source_file" not in a:
            a["source_file"] = "SKILL.md"

    # Merge and deduplicate across both phases
    all_assertions = _deduplicate_assertions(heuristic_assertions + llm_assertions)

    evals = {
        "version": 2,
        "skill": skill_name,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "test_inputs": test_inputs,
        "assertions": all_assertions,
    }

    return evals


def find_skill_dir(skill_name: str, search_dirs: list[str]) -> str | None:
    """
    Find a skill directory by name across multiple search paths.
    Returns the first match, or None.
    """
    for search_dir in search_dirs:
        candidate = os.path.join(search_dir, skill_name)
        if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "SKILL.md")):
            return candidate
    return None


def validate_evals_schema(evals: dict) -> list[str]:
    """
    Validate an evals.json dict against the v2 schema.
    Returns a list of error strings (empty if valid).
    """
    errors = []

    # Top-level required fields
    if "version" not in evals:
        errors.append("Missing required field: version")
    if "skill" not in evals:
        errors.append("Missing required field: skill")

    # test_inputs (v2: array)
    if "test_inputs" not in evals:
        errors.append("Missing required field: test_inputs")
    else:
        test_inputs = evals["test_inputs"]
        if not isinstance(test_inputs, list) or len(test_inputs) == 0:
            errors.append("test_inputs must be a non-empty array")
        else:
            for i, ti in enumerate(test_inputs):
                prefix = f"test_inputs[{i}]"
                if "type" not in ti:
                    errors.append(f"{prefix} missing 'type'")
                elif ti["type"] not in ("file", "prompt"):
                    errors.append(f"{prefix}.type must be 'file' or 'prompt', got '{ti['type']}'")
                if ti.get("type") == "file" and "path" not in ti:
                    errors.append(f"{prefix} with type='file' must have 'path'")
                if ti.get("type") == "prompt" and "text" not in ti:
                    errors.append(f"{prefix} with type='prompt' must have 'text'")
                if "label" not in ti:
                    errors.append(f"{prefix} missing 'label'")

    # assertions
    if "assertions" not in evals:
        errors.append("Missing required field: assertions")
    else:
        for i, a in enumerate(evals["assertions"]):
            prefix = f"assertion[{i}]"
            for field in ("id", "description", "source_rule", "type"):
                if field not in a:
                    errors.append(f"{prefix} missing required field: {field}")

            # v2 required fields on assertions
            if "source_file" not in a:
                errors.append(f"{prefix} missing required field: source_file")
            if "generator" not in a:
                errors.append(f"{prefix} missing required field: generator")

            if "type" in a:
                if a["type"] not in VALID_CHECK_TYPES:
                    errors.append(f"{prefix} has invalid check type: {a['type']}")

                # Type-specific required fields
                if a["type"] in ("regex", "not_regex") and "check" not in a:
                    errors.append(f"{prefix} regex type requires 'check' field")
                if a["type"] in ("contains", "not_contains") and "value" not in a:
                    errors.append(f"{prefix} {a['type']} type requires 'value' field")
                if a["type"] in ("max_words", "min_words") and "value" not in a:
                    errors.append(f"{prefix} {a['type']} type requires 'value' field")

    return errors


def write_evals(skill_dir: str, evals: dict) -> str:
    """Write evals.json to the skill directory. Returns the file path."""
    path = os.path.join(skill_dir, "evals.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(evals, f, indent=2, ensure_ascii=False)
    return path


# ── Internal helpers ──────────────────────────────────────────────────

def _read_skill_md(skill_dir: str) -> str | None:
    """Read SKILL.md from a skill directory."""
    path = os.path.join(skill_dir, "SKILL.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _read_files_with_sources(skill_dir: str) -> list[tuple[str, str]]:
    """Read SKILL.md + references/*.md individually, returning (source_file_name, content) pairs."""
    sources = []

    skill_md = _read_skill_md(skill_dir)
    if skill_md:
        sources.append(("SKILL.md", skill_md))

    refs_dir = os.path.join(skill_dir, "references")
    if os.path.isdir(refs_dir):
        for fname in sorted(os.listdir(refs_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(refs_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    sources.append((f"references/{fname}", f.read()))

    return sources


def _extract_frontmatter_field(content: str, field: str) -> str | None:
    """Extract a field from YAML frontmatter (--- ... ---)."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    frontmatter = match.group(1)
    field_match = re.search(rf"^{field}:\s*(.+)$", frontmatter, re.MULTILINE)
    if field_match:
        return field_match.group(1).strip().strip('"').strip("'")
    return None


def _build_test_inputs(archetype: str, skill_dir: str, content: str) -> list[dict]:
    """Build the test_inputs array for v2 evals.json. Generates 2-3 inputs per skill."""
    skill_name = os.path.basename(os.path.normpath(skill_dir))
    description = _extract_frontmatter_field(content, "description") or ""

    if archetype == "file":
        inputs = []
        # Primary: the default/shortest test file
        path = DEFAULT_TEST_FILE
        if not os.path.exists(path):
            path = _find_shortest_test_file()
        inputs.append({"type": "file", "path": path, "label": f"{skill_name} primary file"})

        # Secondary: try to find another file of different size
        second = _find_second_test_file(path)
        if second:
            inputs.append({"type": "file", "path": second, "label": f"{skill_name} secondary file"})
        return inputs
    else:
        # Prompt-based: generate 2-3 prompts varying in specificity
        inputs = [
            {
                "type": "prompt",
                "text": f"Use the {skill_name} skill. {description}" if description else f"Run the {skill_name} skill with a typical input.",
                "label": f"{skill_name} basic prompt",
            },
            {
                "type": "prompt",
                "text": f"Apply the {skill_name} skill to a complex, realistic scenario. {description}" if description else f"Apply {skill_name} to a complex scenario.",
                "label": f"{skill_name} detailed prompt",
            },
        ]
        return inputs


def _find_shortest_test_file() -> str:
    """Find the shortest text file in the knowledge-base for test input."""
    kb_dir = "/Users/CraSS/Documents/knowledge-base"
    if not os.path.isdir(kb_dir):
        return DEFAULT_TEST_FILE  # return default even if missing

    shortest = None
    shortest_size = float("inf")
    for root, dirs, files in os.walk(kb_dir):
        for f in files:
            if f.endswith((".txt", ".md", ".srt", ".vtt")):
                fpath = os.path.join(root, f)
                try:
                    size = os.path.getsize(fpath)
                    if size < shortest_size and size > 100:  # skip tiny files
                        shortest = fpath
                        shortest_size = size
                except OSError:
                    continue
    return shortest or DEFAULT_TEST_FILE


def _find_second_test_file(exclude_path: str) -> str | None:
    """Find a second test file of different size for variety."""
    kb_dir = "/Users/CraSS/Documents/knowledge-base"
    if not os.path.isdir(kb_dir):
        return None

    exclude_size = os.path.getsize(exclude_path) if os.path.exists(exclude_path) else 0
    candidates = []
    for root, dirs, files in os.walk(kb_dir):
        for f in files:
            if f.endswith((".txt", ".md", ".srt", ".vtt")):
                fpath = os.path.join(root, f)
                try:
                    size = os.path.getsize(fpath)
                    if size > 100 and fpath != exclude_path:
                        candidates.append((fpath, size))
                except OSError:
                    continue

    if not candidates:
        return None

    # Pick one closest to 2x the primary file's size (different but not extreme)
    target = exclude_size * 2
    candidates.sort(key=lambda c: abs(c[1] - target))
    return candidates[0][0]


def _generate_prompt_text(skill_name: str, description: str) -> str:
    """Generate a realistic test prompt for prompt-based skills."""
    # Use the skill's own description to craft a natural invocation
    if description:
        return f"Use the {skill_name} skill. {description}"
    return f"Run the {skill_name} skill with a typical input."


def _extract_rules(content: str) -> list[dict]:
    """
    Extract testable rules from SKILL.md content.

    Looks for:
    - Numbered lists of rules/constraints (e.g., "1. Never ...", "2. Always ...")
    - Bullet points with imperatives
    - Section headers that indicate format requirements
    - Explicit "must" / "never" / "always" statements
    - Bold-emphasized rules (**Rule.**)
    - Russian imperatives (не, должен, всегда, никогда, нельзя)

    Returns list of {"rule": str, "category": str} dicts.
    """
    rules = []

    # Extract numbered rules: "1. Some rule text"
    for match in re.finditer(r"^\d+\.\s+(.+)$", content, re.MULTILINE):
        rule_text = match.group(1).strip()
        if _is_testable_rule(rule_text):
            rules.append({"rule": rule_text, "category": "numbered"})

    # Extract bullet rules: "- Some rule text"
    for match in re.finditer(r"^\-\s+(.+)$", content, re.MULTILINE):
        rule_text = match.group(1).strip()
        # Skip common non-rule bullets (headers, section markers)
        if rule_text.startswith("#"):
            continue
        if rule_text.startswith("**") and rule_text.endswith("**"):
            continue
        # Strip bold markers for analysis
        clean = rule_text.strip("*").strip()
        if _is_testable_rule(clean):
            rules.append({"rule": clean, "category": "bullet"})

    # Extract bold-emphasized rules: "**Some rule.**" (common pattern in skill docs)
    for match in re.finditer(r"\*\*(.+?)\*\*", content):
        bold_text = match.group(1).strip()
        if len(bold_text) > 10 and _is_testable_rule(bold_text):
            rules.append({"rule": bold_text, "category": "bold"})

    # Extract English imperative statements from prose
    for match in re.finditer(r"(?:must|never|always|should|shall)\s+([^.]+\.)", content, re.IGNORECASE):
        full_match = match.group(0).strip()
        if _is_testable_rule(full_match):
            rules.append({"rule": full_match, "category": "imperative"})

    # Extract Russian imperative statements: negative forms (не + verb)
    # Pattern: "Не X" / "никогда не X" / "нельзя X" / "не должен X"
    for match in re.finditer(
        r"(?:не|никогда\s+не|нельзя|не\s*должен|запрещено)\s+([^.!?\n]+[.!?])",
        content, re.IGNORECASE
    ):
        full_match = match.group(0).strip()
        if len(full_match) > 10:
            rules.append({"rule": full_match, "category": "imperative"})

    # Extract Russian positive imperatives: "должен X" / "всегда X" / "обязательно X"
    for match in re.finditer(
        r"(?:должен|всегда|обязательно|нужно|необходимо)\s+([^.!?\n]+[.!?])",
        content, re.IGNORECASE
    ):
        full_match = match.group(0).strip()
        if len(full_match) > 10:
            rules.append({"rule": full_match, "category": "imperative"})

    # Deduplicate by normalized text
    seen = set()
    unique = []
    for r in rules:
        key = r["rule"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


def _is_testable_rule(text: str) -> bool:
    """Check if a rule text is potentially testable as a binary assertion."""
    if len(text) < 5:
        return False
    # Skip subjective rules
    subjective = ["compelling", "clear", "engaging", "beautiful", "elegant",
                  "intuitive", "natural", "interesting", "creative", "good",
                  "bad", "nice", "pretty", "simple (?!test)"]
    text_lower = text.lower()
    for word in subjective:
        if word in text_lower and not any(kw in text_lower for kw in
            ["must", "never", "always", "require", "format", "use ", "include"]):
            return False
    return True


def _run_llm_extraction(
    file_sources: list[tuple[str, str]],
    heuristic_assertions: list[dict],
    skill_name: str,
) -> list[dict]:
    """
    LLM semantic extraction phase: identify rules the heuristics missed.

    In Python, this is a stub that returns an empty list. The actual LLM call
    is handled by SKILL.md during eval generation, which writes additional
    assertions with generator="llm" to evals.json.

    This function exists as a seam for testing: tests can mock it to simulate
    LLM-generated assertions without making real API calls.

    Args:
        file_sources: list of (source_file, content) pairs for the skill
        heuristic_assertions: assertions already generated by the heuristic phase
        skill_name: name of the skill being evaluated

    Returns:
        List of assertion dicts with generator="llm". Empty by default.
    """
    return []


def _rules_to_assertions(rules: list[dict]) -> list[dict]:
    """
    Convert extracted rules into binary assertions.

    Each rule carries source_file; the assertion inherits it.
    All heuristic-generated assertions get generator="heuristic".
    Deduplicates by (type, check/value) — keeps the one with the longer description.
    """
    raw = []
    for rule_info in rules:
        rule = rule_info["rule"]
        source_file = rule_info.get("source_file", "SKILL.md")
        assertion = _rule_to_assertion(rule, 0)  # id assigned after dedup
        if assertion:
            assertion["source_file"] = source_file
            assertion["generator"] = "heuristic"
            raw.append(assertion)

    # Deduplicate: group by (type, check/value), keep most specific description
    return _deduplicate_assertions(raw)


def _deduplicate_assertions(assertions: list[dict]) -> list[dict]:
    """Deduplicate assertions by normalized check pattern. Keeps the one with the longer description."""
    best: dict[tuple, dict] = {}

    for a in assertions:
        key = _assertion_key(a)
        if key not in best:
            best[key] = a
        else:
            # Keep the one with the longer description (more specific)
            if len(a.get("description", "")) > len(best[key].get("description", "")):
                best[key] = a

    # Re-number IDs sequentially
    result = []
    for i, a in enumerate(best.values(), start=1):
        a["id"] = f"a{str(i).zfill(2)}"
        result.append(a)
    return result


def _assertion_key(assertion: dict) -> tuple:
    """Normalize an assertion to a dedup key: (type, check_or_value)."""
    check = assertion.get("check", "")
    value = str(assertion.get("value", ""))
    return (assertion["type"], check, value)


def _rule_to_assertion(rule: str, counter: int) -> dict | None:
    """
    Try to convert a single rule into a binary assertion.
    Supports English and Russian rule patterns.
    Returns None if the rule can't be converted.
    """
    id_str = f"a{str(counter).zfill(2)}"
    rule_lower = rule.lower()

    # Pattern: "Never X" / "No X" / "Не X" / "Никогда не X" → not_contains
    never_match = re.match(
        r"(?:never|no|don'?t|avoid|must not|should not"
        r"|не|никогда\s+не|нельзя|запрещено|не\s*должен)\s+(.+)",
        rule, re.IGNORECASE
    )
    if never_match:
        target = never_match.group(1).strip().rstrip(".")
        # Simple substring → not_contains
        if not any(c in target for c in r"()[]{}.*+?^$|\\"):
            return {
                "id": id_str,
                "description": f"Output must not contain: {target[:60]}",
                "source_rule": rule,
                "type": "not_contains",
                "value": target[:80],
            }

    # Pattern: format requirements (headers, sections, markdown) → regex
    if any(kw in rule_lower for kw in ["header", "heading", "section", "markdown", "#",
                                        "заголовок", "секци"]):
        return {
            "id": id_str,
            "description": "Output uses markdown headers",
            "source_rule": rule,
            "type": "regex",
            "check": r"^#{1,3}\s+\S+",
            "flags": "m",
        }

    # Pattern: word count / numeric limits → max_words / min_words
    # English: "N words" / Russian: "N слов" / General: "N items"
    word_match = re.search(r"(\d+)\s*(?:words?|items?|points?|слов|элемент)", rule_lower)
    if word_match:
        count = int(word_match.group(1))
        if any(kw in rule_lower for kw in ["max", "under", "less", "at most", "no more",
                                            "не более", "максимум", "до"]):
            return {
                "id": id_str,
                "description": f"Output word count ≤ {count}",
                "source_rule": rule,
                "type": "max_words",
                "value": count,
            }
        elif any(kw in rule_lower for kw in ["min", "at least", "more than",
                                              "минимум", "не менее", "от"]):
            return {
                "id": id_str,
                "description": f"Output word count ≥ {count}",
                "source_rule": rule,
                "type": "min_words",
                "value": count,
            }

    # Pattern: compression ratios "1:6", "~1:6" → not_regex for low compression
    ratio_match = re.search(r"~?(\d+):(\d+)", rule)
    if ratio_match:
        # This is a compression ratio — we can check output isn't too verbose
        # by checking min_words with a generous lower bound
        pass  # Skip for now — hard to make a useful binary check from this

    # Pattern: "must include/contain/use X" / "должен X" / "нужно X" → contains
    include_match = re.match(
        r"(?:must|should|always|need to|всегда|должен|нужно|необходимо)\s+"
        r"(?:include|contain|use|have|add|включ|содерж|использ|иметь|добав)\s+(.+)",
        rule, re.IGNORECASE
    )
    if include_match:
        target = include_match.group(1).strip().rstrip(".")
        if len(target) > 3 and len(target) < 80:
            return {
                "id": id_str,
                "description": f"Output includes: {target[:60]}",
                "source_rule": rule,
                "type": "contains",
                "value": target,
            }

    # Pattern: "Write tests first" / "Do X before Y" → contains (keyword presence)
    imperative_match = re.match(
        r"(?:write|run|use|follow|start|always|должен|нужно|необходимо)\s+(.+)",
        rule, re.IGNORECASE
    )
    if imperative_match:
        target = imperative_match.group(1).strip().rstrip(".")
        # Extract key noun/verb for a contains check (works for both EN/RU)
        key_phrases = re.findall(r"\b[A-ZА-ЯЁ][a-zA-Zа-яёА-ЯЁ]+\b", rule)
        if key_phrases:
            return {
                "id": id_str,
                "description": f"Output references: {key_phrases[0]}",
                "source_rule": rule,
                "type": "contains",
                "value": key_phrases[0],
            }

    # Pattern: "X ≠ Y" (not equal / differentiation rules) → not_contains
    # e.g., "визуальное знание ≠ визуальное подтверждение"
    neq_match = re.search(r"(\S+(?:\s+\S+)?)\s*≠\s*(\S+(?:\s+\S+)?)", rule)
    if neq_match:
        forbidden = neq_match.group(2).strip()
        return {
            "id": id_str,
            "description": f"Output must not contain: {forbidden[:60]}",
            "source_rule": rule,
            "type": "not_contains",
            "value": forbidden[:80],
        }

    # Can't convert — skip
    return None


# ── CLI smoke test ────────────────────────────────────────────────────

def main():
    """
    CLI: python3 eval_generator.py <skill_dir>
    Generates evals.json and prints to stdout.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: eval_generator.py <skill_dir>", file=sys.stderr)
        sys.exit(1)

    skill_dir = sys.argv[1]
    if not os.path.isdir(skill_dir):
        print(f"Error: {skill_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    evals = generate_evals(skill_dir)
    errors = validate_evals_schema(evals)
    if errors:
        print(f"Schema validation errors: {errors}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(evals, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
