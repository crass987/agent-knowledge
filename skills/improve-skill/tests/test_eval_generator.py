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
TDD_SKILL = os.path.join(SKILLS_DIR, "tdd")
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
        """A well-formed evals.json should pass validation."""
        evals = {
            "version": 1,
            "skill": "test-skill",
            "generated_at": "2026-05-31T00:00:00Z",
            "test_input": {"type": "prompt", "text": "test"},
            "assertions": [
                {
                    "id": "a01",
                    "description": "test",
                    "source_rule": "rule",
                    "type": "contains",
                    "value": "hello",
                }
            ],
        }
        errors = validate_evals_schema(evals)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_missing_version_fails(self):
        """evals without version field should fail validation."""
        evals = {"skill": "test", "assertions": []}
        errors = validate_evals_schema(evals)
        assert any("version" in e for e in errors)

    def test_missing_skill_fails(self):
        """evals without skill name should fail validation."""
        evals = {"version": 1, "assertions": []}
        errors = validate_evals_schema(evals)
        assert any("skill" in e for e in errors)

    def test_invalid_check_type_fails(self):
        """assertion with unknown check type should fail validation."""
        evals = {
            "version": 1,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_input": {"type": "prompt", "text": "t"},
            "assertions": [
                {
                    "id": "a01",
                    "description": "test",
                    "source_rule": "r",
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
            "version": 1,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_input": {"type": "prompt", "text": "t"},
            "assertions": [{"id": "a01"}],
        }
        errors = validate_evals_schema(evals)
        assert len(errors) > 0

    def test_regex_assertion_needs_check_field(self):
        """regex assertion without 'check' field should fail validation."""
        evals = {
            "version": 1,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_input": {"type": "prompt", "text": "t"},
            "assertions": [
                {"id": "a01", "description": "t", "source_rule": "r", "type": "regex", "flags": ""}
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("check" in e for e in errors)

    def test_contains_assertion_needs_value_field(self):
        """contains assertion without 'value' field should fail validation."""
        evals = {
            "version": 1,
            "skill": "test",
            "generated_at": "2026-01-01T00:00:00Z",
            "test_input": {"type": "prompt", "text": "t"},
            "assertions": [
                {"id": "a01", "description": "t", "source_rule": "r", "type": "contains"}
            ],
        }
        errors = validate_evals_schema(evals)
        assert any("value" in e for e in errors)


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
        assert evals["version"] == 1
        assert evals["test_input"]["type"] == "prompt"
        assert len(evals["test_input"]["text"]) > 0
        assert len(evals["assertions"]) >= 2, "Should generate at least 2 assertions"
        errors = validate_evals_schema(evals)
        assert errors == [], f"Schema validation failed: {errors}"

    def test_generate_evals_for_video_knowledge_extraction(self):
        """Generate evals.json for video-knowledge-extraction and validate."""
        evals = generate_evals(VKE_SKILL)
        assert evals is not None
        assert evals["skill"] == "video-knowledge-extraction"
        assert evals["test_input"]["type"] == "file"
        assert "path" in evals["test_input"]
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
