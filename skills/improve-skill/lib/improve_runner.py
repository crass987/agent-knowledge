"""
improve_runner — deterministic helper library for improve-skill v2.

The model stays the orchestrator (it reads SKILL.md prose and drives the loop).
This module holds the deterministic state + pure decisions the model calls so
it does NOT have to track counters "in its head": argument parsing, score
aggregation, target resolution, rule-string placement, stop conditions,
git operations, report formatting, and crash recovery.

Constraints (ADR 0001):
  - Pure Python, stdlib only. No `claude` CLI subprocess anywhere.
  - All LLM reasoning stays in SKILL.md; Python is for deterministic logic only.
  - Functions never raise on malformed LLM output — they return None / partial.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field, replace
from typing import Literal, Optional


# ── Dataclasses ───────────────────────────────────────────────────────


@dataclass
class LoopState:
    """Mutable-feel state carried across improvement iterations.

    update_state_from_action returns a NEW copy rather than mutating, so the
    orchestrator can treat state immutably and the "forgot to increment
    PLATEAU_COUNT" failure mode cannot occur.
    """
    iteration: int = 1
    prev_score: int = 0
    plateau_count: int = 0
    agent_calls: int = 0
    llm_calls: int = 0
    test_inputs_evaluated: int = 0
    baseline_scores: dict = field(default_factory=dict)  # assertion_id -> bool


@dataclass
class ParsedArgs:
    """Result of parsing /improve-skill invocation arguments."""
    all_skills: bool = False
    regen: bool = False
    dry_run: bool = False
    skill_names: list = field(default_factory=list)


@dataclass
class AggScore:
    """Aggregated score across all test outputs.

    An assertion is in `passed` IFF it passes on ALL outputs (set intersection);
    it is in `failed` if it fails on at least one output.
    """
    total: int = 0
    passed: list = field(default_factory=list)   # assertion ids passing on all
    failed: list = field(default_factory=list)   # assertion ids failing on any
    per_assertion: dict = field(default_factory=dict)  # id -> [bool per output]


@dataclass
class RulePlan:
    """Parsed LLM rule-generation response."""
    analysis: str = ""
    rule: str = ""
    section: str = ""
    position: str = ""


@dataclass
class StopDecision:
    """Outcome of the 3-condition stop check."""
    stop: bool
    reason: str  # "" | "ALL_PASS" | "PLATEAU" | "CAP"
    iteration: int


@dataclass
class AuditFindings:
    """Parsed LLM-as-judge audit response (Phase 4). Empty on malformed input."""
    quality_score: str = "F"  # A/B/C/D/F
    dimensions: dict = field(default_factory=dict)
    # dimensions[name] = {"score": int, "issues": str, "suggestions": str}
    recurring_problems: list = field(default_factory=list)


@dataclass
class RecoveryState:
    """Outcome of git-log crash-recovery parsing."""
    iteration: int = 1
    last_assertion_id: Optional[str] = None
    last_action: str = "unknown"  # "keep" | "revert" | "unknown"


# ── Phase 1: setup ────────────────────────────────────────────────────


def parse_args(argv: list) -> ParsedArgs:
    """
    Parse /improve-skill arguments.

    Flags: --all, --regen, --dry-run. Everything else is a skill name.
    Unknown tokens that aren't flags are treated as skill names (lenient).
    """
    flags = {"--all", "--regen", "--dry-run"}
    parsed = ParsedArgs()
    for token in argv or []:
        if token == "--all":
            parsed.all_skills = True
        elif token == "--regen":
            parsed.regen = True
        elif token == "--dry-run":
            parsed.dry_run = True
        elif token.startswith("--"):
            # unknown flag — ignore leniently
            continue
        else:
            parsed.skill_names.append(token)
    return parsed


def discover_all_skills(search_dirs: list) -> list:
    """
    Discover all skill names (directories containing SKILL.md) across search dirs.

    Returns sorted unique skill NAMES (not paths). Excludes improve-skill itself.
    """
    found = []
    seen = set()
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        try:
            entries = sorted(os.listdir(search_dir))
        except OSError:
            continue
        for name in entries:
            if name in seen:
                continue
            candidate = os.path.join(search_dir, name)
            if name == "improve-skill":
                # never improve the improver
                continue
            if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "SKILL.md")):
                seen.add(name)
                found.append(name)
    return sorted(found)


def load_or_regenerate_evals(skill_dir: str, this_dir: str, regen: bool,
                             _generate=None) -> dict:
    """
    Load evals.json for a skill, optionally regenerating it first.

    Wraps eval_generator.generate_evals. If regen is True, deletes the existing
    evals.json before regenerating. If the loaded file is not valid v2, it is
    regenerated.

    `_generate` is an injectable seam for testing (defaults to real
    eval_generator.generate_evals).
    """
    evals_path = os.path.join(skill_dir, "evals.json")

    if regen and os.path.exists(evals_path):
        os.remove(evals_path)

    if os.path.exists(evals_path):
        try:
            with open(evals_path, "r", encoding="utf-8") as f:
                evals = json.load(f)
        except (json.JSONDecodeError, OSError):
            evals = _do_generate(skill_dir, this_dir, _generate)
        else:
            if evals.get("version") != 2:
                evals = _do_generate(skill_dir, this_dir, _generate)
    else:
        evals = _do_generate(skill_dir, this_dir, _generate)

    return evals


def _do_generate(skill_dir, this_dir, _generate):
    if _generate is not None:
        return _generate(skill_dir)
    lib_dir = os.path.join(this_dir, "lib")
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    from eval_generator import generate_evals
    return generate_evals(skill_dir)


def make_branch_name(skill_name: str, taken: set) -> str:
    """
    Build an improvement branch name, suffixing -2, -3, ... on collision.

    Pure: does not touch the date. Callers wanting a date suffix should bake it
    into skill_name (e.g. "tdd-2026-07-21"). Collision suffix starts at -2.
    """
    base = f"improve/{skill_name}"
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


def create_branch(skill_dir: str, name: str) -> str:
    """
    Create and checkout a git branch in skill_dir. Thin git wrapper.

    Raises subprocess.CalledProcessError if the branch exists; callers should
    resolve collisions via make_branch_name first.
    """
    subprocess.run(
        ["git", "checkout", "-b", name],
        cwd=skill_dir, check=True, capture_output=True, text=True,
    )
    return name


# ── Phase 2 / 3d: score aggregation ───────────────────────────────────


def aggregate_scores(per_output: list) -> AggScore:
    """
    Aggregate per-output run_assertions results into a single score.

    An assertion passes IFF it passes on ALL outputs (set intersection of
    passed-id sets). It fails if it fails on at least one output.
    """
    if not per_output:
        return AggScore(total=0, passed=[], failed=[], per_assertion={})

    total = per_output[0].get("total", 0)

    passed_sets = []
    for r in per_output:
        passed_sets.append({p.get("id") for p in r.get("passed", [])})

    passed_all = set.intersection(*passed_sets) if passed_sets else set()

    # Union of all ids seen anywhere (passed or failed)
    all_ids = set()
    for r in per_output:
        for p in r.get("passed", []):
            all_ids.add(p.get("id"))
        for f in r.get("failed", []):
            all_ids.add(f.get("id"))

    failed_any = all_ids - passed_all

    # Per-assertion boolean matrix: id -> [bool per output in order]
    per_assertion = {}
    for r in per_output:
        passed_ids = {p.get("id") for p in r.get("passed", [])}
        for aid in all_ids:
            per_assertion.setdefault(aid, []).append(aid in passed_ids)

    return AggScore(
        total=total,
        passed=sorted(passed_all),
        failed=sorted(failed_any),
        per_assertion=per_assertion,
    )


def pick_target_assertion(agg: AggScore) -> dict:
    """
    Pick the first failing assertion (lowest id sort).

    Returns {"id": "aXX"} or {} if nothing is failing. The orchestrator enriches
    this with the full assertion record (source_file, description, ...) from
    evals.json by id before calling resolve_target_file.
    """
    if not agg.failed:
        return {}
    # Sort by id; ids are like "a02", "a10" — lexical sort works for zero-padded
    first = sorted(agg.failed)[0]
    return {"id": first}


# ── Phase 3a: target file resolution ──────────────────────────────────


def resolve_target_file(assertion: dict) -> str:
    """
    Resolve which file to edit for an assertion.

    Cascade: source_file (if a specific non-SKILL.md file) → SKILL.md.
    """
    source_file = assertion.get("source_file")
    if source_file and source_file != "SKILL.md":
        return source_file
    return "SKILL.md"


# ── Phase 3b: rule-response parsing ───────────────────────────────────


def parse_rule_response(text: str) -> Optional[RulePlan]:
    """
    Parse an LLM rule-generation response into a RulePlan.

    Expected fields: ANALYSIS, RULE, SECTION, POSITION (each `LABEL: value`).
    RULE is essential — without it, returns None. Never raises.
    """
    if not text:
        return None
    try:
        rule = _extract_field(text, "RULE")
        if not rule:
            return None
        section = _extract_field(text, "SECTION") or ""
        position = _extract_field(text, "POSITION") or ""
        analysis = _extract_field(text, "ANALYSIS") or ""
        return RulePlan(analysis=analysis, rule=rule, section=section, position=position)
    except Exception:
        return None


def _extract_field(text: str, label: str) -> Optional[str]:
    """Extract `LABEL: value` where value runs until the next ALL_CAPS label or EOF."""
    pattern = rf"{label}:\s*(.*?)(?=\n[A-Z][A-Z_]+:|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return None
    return m.group(1).strip()


# ── Phase 3c: rule formatting + injection ─────────────────────────────


def format_rule_marker(iteration: int, assertion_id: str, rule_text: str) -> str:
    """Build the traceability-wrapped rule block to inject into a .md file."""
    return (
        f"<!-- improve-skill: iteration {iteration}, assertion {assertion_id} -->\n"
        f"- {rule_text}\n"
        f"<!-- /improve-skill -->"
    )


def inject_rule(file_content: str, plan: RulePlan, block: Optional[str] = None) -> str:
    """
    PURE string function: place a rule block into file_content per plan.

    Placement logic honours POSITION (after / before / end of section). Code
    fences containing ## are NOT treated as headings. Frontmatter is preserved.

    `block` defaults to a plain "- {plan.rule}" bullet; the orchestrator passes
    a marker from format_rule_marker in production.
    """
    if block is None:
        block = f"- {plan.rule}"

    frontmatter, body = _split_frontmatter(file_content)

    new_body = _place_in_body(body, block, plan.section or "", plan.position or "")

    if frontmatter:
        return frontmatter + "\n" + new_body
    return new_body


def _split_frontmatter(content: str):
    """Split leading YAML frontmatter (--- ... ---) from body. Returns (fm_str, body)."""
    if not content.startswith("---"):
        return ("", content)
    # closing delimiter is a line that is exactly --- (or ----)
    m = re.match(r"^---[^\n]*\n.*?\n---[ \t]*\n", content, re.DOTALL)
    if not m:
        return ("", content)
    return (m.group(0), content[m.end():])


def _place_in_body(body: str, block: str, section: str, position: str) -> str:
    """Apply placement rules to the body (frontmatter already stripped)."""
    if body == "":
        return block if block.endswith("\n") else block + "\n"

    lines = body.splitlines(keepends=True)
    pos_lower = position.lower().strip()

    if pos_lower:
        if pos_lower.startswith("before"):
            target = _extract_quoted(position) or _strip_prefix(position, "before")
            idx = _find_line_index(lines, target)
            if idx is not None:
                return _splice(lines, idx, block, before=True)
        elif pos_lower.startswith("after"):
            target = _extract_quoted(position) or _strip_prefix(position, "after")
            idx = _find_line_index(lines, target)
            if idx is not None:
                return _splice(lines, idx, block, before=False)
        elif pos_lower.startswith("end of section"):
            target = _extract_quoted(position) or _strip_prefix(position, "end of section")
            idx = _find_section_end_index(lines, target or section)
            if idx is not None:
                return _splice(lines, idx, block, before=False)

    # Section-only placement (no position, or position not matched): end of section.
    if section:
        idx = _find_section_end_index(lines, section)
        if idx is not None:
            return _splice(lines, idx, block, before=False)

    # Fallback: append at end of body.
    return _append_to_end(body, block)


def _find_line_index(lines: list, target: str):
    """Find the index of the first line containing `target` (not inside a code fence)."""
    if not target:
        return None
    target_lower = target.lower().strip()
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if target_lower in line.lower():
            return i
    return None


def _norm_heading(s: str) -> str:
    """Normalize a heading query/title: strip leading # markers and whitespace."""
    return re.sub(r"^#{0,6}\s*", "", (s or "")).strip().lower()


