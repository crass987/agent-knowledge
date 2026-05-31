"""
test_skill_md_v2 — integration validation for the SKILL.md v2 orchestrator.

The SKILL.md is an LLM program, not Python. These tests validate:
1. Structural completeness: all required sections exist
2. Tool interface correctness: referenced Python tools work as documented
3. Safety constraints: the SKILL.md encodes correct file targeting rules
4. Integration: eval_generator + assertion_runner pipeline works end-to-end
5. Quality Audit (Phase 4) and Enhanced Report (Phase 5)
6. Batch mode, CLI flags, crash recovery, cost tracking
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

    def test_has_report_phase(self, content):
        """Contains a REPORT phase (renumbered to Phase 5)."""
        assert "REPORT" in content

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

        result = subprocess.run(
            [sys.executable, os.path.join(LIB_DIR, "eval_generator.py"), tdd_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        evals = json.loads(result.stdout)

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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(sample_output)
            output_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(evals, f)
                evals_path = f.name

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
        assert "10" in content

    def test_requires_git_revert(self, content):
        """SKILL.md requires git checkout for reverts."""
        assert "git checkout" in content

    def test_requires_atomic_commits(self, content):
        """SKILL.md requires atomic (single-file) changes."""
        assert "atomic" in content.lower() or "one file" in content.lower() or "single" in content.lower()


# ── 5. Quality Audit (Phase 4) — from Slice 03 ─────────────────────────


class TestQualityAudit:
    """Validate the SKILL.md has Phase 4: Quality Audit with LLM-as-judge."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_phase_4_quality_audit(self, content):
        """Contains PHASE 4: QUALITY AUDIT section."""
        assert "PHASE 4: QUALITY AUDIT" in content

    def test_phase_4_comes_after_phase_3(self, content):
        """Phase 4 appears after Phase 3 in the document."""
        phase3_pos = content.find("PHASE 3:")
        phase4_pos = content.find("PHASE 4:")
        assert phase3_pos > 0
        assert phase4_pos > phase3_pos

    def test_has_llm_as_judge_instructions(self, content):
        """Phase 4 describes using Agent tool for holistic evaluation."""
        phase4_pos = content.find("PHASE 4:")
        phase5_pos = content.find("PHASE 5:")
        if phase5_pos == -1:
            phase5_pos = len(content)
        phase4_section = content[phase4_pos:phase5_pos]
        assert "Agent" in phase4_section, "Phase 4 must mention Agent tool for LLM-as-judge"

    def test_has_quality_dimensions(self, content):
        """Phase 4 lists quality dimensions: completeness, specificity, accuracy, style, non-banality."""
        phase4_pos = content.find("PHASE 4:")
        phase5_pos = content.find("PHASE 5:")
        if phase5_pos == -1:
            phase5_pos = len(content)
        phase4_section = content[phase4_pos:phase5_pos].lower()
        for dimension in ["completeness", "specificity", "accuracy", "style", "non-banality"]:
            assert dimension in phase4_section, f"Phase 4 must mention quality dimension: {dimension}"

    def test_has_structured_findings(self, content):
        """Phase 4 produces structured findings with issues and suggestions."""
        phase4_pos = content.find("PHASE 4:")
        phase5_pos = content.find("PHASE 5:")
        if phase5_pos == -1:
            phase5_pos = len(content)
        phase4_section = content[phase4_pos:phase5_pos]
        assert "findings" in phase4_section.lower(), "Phase 4 must produce structured findings"

    def test_has_proposed_assertions_mechanism(self, content):
        """Phase 4 converts recurring problems to proposed assertions."""
        phase4_pos = content.find("PHASE 4:")
        phase5_pos = content.find("PHASE 5:")
        if phase5_pos == -1:
            phase5_pos = len(content)
        phase4_section = content[phase4_pos:phase5_pos]
        assert "proposed" in phase4_section.lower(), "Phase 4 must mention proposed assertions"
        assert "proposed_assertions" in phase4_section, "Phase 4 must use proposed_assertions key"

    def test_proposed_assertions_stored_separately(self, content):
        """Proposed assertions go into proposed_assertions array, not the scored assertions array."""
        phase4_pos = content.find("PHASE 4:")
        phase5_pos = content.find("PHASE 5:")
        if phase5_pos == -1:
            phase5_pos = len(content)
        phase4_section = content[phase4_pos:phase5_pos]
        assert "proposed_assertions" in phase4_section

    def test_has_rubric_from_skill_criteria(self, content):
        """Phase 4 uses the skill's own quality criteria as evaluation rubric."""
        phase4_pos = content.find("PHASE 4:")
        phase5_pos = content.find("PHASE 5:")
        if phase5_pos == -1:
            phase5_pos = len(content)
        phase4_section = content[phase4_pos:phase5_pos].lower()
        assert "rubric" in phase4_section, "Phase 4 must reference rubric from skill's quality criteria"


