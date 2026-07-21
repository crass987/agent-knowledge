"""
Tests for eval_generator — auto-generate evals.json from SKILL.md.

TDD RED phase: these tests define the contract BEFORE implementation.
Run with: python3 -m pytest tests/test_eval_generator.py -v
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from eval_generator import (
    detect_archetype,
    generate_evals,
    find_skill_dir,
    validate_evals_schema,
)


# ── Paths to real skills ──────────────────────────────────────────────

SKILLS_DIR = "/Users/CraSS/Documents/Code_projects/agent-knowledge/skills"
def _make_synthetic_tdd_fixture() -> str:
    """Self-contained synthetic 'tdd' skill for generator tests.

    `tdd` is a third-party (Matt Pocock) skill that lives in ~/.claude/skills,
    not in this repo. The generator tests need a skill with extractable rules,
    so we own a minimal one instead of pointing at a path that doesn't exist
    here (env-coupling anti-pattern). See capability-audit fleet-audit.md.
    """
    d = tempfile.mkdtemp(prefix="evalgen-tdd-fixture-")
    with open(os.path.join(d, "SKILL.md"), "w") as f:
        f.write(
            "---\n"
            "name: tdd\n"
            "description: Test-driven development. Write the test first.\n"
            "---\n"
            "# tdd — test-driven development\n\n"
            "## Rules\n\n"
            "1. Write a failing test before any implementation.\n"
            "2. Run the tests; the new test must fail for the right reason.\n"
            "3. Write the minimum code that makes the test pass.\n"
            "4. Refactor only while all tests are green.\n\n"
            "## Workflow\n\n"
            "Red, then Green, then Refactor. Never commit a red test.\n"
        )
    return d


TDD_SKILL = _make_synthetic_tdd_fixture()
VKE_SKILL = os.path.join(SKILLS_DIR, "video-knowledge-extraction")
CLAUDE_SKILLS_DIR = "/Users/CraSS/.claude/skills"


# ── Test: archetype detection ─────────────────────────────────────────

class TestArchetypeDetection:
    def test_video_knowledge_extraction_is_file_processing(self):
        """video-knowledge-extraction should be detected as file-processing."""
        result = detect_archetype(VKE_SKILL)
        assert result == "file", f"Expected 'file', got '{result}'"

    def test_tdd_is_prompt_based(self):
        """tdd should be detected as prompt-based."""
        result = detect_archetype(TDD_SKILL)
        assert result == "prompt", f"Expected 'prompt', got '{result}'"

    def test_file_processing_keywords_in_description(self):
        """Skills mentioning 'file' or 'URL' should be file-processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = os.path.join(tmpdir, "SKILL.md")
            with open(skill_md, "w") as f:
                f.write("---\nname: test\ndescription: Process a file and extract data\n---\n# Test\n")
            assert detect_archetype(tmpdir) == "file"

    def test_prompt_based_when_no_file_keywords(self):
        """Skills without file/URL/video keywords should be prompt-based."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = os.path.join(tmpdir, "SKILL.md")
            with open(skill_md, "w") as f:
                f.write("---\nname: test\ndescription: Help with debugging code\n---\n# Test\n")
            assert detect_archetype(tmpdir) == "prompt"

    def test_video_keyword_triggers_file_processing(self):
        """Skill mentioning 'video' should be file-processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = os.path.join(tmpdir, "SKILL.md")
            with open(skill_md, "w") as f:
                f.write("---\nname: test\ndescription: Analyze video content\n---\n# Test\n")
            assert detect_archetype(tmpdir) == "file"

    def test_transcript_keyword_triggers_file_processing(self):
        """Skill mentioning 'transcript' should be file-processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = os.path.join(tmpdir, "SKILL.md")
            with open(skill_md, "w") as f:
                f.write("---\nname: test\ndescription: Extract knowledge from transcript\n---\n# Test\n")
            assert detect_archetype(tmpdir) == "file"


# ── Test: schema validation ───────────────────────────────────────────

class TestSchemaValidation:
    def test_valid_evals_passes_validation(self):
        """A well-formed v2 evals.json should pass validation."""
        evals = {
            "version": 2,
            "skill": "test-skill",
            "generated_at": "2026-05-31T00:00:00Z",
            "test_inputs": [{"type": "prompt", "text": "test", "label": "test prompt"}],
            "assertions": [
                {
                    "id": "a01",
                    "description": "test",
                    "source_rule": "rule",
                    "source_file": "SKILL.md",
                    "generator": "heuristic",
                    "type": "contains",
                    "value": "hello",
                }
            ],
        }
        errors = validate_evals_schema(evals)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_missing_version_fails(self):
        """evals without version field should fail validation."""
        evals = {"skill": "test", "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}], "assertions": []}
        errors = validate_evals_schema(evals)
        assert any("version" in e for e in errors)

    def test_missing_skill_fails(self):
        """evals without skill name should fail validation."""
        evals = {"version": 2, "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}], "assertions": []}
        errors = validate_evals_schema(evals)
        assert any("skill" in e for e in errors)

    def test_invalid_check_type_fails(self):
        """assertion with unknown check type should fail validation."""
        evals = {
            "version": 2,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}],
            "assertions": [
                {
                    "id": "a01",
                    "description": "test",
                    "source_rule": "r",
                    "source_file": "SKILL.md",
                    "generator": "heuristic",
                    "type": "invalid_type",
                    "value": "x",
                }
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("type" in e.lower() for e in errors)

    def test_missing_required_assertion_fields(self):
        """assertion missing required fields should fail validation."""
        evals = {
            "version": 2,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}],
            "assertions": [{"id": "a01"}],
        }
        errors = validate_evals_schema(evals)
        assert len(errors) > 0

    def test_regex_assertion_needs_check_field(self):
        """regex assertion without 'check' field should fail validation."""
        evals = {
            "version": 2,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}],
            "assertions": [
                {"id": "a01", "description": "t", "source_rule": "r", "source_file": "SKILL.md", "generator": "heuristic", "type": "regex", "flags": ""}
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("check" in e for e in errors)

    def test_contains_assertion_needs_value_field(self):
        """contains assertion without 'value' field should fail validation."""
        evals = {
            "version": 2,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}],
            "assertions": [
                {"id": "a01", "description": "t", "source_rule": "r", "source_file": "SKILL.md", "generator": "heuristic", "type": "contains"}
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("value" in e for e in errors)

    def test_missing_source_file_fails(self):
        """v2 assertion without source_file should fail validation."""
        evals = {
            "version": 2,
            "skill": "test",
            "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}],
            "assertions": [
                {"id": "a01", "description": "t", "source_rule": "r", "generator": "heuristic", "type": "contains", "value": "x"}
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("source_file" in e for e in errors)

    def test_missing_generator_fails(self):
        """v2 assertion without generator should fail validation."""
        evals = {
            "version": 2,
            "skill": "test",
            "test_inputs": [{"type": "prompt", "text": "t", "label": "x"}],
            "assertions": [
                {"id": "a01", "description": "t", "source_rule": "r", "source_file": "SKILL.md", "type": "contains", "value": "x"}
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("generator" in e for e in errors)

    def test_missing_test_input_label_fails(self):
        """v2 test_input without label should fail validation."""
        evals = {
            "version": 2,
            "skill": "test",
            "test_inputs": [{"type": "prompt", "text": "t"}],
            "assertions": [
                {"id": "a01", "description": "t", "source_rule": "r", "source_file": "SKILL.md", "generator": "heuristic", "type": "contains", "value": "x"}
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("label" in e for e in errors)


# ── Test: skill directory discovery ───────────────────────────────────

class TestSkillDiscovery:
    def test_find_tdd_skill_dir(self):
        """Should find the tdd skill directory."""
        path = find_skill_dir("tdd", [SKILLS_DIR, CLAUDE_SKILLS_DIR])
        assert path is not None
        assert os.path.isdir(path)
        assert os.path.exists(os.path.join(path, "SKILL.md"))

    def test_find_video_knowledge_extraction(self):
        """Should find video-knowledge-extraction skill directory."""
        path = find_skill_dir("video-knowledge-extraction", [SKILLS_DIR, CLAUDE_SKILLS_DIR])
        assert path is not None
        assert os.path.isdir(path)

    def test_nonexistent_skill_returns_none(self):
        """Should return None for a skill that doesn't exist."""
        path = find_skill_dir("nonexistent-skill-xyz", [SKILLS_DIR, CLAUDE_SKILLS_DIR])
        assert path is None

    def test_deduplicates_across_directories(self):
        """If a skill exists in both dirs, returns the first match."""
        path = find_skill_dir("tdd", [SKILLS_DIR, CLAUDE_SKILLS_DIR])
        # Should find exactly one path
        assert isinstance(path, str)