def _find_section_end_index(lines: list, name: str):
    """Find the index of the last content line of the section headed by `name`.

    Returns None if the section heading isn't found. Headings inside code fences
    are ignored. `name` may be passed with or without the leading `## `.
    """
    name_n = _norm_heading(name)
    if not name_n:
        return None
    in_fence = False
    heading_idx = None
    heading_level = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            title_n = _norm_heading(m.group(2))
            if heading_idx is None and (name_n in title_n or title_n in name_n):
                heading_idx = i
                heading_level = level
                continue
            # if we're inside the section and hit a same-or-higher heading → end
            if heading_idx is not None and level <= heading_level:
                # section ended just before this heading
                return _last_non_blank_before(lines, i)

    if heading_idx is None:
        return None

    # Section runs to EOF
    return _last_non_blank_before(lines, len(lines))


def _last_non_blank_before(lines: list, exclusive_end: int):
    """Index of the last non-blank line strictly before exclusive_end."""
    idx = exclusive_end - 1
    while idx >= 0:
        if lines[idx].strip():
            return idx
        idx -= 1
    return None


def _find_section_heading_index(lines: list, name: str):
    """Find the index of a section heading by name (unused helper, kept for clarity)."""
    name_n = _norm_heading(name)
    if not name_n:
        return None
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            title_n = _norm_heading(m.group(1))
            if name_n in title_n or title_n in name_n:
                return i
    return None