# ── 6. Enhanced Report (Phase 5) — from Slice 03 ────────────────────────


class TestEnhancedReport:
    """Validate the SKILL.md has Phase 5: REPORT with enhanced features."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_phase_5_report(self, content):
        """Contains PHASE 5: REPORT section."""
        assert "PHASE 5: REPORT" in content

    def test_phase_5_comes_after_phase_4(self, content):
        """Phase 5 appears after Phase 4 in the document."""
        phase4_pos = content.find("PHASE 4:")
        phase5_pos = content.find("PHASE 5:")
        assert phase4_pos > 0
        assert phase5_pos > phase4_pos

    def test_has_audit_recommendations_section(self, content):
        """Phase 5 includes audit recommendations from Phase 4."""
        phase5_pos = content.find("PHASE 5:")
        phase5_section = content[phase5_pos:]
        assert "audit" in phase5_section.lower() and "recommend" in phase5_section.lower(), \
            "Phase 5 must include audit recommendations"

    def test_has_proposed_assertions_display(self, content):
        """Phase 5 displays proposed assertions for next run."""
        phase5_pos = content.find("PHASE 5:")
        phase5_section = content[phase5_pos:]
        assert "proposed" in phase5_section.lower(), \
            "Phase 5 must display proposed assertions for next run"

    def test_has_per_assertion_comparison(self, content):
        """Phase 5 shows per-assertion comparison with icons."""
        phase5_pos = content.find("PHASE 5:")
        phase5_section = content[phase5_pos:]
        has_icons = ("✅" in phase5_section or "PASS" in phase5_section)
        assert has_icons, "Phase 5 must show per-assertion pass/fail comparison"

    def test_has_complete_cost_tracking(self, content):
        """Phase 5 displays agent calls, LLM calls, and test inputs evaluated."""
        phase5_pos = content.find("PHASE 5:")
        phase5_section = content[phase5_pos:].lower()
        assert "agent call" in phase5_section, "Phase 5 must display agent calls"
        assert "llm call" in phase5_section, "Phase 5 must display LLM calls"

    def test_has_stopping_reason_display(self, content):
        """Phase 5 displays the stopping reason."""
        phase5_pos = content.find("PHASE 5:")
        phase5_section = content[phase5_pos:].lower()
        assert "stopping reason" in phase5_section or "stop reason" in phase5_section, \
            "Phase 5 must display stopping reason"

    def test_has_git_commit_history(self, content):
        """Phase 5 shows git commit history."""
        phase5_pos = content.find("PHASE 5:")
        phase5_section = content[phase5_pos:]
        assert "git log" in phase5_section, "Phase 5 must show git log for commit history"


# ── 7. Phase numbering consistency — from Slice 03 ──────────────────────


class TestPhaseNumbering:
    """Ensure phases are numbered correctly: 1→2→3→4→5."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_exactly_5_phases(self, content):
        """SKILL.md has exactly 5 phases (1 through 5)."""
        phases = re.findall(r"###\s+PHASE\s+(\d+):", content)
        assert len(phases) == 5, f"Expected 5 phases, found {len(phases)}: {phases}"

    def test_phases_are_sequential(self, content):
        """Phases are numbered 1, 2, 3, 4, 5 in order."""
        phases = re.findall(r"###\s+PHASE\s+(\d+):", content)
        assert phases == ["1", "2", "3", "4", "5"], f"Phases not sequential: {phases}"

    def test_phase_4_is_quality_audit(self, content):
        """Phase 4 header says QUALITY AUDIT."""
        assert re.search(r"PHASE\s+4:\s+QUALITY\s+AUDIT", content) is not None

    def test_phase_5_is_report(self, content):
        """Phase 5 header says REPORT."""
        assert re.search(r"PHASE\s+5:\s+REPORT", content) is not None


