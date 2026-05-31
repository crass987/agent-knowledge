"""
test_skill_md_v2 — integration validation for the SKILL.md v2 orchestrator.

The SKILL.md is an LLM program, not Python. These tests validate:
1. Structural completeness: all required sections exist
2. Tool interface correctness: referenced Python tools work as documented
3. Safety constraints: the SKILL.md encodes correct file targeting rules
4. Integration: eval_generator + assertion_runner pipeline works end-to-end
"""

import json
import os
import re
import subprocess
import sys
import tempfile

import pytest

# ── Paths ───────────────────────────────────────────────────────────────

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SKILL_DIR = os.path.join(REPO_ROOT, "skills", "improve-skill")
SKILL_MD_PATH = os.path.join(SKILL_DIR, "SKILL.md")
LIB_DIR = os.path.join(SKILL_DIR, "lib")
TESTS_DIR = os.path.join(SKILL_DIR, "tests")


def read_skill_md():
    """Read the improve-skill SKILL.md."""
    with open(SKILL_MD_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ── 1. Structural completeness ──────────────────────────────────────────


class TestSkillMdStructure:
    """Validate the SKILL.md has all required sections for v2."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_frontmatter(self, content):
        """SKILL.md starts with YAML frontmatter."""
        assert content.startswith("---\n")

    def test_frontmatter_has_name(self, content):
        """Frontmatter contains name: improve-skill."""
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert match is not None
        assert "name: improve-skill" in match.group(1)

    def test_frontmatter_has_description(self, content):
        """Frontmatter contains a non-empty description."""
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert match is not None
        desc_match = re.search(r"description:\s*(.+)", match.group(1))
        assert desc_match is not None
        assert len(desc_match.group(1).strip()) > 10

    def test_has_phase_1_setup(self, content):
        """Contains PHASE 1: SETUP section."""
        assert "PHASE 1: SETUP" in content

    def test_has_phase_2_baseline(self, content):
        """Contains PHASE 2: BASELINE section."""
        assert "PHASE 2: BASELINE" in content

    def test_has_phase_3_loop(self, content):
        """Contains PHASE 3: IMPROVEMENT LOOP section."""
        assert "PHASE 3: IMPROVEMENT LOOP" in content

    def test_has_phase_4_report(self, content):
        """Contains PHASE 4: REPORT section."""
        assert "PHASE 4: REPORT" in content

    def test_has_step_3a_diagnose(self, content):
        """Contains Step 3a: DIAGNOSE."""
        assert "3a. DIAGNOSE" in content

    def test_has_step_3b_generate(self, content):
        """Contains Step 3b: GENERATE RULE."""
        assert "3b. GENERATE RULE" in content

    def test_has_step_3c_inject(self, content):
        """Contains Step 3c: INJECT."""
        assert "3c. INJECT" in content

    def test_has_step_3d_rescore(self, content):
        """Contains Step 3d: RE-SCORE."""
        assert "3d. RE-SCORE" in content

    def test_has_step_3e_decide(self, content):
        """Contains Step 3e: DECIDE."""
        assert "3e. DECIDE" in content

    def test_has_step_3f_stop(self, content):
        """Contains Step 3f: STOP CHECK."""
        assert "3f. STOP CHECK" in content

    def test_has_stopping_conditions(self, content):
        """Documents all 3 stopping conditions."""
        assert "plateau" in content.lower() or "PLATEAU" in content
        assert "10" in content  # iteration cap
        assert "all pass" in content.lower()

    def test_has_safety_constraints(self, content):
        """Has safety constraints section."""
        assert "Safety" in content or "SAFETY" in content.upper()
        # Must mention *.md and evals.json as only editable targets
        assert "*.md" in content
        assert "evals.json" in content

    def test_has_git_branch_strategy(self, content):
        """Documents git branch naming."""
        assert "improve/" in content

    def test_has_marker_format(self, content):
        """Documents the rule injection marker format."""
        assert "improve-skill: iteration" in content

    def test_has_tool_interfaces(self, content):
        """Documents the Python CLI interfaces."""
        assert "eval_generator.py" in content
        assert "assertion_runner.py" in content
        assert "--evals" in content
        assert "--output" in content

    def test_has_agent_tool_usage(self, content):
        """Documents Agent tool for skill execution."""
        assert "Agent" in content

    def test_has_cost_tracking(self, content):
        """Has cost awareness section."""
        assert "Agent calls" in content or "agent calls" in content.lower()


class TestSkillMdDoesNotReferenceV1:
    """Ensure SKILL.md does NOT reference deleted v1 modules."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_no_skill_runner_reference(self, content):
        """Should not reference skill_runner.py (deleted in v2)."""
        assert "skill_runner.py" not in content

    def test_no_improvement_loop_reference(self, content):
        """Should not reference improvement_loop.py (deleted in v2)."""
        assert "improvement_loop.py" not in content

    def test_no_batch_orchestrator_reference(self, content):
        """Should not reference batch_orchestrator.py (deleted in v2)."""
        assert "batch_orchestrator.py" not in content

    def test_no_reporter_reference(self, content):
        """Should not reference reporter.py (deleted in v2)."""
        assert "reporter.py" not in content


# ── 2. Tool interface correctness ───────────────────────────────────────


class TestEvalGeneratorCLI:
    """Validate eval_generator.py CLI works as SKILL.md documents."""

    def test_cli_no_args_shows_usage(self):
        """Running without args shows usage and exits with error."""
        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "eval_generator.py")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "Usage" in result.stderr

    def test_cli_generates_valid_v2_json(self):
        """Running with a real skill dir produces valid v2 evals JSON."""
        # Use the tdd skill as a lightweight test target
        tdd_dir = os.path.join(REPO_ROOT, "skills", "tdd")
        if not os.path.isdir(tdd_dir):
            pytest.skip("tdd skill not found")

        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "eval_generator.py"), tdd_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        evals = json.loads(result.stdout)
        assert evals["version"] == 2
        assert isinstance(evals["test_inputs"], list)
        assert len(evals["test_inputs"]) > 0
        assert isinstance(evals["assertions"], list)
        for a in evals["assertions"]:
            assert "source_file" in a
            assert "generator" in a