def _splice(lines: list, idx: int, block: str, before: bool) -> str:
    """Splice `block` into the joined line list, before or after line idx."""
    # Ensure block ends with exactly one newline.
    block_text = block.rstrip("\n") + "\n"

    if before:
        prefix = "".join(lines[:idx])
        # ensure prefix ends with newline so block starts on its own line
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        suffix = "".join(lines[idx:])
        return prefix + block_text + suffix
    else:
        prefix = "".join(lines[: idx + 1])
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        suffix = "".join(lines[idx + 1:])
        # ensure a blank line separates block from following content if needed
        if suffix and not suffix.startswith("\n") and block_text and not block_text.endswith("\n\n"):
            pass  # single newline is fine; content continues on next line
        return prefix + block_text + suffix


def _append_to_end(body: str, block: str) -> str:
    """Append block to the end of body, ensuring clean newline separation."""
    block_text = block.rstrip("\n")
    if body == "":
        return block_text + "\n"
    if body.endswith("\n"):
        # ensure exactly one blank line before the block if not already present
        if not body.endswith("\n\n"):
            return body + "\n" + block_text + "\n"
        return body + block_text + "\n"
    return body + "\n\n" + block_text + "\n"


def _extract_quoted(text: str):
    """Pull the first double- or single-quoted substring from text."""
    m = re.search(r'["\']([^"\']+)["\']', text)
    return m.group(1) if m else None