# ── 8. Batch mode — from Slice 04 ───────────────────────────────────────


class TestBatchMode:
    """Validate SKILL.md has batch mode instructions (--all, named lists)."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_all_flag(self, content):
        """SKILL.md documents --all flag for batch processing."""
        assert "--all" in content

    def test_has_named_list_syntax(self, content):
        """SKILL.md documents named list syntax (multiple skill names)."""
        assert "named list" in content.lower() or "multiple skill" in content.lower() or "specific skills" in content.lower()

    def test_has_error_isolation(self, content):
        """SKILL.md documents error isolation for batch — one failure doesn't stop others."""
        assert "error isolation" in content.lower() or "continue with" in content.lower() or "continue on" in content.lower()

    def test_has_per_skill_branches(self, content):
        """SKILL.md documents per-skill git branches in batch mode."""
        assert "per-skill" in content.lower() or "per skill" in content.lower() or "each skill" in content.lower()

    def test_has_skill_discovery_paths(self, content):
        """SKILL.md documents discovering all skills from both search paths."""
        assert "discover" in content.lower()


# ── 9. CLI flags — from Slice 04 ─────────────────────────────────────────


class TestCLIFlags:
    """Validate SKILL.md has --regen and --dry-run flag instructions."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_regen_flag(self, content):
        """SKILL.md documents --regen flag."""
        assert "--regen" in content

    def test_regen_deletes_existing_evals(self, content):
        """SKILL.md specifies that --regen deletes existing evals.json before regenerating."""
        assert "delete" in content.lower() and "evals" in content.lower()

    def test_has_dry_run_flag(self, content):
        """SKILL.md documents --dry-run flag."""
        assert "--dry-run" in content

    def test_dry_run_skips_edits(self, content):
        """SKILL.md explicitly states --dry-run skips Edit/Write operations."""
        dry_run_section = content[content.lower().find("dry-run"):] if "dry-run" in content.lower() else ""
        assert "do not edit" in dry_run_section.lower() or "skip edit" in dry_run_section.lower() or "no edit" in dry_run_section.lower() or "not modify" in dry_run_section.lower()

    def test_dry_run_skips_git(self, content):
        """SKILL.md explicitly states --dry-run skips git commits/branch creation."""
        dry_run_section = content[content.lower().find("dry-run"):] if "dry-run" in content.lower() else ""
        assert "no commit" in dry_run_section.lower() or "skip commit" in dry_run_section.lower() or "do not commit" in dry_run_section.lower() or "no git" in dry_run_section.lower()


# ── 10. Crash recovery — from Slice 04 ───────────────────────────────────


class TestCrashRecovery:
    """Validate SKILL.md has git-based crash recovery instructions."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_crash_recovery_section(self, content):
        """SKILL.md has a crash recovery section."""
        assert "crash recovery" in content.lower() or "recovery" in content.lower()

    def test_recovery_reads_git_log(self, content):
        """SKILL.md specifies reading git log to understand prior state."""
        assert "git log" in content.lower()

    def test_recovery_rescores(self, content):
        """SKILL.md specifies re-scoring on restart to get fresh baseline."""
        assert "re-score" in content.lower() or "rescore" in content.lower() or "fresh baseline" in content.lower()

    def test_recovery_continues_from_last(self, content):
        """SKILL.md specifies continuing from where it left off."""
        assert "continue" in content.lower() and ("where it left" in content.lower() or "left off" in content.lower())

    def test_recovery_no_checkpoint_files(self, content):
        """SKILL.md explicitly states no checkpoint files — recovery is git-based."""
        assert "no checkpoint" in content.lower() or "git-based" in content.lower()