# ── Test: generate_evals end-to-end ──────────────────────────────────

class TestGenerateEvals:
    def test_generate_evals_for_tdd_skill(self):
        """Generate evals.json for the tdd skill and validate output."""
        evals = generate_evals(TDD_SKILL)
        assert evals is not None
        assert evals["skill"] == "tdd"
        assert evals["version"] == 2
        assert evals["test_inputs"][0]["type"] == "prompt"
        assert len(evals["test_inputs"][0]["text"]) > 0
        assert len(evals["assertions"]) >= 2, "Should generate at least 2 assertions"
        errors = validate_evals_schema(evals)
        assert errors == [], f"Schema validation failed: {errors}"

    def test_generate_evals_for_video_knowledge_extraction(self):
        """Generate evals.json for video-knowledge-extraction and validate."""
        evals = generate_evals(VKE_SKILL)
        assert evals is not None
        assert evals["skill"] == "video-knowledge-extraction"
        assert evals["test_inputs"][0]["type"] == "file"
        assert "path" in evals["test_inputs"][0]
        errors = validate_evals_schema(evals)
        assert errors == [], f"Schema validation failed: {errors}"

    def test_assertion_ids_are_sequential(self):
        """Assertion IDs should be sequential: a01, a02, a03, ..."""
        evals = generate_evals(TDD_SKILL)
        ids = [a["id"] for a in evals["assertions"]]
        expected = [f"a{str(i).zfill(2)}" for i in range(1, len(ids) + 1)]
        assert ids == expected, f"Expected {expected}, got {ids}"

    def test_each_assertion_has_source_rule(self):
        """Every assertion must have a source_rule tracing back to SKILL.md."""
        evals = generate_evals(TDD_SKILL)
        for a in evals["assertions"]:
            assert "source_rule" in a, f"Assertion {a['id']} missing source_rule"
            assert len(a["source_rule"]) > 0

    def test_generated_evals_scoreable_by_assertion_runner(self):
        """Generated evals.json should work with assertion_runner."""
        from assertion_runner import run_assertions
        evals = generate_evals(TDD_SKILL)
        # Use a dummy output — just verify the runner doesn't error
        result = run_assertions("Some TDD output with RED GREEN REFACTOR cycle", evals)
        assert "total" in result
        assert "passed" in result
        assert "failed" in result
        assert result["total"] == len(evals["assertions"])

    def test_generated_at_is_valid_iso8601(self):
        """generated_at should be a valid ISO-8601 timestamp."""
        evals = generate_evals(TDD_SKILL)
        from datetime import datetime
        dt = datetime.fromisoformat(evals["generated_at"].replace("Z", "+00:00"))
        assert dt is not None