def _strip_prefix(text: str, prefix: str) -> str:
    """Remove a leading prefix word and return the rest trimmed."""
    out = re.sub(rf"^\s*{re.escape(prefix)}\s*", "", text, flags=re.IGNORECASE)
    return out.strip().strip('"').strip("'")


# ── Phase 3e: decide + git ────────────────────────────────────────────


def decide_action(new_score: int, prev_score: int) -> Literal["keep", "revert"]:
    """Keep only on strict improvement; revert on equal-or-lower."""
    return "keep" if new_score > prev_score else "revert"


def commit_keep(skill_dir: str, target_file: str, rule_text: str,
                prev: int, new: int, assertion_id: str = "") -> str:
    """
    git add + commit a kept change. Returns the commit message.

    The assertion id is embedded in the message so crash recovery can identify
    what was attempted from `git log` alone.
    """
    rule_snippet = _truncate(rule_text.strip(), 60)
    if assertion_id:
        # leave room for the [id] prefix inside the 60-char spirit
        rule_snippet = _truncate(rule_text.strip(), 54)
        msg = f"improve: [{assertion_id}] {rule_snippet} (score {prev}→{new})"
    else:
        msg = f"improve: {rule_snippet} (score {prev}→{new})"

    subprocess.run(["git", "add", "--", target_file],
                   cwd=skill_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", msg, "--"],
                   cwd=skill_dir, check=True, capture_output=True, text=True)
    return msg


