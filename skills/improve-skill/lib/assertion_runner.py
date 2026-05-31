"""
assertion_runner — deterministic eval engine for improve-skill.

Pure function: text + evals.json → structured pass/fail result.
No LLM calls, no randomness, no I/O beyond reading evals.json from disk.
"""

import re


def run_assertions(output: str, evals: dict) -> dict:
    """
    Evaluate raw text output against a set of binary assertions.

    Args:
        output: The raw text output to evaluate.
        evals: An evals.json dict with an "assertions" array.

    Returns:
        {"total": int, "passed": [...], "failed": [...]}
        Each failed entry includes "actual" — what was found instead.
    """
    assertions = evals.get("assertions", [])
    passed = []
    failed = []

    for assertion in assertions:
        result = _check_one(output, assertion)
        if result["pass"]:
            passed.append({"id": assertion["id"], "description": assertion["description"]})
        else:
            failed.append({
                "id": assertion["id"],
                "description": assertion["description"],
                "actual": result["actual"],
            })

    return {
        "total": len(assertions),
        "passed": passed,
        "failed": failed,
    }


def _check_one(output: str, assertion: dict) -> dict:
    """Run a single assertion check. Returns {"pass": bool, "actual": str}."""

    check_type = assertion["type"]

    if check_type == "regex":
        return _check_regex(output, assertion)
    elif check_type == "not_regex":
        return _check_not_regex(output, assertion)
    elif check_type == "contains":
        return _check_contains(output, assertion)
    elif check_type == "not_contains":
        return _check_not_contains(output, assertion)
    elif check_type == "max_words":
        return _check_max_words(output, assertion)
    elif check_type == "min_words":
        return _check_min_words(output, assertion)
    else:
        return {"pass": False, "actual": f"Unknown check type: {check_type}"}


def _parse_flags(flags_str: str) -> int:
    """Convert flag string like 'mi' to re.IGNORECASE | re.MULTILINE."""
    flags = 0
    if "i" in flags_str:
        flags |= re.IGNORECASE
    if "m" in flags_str:
        flags |= re.MULTILINE
    return flags


def _check_regex(output: str, assertion: dict) -> dict:
    pattern = assertion["check"]
    flags = _parse_flags(assertion.get("flags", ""))
    match = re.search(pattern, output, flags)
    if match:
        return {"pass": True, "actual": None}
    return {"pass": False, "actual": f"Pattern /{pattern}/ not found in output"}


def _check_not_regex(output: str, assertion: dict) -> dict:
    pattern = assertion["check"]
    flags = _parse_flags(assertion.get("flags", ""))
    match = re.search(pattern, output, flags)
    if not match:
        return {"pass": True, "actual": None}
    return {"pass": False, "actual": f"Found forbidden pattern match: '{match.group()}'"}


def _check_contains(output: str, assertion: dict) -> dict:
    substring = str(assertion["value"])
    if substring in output:
        return {"pass": True, "actual": None}
    return {"pass": False, "actual": f"'{substring}' not found in output"}


def _check_not_contains(output: str, assertion: dict) -> dict:
    substring = str(assertion["value"])
    if substring not in output:
        return {"pass": True, "actual": None}
    return {"pass": False, "actual": f"Found forbidden substring: '{substring}'"}


def _count_words(text: str) -> int:
    """Count words by splitting on whitespace."""
    return len(text.split())


def _check_max_words(output: str, assertion: dict) -> dict:
    limit = int(assertion["value"])
    count = _count_words(output)
    if count <= limit:
        return {"pass": True, "actual": None}
    return {"pass": False, "actual": f"Word count {count} exceeds limit {limit}"}


def _check_min_words(output: str, assertion: dict) -> dict:
    minimum = int(assertion["value"])
    count = _count_words(output)
    if count >= minimum:
        return {"pass": True, "actual": None}
    return {"pass": False, "actual": f"Word count {count} below minimum {minimum}"}


# ── CLI smoke test ────────────────────────────────────────────────────

def main():
    """
    CLI: python3 assertion_runner.py --evals <file> --output <file>
    Prints structured JSON result to stdout.
    """
    import json
    import sys

    args = sys.argv[1:]
    if "--evals" not in args or "--output" not in args:
        print("Usage: assertion_runner.py --evals <evals.json> --output <output.txt>", file=sys.stderr)
        sys.exit(1)

    evals_path = args[args.index("--evals") + 1]
    output_path = args[args.index("--output") + 1]

    with open(evals_path, "r") as f:
        evals = json.load(f)
    with open(output_path, "r") as f:
        output = f.read()

    result = run_assertions(output, evals)
    print(json.dumps(result, indent=2))
    sys.exit(0 if len(result["failed"]) == 0 else 1)


if __name__ == "__main__":
    main()