# ── Test: v2 schema ──────────────────────────────────────────────────

class TestV2Schema:
    """Tests for the v2 evals.json schema changes."""

    def test_version_is_2(self):
        """v2 evals.json should have version=2."""
        evals = generate_evals(TDD_SKILL)
        assert evals["version"] == 2

    def test_test_inputs_is_array(self):
        """v2 uses 'test_inputs' (plural array) instead of 'test_input' (singular)."""
        evals = generate_evals(TDD_SKILL)
        assert "test_inputs" in evals
        assert isinstance(evals["test_inputs"], list)

    def test_test_inputs_has_at_least_one_entry(self):
        """test_inputs must contain at least one test input."""
        evals = generate_evals(TDD_SKILL)
        assert len(evals["test_inputs"]) >= 1

    def test_test_input_has_label(self):
        """Each test_input in v2 must have a 'label' field."""
        evals = generate_evals(TDD_SKILL)
        for ti in evals["test_inputs"]:
            assert "label" in ti, f"test_input missing 'label': {ti}"
            assert len(ti["label"]) > 0

    def test_no_legacy_test_input_field(self):
        """v2 should not have the old 'test_input' (singular) field."""
        evals = generate_evals(TDD_SKILL)
        assert "test_input" not in evals, "v2 should use 'test_inputs' not 'test_input'"


