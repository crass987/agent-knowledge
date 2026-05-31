"""
Tests for improvement_loop — the Karpathy-style improvement cycle.

TDD RED phase: these tests define the contract BEFORE implementation.
Run with: python3 -m pytest tests/test_improvement_loop.py -v
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from improvement_loop import (
    check_stopping_conditions,
    create_improvement_branch,
    inject_rule,
    run_improvement_loop,
    select_target_file,
    IterationResult,
)


# ── Test: stopping conditions ─────────────────────────────────────────

class TestStoppingConditions:
    def test_stops_on_perfect_score(self):
        """Should stop when all assertions pass."""
        result = check_stopping_conditions(
            iteration=3,
            score=10,
            total=10,
            plateau_count=0,
        )
        assert result == "perfect_score"

    def test_stops_on_plateau(self):
        """Should stop after 3 consecutive non-improving iterations."""
        result = check_stopping_conditions(
            iteration=5,
            score=7,
            total=10,
            plateau_count=3,
        )
        assert result == "plateau"

    def test_stops_on_hard_cap(self):
        """Should stop after 10 iterations max."""
        result = check_stopping_conditions(
            iteration=10,
            score=7,
            total=10,
            plateau_count=0,
        )
        assert result == "hard_cap"

    def test_continues_when_not_done(self):
        """Should return None when no stopping condition met."""
        result = check_stopping_conditions(
            iteration=3,
            score=7,
            total=10,
            plateau_count=1,
        )
        assert result is None

    def test_plateau_takes_priority_over_hard_cap(self):
        """If both plateau and hard cap, plateau wins (more specific)."""
        result = check_stopping_conditions(
            iteration=10,
            score=7,
            total=10,
            plateau_count=3,
        )
        assert result == "plateau"

    def test_perfect_score_beats_plateau(self):
        """Perfect score is the highest priority stop reason."""
        result = check_stopping_conditions(
            iteration=10,
            score=10,
            total=10,
            plateau_count=3,
        )
        assert result == "perfect_score"


# ── Test: target file selection ───────────────────────────────────────

class TestTargetFileSelection:
    def test_iterations_1_2_select_skill_md(self):
        """Iterations 1-2 should always target SKILL.md."""
        assert select_target_file(1, []) == "SKILL.md"
        assert select_target_file(2, []) == "SKILL.md"

    def test_iteration_3_falls_back_to_references(self):
        """Iteration 3+ should fall back to reference files."""
        refs = ["templates.md", "quality-checklists.md", "notes.md"]
        result = select_target_file(3, refs)
        assert result == "templates.md"

    def test_iteration_3_no_refs_returns_skill_md(self):
        """If no reference files, iteration 3+ still uses SKILL.md."""
        result = select_target_file(3, [])
        assert result == "SKILL.md"

    def test_reference_priority_order(self):
        """Reference priority: templates → quality-checklists → other."""
        refs = ["notes.md", "quality-checklists.md", "templates.md"]
        result = select_target_file(3, refs)
        assert result == "templates.md"

    def test_no_templates_uses_quality_checklists(self):
        """If no templates.md, fall back to quality-checklists.md."""
        refs = ["notes.md", "quality-checklists.md"]
        result = select_target_file(3, refs)
        assert result == "quality-checklists.md"

    def test_no_priority_refs_uses_first_ref(self):
        """If no priority refs, use first available reference."""
        refs = ["notes.md", "extras.md"]
        result = select_target_file(3, refs)
        assert result == "notes.md"


# ── Test: rule injection ──────────────────────────────────────────────

class TestRuleInjection:
    def test_injects_into_skill_md_with_section(self):
        """Should inject rule into 'Auto-Generated Quality Rules' section."""
        content = "# Skill\n\nSome rules here.\n"
        result = inject_rule(
            content, "SKILL.md", 1, "a01",
            "Always include a summary at the end."
        )
        assert "Auto-Generated Quality Rules" in result
        assert "improve-skill: iteration 1, assertion a01" in result
        assert "Always include a summary at the end." in result
        assert "<!-- /improve-skill -->" in result

    def test_injects_into_existing_auto_section(self):
        """Should append to existing auto-generated section."""
        content = (
            "# Skill\n\n"
            "<!-- improve-skill: iteration 1, assertion a01 -->\n"
            "- Old rule\n"
            "<!-- /improve-skill -->\n"
        )
        result = inject_rule(
            content, "SKILL.md", 2, "a02",
            "New rule text."
        )
        assert "Old rule" in result
        assert "New rule text." in result
        assert "iteration 2, assertion a02" in result

    def test_injects_into_reference_file(self):
        """Should append to reference file with relevant section."""
        content = "## Templates\n\n- Template 1\n"
        result = inject_rule(
            content, "templates.md", 3, "a03",
            "Never use placeholder text."
        )
        assert "Never use placeholder text." in result
        assert "iteration 3, assertion a03" in result

    def test_marker_format_is_correct(self):
        """Injected rule must use exact marker format."""
        content = "# Skill\n"
        result = inject_rule(content, "SKILL.md", 1, "a01", "Rule text.")
        assert "<!-- improve-skill: iteration 1, assertion a01 -->" in result
        assert "- Rule text." in result
        assert "<!-- /improve-skill -->" in result

    def test_injected_rule_starts_with_dash(self):
        """Each injected rule line must start with '- '."""
        content = "# Skill\n"
        result = inject_rule(content, "SKILL.md", 1, "a01", "Rule text.")
        lines = result.strip().split("\n")
        rule_line = [l for l in lines if "Rule text." in l and "improve-skill" not in l]
        assert any(l.strip().startswith("- ") for l in rule_line)


# ── Test: git branch creation ─────────────────────────────────────────

class TestGitBranch:
    def test_branch_name_format_single_skill(self):
        """Single skill branch should be improve/<skill>-YYYY-MM-DD."""
        # We can't test actual git operations in unit tests,
        # but we can test the name format
        from improvement_loop import format_branch_name
        name = format_branch_name("tdd", batch=False)
        assert name.startswith("improve/tdd-")
        # Should contain today's date
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        assert today in name

    def test_branch_name_format_batch(self):
        """Batch branch should be improve/batch-YYYY-MM-DD."""
        from improvement_loop import format_branch_name
        name = format_branch_name("", batch=True)
        assert name.startswith("improve/batch-")
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        assert today in name


# ── Test: IterationResult dataclass ───────────────────────────────────

class TestIterationResult:
    def test_iteration_result_fields(self):
        """IterationResult should have all required fields."""
        r = IterationResult(
            iteration=1,
            target_file="SKILL.md",
            rule_injected="Always include summary",
            assertion_id="a01",
            score_before=5,
            score_after=7,
            total=10,
            action="committed",
        )
        assert r.iteration == 1
        assert r.target_file == "SKILL.md"
        assert r.action == "committed"
        assert r.score_after > r.score_before

    def test_iteration_result_reverted(self):
        """Reverted iterations should have action='reverted'."""
        r = IterationResult(
            iteration=2,
            target_file="SKILL.md",
            rule_injected="Bad rule",
            assertion_id="a02",
            score_before=7,
            score_after=7,
            total=10,
            action="reverted",
        )
        assert r.action == "reverted"
        assert r.score_after == r.score_before


# ── Test: run_improvement_loop with mocks ─────────────────────────────

class TestImprovementLoopMocked:
    def test_loop_tracks_iterations(self):
        """Loop should track iteration history."""
        from unittest.mock import patch, MagicMock

        # Mock all external dependencies
        mock_evals = {
            "version": 1, "skill": "test", "generated_at": "2026-01-01T00:00:00Z",
            "test_input": {"type": "prompt", "text": "test"},
            "assertions": [
                {"id": "a01", "description": "Has header", "source_rule": "r",
                 "type": "regex", "check": "^## ", "flags": "m"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal skill dir
            with open(os.path.join(tmpdir, "SKILL.md"), "w") as f:
                f.write("# Test Skill\n\nDo things.\n")

            with patch("improvement_loop.generate_evals", return_value=mock_evals), \
                 patch("improvement_loop.run_skill", return_value="## Output\nSome text"), \
                 patch("improvement_loop.git_commit"), \
                 patch("improvement_loop.git_checkout_file"), \
                 patch("improvement_loop.create_improvement_branch"):

                result = run_improvement_loop(
                    skill_dir=tmpdir,
                    skill_name="test",
                    max_iterations=3,
                )

                assert "iterations" in result
                assert "baseline_score" in result
                assert "final_score" in result
                assert "stopping_reason" in result

    def test_loop_stops_on_perfect_score(self):
        """Loop should stop immediately on perfect score."""
        from unittest.mock import patch

        mock_evals = {
            "version": 1, "skill": "test", "generated_at": "2026-01-01T00:00:00Z",
            "test_input": {"type": "prompt", "text": "test"},
            "assertions": [
                {"id": "a01", "description": "Has text", "source_rule": "r",
                 "type": "contains", "value": "text"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "SKILL.md"), "w") as f:
                f.write("# Test\n")

            with patch("improvement_loop.generate_evals", return_value=mock_evals), \
                 patch("improvement_loop.run_skill", return_value="some text here"), \
                 patch("improvement_loop.create_improvement_branch"):

                result = run_improvement_loop(
                    skill_dir=tmpdir,
                    skill_name="test",
                    max_iterations=10,
                )

                assert result["stopping_reason"] == "perfect_score"
                assert len(result["final_score"]["passed"]) == 1
                assert len(result["iterations"]) == 0  # No iterations needed
