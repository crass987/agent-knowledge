"""
batch_orchestrator — --all and multi-skill invocation.

Handles single-skill, named-list, and --all modes.
Discovers skills, runs improvement loop sequentially, and aggregates results.
"""

import json
import os
import subprocess
import sys
import time

from eval_generator import find_skill_dir
from improvement_loop import (
    create_improvement_branch,
    format_branch_name,
    run_improvement_loop,
)


# ── Constants ─────────────────────────────────────────────────────────

SEARCH_DIRS = [
    "/Users/CraSS/Documents/Code_projects/agent-knowledge/skills",
    "/Users/CraSS/.claude/skills",
]


# ── Public API ────────────────────────────────────────────────────────

def parse_args(args: list[str]) -> dict:
    """
    Parse CLI arguments into a structured config.

    Modes:
    - ["skill-name"] → single
    - ["--all"] → all
    - ["s1", "s2", ...] → batch
    - ["--regen"] → regen flag

    Returns:
        {"mode": str, "skills": list[str], "regen": bool}

    Raises:
        ValueError: if no arguments provided.
    """
    if not args:
        raise ValueError("No arguments provided. Specify a skill name or --all.")

    regen = "--regen" in args
    filtered = [a for a in args if a != "--regen"]

    if "--all" in filtered:
        return {"mode": "all", "skills": [], "regen": regen}

    if len(filtered) == 1:
        return {"mode": "single", "skills": [filtered[0]], "regen": regen}

    return {"mode": "batch", "skills": filtered, "regen": regen}


def discover_skills(search_dirs: list[str]) -> list[str]:
    """
    Discover all skills with SKILL.md across search directories.

    - Skips "improve-skill" itself (don't improve the improver)
    - Skips directories without SKILL.md
    - Deduplicates by name
    - Returns sorted list of skill names
    """
    seen = set()
    skills = []

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for entry in sorted(os.listdir(search_dir)):
            if entry in seen:
                continue
            if entry == "improve-skill":
                continue
            skill_path = os.path.join(search_dir, entry)
            skill_md = os.path.join(skill_path, "SKILL.md")
            if os.path.isdir(skill_path) and os.path.exists(skill_md):
                seen.add(entry)
                skills.append(entry)

    return sorted(skills)


def run_batch(
    skill_names: list[str],
    search_dirs: list[str] | None = None,
    max_iterations: int = 10,
) -> dict:
    """
    Run improvement loop across multiple skills sequentially.

    Args:
        skill_names: List of skill names to improve.
        search_dirs: Directories to search for skills (default: SEARCH_DIRS).
        max_iterations: Max iterations per skill.

    Returns:
        {
            "skills": [{"skill_name": str, "status": str, "result": dict}, ...],
            "total_skills": int,
            "improved": int,
            "unchanged": int,
            "failed": int,
            "total_iterations": int,
        }
    """
    if search_dirs is None:
        search_dirs = SEARCH_DIRS

    results = []
    improved = 0
    unchanged = 0
    failed = 0
    total_iterations = 0

    is_batch = len(skill_names) > 1
    branch_created = False

    for skill_name in skill_names:
        # Find skill directory
        skill_dir = find_skill_dir(skill_name, search_dirs)
        if not skill_dir:
            results.append({
                "skill_name": skill_name,
                "status": "failed",
                "error": f"Skill directory not found: {skill_name}",
            })
            failed += 1
            continue

        # Create branch (once for batch, once per skill for single)
        if not branch_created:
            create_improvement_branch(skill_dir, skill_name, batch=is_batch)
            branch_created = True

        # Run the improvement loop
        try:
            loop_result = run_improvement_loop(
                skill_dir=skill_dir,
                skill_name=skill_name,
                max_iterations=max_iterations,
            )

            baseline = len(loop_result["baseline_score"]["passed"])
            final = len(loop_result["final_score"]["passed"])
            iter_count = len(loop_result["iterations"])

            if final > baseline:
                status = "improved"
                improved += 1
            else:
                status = "unchanged"
                unchanged += 1

            total_iterations += iter_count

            results.append({
                "skill_name": skill_name,
                "status": status,
                "result": loop_result,
            })

        except Exception as e:
            results.append({
                "skill_name": skill_name,
                "status": "failed",
                "error": str(e),
            })
            failed += 1

    return {
        "skills": results,
        "total_skills": len(skill_names),
        "improved": improved,
        "unchanged": unchanged,
        "failed": failed,
        "total_iterations": total_iterations,
    }


# ── CLI entry point ───────────────────────────────────────────────────

def main():
    """
    CLI: python3 batch_orchestrator.py <skill-name> [--all] [--regen]
    """
    args = sys.argv[1:]
    config = parse_args(args)

    if config["mode"] == "all":
        skill_names = discover_skills(SEARCH_DIRS)
        print(f"[discover] Found {len(skill_names)} skills")
    else:
        skill_names = config["skills"]

    result = run_batch(skill_names, max_iterations=10)
    print(json.dumps({
        "total": result["total_skills"],
        "improved": result["improved"],
        "unchanged": result["unchanged"],
        "failed": result["failed"],
        "iterations": result["total_iterations"],
        "skills": [
            {"name": s["skill_name"], "status": s["status"]}
            for s in result["skills"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
