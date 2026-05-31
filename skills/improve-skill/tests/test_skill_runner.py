"""
Tests for skill_runner — execute skill against test input and capture output.

TDD RED phase: these tests define the contract BEFORE implementation.
Run with: python3 -m pytest tests/test_skill_runner.py -v
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from skill_runner import (
    build_skill_prompt,
    read_skill_files,
    run_skill,
)


# ── Paths ─────────────────────────────────────────────────────────────

SKILLS_DIR = "/Users/CraSS/Documents/Code_projects/agent-knowledge/skills"
TDD_SKILL = os.path.join(SKILLS_DIR, "tdd")
VKE_SKILL = os.path.join(SKILLS_DIR, "video-knowledge-extraction")


# ── Test: read_skill_files ────────────────────────────────────────────

class TestReadSkillFiles:
    def test_reads_skill_md(self):
        """Should read SKILL.md from a skill directory."""
        files = read_skill_files(TDD_SKILL)
        assert "SKILL.md" in files
        assert len(files["SKILL.md"]) > 0
        assert "TDD Skill" in files["SKILL.md"]

    def test_reads_reference_files(self):
        """Should read .md files from references/ subdirectory."""
        files = read_skill_files(VKE_SKILL)
        assert "SKILL.md" in files
        # video-knowledge-extraction has references/
        ref_keys = [k for k in files if k != "SKILL.md"]
        assert len(ref_keys) > 0, "Should find reference files"
        # Check specific reference file exists
        assert any("knowledge-extraction" in k for k in ref_keys)

    def test_handles_missing_references_dir(self):
        """Should handle skill with no references/ directory."""
        files = read_skill_files(TDD_SKILL)
        assert "SKILL.md" in files
        # tdd has no references/ — only SKILL.md
        assert len(files) == 1

    def test_does_not_read_scripts(self):
        """Should NOT read files from scripts/ directory."""
        files = read_skill_files(VKE_SKILL)
        for key in files:
            assert "scripts" not in key.lower(), f"Should not read scripts: {key}"

    def test_does_not_read_non_md_files(self):
        """Should only read .md files."""
        files = read_skill_files(VKE_SKILL)
        for key in files:
            assert key.endswith(".md") or key == "SKILL.md", f"Non-md file read: {key}"

    def test_handles_nonexistent_dir(self):
        """Should raise for non-existent directory."""
        with pytest.raises((FileNotFoundError, ValueError)):
            read_skill_files("/nonexistent/path")


# ── Test: build_skill_prompt ──────────────────────────────────────────

class TestBuildSkillPrompt:
    def test_builds_system_context(self):
        """Prompt should include skill instructions as system context."""
        files = {"SKILL.md": "# Test Skill\n\nDo the thing."}
        test_input = {"type": "prompt", "text": "Test the thing"}

        system, user = build_skill_prompt(files, test_input)
        assert "# Test Skill" in system
        assert "Do the thing." in system

    def test_includes_reference_files_in_context(self):
        """Prompt should include reference file contents."""
        files = {
            "SKILL.md": "# Skill\n\nSee references.",
            "templates.md": "## Template\n\n- Item 1\n- Item 2",
        }
        test_input = {"type": "prompt", "text": "Do stuff"}

        system, user = build_skill_prompt(files, test_input)
        assert "Template" in system
        assert "templates.md" in system

    def test_prompt_type_sends_text_directly(self):
        """For prompt-type input, user message should be the text."""
        files = {"SKILL.md": "# Skill\n"}
        test_input = {"type": "prompt", "text": "Write a TDD test for users"}

        system, user = build_skill_prompt(files, test_input)
        assert user == "Write a TDD test for users"

    def test_file_type_reads_and_wraps_content(self):
        """For file-type input, user message should wrap file contents."""
        files = {"SKILL.md": "# Skill\n"}
        # Use a real file that exists
        test_input = {
            "type": "file",
            "path": "/Users/CraSS/Documents/Code_projects/agent-knowledge/skills/tdd/SKILL.md",
        }

        system, user = build_skill_prompt(files, test_input)
        assert "TDD Skill" in user
        assert "Process the following content" in user

    def test_file_type_missing_file_raises(self):
        """For file-type input with missing file, should raise."""
        files = {"SKILL.md": "# Skill\n"}
        test_input = {"type": "file", "path": "/nonexistent/file.txt"}

        with pytest.raises(FileNotFoundError):
            build_skill_prompt(files, test_input)


# ── Test: run_skill with mock ─────────────────────────────────────────

class TestRunSkillMocked:
    def test_returns_string_output(self):
        """run_skill should return a string output."""
        # This test will actually call the skill runner which uses Agent tool
        # For unit testing, we mock the sub-agent call
        from unittest.mock import patch, MagicMock

        files = {"SKILL.md": "# Test\nDo things."}
        test_input = {"type": "prompt", "text": "Do things"}

        with patch("skill_runner._execute_subagent", return_value="Mocked output from skill"):
            result = run_skill(files, test_input)
            assert isinstance(result, str)
            assert result == "Mocked output from skill"

    def test_output_is_plain_text(self):
        """Output should be plain text without control characters."""
        from unittest.mock import patch

        files = {"SKILL.md": "# Test\n"}
        test_input = {"type": "prompt", "text": "test"}

        with patch("skill_runner._execute_subagent", return_value="Normal text output"):
            result = run_skill(files, test_input)
            assert "\x00" not in result
            assert "\x1b" not in result

    def test_does_not_modify_files(self):
        """Skill runner should be read-only."""
        files = {"SKILL.md": "# Original\nOriginal content."}
        test_input = {"type": "prompt", "text": "test"}

        original_content = files["SKILL.md"]

        from unittest.mock import patch
        with patch("skill_runner._execute_subagent", return_value="output"):
            run_skill(files, test_input)

        # Verify files dict wasn't mutated
        assert files["SKILL.md"] == original_content