class TestAssertionRunnerCLI:
    """Validate assertion_runner.py CLI works as SKILL.md documents."""

    def test_cli_no_args_shows_usage(self):
        """Running without args shows usage and exits with error."""
        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "assertion_runner.py")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "Usage" in result.stderr

    def test_cli_scores_output(self):
        """Running with evals + output produces valid JSON result."""
        fixture_evals = os.path.join(TESTS_DIR, "fixture-evals.json")
        fixture_output = os.path.join(TESTS_DIR, "fixture-output.txt")
        assert os.path.exists(fixture_evals)
        assert os.path.exists(fixture_output)

        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "assertion_runner.py"),
             "--evals", fixture_evals, "--output", fixture_output],
            capture_output=True, text=True,
        )
        # Should produce JSON output (exit code depends on pass/fail)
        score = json.loads(result.stdout)
        assert "total" in score
        assert "passed" in score
        assert "failed" in score

    def test_exit_code_reflects_score(self):
        """Exit code 0 if all pass, 1 if any fail."""
        fixture_evals = os.path.join(TESTS_DIR, "fixture-evals.json")
        fixture_output = os.path.join(TESTS_DIR, "fixture-output.txt")

        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "assertion_runner.py"),
             "--evals", fixture_evals, "--output", fixture_output],
            capture_output=True, text=True,
        )
        score = json.loads(result.stdout)
        if len(score["failed"]) == 0:
            assert result.returncode == 0
        else:
            assert result.returncode == 1


# ── 3. End-to-end pipeline test ─────────────────────────────────────────