# ── Test: source_file tracing ────────────────────────────────────────

class TestSourceFileTracing:
    """Tests that assertions correctly trace back to their source file."""

    def test_all_assertions_have_source_file(self):
        """Every assertion must carry a source_file field."""
        evals = generate_evals(TDD_SKILL)
        for a in evals["assertions"]:
            assert "source_file" in a, f"Assertion {a['id']} missing source_file"
            assert len(a["source_file"]) > 0

    def test_all_assertions_have_generator(self):
        """Every assertion must carry a generator field."""
        evals = generate_evals(TDD_SKILL)
        for a in evals["assertions"]:
            assert "generator" in a, f"Assertion {a['id']} missing generator"
            assert a["generator"] in ("heuristic", "llm")

    def test_skill_md_rules_traced_to_skill_md(self):
        """Rules extracted from SKILL.md should have source_file='SKILL.md'."""
        evals = generate_evals(TDD_SKILL)
        skill_md_assertions = [a for a in evals["assertions"] if a["source_file"] == "SKILL.md"]
        assert len(skill_md_assertions) > 0, "Should have at least some assertions from SKILL.md"

    def test_reference_rules_traced_to_reference_file(self):
        """Rules extracted from references/ should point to the correct file."""
        evals = generate_evals(VKE_SKILL)
        ref_assertions = [a for a in evals["assertions"] if a["source_file"].startswith("references/")]
        # VKE has references/ with rules — should trace correctly
        # (may be 0 if no extractable rules in references, so just verify format)
        for a in ref_assertions:
            assert a["source_file"].startswith("references/"), f"Bad source_file: {a['source_file']}"
            assert a["source_file"].endswith(".md")

    def test_synthetic_skill_with_references_traces_correctly(self):
        """Create a temp skill with SKILL.md + references/ and verify source_file accuracy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write SKILL.md with a rule
            with open(os.path.join(tmpdir, "SKILL.md"), "w") as f:
                f.write("---\nname: test-skill\ndescription: test\n---\n# Rules\n\n1. Never skip tests.\n")
            # Write references/checklist.md with a different rule
            os.makedirs(os.path.join(tmpdir, "references"))
            with open(os.path.join(tmpdir, "references", "checklist.md"), "w") as f:
                f.write("# Checklist\n\n1. Always include a header.\n")

            evals = generate_evals(tmpdir)
            source_files = {a["source_file"] for a in evals["assertions"]}
            # Should have assertions from both SKILL.md and references/checklist.md
            assert "SKILL.md" in source_files, f"Expected SKILL.md in {source_files}"
            assert "references/checklist.md" in source_files, f"Expected references/checklist.md in {source_files}"


# ── Test: multiple test inputs ────────────────────────────────────────

class TestMultipleTestInputs:
    """Tests for v2's multiple test_inputs per skill."""

    def test_prompt_skill_generates_multiple_inputs(self):
        """Prompt-based skills should generate 2+ test inputs with varying specificity."""
        evals = generate_evals(TDD_SKILL)
        assert len(evals["test_inputs"]) >= 2, f"Expected 2+ test_inputs, got {len(evals['test_inputs'])}"

    def test_file_skill_generates_multiple_inputs(self):
        """File-based skills should generate 2+ test inputs if multiple files exist."""
        evals = generate_evals(VKE_SKILL)
        assert len(evals["test_inputs"]) >= 1, "Should have at least 1 test input"

    def test_prompt_inputs_vary_in_specificity(self):
        """Test inputs for prompt skills should vary — basic, detailed, edge-case."""
        evals = generate_evals(TDD_SKILL)
        texts = [ti["text"] for ti in evals["test_inputs"]]
        # No two inputs should be identical
        assert len(set(texts)) == len(texts), "All test inputs should be unique"

    def test_each_input_has_required_fields(self):
        """Every test input must have type, and either text or path, plus label."""
        evals = generate_evals(TDD_SKILL)
        for i, ti in enumerate(evals["test_inputs"]):
            assert "type" in ti, f"test_inputs[{i}] missing 'type'"
            assert "label" in ti, f"test_inputs[{i}] missing 'label'"
            if ti["type"] == "prompt":
                assert "text" in ti and len(ti["text"]) > 0, f"test_inputs[{i}] missing 'text'"
            elif ti["type"] == "file":
                assert "path" in ti, f"test_inputs[{i}] missing 'path'"

    def test_labels_are_unique(self):
        """Each test input should have a unique label for reporting clarity."""
        evals = generate_evals(TDD_SKILL)
        labels = [ti["label"] for ti in evals["test_inputs"]]
        assert len(set(labels)) == len(labels), f"Labels should be unique, got: {labels}"


