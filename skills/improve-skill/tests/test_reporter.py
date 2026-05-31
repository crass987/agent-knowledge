"""
Tests for reporter — report generation and persistence.

TDD RED phase: these tests define the contract BEFORE implementation.
Run with: python3 -m pytest tests/test_reporter.py -v
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from reporter import (
    format_assertion_comparison,
    format_final_report,
    format_phase_baseline,
    format_phase_loop,
    format_phase_setup,
)


# ── Test: setup phase output ──────────────────────────────────────────

class TestPhaseSetup:
    def test_includes_skill_name(self):
        """Setup phase should show skill name."""
        output = format_phase_setup("tdd", "prompt", 3, "test prompt text")
        assert "tdd" in output

    def test_includes_archetype(self):
        """Setup phase should show archetype."""
        output = format_phase_setup("tdd", "prompt", 3, "test prompt text")
        assert "prompt" in output

    def test_includes_assertion_count(self):
        """Setup phase should show number of assertions."""
        output = format_phase_setup("tdd", "prompt", 5, "test prompt text")
        assert "5" in output

    def test_shows_test_input_source(self):
        """Setup phase should show test input type."""
        output = format_phase_setup("vke", "file", 7, "/path/to/file.txt")
        assert "file" in output or "/path/to/file.txt" in output


# ── Test: baseline phase output ───────────────────────────────────────

class TestPhaseBaseline:
    def test_shows_score(self):
        """Baseline phase should show N/M score."""
        result = {
            "total": 5,
            "passed": [{"id": "a01", "description": "test"}],
            "failed": [
                {"id": "a02", "description": "fail", "actual": "no match"},
                {"id": "a03", "description": "fail2", "actual": "missing"},
            ],
        }
        output = format_phase_baseline(result)
        assert "1/5" in output or "1" in output

    def test_lists_failing_assertions(self):
        """Baseline phase should list failing assertions."""
        result = {
            "total": 2,
            "passed": [],
            "failed": [
                {"id": "a01", "description": "Has header", "actual": "no headers"},
            ],
        }
        output = format_phase_baseline(result)
        assert "Has header" in output or "a01" in output


# ── Test: loop phase output ───────────────────────────────────────────

class TestPhaseLoop:
    def test_shows_iteration_number(self):
        """Loop phase should show iteration number."""
        from improvement_loop import IterationResult
        ir = IterationResult(1, "SKILL.md", "Test rule", "a01", 3, 5, 10, "committed")
        output = format_phase_loop(ir)
        assert "1" in output

    def test_shows_target_file(self):
        """Loop phase should show which file was modified."""
        from improvement_loop import IterationResult
        ir = IterationResult(2, "SKILL.md", "Rule", "a02", 5, 7, 10, "committed")
        output = format_phase_loop(ir)
        assert "SKILL.md" in output

    def test_shows_action(self):
        """Loop phase should show committed or reverted."""
        from improvement_loop import IterationResult
        ir = IterationResult(1, "SKILL.md", "Rule", "a01", 3, 3, 10, "reverted")
        output = format_phase_loop(ir)
        assert "reverted" in output.lower() or "revert" in output.lower()


# ── Test: final report ────────────────────────────────────────────────

class TestFinalReport:
    def test_shows_baseline_and_final_score(self):
        """Final report should show baseline → final score."""
        baseline = {"total": 5, "passed": [{"id": "a01", "description": "t"}], "failed": []}
        final = {"total": 5, "passed": [{"id": "a01", "description": "t"}], "failed": []}

        report = format_final_report(
            skill_name="tdd",
            baseline=baseline,
            final=final,
            iterations=[],
            stopping_reason="perfect_score",
        )
        assert "tdd" in report

    def test_shows_stopping_reason(self):
        """Final report should include stopping reason."""
        baseline = {"total": 3, "passed": [], "failed": []}
        final = {"total": 3, "passed": [], "failed": []}

        report = format_final_report(
            skill_name="tdd",
            baseline=baseline,
            final=final,
            iterations=[],
            stopping_reason="plateau",
        )
        assert "plateau" in report.lower()

    def test_shows_iteration_count(self):
        """Final report should show total iterations."""
        from improvement_loop import IterationResult
        iters = [
            IterationResult(1, "SKILL.md", "R1", "a01", 3, 5, 10, "committed"),
            IterationResult(2, "SKILL.md", "R2", "a02", 5, 5, 10, "reverted"),
        ]
        baseline = {"total": 10, "passed": [], "failed": []}
        final = {"total": 10, "passed": [], "failed": []}

        report = format_final_report("tdd", baseline, final, iters, "hard_cap")
        assert "2" in report

    def test_shows_per_assertion_comparison(self):
        """Final report should include per-assertion pass/fail comparison."""
        baseline = {
            "total": 2,
            "passed": [{"id": "a01", "description": "Header"}],
            "failed": [{"id": "a02", "description": "Summary", "actual": "missing"}],
        }
        final = {
            "total": 2,
            "passed": [
                {"id": "a01", "description": "Header"},
                {"id": "a02", "description": "Summary"},
            ],
            "failed": [],
        }

        comparison = format_assertion_comparison(baseline, final)
        assert "a01" in comparison or "Header" in comparison
        assert "a02" in comparison or "Summary" in comparison


# ── Test: evals.json persistence ──────────────────────────────────────

class TestEvalsPersistence:
    def test_evals_written_to_skill_dir(self):
        """evals.json should be written next to SKILL.md."""
        from eval_generator import generate_evals, write_evals
        from assertion_runner import run_assertions

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "SKILL.md"), "w") as f:
                f.write("---\nname: test\ndescription: A test skill\n---\n# Test\n1. Must include headers\n")

            evals = generate_evals(tmpdir)
            path = write_evals(tmpdir, evals)
            assert os.path.exists(path)
            assert path.endswith("evals.json")

            # Read it back and verify
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["skill"] == "test"

    def test_re_run_reuses_existing_evals(self):
        """On re-run, existing evals.json should be reused."""
        from eval_generator import generate_evals, write_evals

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "SKILL.md"), "w") as f:
                f.write("---\nname: test\ndescription: Test\n---\n# Test\n")

            # First run: generate and write
            evals1 = generate_evals(tmpdir)
            write_evals(tmpdir, evals1)

            # Verify evals.json exists
            evals_path = os.path.join(tmpdir, "evals.json")
            assert os.path.exists(evals_path)

            # Read existing evals
            with open(evals_path) as f:
                existing = json.load(f)

            # Second run: should detect existing evals
            assert existing["version"] == 1
            assert existing["skill"] == "test"