def revert_change(skill_dir: str, target_file: str) -> None:
    """Revert an unhelpful change via git checkout."""
    subprocess.run(["git", "checkout", "--", target_file],
                   cwd=skill_dir, check=True, capture_output=True, text=True)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


# ── Phase 3f: stop check ──────────────────────────────────────────────


def check_stop(new_score: int, total: int, plateau_count: int,
               iteration: int) -> StopDecision:
    """
    Three stop conditions, in priority order:
      1. ALL_PASS — new_score >= total (and total > 0)
      2. PLATEAU  — plateau_count >= 3
      3. CAP      — iteration >= 10
    """
    if total > 0 and new_score >= total:
        return StopDecision(True, "ALL_PASS", iteration)
    if plateau_count >= 3:
        return StopDecision(True, "PLATEAU", iteration)
    if iteration >= 10:
        return StopDecision(True, "CAP", iteration)
    return StopDecision(False, "", iteration)


# ── Phase 4: audit parsing + proposed assertions ──────────────────────


def parse_audit_response(text: str) -> AuditFindings:
    """
    Parse the LLM-as-judge audit response. Returns an AuditFindings always
    (possibly empty); never raises on malformed input.
    """
    if not text:
        return AuditFindings()
    try:
        quality = "F"
        qm = re.search(r"QUALITY_SCORE:\s*([A-F])", text)
        if qm:
            quality = qm.group(1)

        dimensions = {}
        # DIMENSION: <name>\n Score: <n> ... up to next DIMENSION:/RECURRING_PROBLEMS:/EOF
        for m in re.finditer(
            r"DIMENSION:\s*(.+?)\n\s*Score:\s*(\d+)(.*?)"
            r"(?=\nDIMENSION:|\nRECURRING_PROBLEMS:|\Z)",
            text, re.DOTALL,
        ):
            name = m.group(1).strip()
            score = int(m.group(2))
            body = m.group(3)
            dimensions[name] = {
                "score": score,
                "issues": _extract_inline(body, "Issues"),
                "suggestions": _extract_inline(body, "Suggestions"),
            }

        problems = []
        rp = re.search(r"RECURRING_PROBLEMS:\s*(.*)", text, re.DOTALL)
        if rp:
            for line in rp.group(1).strip().split("\n"):
                cleaned = line.lstrip("-").lstrip("*").strip()
                if cleaned:
                    problems.append(cleaned)

        return AuditFindings(
            quality_score=quality,
            dimensions=dimensions,
            recurring_problems=problems,
        )
    except Exception:
        return AuditFindings()


def _extract_inline(body: str, label: str) -> str:
    """Extract `Label: value` on a single line (inline)."""
    m = re.search(rf"{label}:\s*(.+)", body)
    return m.group(1).strip() if m else ""


def problems_to_proposed_assertions(problems: list) -> list:
    """
    Convert recurring problem strings into proposed-assertion dicts (p<NN> ids).

    These are PROPOSALS for the human to curate — the deterministic heuristic
    picks a check type from keywords but cannot guarantee semantic correctness.
    Stored under proposed_assertions, never scored by assertion_runner.
    """
    result = []
    for i, problem in enumerate(problems, start=1):
        check_type, value = _problem_to_check(problem)
        result.append({
            "id": f"p{str(i).zfill(2)}",
            "description": _truncate(problem.strip(), 100),
            "source_rule": problem.strip(),
            "type": check_type,
            "value": value,
            "source_file": "SKILL.md",
            "generator": "audit",
            "status": "proposed",
        })
    return result