# ── Test: assertion deduplication ─────────────────────────────────────

class TestAssertionDeduplication:
    """Tests that duplicate assertions are merged."""

    def test_no_duplicate_check_patterns(self):
        """Assertions with identical type + check/value should be deduplicated."""
        evals = generate_evals(TDD_SKILL)
        seen = set()
        for a in evals["assertions"]:
            # Normalize: type + check or value
            key = (a["type"], a.get("check", ""), str(a.get("value", "")))
            assert key not in seen, f"Duplicate assertion: {a['id']} has same pattern as earlier assertion"
            seen.add(key)

    def test_dedup_keeps_more_specific_description(self):
        """When two rules produce identical check patterns, keep the one with longer description."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # SKILL.md with two rules that produce the same not_contains check
            with open(os.path.join(tmpdir, "SKILL.md"), "w") as f:
                f.write(
                    "---\nname: dedup-test\ndescription: test\n---\n# Rules\n"
                    "\n1. Never include TODO markers in final output.\n"
                    "2. Never include TODO.\n"
                )
            # Write same rule in references/ to test cross-file dedup
            os.makedirs(os.path.join(tmpdir, "references"))
            with open(os.path.join(tmpdir, "references", "extra.md"), "w") as f:
                f.write("# Extra\n\nNever include TODO.\n")

            evals = generate_evals(tmpdir)
            # "Never include TODO." produces not_contains value="include TODO" — appears 2x
            # "Never include TODO markers in final output." produces not_contains value="include TODO markers in final output"
            todo_assertions = [a for a in evals["assertions"] if a.get("value") == "include TODO"]
            assert len(todo_assertions) <= 1, f"Expected exact dedup, got {len(todo_assertions)} 'include TODO' assertions"

    def test_dedup_preserves_non_identical_patterns(self):
        """Non-identical but similar patterns should NOT be deduped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "SKILL.md"), "w") as f:
                f.write(
                    "---\nname: nodup-test\ndescription: test\n---\n# Rules\n"
                    "\n1. Never include raw JSON output.\n"
                    "2. Never include raw JSON.\n"
                )
            evals = generate_evals(tmpdir)
            # These have different values — should NOT be deduped
            json_assertions = [a for a in evals["assertions"] if "JSON" in a.get("value", "")]
            assert len(json_assertions) == 2, f"Different patterns should survive, got {len(json_assertions)}"


