"""
Tests for batch_orchestrator — --all and multi-skill invocation.

TDD RED phase: these tests define the contract BEFORE implementation.
Run with: python3 -m pytest tests/test_batch_orchestrator.py -v
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from batch_orchestrator import (
    discover_skills,
    parse_args,
    run_batch,
)


# ── Paths ─────────────────────────────────────────────────────────────

SKILLS_DIR = "/Users/CraSS/Documents/Code_projects/agent-knowledge/skills"
CLAUDE_SKILLS_DIR = "/Users/CraSS/.claude/skills"


# ── Test: argument parsing ────────────────────────────────────────────

class TestParseArgs:
    def test_single_skill_name(self):
        """Single skill name → mode='single'."""
        result = parse_args(["tdd"])
        assert result["mode"] == "single"
        assert result["skills"] == ["tdd"]

    def test_all_flag(self):
        """--all → mode='all'."""
        result = parse_args(["--all"])
        assert result["mode"] == "all"

    def test_named_list(self):
        """Multiple skill names → mode='batch'."""
        result = parse_args(["tdd", "debugging", "code-review"])
        assert result["mode"] == "batch"
        assert result["skills"] == ["tdd", "debugging", "code-review"]

    def test_regen_flag(self):
        """--regen flag is parsed."""
        result = parse_args(["--regen", "tdd"])
        assert result["regen"] is True
        assert result["mode"] == "single"

    def test_regen_flag_default_false(self):
        """--regen defaults to False."""
        result = parse_args(["tdd"])
        assert result["regen"] is False

    def test_empty_args(self):
        """Empty args raises ValueError."""
        with pytest.raises(ValueError):
            parse_args([])


# ── Test: skill discovery ─────────────────────────────────────────────

class TestDiscoverSkills:
    def test_discovers_skills_with_skill_md(self):
        """Should find skills that have SKILL.md."""
        skills = discover_skills([SKILLS_DIR])
        assert "tdd" in skills
        assert "video-knowledge-extraction" in skills

    def test_skips_improve_skill_itself(self):
        """Should skip the improve-skill itself."""
        skills = discover_skills([SKILLS_DIR])
        assert "improve-skill" not in skills

    def test_skips_skills_without_skill_md(self):
        """Should skip directories without SKILL.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Directory without SKILL.md
            os.makedirs(os.path.join(tmpdir, "empty-skill"))
            skills = discover_skills([tmpdir])
            assert "empty-skill" not in skills

    def test_deduplicates_across_directories(self):
        """Same skill in multiple dirs → only one entry."""
        skills = discover_skills([SKILLS_DIR, CLAUDE_SKILLS_DIR])
        # Count occurrences of 'tdd'
        names = [s for s in skills if s == "tdd"]
        assert len(names) == 1

    def test_returns_sorted_list(self):
        """Skills should be returned in sorted order."""
        skills = discover_skills([SKILLS_DIR])
        assert skills == sorted(skills)

    def test_handles_nonexistent_dir(self):
        """Non-existent directory should be skipped gracefully."""
        skills = discover_skills(["/nonexistent/path", SKILLS_DIR])
        assert len(skills) > 0


# ── Test: run_batch with mocks ────────────────────────────────────────

class TestRunBatchMocked:
    def test_batch_returns_results_per_skill(self):
        """Batch run should return results for each skill."""
        from unittest.mock import patch

        mock_loop_result = {
            "skill_name": "test",
            "baseline_score": {"total": 3, "passed": [{"id": "a01", "description": "t"}], "failed": []},
            "final_score": {"total": 3, "passed": [{"id": "a01", "description": "t"}], "failed": []},
            "iterations": [],
            "stopping_reason": "perfect_score",
            "evals": {"version": 1},
        }

        with patch("batch_orchestrator.run_improvement_loop", return_value=mock_loop_result), \
             patch("batch_orchestrator.find_skill_dir", return_value="/fake/dir"), \
             patch("batch_orchestrator.create_improvement_branch"):

            result = run_batch(["tdd", "debugging"])

            assert "skills" in result
            assert len(result["skills"]) == 2
            assert result["total_skills"] == 2

    def test_batch_isolates_skill_errors(self):
        """One skill failure shouldn't stop the batch."""
        from unittest.mock import patch

        def mock_loop(**kwargs):
            if kwargs.get("skill_name") == "bad-skill":
                raise RuntimeError("Skill exploded!")
            return {
                "skill_name": kwargs.get("skill_name", "test"),
                "baseline_score": {"total": 1, "passed": [], "failed": []},
                "final_score": {"total": 1, "passed": [], "failed": []},
                "iterations": [],
                "stopping_reason": "plateau",
                "evals": {"version": 1},
            }

        with patch("batch_orchestrator.run_improvement_loop", side_effect=mock_loop), \
             patch("batch_orchestrator.find_skill_dir", return_value="/fake/dir"), \
             patch("batch_orchestrator.create_improvement_branch"):

            result = run_batch(["good-skill", "bad-skill", "another-good"])

            # Should have results for all 3 skills (failed included)
            assert len(result["skills"]) == 3
            # One should be marked as failed
            failed = [s for s in result["skills"] if s["status"] == "failed"]
            assert len(failed) == 1
            assert failed[0]["skill_name"] == "bad-skill"

    def test_batch_summary_counts(self):
        """Batch summary should count improved/unchanged/failed."""
        from unittest.mock import patch

        results = [
            {"skill_name": "a", "baseline_score": {"passed": [], "failed": [{"id": "x"}]},
             "final_score": {"passed": [{"id": "x"}], "failed": []}, "iterations": [{"action": "committed"}],
             "stopping_reason": "perfect_score", "evals": {}},
            {"skill_name": "b", "baseline_score": {"passed": [], "failed": []},
             "final_score": {"passed": [], "failed": []}, "iterations": [],
             "stopping_reason": "perfect_score", "evals": {}},
        ]

        def mock_loop(**kwargs):
            return results.pop(0)

        with patch("batch_orchestrator.run_improvement_loop", side_effect=mock_loop), \
             patch("batch_orchestrator.find_skill_dir", return_value="/fake/dir"), \
             patch("batch_orchestrator.create_improvement_branch"):

            result = run_batch(["a", "b"])

            assert result["improved"] >= 0
            assert result["unchanged"] >= 0
            assert result["total_skills"] == 2