def _problem_to_check(problem: str):
    """Best-effort deterministic check from a problem description."""
    p = problem.lower()
    # Absence / missing → check presence of the key noun
    absence = any(k in p for k in ("missing", "absent", "lacks", "no ", "without", "omits"))
    presence = any(k in p for k in ("includes", "contains", "too many", "vague", "generic",
                                    "repeats", "redundant", "clich"))
    if absence and not presence:
        return "contains", _key_phrase(problem)
    return "not_contains", _key_phrase(problem)


def _key_phrase(problem: str) -> str:
    """Extract a short check value (first few words) from a problem string."""
    words = problem.strip().split()
    if not words:
        return problem.strip()
    return _truncate(" ".join(words[:6]), 60)


def append_proposed_assertions(evals_path: str, proposed: list) -> dict:
    """
    Append proposed assertions to evals.json under `proposed_assertions`.
    Round-trip safe: creates the array if missing, extends if present.
    """
    with open(evals_path, "r", encoding="utf-8") as f:
        evals = json.load(f)
    existing = evals.get("proposed_assertions", [])
    existing.extend(proposed)
    evals["proposed_assertions"] = existing
    with open(evals_path, "w", encoding="utf-8") as f:
        json.dump(evals, f, indent=2, ensure_ascii=False)
    return evals


# ── Phase 5: report formatting ────────────────────────────────────────


def format_baseline_report(skill_name: str, total: int, passing: list,
                            failing: list) -> str:
    """
    Phase 2 baseline summary.

    failing: list of (id, description) tuples.
    passing: list of assertion ids.
    """
    lines = [f"Skill:      {skill_name}"]
    lines.append(f"Baseline:   {len(passing)}/{total} passed")
    if failing:
        lines.append("Failing:")
        for fid, desc in failing:
            lines.append(f"  {fid}: {desc}")
    else:
        lines.append("Failing:    (none)")
    if passing:
        lines.append("Passing:    " + ", ".join(passing))
    else:
        lines.append("Passing:    (none)")
    return "\n".join(lines)


def format_iteration_report(state: LoopState, delta: dict) -> str:
    """
    Per-iteration cost + decision report.

    delta keys: new, prev, total, action.
    """
    action = delta.get("action", "revert")
    action_label = "KEEP — score improved" if action == "keep" else "REVERT — score did not improve"
    lines = [
        f"── Iteration {state.iteration}/10 ──",
        f"Score:      {delta.get('new', state.prev_score)}/{delta.get('total', '?')}"
        f" (was {delta.get('prev', state.prev_score)}, delta {delta.get('new', 0) - delta.get('prev', 0):+d})",
        f"Action:     {action_label}",
        f"[COST] agent calls: {state.agent_calls}, llm calls: {state.llm_calls}, "
        f"inputs evaluated: {state.test_inputs_evaluated}",
    ]
    return "\n".join(lines)


def format_final_report(state: LoopState, baseline: dict, final: dict,
                         audit: AuditFindings, proposed: list) -> str:
    """
    Phase 5 final summary: baseline vs final, audit, proposed assertions.
    """
    b_pass = baseline.get("passed", 0)
    b_total = baseline.get("total", 0)
    f_pass = final.get("passed", 0)
    f_total = final.get("total", 0)
    improved = f_pass - b_pass

    lines = ["══════════════════════════════════════════════", "PHASE 5: REPORT",
             "══════════════════════════════════════════════"]
    lines.append(f"Baseline:   {b_pass}/{b_total}")
    lines.append(f"Final:      {f_pass}/{f_total}")
    lines.append(f"Improved:   {improved:+d} assertions fixed")
    lines.append(f"Test inputs evaluated: {state.test_inputs_evaluated}")

    per = final.get("per_assertion", {})
    if per:
        lines.append("Per-assertion:")
        for aid in sorted(per):
            entry = per[aid]
            base_b, final_b = entry[0], entry[1]
            desc = entry[2] if len(entry) > 2 else ""
            b_icon = "✅" if base_b else "❌"
            f_icon = "✅" if final_b else "❌"
            tag = ""
            if not base_b and final_b:
                tag = "  ← FIXED"
            elif not final_b:
                tag = "  ← STILL FAILING"
            lines.append(f"  {aid}: {b_icon} → {f_icon}  ({desc}){tag}")

    lines.append("")
    lines.append(f"Audit score:    {audit.quality_score}")
    if audit.dimensions:
        lines.append("Dimensions:")
        for name, info in audit.dimensions.items():
            issues = info.get("issues", "") or "ok"
            lines.append(f"  {name}: {info.get('score', '?')}/5  — {issues}")
    if audit.recurring_problems:
        lines.append("Audit recommendations:")
        for prob in audit.recurring_problems:
            lines.append(f"  - {prob}")

    lines.append("")
    lines.append(f"Agent calls:    {state.agent_calls}")
    lines.append(f"LLM calls:      {state.llm_calls}")
    lines.append(f"Stopping reason: {_stop_reason_label(state)}")

    if proposed:
        lines.append("")
        lines.append("Proposed assertions (for next run — not scored this run):")
        for p in proposed:
            lines.append(f"  {p.get('id', 'p??')}: {p.get('description', '')}")
    else:
        lines.append("")
        lines.append("No proposed assertions from audit.")

    return "\n".join(lines)


