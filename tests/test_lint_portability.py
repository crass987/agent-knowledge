import importlib.util
from pathlib import Path


def _load_linter():
    here = Path(__file__).resolve().parent
    script = here.parent / "scripts" / "lint-portability.py"
    spec = importlib.util.spec_from_file_location("lint_portability", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_flags_hardcoded_toolname(tmp_path):
    (tmp_path / "SKILL.md").write_text("Use mcp__jira__get_issue for Jira.\n")
    mod = _load_linter()
    findings = mod.scan_dir(tmp_path)
    assert any("mcp__jira__get_issue" in f for f in findings), findings


def test_clean_skill_passes(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        "Use the jira capability (see AGENTS.md tool-registry).\n"
    )
    mod = _load_linter()
    assert mod.scan_dir(tmp_path) == []