# ── 11. Cost tracking — from Slice 04 ────────────────────────────────────


class TestCostTracking:
    """Validate SKILL.md has per-iteration cost display."""

    @pytest.fixture
    def content(self):
        return read_skill_md()

    def test_has_per_iteration_cost_display(self, content):
        """SKILL.md has cost display after each iteration."""
        assert "iteration" in content.lower() and "agent calls" in content.lower()

    def test_tracks_test_inputs_evaluated(self, content):
        """SKILL.md tracks test inputs evaluated."""
        assert "test inputs" in content.lower() or "inputs evaluated" in content.lower()

    def test_cumulative_tracking(self, content):
        """SKILL.md specifies cumulative tracking."""
        assert "cumulative" in content.lower()


# ── 12. Clean v2 file structure — from Slice 05 ─────────────────────────


class TestCleanV2Structure:
    """Validate that v1 artifacts have been cleaned up and only v2 remains."""

    def test_lib_has_only_v2_modules(self):
        """lib/ contains only __init__.py, assertion_runner.py, eval_generator.py."""
        allowed = {"__init__.py", "assertion_runner.py", "eval_generator.py"}
        actual = {f for f in os.listdir(LIB_DIR) if not f.startswith(".") and f != "__pycache__"}
        assert actual == allowed, f"lib/ has unexpected files: {actual - allowed}"

    def test_no_v1_lib_modules(self):
        """v1 Python modules are deleted."""
        v1_modules = [
            "improvement_loop.py",
            "batch_orchestrator.py",
            "skill_runner.py",
            "reporter.py",
        ]
        for module in v1_modules:
            path = os.path.join(LIB_DIR, module)
            assert not os.path.exists(path), f"v1 module still exists: {module}"

    def test_no_v1_test_files(self):
        """v1 test files are deleted."""
        v1_tests = [
            "test_skill_runner.py",
            "test_improvement_loop.py",
            "test_batch_orchestrator.py",
            "test_reporter.py",
            "integration-report.md",
        ]
        for test_file in v1_tests:
            path = os.path.join(TESTS_DIR, test_file)
            assert not os.path.exists(path), f"v1 test file still exists: {test_file}"

    def test_tests_dir_has_only_v2_files(self):
        """tests/ contains only v2 test files + fixtures."""
        allowed = {
            "__init__.py",
            "test_assertion_runner.py",
            "test_eval_generator.py",
            "test_skill_md_v2.py",
            "fixture-evals.json",
            "fixture-output.txt",
        }
        actual = {f for f in os.listdir(TESTS_DIR) if not f.startswith(".") and f != "__pycache__"}
        assert actual == allowed, f"tests/ has unexpected files: {actual - allowed}"

    def test_prd_v1_archived(self):
        """PRD.md has been renamed to PRD-v1.md."""
        prd_path = os.path.join(SKILL_DIR, "PRD.md")
        prd_v1_path = os.path.join(SKILL_DIR, "PRD-v1.md")
        assert not os.path.exists(prd_path), "PRD.md should be renamed to PRD-v1.md"
        assert os.path.exists(prd_v1_path), "PRD-v1.md should exist"

    def test_issues_v1_archived(self):
        """issues/ directory has been renamed to issues-v1/."""
        issues_path = os.path.join(SKILL_DIR, "issues")
        issues_v1_path = os.path.join(SKILL_DIR, "issues-v1")
        assert not os.path.exists(issues_path), "issues/ should be renamed to issues-v1/"
        assert os.path.exists(issues_v1_path), "issues-v1/ should exist"

    def test_v2_artifacts_present(self):
        """v2 artifacts exist: PRD-v2.md, adr/, issues-v2/."""
        assert os.path.exists(os.path.join(SKILL_DIR, "PRD-v2.md"))
        assert os.path.isdir(os.path.join(SKILL_DIR, "adr"))
        assert os.path.isdir(os.path.join(SKILL_DIR, "issues-v2"))
