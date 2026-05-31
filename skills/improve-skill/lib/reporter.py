"""
reporter — phase-by-phase console output and report generation.

Generates human-readable output for each phase of the improvement loop,
plus a final report with per-assertion pass/fail comparison.
"""

import os
import subprocess
import sys


# ── Public API ────────────────────────────────────────────────────────

def format_phase_setup(
    skill_name: str,
    archetype: str,
    assertion_count: int,
    test_input_source: str,
) -> str:
    """
    Format the setup phase output.

    Shows: skill name, archetype, assertion count, test input source.
    """
    lines = [
        f"═══ SETUP ═══════════════════════════════════════",
        f"  Skill:       {skill_name}",
        f"  Archetype:   {archetype}",
        f"  Assertions:  {assertion_count}",
        f"  Test input:  {test_input_source[:80]}",
        f"══════════════════════════════════════════════════",
    ]
    return "\n".join(lines)


def format_phase_baseline(result: dict) -> str:
    """
    Format the baseline phase output.

    Shows: score (N/M), list of failing assertions.
    """
    passed = len(result["passed"])
    total = result["total"]
    lines = [
        f"\n═══ BASELINE ════════════════════════════════════",
        f"  Score: {passed}/{total}",
    ]

    if result["failed"]:
        lines.append("  Failing assertions:")
        for f in result["failed"]:
            lines.append(f"    ✗ {f['id']}: {f['description']}")
            if f.get("actual"):
                lines.append(f"      → {f['actual'][:80]}")
    else:
        lines.append("  ✓ All assertions pass!")

    lines.append("══════════════════════════════════════════════════")
    return "\n".join(lines)


def format_phase_loop(iteration_result) -> str:
    """
    Format a single loop iteration output.

    Shows: iteration number, target file, rule injected, score delta, action.
    """
    ir = iteration_result
    score_delta = f"{ir.score_before}→{ir.score_after}"
    action_icon = "✓" if ir.action == "committed" else "✗"
    action_text = "COMMITTED" if ir.action == "committed" else "REVERTED"

    lines = [
        f"\n  [{action_icon}] Iteration {ir.iteration}: {ir.target_file}",
        f"      Rule:     {ir.rule_injected[:70]}",
        f"      Score:    {score_delta} / {ir.total}",
        f"      Action:   {action_text}",
    ]
    return "\n".join(lines)


def format_final_report(
    skill_name: str,
    baseline: dict,
    final: dict,
    iterations: list,
    stopping_reason: str,
    git_commits: list[str] | None = None,
) -> str:
    """
    Format the final report.

    Shows: skill name, baseline→final score, per-assertion comparison,
    git commits, stopping reason, total iterations.
    """
    baseline_passed = len(baseline["passed"])
    final_passed = len(final["passed"])
    total = baseline["total"]

    lines = [
        f"\n{'='*60}",
        f"  IMPROVEMENT REPORT: {skill_name}",
        f"{'='*60}",
        f"",
        f"  Score:  {baseline_passed}/{total} → {final_passed}/{total}",
        f"  Reason: {stopping_reason}",
        f"  Iterations: {len(iterations)}",
        f"",
    ]

    # Per-assertion comparison
    if baseline.get("assertions") or final.get("assertions"):
        pass  # will use format_assertion_comparison
    else:
        comparison = format_assertion_comparison(baseline, final)
        if comparison:
            lines.append("  Per-assertion comparison:")
            lines.append(comparison)

    # Git commits
    if git_commits:
        lines.append("")
        lines.append("  Git commits:")
        for commit in git_commits:
            lines.append(f"    {commit}")

    lines.append(f"\n{'='*60}")
    return "\n".join(lines)


def format_assertion_comparison(baseline: dict, final: dict) -> str:
    """
    Format per-assertion pass/fail comparison between baseline and final.

    Returns a table showing each assertion's status at baseline vs final.
    """
    baseline_ids = {
        p["id"]: "✓" for p in baseline.get("passed", [])
    }
    baseline_ids.update({
        f["id"]: "✗" for f in baseline.get("failed", [])
    })

    final_ids = {
        p["id"]: "✓" for p in final.get("passed", [])
    }
    final_ids.update({
        f["id"]: "✗" for f in final.get("failed", [])
    })

    # Collect all assertion IDs and descriptions
    all_assertions = {}
    for p in baseline.get("passed", []):
        all_assertions[p["id"]] = p["description"]
    for f in baseline.get("failed", []):
        all_assertions[f["id"]] = f["description"]
    for p in final.get("passed", []):
        all_assertions[p["id"]] = p["description"]
    for f in final.get("failed", []):
        all_assertions[f["id"]] = f["description"]

    lines = []
    for aid, desc in sorted(all_assertions.items()):
        b_status = baseline_ids.get(aid, "?")
        f_status = final_ids.get(aid, "?")
        changed = " ← FIXED" if b_status == "✗" and f_status == "✓" else ""
        lines.append(f"    {aid} | baseline: {b_status} | final: {f_status} | {desc[:40]}{changed}")

    return "\n".join(lines)


def get_git_commits(skill_dir: str, branch: str = None) -> list[str]:
    """Get improvement commits from git log."""
    try:
        cmd = ["git", "log", "--oneline", "--grep=improve"]
        if branch:
            cmd.extend([branch])
        result = subprocess.run(
            cmd,
            cwd=skill_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except Exception:
        pass
    return []


# ── CLI smoke test ────────────────────────────────────────────────────

def main():
    """CLI: python3 reporter.py — prints a sample report."""
    sample_baseline = {
        "total": 3,
        "passed": [{"id": "a01", "description": "Has header"}],
        "failed": [
            {"id": "a02", "description": "Has summary", "actual": "No summary found"},
            {"id": "a03", "description": "Under 500 words", "actual": "Word count 600 exceeds limit 500"},
        ],
    }
    sample_final = {
        "total": 3,
        "passed": [
            {"id": "a01", "description": "Has header"},
            {"id": "a02", "description": "Has summary"},
            {"id": "a03", "description": "Under 500 words"},
        ],
        "failed": [],
    }

    print(format_phase_setup("tdd", "prompt", 3, "Use the tdd skill. Test-driven development workflow"))
    print(format_phase_baseline(sample_baseline))

    from improvement_loop import IterationResult
    ir = IterationResult(1, "SKILL.md", "Include summary section", "a02", 1, 2, 3, "committed")
    print(format_phase_loop(ir))

    print(format_final_report(
        "tdd", sample_baseline, sample_final,
        [ir], "perfect_score",
        git_commits=["abc1234 improve(tdd): Include summary section (score 1→2)"],
    ))


if __name__ == "__main__":
    main()