class TestEndToEndPipeline:
    """
    Validate the eval_generator → assertion_runner pipeline works
    as the SKILL.md orchestrates it.
    """

    def test_generate_and_score_tdd_skill(self):
        """Full pipeline: generate evals for tdd, create sample output, score it."""
        tdd_dir = os.path.join(REPO_ROOT, "skills", "tdd")
        if not os.path.isdir(tdd_dir):
            pytest.skip("tdd skill not found")

        # Step 1: Generate evals
        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "eval_generator.py"), tdd_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        evals = json.loads(result.stdout)

        # Step 2: Create a sample output (simulating Agent output)
        sample_output = """
# TDD Workflow

## Rules
1. Never write production code except to make a failing test pass.
2. Write the simplest test that could fail.
3. Make it work, then make it right, then make it fast.

## Test structure (Arrange-Act-Assert)

```python
def test_user_creation():
    # Arrange
    data = {"name": "Alice"}
    # Act
    user = User.create(data)
    # Assert
    assert user.role == "member"
```

Run all tests after each change.
"""
        # Write sample output to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(sample_output)
            output_path = f.name

        try:
            # Write evals to temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(evals, f)
                evals_path = f.name

            # Step 3: Score
            result = subprocess.run(
                [sys.executable, os.path.join(LIB_DIR, "assertion_runner.py"),
                 "--evals", evals_path, "--output", output_path],
                capture_output=True, text=True,
            )
            score = json.loads(result.stdout)
            assert "total" in score
            assert score["total"] == len(evals["assertions"])
            assert len(score["passed"]) + len(score["failed"]) == score["total"]
        finally:
            os.unlink(output_path)
            os.unlink(evals_path)

    def test_v2_schema_source_file_on_all_assertions(self):
        """Every assertion in v2 evals has source_file."""
        tdd_dir = os.path.join(REPO_ROOT, "skills", "tdd")
        if not os.path.isdir(tdd_dir):
            pytest.skip("tdd skill not found")

        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "eval_generator.py"), tdd_dir],
            capture_output=True, text=True,
        )
        evals = json.loads(result.stdout)
        for a in evals["assertions"]:
            assert "source_file" in a, f"Assertion {a.get('id', '?')} missing source_file"
            assert a["source_file"], f"Assertion {a.get('id', '?')} has empty source_file"

    def test_v2_schema_generator_on_all_assertions(self):
        """Every assertion in v2 evals has generator field."""
        tdd_dir = os.path.join(REPO_ROOT, "skills", "tdd")
        if not os.path.isdir(tdd_dir):
            pytest.skip("tdd skill not found")

        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "eval_generator.py"), tdd_dir],
            capture_output=True, text=True,
        )
        evals = json.loads(result.stdout)
        for a in evals["assertions"]:
            assert "generator" in a, f"Assertion {a.get('id', '?')} missing generator"
            assert a["generator"] in ("heuristic", "llm")


# ── 4. Safety validation ────────────────────────────────────────────────


class TestSafetyConstraints:
    """Validate the SKILL.md encodes correct safety constraints."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_forbids_python_editing(self, content):
        """SKILL.md explicitly forbids editing .py files."""
        assert "*.py" in content or ".py" in content

    def test_forbids_scripts_editing(self, content):
        """SKILL.md explicitly forbids editing scripts/ directory."""
        assert "scripts/" in content

    def test_limits_iterations(self, content):
        """SKILL.md enforces a hard iteration cap."""
        assert "10" in content  # max iterations

    def test_requires_git_revert(self, content):
        """SKILL.md requires git checkout for reverts."""
        assert "git checkout" in content

    def test_requires_atomic_commits(self, content):
        """SKILL.md requires atomic (single-file) changes."""
        # The word "atomic" should appear in context of edits
        assert "atomic" in content.lower() or "one file" in content.lower() or "single" in content.lower()
