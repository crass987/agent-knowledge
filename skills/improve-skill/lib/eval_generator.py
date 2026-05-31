"""
eval_generator — auto-generate evals.json from SKILL.md.

Reads a skill directory, extracts rules from SKILL.md (and reference .md files),
converts extractable rules into binary code-based assertions, and returns
a valid evals.json dict.

For v1, rule extraction uses deterministic heuristics (regex-based).
LLM-powered extraction can be layered on top in v2.
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
    1. Read SKILL.md + reference .md files
    2. Detect archetype (file vs prompt)
    3. Extract rules from skill content
    4. Convert extractable rules to binary assertions
    5. Build and return the evals.json structure
    """
    skill_md = _read_skill_md(skill_dir)
    # Prefer the name from SKILL.md frontmatter, fall back to directory name
    skill_name = _extract_frontmatter_field(skill_md or "", "name") or os.path.basename(os.path.normpath(skill_dir))
    reference_content = _read_reference_files(skill_dir)
    all_content = skill_md or ""

    archetype = detect_archetype(skill_dir)
    test_input = _build_test_input(archetype, skill_dir, all_content)

    # Extract rules and generate assertions
    rules = _extract_rules(all_content)
    assertions = _rules_to_assertions(rules, reference_content)

    evals = {
        "version": 1,
        "skill": skill_name,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "test_input": test_input,
        "assertions": assertions,
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
    Validate an evals.json dict against the expected schema.
    Returns a list of error strings (empty if valid).
    """
    errors = []

    # Top-level required fields
    if "version" not in evals:
        errors.append("Missing required field: version")
    if "skill" not in evals:
        errors.append("Missing required field: skill")

    # test_input
    if "test_input" not in evals:
        errors.append("Missing required field: test_input")
    else:
        ti = evals["test_input"]
        if "type" not in ti:
            errors.append("test_input missing 'type'")
        elif ti["type"] not in ("file", "prompt"):
            errors.append(f"test_input.type must be 'file' or 'prompt', got '{ti['type']}'")
        if ti.get("type") == "file" and "path" not in ti:
            errors.append("test_input with type='file' must have 'path'")
        if ti.get("type") == "prompt" and "text" not in ti:
            errors.append("test_input with type='prompt' must have 'text'")

    # assertions
    if "assertions" not in evals:
        errors.append("Missing required field: assertions")
    else:
        for i, a in enumerate(evals["assertions"]):
            prefix = f"assertion[{i}]"
            for field in ("id", "description", "source_rule", "type"):
                if field not in a:
                    errors.append(f"{prefix} missing required field: {field}")

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


def _read_reference_files(skill_dir: str) -> str:
    """Read all .md files from references/ subdirectory."""
    refs_dir = os.path.join(skill_dir, "references")
    if not os.path.isdir(refs_dir):
        return ""

    parts = []
    for fname in sorted(os.listdir(refs_dir)):
        if fname.endswith(".md"):
            fpath = os.path.join(refs_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                parts.append(f.read())
    return "\n\n".join(parts)


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


def _build_test_input(archetype: str, skill_dir: str, content: str) -> dict:
    """Build the test_input section of evals.json."""
    if archetype == "file":
        path = DEFAULT_TEST_FILE
        if not os.path.exists(path):
            # Fallback: try to find the shortest text file in knowledge-base
            path = _find_shortest_test_file()
        return {"type": "file", "path": path}
    else:
        # Generate a realistic prompt from the skill's name/description
        description = _extract_frontmatter_field(content, "description") or ""
        skill_name = os.path.basename(os.path.normpath(skill_dir))
        prompt = _generate_prompt_text(skill_name, description)
        return {"type": "prompt", "text": prompt}


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


def _rules_to_assertions(rules: list[dict], reference_content: str) -> list[dict]:
    """
    Convert extracted rules into binary assertions.

    Strategy:
    - Rules about format (headers, sections, structure) → regex/contains checks
    - Rules about what NOT to include → not_regex/not_contains checks
    - Rules about length → max_words/min_words checks
    - Rules about required content → contains checks

    For rules that can't be auto-converted, skip them.
    """
    assertions = []
    counter = 1

    for rule_info in rules:
        rule = rule_info["rule"]
        assertion = _rule_to_assertion(rule, counter)
        if assertion:
            assertions.append(assertion)
            counter += 1

    return assertions


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
