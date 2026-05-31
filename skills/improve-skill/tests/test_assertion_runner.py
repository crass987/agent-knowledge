"""
Tests for assertion_runner — the deterministic eval engine.

TDD RED phase: these tests define the contract BEFORE implementation.
Run with: python -m pytest tests/test_assertion_runner.py -v
"""

import json
import sys
import os
import re

import pytest

# Add lib to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from assertion_runner import run_assertions


# ── Fixtures ──────────────────────────────────────────────────────────

def make_evals(assertions):
    """Helper: wrap assertions into a minimal evals.json structure."""
    return {
        "version": 1,
        "skill": "test-skill",
        "generated_at": "2026-05-31T00:00:00Z",
        "test_input": {"type": "prompt", "text": "test"},
        "assertions": assertions,
    }


def make_assertion(id, description, type, source_rule="test rule", **kwargs):
    """Helper: build a single assertion dict."""
    a = {"id": id, "description": description, "source_rule": source_rule, "type": type}
    if type in ("regex", "not_regex"):
        a["check"] = kwargs["check"]
        a["flags"] = kwargs.get("flags", "")
    elif type in ("contains", "not_contains"):
        a["value"] = kwargs["value"]
    elif type in ("max_words", "min_words"):
        a["value"] = kwargs["value"]
    return a


SAMPLE_OUTPUT = """## Key Ideas

1. **Test-driven development** means writing tests before code.
2. Each cycle is: RED → GREEN → REFACTOR.
3. Keep tests simple — one assertion per test.

## Common Mistakes

- Testing implementation details instead of behavior.
- Skipping the refactor step.
- Writing too many tests at once.
"""


# ── Test: regex check type ────────────────────────────────────────────