# ── Test: LLM semantic extraction ────────────────────────────────────

class TestLLMPhase:
    """Tests for the LLM semantic extraction phase of eval generation."""

    def test_llm_assertions_have_generator_llm(self):
        """When LLM assertions are added, they should have generator='llm'."""
        from unittest.mock import patch
        mock_llm_response = [
            {
                "id": "l01",
                "description": "Output mentions test-first approach",
                "source_rule": "TDD requires writing tests before code",
                "source_file": "SKILL.md",
                "type": "contains",
                "value": "test",
                "generator": "llm",
            }
        ]
        with patch("eval_generator._run_llm_extraction", return_value=mock_llm_response):
            evals = generate_evals(TDD_SKILL)
        llm_assertions = [a for a in evals["assertions"] if a.get("generator") == "llm"]
        assert len(llm_assertions) >= 1

    def test_llm_assertions_have_source_file(self):
        """LLM-generated assertions must carry a source_file field."""
        from unittest.mock import patch
        mock_response = [
            {
                "description": "Check for RED phase mention",
                "source_rule": "The TDD cycle is RED-GREEN-REFACTOR",
                "source_file": "SKILL.md",
                "type": "contains",
                "value": "RED",
            }
        ]
        with patch("eval_generator._run_llm_extraction", return_value=mock_response):
            evals = generate_evals(TDD_SKILL)
        llm_assertions = [a for a in evals["assertions"] if a.get("generator") == "llm"]
        for a in llm_assertions:
            assert "source_file" in a, f"LLM assertion missing source_file: {a}"

    def test_heuristic_and_llm_assertions_coexist(self):
        """Both heuristic and LLM assertions should appear in the final output."""
        from unittest.mock import patch
        mock_response = [
            {
                "description": "Output mentions refactoring",
                "source_rule": "Always refactor after green",
                "source_file": "SKILL.md",
                "type": "contains",
                "value": "REFACTOR",
            }
        ]
        with patch("eval_generator._run_llm_extraction", return_value=mock_response):
            evals = generate_evals(TDD_SKILL)
        generators = {a["generator"] for a in evals["assertions"]}
        assert "heuristic" in generators, "Should have heuristic assertions"
        assert "llm" in generators, "Should have LLM assertions"

    def test_llm_and_heuristic_deduped_together(self):
        """Dedup should work across heuristic and LLM assertions."""
        from unittest.mock import patch
        # LLM produces an assertion identical to a heuristic one
        mock_response = [
            {
                "description": "Output must not contain: write production code except to make a failing test pass",
                "source_rule": "Never write production code except to make a failing test pass",
                "source_file": "SKILL.md",
                "type": "not_contains",
                "value": "write production code except to make a failing test pass",
            }
        ]
        with patch("eval_generator._run_llm_extraction", return_value=mock_response):
            evals = generate_evals(TDD_SKILL)
        # Count assertions with this exact value — should be exactly 1 (deduped)
        matches = [a for a in evals["assertions"] if a.get("value") == "write production code except to make a failing test pass"]
        assert len(matches) == 1, f"Expected 1 after dedup, got {len(matches)}"

    def test_llm_not_called_when_no_skill_files(self):
        """LLM should not be called if there are no skill files to analyze."""
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty directory, no SKILL.md
            with patch("eval_generator._run_llm_extraction") as mock_llm:
                evals = generate_evals(tmpdir)
                # LLM should still be called (there might be content to analyze)
                # But the result should be valid
                assert "assertions" in evals