def _stop_reason_label(state: LoopState) -> str:
    if state.plateau_count >= 3:
        return "PLATEAU (3 iterations)"
    if state.iteration >= 10:
        return "CAP (10 iterations)"
    return "ALL PASS"


def format_batch_summary(results: list) -> str:
    """
    Batch summary for --all / named list runs.

    results: list of {"skill": name, "status": "success"|"failed", "error": str?}
    """
    succeeded = [r["skill"] for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]
    lines = ["══════════════════════════════════════════════", "BATCH SUMMARY",
             "══════════════════════════════════════════════"]
    lines.append(f"Succeeded:   {', '.join(succeeded) if succeeded else '(none)'}")
    if failed:
        lines.append("Failed:")
        for r in failed:
            err = r.get("error", "")
            lines.append(f"  {r.get('skill', '?')}: {err}")
    else:
        lines.append("Failed:      (none)")
    lines.append(f"Total:       {len(results)} skills processed")
    return "\n".join(lines)


# ── Crash recovery ────────────────────────────────────────────────────


def parse_git_log_recovery(skill_dir: str) -> RecoveryState:
    """
    Read git log in skill_dir and infer recovery state (iteration, last target).
    Recovery is git-based — there are no checkpoint files.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-50"],
            cwd=skill_dir, capture_output=True, text=True, check=True,
        )
        return _parse_recovery_from_log(result.stdout)
    except (subprocess.CalledProcessError, OSError):
        return RecoveryState(iteration=1, last_assertion_id=None, last_action="unknown")


def _parse_recovery_from_log(log: str) -> RecoveryState:
    """
    Pure parser: count improve(...) commits, extract last assertion id + action.

    Commit messages are of the form:
        improve: [a02] rule text… (score 2→3)
    An arrow with increasing score marks a keep; absence marks a revert attempt.
    """
    if not log:
        return RecoveryState(iteration=1, last_assertion_id=None, last_action="unknown")

    commits = [line for line in log.split("\n") if "improve(" in line or re.search(r"^\w+\s+improve:", line)]
    if not commits:
        return RecoveryState(iteration=1, last_assertion_id=None, last_action="unknown")

    iteration = len(commits) + 1
    last = commits[0]  # git log is newest-first

    last_id = None
    id_match = re.search(r"\[(a\d+)\]", last)
    if id_match:
        last_id = id_match.group(1)

    last_action = "unknown"
    score_match = re.search(r"score\s+\d+\s*→\s*\d+", last)
    if score_match:
        nums = re.findall(r"\d+", score_match.group(0))
        if len(nums) >= 2 and int(nums[1]) > int(nums[0]):
            last_action = "keep"
        else:
            last_action = "revert"

    return RecoveryState(iteration=iteration, last_assertion_id=last_id, last_action=last_action)


def update_state_from_action(state: LoopState, action: Literal["keep", "revert"],
                              delta: int) -> LoopState:
    """
    Single counter mutator for the keep/revert decision.

    Returns a NEW LoopState (original untouched). On keep: prev_score advances,
    plateau resets. On revert: plateau increments, prev_score unchanged.

    This closes the "model forgot to increment PLATEAU_COUNT" failure mode by
    making the bookkeeping a pure function of the action, not model memory.
    """
    new = replace(state)
    if action == "keep":
        new.prev_score = state.prev_score + max(delta, 0)
        new.plateau_count = 0
    elif action == "revert":
        new.plateau_count = state.plateau_count + 1
    return new


# ── CLI dispatcher ──────────────────────────────────────────────────────
#
# Thin CLI so the SKILL.md orchestrator can call every public function above
# from a skill run via Bash, matching the eval_generator.py / assertion_runner
# CLI→JSON pattern. Contract:
#   python3 lib/improve_runner.py <command> [--skill-dir PATH]
# Reads ONE JSON object from stdin (when the command needs input; `recovery`
# uses --skill-dir instead). Writes ONE JSON object to stdout. Dataclass
# results → asdict(...); None → {"result": null}; bare str → {"result": "<str>"}.
# On malformed stdin / unknown command: prints {"error": "<msg>"} AND exits
# non-zero. Never raises a traceback to the caller.

_VALID_COMMANDS = {
    "parse-args", "make-branch", "aggregate", "pick-target", "resolve-file",
    "parse-rule", "inject", "decide", "stop", "update-state", "parse-audit",
    "problems-to-assertions", "recovery",
}


def _run_command(command: str, data: dict, skill_dir: Optional[str] = None) -> dict:
    """Dispatch a CLI command on already-parsed JSON input.

    Returns a JSON-serializable dict. Raises on bad input (missing keys, bad
    types); main() converts any raised exception into {"error": ...} + exit 1.
    Factored out so tests can exercise the dispatch directly without subprocess.
    """
    if command == "parse-args":
        return asdict(parse_args(data["argv"]))

    if command == "make-branch":
        taken = set(data.get("taken", []))
        return {"name": make_branch_name(data["skill_name"], taken)}

    if command == "aggregate":
        return asdict(aggregate_scores(data["per_output"]))

    if command == "pick-target":
        agg = AggScore(**data["agg"])
        target = pick_target_assertion(agg)
        return target if target else {"target": None}

    if command == "resolve-file":
        return {"file": resolve_target_file(data["assertion"])}

    if command == "parse-rule":
        plan = parse_rule_response(data["text"])
        return asdict(plan) if plan else {"result": None}

    if command == "inject":
        plan = RulePlan(**data["plan"])
        block = data.get("block")
        return {"content": inject_rule(data["content"], plan, block)}

    if command == "decide":
        return {"action": decide_action(data["new"], data["prev"])}

    if command == "stop":
        return asdict(check_stop(data["new"], data["total"],
                                 data["plateau"], data["iteration"]))

    if command == "update-state":
        state = LoopState(**data["state"])
        delta = int(data.get("delta", 0))
        return asdict(update_state_from_action(state, data["action"], delta))

    if command == "parse-audit":
        return asdict(parse_audit_response(data["text"]))

    if command == "problems-to-assertions":
        return {"result": problems_to_proposed_assertions(data["problems"])}

    if command == "recovery":
        return asdict(parse_git_log_recovery(skill_dir))

    raise ValueError(f"unknown command: {command}")


def main():
    """CLI entry point. See module docstring at the CLI dispatcher section."""
    parser = argparse.ArgumentParser(
        prog="improve_runner.py",
        description="CLI dispatcher for improve-skill deterministic helpers.",
    )
    parser.add_argument("command", help="Subcommand to dispatch.")
    parser.add_argument("--skill-dir", default=None,
                        help="Skill directory (used by the `recovery` command).")
    args = parser.parse_args()

    # Unknown command → error + non-zero, before touching stdin.
    if args.command not in _VALID_COMMANDS:
        print(json.dumps({"error": f"unknown command: {args.command}"}))
        sys.exit(1)

    # `recovery` takes --skill-dir and reads no stdin.
    if args.command == "recovery":
        try:
            out = _run_command(args.command, {}, args.skill_dir)
        except Exception as exc:
            print(json.dumps({"error": str(exc)}))
            sys.exit(1)
        print(json.dumps(out))
        return

    # All other commands read one JSON object from stdin.
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"malformed stdin: {exc}"}))
        sys.exit(1)

    try:
        out = _run_command(args.command, data, args.skill_dir)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