class TestRegexCheck:
    def test_regex_match_passes(self):
        """regex assertion passes when output matches the pattern."""
        evals = make_evals([
            make_assertion("a01", "Has a header", "regex", check=r"^## "),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert result["total"] == 1
        assert len(result["passed"]) == 1
        assert result["passed"][0]["id"] == "a01"
        assert len(result["failed"]) == 0

    def test_regex_no_match_fails(self):
        """regex assertion fails when output does not match."""
        evals = make_evals([
            make_assertion("a01", "Has YAML frontmatter", "regex", check=r"^---"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert result["total"] == 1
        assert len(result["failed"]) == 1
        assert result["failed"][0]["id"] == "a01"
        assert "actual" in result["failed"][0]

    def test_regex_with_ignore_case_flag(self):
        """regex with 'i' flag matches case-insensitively."""
        evals = make_evals([
            make_assertion("a01", "Mentions TDD", "regex", check=r"test-driven development", flags="i"),
        ])
        result = run_assertions("SOME TEST-DRIVEN DEVELOPMENT text", evals)
        assert len(result["passed"]) == 1

    def test_regex_with_multiline_flag(self):
        """regex with 'm' flag treats ^/$ per line."""
        evals = make_evals([
            make_assertion("a01", "Each item starts with number", "regex", check=r"^\d+\.", flags="m"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["passed"]) == 1

    def test_regex_with_combined_flags(self):
        """regex with 'mi' flags: multiline + case-insensitive."""
        evals = make_evals([
            make_assertion("a01", "Has numbered items", "regex", check=r"^\d+\.", flags="mi"),
        ])
        result = run_assertions("1. First\n2. SECOND", evals)
        assert len(result["passed"]) == 1


# ── Test: not_regex check type ────────────────────────────────────────

class TestNotRegexCheck:
    def test_not_regex_passes_when_no_match(self):
        """not_regex passes when pattern does NOT match."""
        evals = make_evals([
            make_assertion("a01", "No TODO markers", "not_regex", check=r"\[TODO\]"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["passed"]) == 1

    def test_not_regex_fails_when_matches(self):
        """not_regex fails when pattern DOES match."""
        evals = make_evals([
            make_assertion("a01", "No placeholder text", "not_regex", check=r"\[SUMMARY\]"),
        ])
        result = run_assertions("Here is a [SUMMARY] of the video.", evals)
        assert len(result["failed"]) == 1
        assert "[SUMMARY]" in result["failed"][0]["actual"]


# ── Test: contains check type ─────────────────────────────────────────

class TestContainsCheck:
    def test_contains_passes_when_substring_present(self):
        """contains passes when the exact substring is found."""
        evals = make_evals([
            make_assertion("a01", "Mentions refactor", "contains", value="REFACTOR"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["passed"]) == 1

    def test_contains_fails_when_substring_absent(self):
        """contains fails when the substring is not in the output."""
        evals = make_evals([
            make_assertion("a01", "Has conclusion section", "contains", value="## Conclusion"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["failed"]) == 1

    def test_contains_is_case_sensitive(self):
        """contains is case-sensitive by default."""
        evals = make_evals([
            make_assertion("a01", "Has exact case", "contains", value="Test-Driven Development"),
        ])
        result = run_assertions("test-driven development is great", evals)
        assert len(result["failed"]) == 1


# ── Test: not_contains check type ─────────────────────────────────────

class TestNotContainsCheck:
    def test_not_contains_passes_when_absent(self):
        """not_contains passes when substring is NOT in output."""
        evals = make_evals([
            make_assertion("a01", "No clichés", "not_contains", value="AI will change everything"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["passed"]) == 1

    def test_not_contains_fails_when_present(self):
        """not_contains fails when substring IS in output."""
        evals = make_evals([
            make_assertion("a01", "No raw transcript", "not_contains", value="um, like"),
        ])
        result = run_assertions("The speaker said um, like, you know", evals)
        assert len(result["failed"]) == 1


# ── Test: max_words check type ────────────────────────────────────────

class TestMaxWordsCheck:
    def test_max_words_passes_when_under_limit(self):
        """max_words passes when word count <= value."""
        evals = make_evals([
            make_assertion("a01", "Output under 200 words", "max_words", value=200),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["passed"]) == 1

    def test_max_words_passes_at_exact_limit(self):
        """max_words passes when word count == value (boundary)."""
        text = "one two three"  # 3 words
        evals = make_evals([
            make_assertion("a01", "Exactly 3 words", "max_words", value=3),
        ])
        result = run_assertions(text, evals)
        assert len(result["passed"]) == 1

    def test_max_words_fails_when_over_limit(self):
        """max_words fails when word count > value."""
        evals = make_evals([
            make_assertion("a01", "Output under 5 words", "max_words", value=5),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["failed"]) == 1
        assert result["failed"][0]["actual"]  # should say actual word count


# ── Test: min_words check type ────────────────────────────────────────

class TestMinWordsCheck:
    def test_min_words_passes_when_over_minimum(self):
        """min_words passes when word count >= value."""
        evals = make_evals([
            make_assertion("a01", "At least 10 words", "min_words", value=10),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["passed"]) == 1

    def test_min_words_passes_at_exact_limit(self):
        """min_words passes when word count == value (boundary)."""
        text = "one two three"  # 3 words
        evals = make_evals([
            make_assertion("a01", "At least 3 words", "min_words", value=3),
        ])
        result = run_assertions(text, evals)
        assert len(result["passed"]) == 1

    def test_min_words_fails_when_under_minimum(self):
        """min_words fails when word count < value."""
        evals = make_evals([
            make_assertion("a01", "At least 1000 words", "min_words", value=1000),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert len(result["failed"]) == 1


# ── Test: result structure ────────────────────────────────────────────

class TestResultStructure:
    def test_total_equals_sum_of_passed_and_failed(self):
        """total must equal len(passed) + len(failed)."""
        evals = make_evals([
            make_assertion("a01", "Has header", "regex", check=r"^## "),
            make_assertion("a02", "No TODO", "not_regex", check=r"TODO"),
            make_assertion("a03", "Has banana", "contains", value="banana"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert result["total"] == len(result["passed"]) + len(result["failed"])

    def test_passed_entries_have_id_and_description(self):
        """Each passed entry must have 'id' and 'description'."""
        evals = make_evals([
            make_assertion("a01", "Has header", "regex", check=r"^## "),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert result["passed"][0]["id"] == "a01"
        assert result["passed"][0]["description"] == "Has header"

    def test_failed_entries_have_actual(self):
        """Each failed entry must have 'actual' describing what was found."""
        evals = make_evals([
            make_assertion("a01", "Has YAML", "regex", check=r"^---"),
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert "actual" in result["failed"][0]
        assert isinstance(result["failed"][0]["actual"], str)
        assert len(result["failed"][0]["actual"]) > 0


# ── Test: edge cases ──────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_output_string(self):
        """All assertions should fail gracefully on empty output."""
        evals = make_evals([
            make_assertion("a01", "Non-empty", "min_words", value=1),
            make_assertion("a02", "Has content", "contains", value="something"),
        ])
        result = run_assertions("", evals)
        assert result["total"] == 2
        assert len(result["passed"]) == 0
        assert len(result["failed"]) == 2

    def test_special_regex_characters(self):
        """Regex with special chars like ( ), [ ], . should be handled."""
        evals = make_evals([
            make_assertion("a01", "Has bullet point", "regex", check=r"^\- ", flags="m"),
        ])
        result = run_assertions("- an item\n- another item", evals)
        assert len(result["passed"]) == 1

    def test_assertions_with_no_flags(self):
        """regex/not_regex with empty flags field works correctly."""
        evals = make_evals([
            make_assertion("a01", "Has TDD", "regex", check="TDD", flags=""),
        ])
        result = run_assertions("TDD is great", evals)
        assert len(result["passed"]) == 1

    def test_deterministic_100_runs(self):
        """Same input + same evals = same result, 100 times."""
        evals = make_evals([
            make_assertion("a01", "Has header", "regex", check=r"^## "),
            make_assertion("a02", "Under 500 words", "max_words", value=500),
            make_assertion("a03", "Has refactor", "contains", value="REFACTOR"),
        ])
        first = run_assertions(SAMPLE_OUTPUT, evals)
        for _ in range(99):
            result = run_assertions(SAMPLE_OUTPUT, evals)
            assert result == first, "Assertion runner is not deterministic!"

    def test_multiple_assertions_mixed_results(self):
        """Mix of passing and failing assertions in one eval."""
        evals = make_evals([
            make_assertion("a01", "Has header", "regex", check=r"^## "),           # pass
            make_assertion("a02", "Has conclusion", "contains", value="## Conclusion"),  # fail
            make_assertion("a03", "Under 500 words", "max_words", value=500),      # pass
            make_assertion("a04", "No TODO", "not_contains", value="[TODO]"),      # pass
        ])
        result = run_assertions(SAMPLE_OUTPUT, evals)
        assert result["total"] == 4
        assert len(result["passed"]) == 3
        assert len(result["failed"]) == 1
        assert result["failed"][0]["id"] == "a02"

    def test_word_count_whitespace_handling(self):
        """Word count should handle multiple spaces, newlines, tabs."""
        text = "one  two\n\nthree\tfour"
        evals = make_evals([
            make_assertion("a01", "Exactly 4 words", "max_words", value=4),
            make_assertion("a02", "At least 4 words", "min_words", value=4),
        ])
        result = run_assertions(text, evals)
        assert len(result["passed"]) == 2
