"""
skill_runner — execute a skill against test input and capture output.

Reads skill files, constructs a sub-agent prompt, sends the test input,
and captures raw text output. The actual sub-agent execution is delegated
to an executor function that can be mocked for testing.
"""

import os
import subprocess
import sys


# ── Public API ────────────────────────────────────────────────────────

def read_skill_files(skill_dir: str) -> dict[str, str]:
    """
    Read all skill content files from a skill directory.

    Returns dict mapping filename → content.
    Reads SKILL.md and all .md files from references/ subdirectory.
    Does NOT read scripts/ or non-.md files.

    Raises FileNotFoundError if skill_dir doesn't exist.
    Raises ValueError if SKILL.md is missing.
    """
    if not os.path.isdir(skill_dir):
        raise FileNotFoundError(f"Skill directory not found: {skill_dir}")

    files = {}

    # Read SKILL.md (required)
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md_path):
        raise ValueError(f"No SKILL.md found in {skill_dir}")
    with open(skill_md_path, "r", encoding="utf-8") as f:
        files["SKILL.md"] = f.read()

    # Read reference .md files (optional)
    refs_dir = os.path.join(skill_dir, "references")
    if os.path.isdir(refs_dir):
        for fname in sorted(os.listdir(refs_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(refs_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    files[fname] = f.read()

    # Explicitly skip scripts/ — do NOT read executable files
    return files


def build_skill_prompt(files: dict[str, str], test_input: dict) -> tuple[str, str]:
    """
    Build the system context and user message for the sub-agent.

    Args:
        files: Dict of filename → content from read_skill_files().
        test_input: {"type": "prompt", "text": "..."} or {"type": "file", "path": "..."}

    Returns:
        (system_prompt, user_message) tuple.

    Raises:
        FileNotFoundError: if file-type input path doesn't exist.
    """
    # Build system context from all skill files
    system_parts = []
    if "SKILL.md" in files:
        system_parts.append(files["SKILL.md"])

    # Add reference files with their filenames as labels
    for fname, content in sorted(files.items()):
        if fname == "SKILL.md":
            continue
        system_parts.append(f"\n--- {fname} ---\n{content}")

    system_prompt = "\n\n".join(system_parts)

    # Build user message based on test input type
    if test_input["type"] == "file":
        file_path = test_input["path"]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test input file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        user_message = (
            f"Process the following content according to the skill instructions:\n\n"
            f"{file_content}"
        )
    else:
        user_message = test_input["text"]

    return system_prompt, user_message


def run_skill(
    files: dict[str, str],
    test_input: dict,
    executor: callable = None,
) -> str:
    """
    Run a skill against test input and return the raw text output.

    Args:
        files: Dict from read_skill_files().
        test_input: {"type": "prompt/file", ...} from evals.json.
        executor: Optional callable(system_prompt, user_message) -> str.
                  If None, uses the default sub-agent executor.

    Returns:
        Raw text output string from the skill execution.
    """
    system_prompt, user_message = build_skill_prompt(files, test_input)

    if executor is None:
        executor = _execute_subagent

    output = executor(system_prompt, user_message)
    return output


# ── Internal: sub-agent executor ──────────────────────────────────────

def _execute_subagent(system_prompt: str, user_message: str) -> str:
    """
    Execute the skill via a sub-agent.

    In production, this would use Claude Code's Agent tool.
    For standalone CLI use, it runs claude with the prompt.

    Returns the sub-agent's raw text output.
    """
    # Build the full prompt for claude CLI
    full_prompt = (
        f"SYSTEM INSTRUCTIONS (follow these exactly):\n\n"
        f"{system_prompt}\n\n"
        f"---\n\n"
        f"USER REQUEST:\n\n"
        f"{user_message}"
    )

    try:
        result = subprocess.run(
            ["claude", "--print", "--no-input", full_prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout.strip() if result.stdout else ""
    except FileNotFoundError:
        # claude CLI not available — return empty string
        # This path is used when running outside Claude Code
        return ""
    except subprocess.TimeoutExpired:
        return ""


# ── CLI smoke test ────────────────────────────────────────────────────

def main():
    """
    CLI: python3 skill_runner.py <skill_dir> <evals.json>
    Runs the skill and prints captured output to stdout.
    """
    if len(sys.argv) < 3:
        print("Usage: skill_runner.py <skill_dir> <evals.json>", file=sys.stderr)
        sys.exit(1)

    skill_dir = sys.argv[1]
    evals_path = sys.argv[2]

    import json
    with open(evals_path, "r") as f:
        evals = json.load(f)

    files = read_skill_files(skill_dir)
    output = run_skill(files, evals["test_input"])
    print(output)


if __name__ == "__main__":
    main()
