"""
improvement_loop — the Karpathy-style improvement cycle.

Core loop: change → test → keep or revert.
Orchestrates all foundation modules (eval_generator, skill_runner, assertion_runner)
to autonomously improve a skill's output quality.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from typing import Callable

from assertion_runner import run_assertions
from eval_generator import generate_evals, write_evals, validate_evals_schema
from skill_runner import read_skill_files, run_skill


# ── Data structures ───────────────────────────────────────────────────

@dataclass
class IterationResult:
    """Result of a single improvement iteration."""
    iteration: int
    target_file: str
    rule_injected: str
    assertion_id: str
    score_before: int
    score_after: int
    total: int
    action: str  # "committed" or "reverted"


# ── Public API ────────────────────────────────────────────────────────

def check_stopping_conditions(
    iteration: int,
    score: int,
    total: int,
    plateau_count: int,
) -> str | None:
    """
    Check if the loop should stop.

    Returns:
        "perfect_score" — all assertions pass
        "plateau" — 3 consecutive non-improving iterations
        "hard_cap" — 10 iterations reached
        None — continue looping
    """
    if score == total:
        return "perfect_score"
    if plateau_count >= 3:
        return "plateau"
    if iteration >= 10:
        return "hard_cap"
    return None


def select_target_file(iteration: int, reference_files: list[str]) -> str:
    """
    Select which file to modify in this iteration.

    Priority:
    - Iterations 1-2: always SKILL.md
    - Iterations 3+: reference files (templates → quality-checklists → other)
    - Fallback: SKILL.md if no reference files
    """
    if iteration <= 2:
        return "SKILL.md"

    if not reference_files:
        return "SKILL.md"

    # Priority order: templates.md → quality-checklists.md → first available
    priority_names = ["templates.md", "quality-checklists.md"]
    for name in priority_names:
        if name in reference_files:
            return name

    return reference_files[0]


def inject_rule(
    content: str,
    filename: str,
    iteration: int,
    assertion_id: str,
    rule_text: str,
) -> str:
    """
    Inject a rule into file content with proper markers.

    For SKILL.md: appends to "Auto-Generated Quality Rules" section.
    For reference files: appends to the end with a marker.

    Returns the modified content string.
    """
    marker_open = f"<!-- improve-skill: iteration {iteration}, assertion {assertion_id} -->"
    marker_close = "<!-- /improve-skill -->"
    rule_line = f"- {rule_text}"
    block = f"{marker_open}\n{rule_line}\n{marker_close}"

    if filename == "SKILL.md":
        # Check if auto-generated section already exists
        section_header = "## Auto-Generated Quality Rules"
        if section_header in content:
            # Append to existing section
            insert_pos = content.rfind(marker_close)
            if insert_pos != -1:
                # Append after the last improve-skill block
                after = insert_pos + len(marker_close)
                return content[:after] + "\n" + block + "\n" + content[after:]
            else:
                # Section exists but no blocks yet — append after header
                header_pos = content.find(section_header)
                after_header = header_pos + len(section_header)
                return content[:after_header] + "\n\n" + block + "\n" + content[after_header:]
        else:
            # Create new section at the end
            return content.rstrip() + f"\n\n{section_header}\n\n{block}\n"
    else:
        # Reference file — just append with a section break
        return content.rstrip() + f"\n\n{block}\n"


def format_branch_name(skill_name: str, batch: bool = False) -> str:
    """Format the git branch name for improvement."""
    today = date.today().strftime("%Y-%m-%d")
    if batch:
        return f"improve/batch-{today}"
    return f"improve/{skill_name}-{today}"


def run_improvement_loop(
    skill_dir: str,
    skill_name: str,
    max_iterations: int = 10,
    executor: Callable = None,
) -> dict:
    """
    Run the full improvement loop on a single skill.

    Steps:
    1. Generate evals.json (if not present)
    2. Run skill to get baseline score
    3. Loop: inject rule → run → score → commit or revert
    4. Return structured result

    Args:
        skill_dir: Path to the skill directory.
        skill_name: Name of the skill.
        max_iterations: Hard cap on iterations (default 10).
        executor: Optional skill executor override (for testing).

    Returns:
        {
            "skill_name": str,
            "baseline_score": {"passed": int, "total": int, ...},
            "final_score": {"passed": int, "total": int, ...},
            "iterations": [IterationResult, ...],
            "stopping_reason": str,
            "evals": dict,
        }
    """
    # Phase 1: Setup — generate or load evals.json
    evals_path = os.path.join(skill_dir, "evals.json")
    if os.path.exists(evals_path):
        with open(evals_path, "r") as f:
            evals = json.load(f)
        print(f"[setup] Reusing existing evals.json ({len(evals['assertions'])} assertions)")
    else:
        evals = generate_evals(skill_dir)
        write_evals(skill_dir, evals)
        print(f"[setup] Generated evals.json ({len(evals['assertions'])} assertions)")

    # Phase 2: Baseline — run skill and score
    files = read_skill_files(skill_dir)
    output = run_skill(files, evals["test_input"], executor=executor)
    baseline = run_assertions(output, evals)
    baseline_passed = len(baseline["passed"])

    print(f"[baseline] Score: {baseline_passed}/{baseline['total']}")

    # Check if already perfect
    stopping = check_stopping_conditions(0, baseline_passed, baseline["total"], 0)
    if stopping:
        return {
            "skill_name": skill_name,
            "baseline_score": baseline,
            "final_score": baseline,
            "iterations": [],
            "stopping_reason": stopping,
            "evals": evals,
        }

    # Phase 3: Improvement Loop
    iterations = []
    plateau_count = 0
    current_score = baseline_passed
    total = baseline["total"]

    # Discover reference files
    refs_dir = os.path.join(skill_dir, "references")
    reference_files = []
    if os.path.isdir(refs_dir):
        reference_files = sorted(
            f for f in os.listdir(refs_dir) if f.endswith(".md")
        )

    for i in range(1, max_iterations + 1):
        # Select target file
        target = select_target_file(i, reference_files)
        target_path = os.path.join(skill_dir, target)

        # Identify first failing assertion
        re_output = run_skill(files, evals["test_input"], executor=executor)
        re_result = run_assertions(re_output, evals)
        failing = re_result["failed"]

        if not failing:
            # Perfect score achieved during iteration
            break

        first_fail = failing[0]
        assertion_id = first_fail["id"]

        # Generate rule to fix the failing assertion
        new_rule = _generate_fix_rule(assertion_id, first_fail, evals)

        # Read current content of target file
        with open(target_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Inject the rule
        modified_content = inject_rule(
            original_content, target, i, assertion_id, new_rule
        )

        # Write modified file
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(modified_content)

        # Re-run with modified skill
        modified_files = read_skill_files(skill_dir)
        new_output = run_skill(modified_files, evals["test_input"], executor=executor)
        new_result = run_assertions(new_output, evals)
        new_score = len(new_result["passed"])

        # Decide: keep or revert
        if new_score > current_score:
            # Improvement! Commit
            git_commit(skill_dir, skill_name, new_rule, current_score, new_score)
            action = "committed"
            plateau_count = 0
            current_score = new_score
            # Update files dict
            files = modified_files
        else:
            # No improvement — revert
            git_checkout_file(skill_dir, target)
            action = "reverted"
            plateau_count += 1
            # Restore original content in working memory
            with open(target_path, "r", encoding="utf-8") as f:
                pass  # File already reverted by git checkout

        iter_result = IterationResult(
            iteration=i,
            target_file=target,
            rule_injected=new_rule,
            assertion_id=assertion_id,
            score_before=current_score if action == "committed" else current_score,
            score_after=new_score,
            total=total,
            action=action,
        )
        iterations.append(iter_result)

        print(f"[loop] Iteration {i}: {target} → score {current_score}→{new_score} ({action})")

        # Check stopping conditions
        stopping = check_stopping_conditions(i, new_score, total, plateau_count)
        if stopping:
            break

    # Final score
    final_output = run_skill(files, evals["test_input"], executor=executor)
    final_result = run_assertions(final_output, evals)

    stopping_reason = stopping or "hard_cap"

    return {
        "skill_name": skill_name,
        "baseline_score": baseline,
        "final_score": final_result,
        "iterations": iterations,
        "stopping_reason": stopping_reason,
        "evals": evals,
    }


# ── Internal helpers ──────────────────────────────────────────────────

def _generate_fix_rule(assertion_id: str, failure: dict, evals: dict) -> str:
    """
    Generate a rule to fix a failing assertion.

    For v1: uses the assertion's description and source_rule to create
    a prescriptive rule. In v2, this can be upgraded to LLM-based generation.
    """
    # Find the assertion details
    for a in evals["assertions"]:
        if a["id"] == assertion_id:
            desc = a.get("description", "")
            source = a.get("source_rule", "")
            check_type = a.get("type", "")

            if check_type in ("not_contains", "not_regex"):
                # Negative rule — emphasize prohibition
                return f"Avoid output that {desc.lower().replace('output must not contain: ', '')}"
            elif check_type == "contains":
                # Positive rule — emphasize requirement
                return f"Ensure output includes: {desc.lower().replace('output includes: ', '')}"
            elif check_type == "regex":
                return f"Format requirement: {desc}"
            elif check_type == "min_words":
                return "Provide a more detailed and comprehensive response"
            elif check_type == "max_words":
                return "Keep the output concise and focused"
            else:
                return f"Follow the rule: {source}"

    return f"Address assertion {assertion_id}"


# ── Git operations ────────────────────────────────────────────────────

def create_improvement_branch(skill_dir: str, skill_name: str, batch: bool = False):
    """Create a git branch for the improvement work."""
    branch = format_branch_name(skill_name, batch=batch)
    try:
        subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=skill_dir,
            capture_output=True,
            check=True,
        )
        print(f"[git] Created branch: {branch}")
    except subprocess.CalledProcessError:
        # Branch might already exist — just checkout
        subprocess.run(
            ["git", "checkout", branch],
            cwd=skill_dir,
            capture_output=True,
            check=False,
        )


def git_commit(skill_dir: str, skill_name: str, description: str, score_before: int, score_after: int):
    """Commit the current change with the standard format."""
    msg = f"improve({skill_name}): {description[:60]} (score {score_before}→{score_after})"
    subprocess.run(["git", "add", "-A"], cwd=skill_dir, capture_output=True, check=False)
    subprocess.run(
        ["git", "commit", "-m", msg, "--no-gpg-sign"],
        cwd=skill_dir,
        capture_output=True,
        check=False,
    )


def git_checkout_file(skill_dir: str, filename: str):
    """Revert a single file to its last committed state."""
    subprocess.run(
        ["git", "checkout", "--", filename],
        cwd=skill_dir,
        capture_output=True,
        check=False,
    )


# ── CLI smoke test ────────────────────────────────────────────────────

def main():
    """
    CLI: python3 improvement_loop.py <skill_dir>
    Runs the improvement loop and prints the result.
    """
    if len(sys.argv) < 2:
        print("Usage: improvement_loop.py <skill_dir>", file=sys.stderr)
        sys.exit(1)

    skill_dir = sys.argv[1]
    skill_name = os.path.basename(os.path.normpath(skill_dir))

    result = run_improvement_loop(skill_dir, skill_name)
    print(json.dumps({
        "skill_name": result["skill_name"],
        "stopping_reason": result["stopping_reason"],
        "baseline": len(result["baseline_score"]["passed"]),
        "final": len(result["final_score"]["passed"]),
        "total": result["baseline_score"]["total"],
        "iterations": [
            {
                "iteration": ir.iteration,
                "target": ir.target_file,
                "action": ir.action,
                "score": f"{ir.score_before}→{ir.score_after}",
            }
            for ir in result["iterations"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
