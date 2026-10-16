"""Tests for scripts/store_check.py — mechanical store hygiene checks.

Run:  python3 -m unittest tests.test_store_check -v   (from agent-knowledge root)
"""
import importlib.util
import os
import tempfile
import textwrap
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("store_check", _REPO / "scripts" / "store_check.py")
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)


def write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return p


def entry(key="k1", insight="a fact", extra="", body=""):
    lines = [
        "---",
        "type: operational",
        f"key: {key}",
        f"insight: {insight}",
        "confidence: 8",
        "source: observed",
        "ts: 2026-10-14",
        "scope: harness",
    ]
    if extra:
        lines.append(extra.rstrip("\n"))
    lines.append("---")
    if body:
        lines.append(body)
    return "\n".join(lines) + "\n"


class StoreCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, **kw):
        return sc.check(self.root, **kw)

    def levels(self, findings):
        return [(f.level, f.code) for f in findings]

    # --- entry-level ---

    def test_valid_entry_produces_no_findings(self):
        write(self.root, "learnings/operational.md", entry())
        self.assertEqual(self.run_check(), [])

    def test_missing_required_field_is_error(self):
        text = entry().replace("key: k1\n", "")  # drop key line
        write(self.root, "learnings/operational.md", text)
        findings = self.run_check()
        self.assertIn(("ERROR", "missing-field"), self.levels(findings))

    def test_invalid_confidence_is_error(self):
        text = entry().replace("confidence: 8", "confidence: high")
        write(self.root, "learnings/operational.md", text)
        self.assertIn(("ERROR", "bad-confidence"), self.levels(self.run_check()))

    def test_invalid_ts_is_error(self):
        text = entry().replace("ts: 2026-10-14", "ts: 2026-13-45")
        write(self.root, "learnings/operational.md", text)
        self.assertIn(("ERROR", "bad-ts"), self.levels(self.run_check()))

    def test_duplicate_key_across_files_is_error(self):
        write(self.root, "learnings/operational.md", entry(key="dup"))
        write(self.root, "learnings/pitfalls.md", entry(key="dup", insight="other"))
        self.assertIn(("ERROR", "dup-key"), self.levels(self.run_check()))

    def test_stale_files_ref_is_error(self):
        text = entry(extra="files: [no/such/path.md]\n")
        write(self.root, "learnings/operational.md", text)
        self.assertIn(("ERROR", "stale-files-ref"), self.levels(self.run_check()))

    def test_existing_files_ref_resolved_relative_to_root(self):
        write(self.root, "docs/real.md", "x\n")
        text = entry(extra="files: [docs/real.md]\n")
        write(self.root, "learnings/operational.md", text)
        self.assertNotIn("stale-files-ref", [f.code for f in self.run_check()])

    def test_files_ref_resolved_in_workspace_root(self):
        ws = Path(tempfile.mkdtemp())  # sibling workspace root
        self.addCleanup(lambda: __import__("shutil").rmtree(ws, ignore_errors=True))
        write(ws, "PM/notes/file.md", "x\n")
        text = entry(extra="files: [PM/notes/file.md]\n")
        write(self.root, "learnings/operational.md", text)
        findings = self.run_check(resolve_roots=(ws,))
        self.assertNotIn("stale-files-ref", [f.code for f in findings])

    def test_broken_wikilink_is_error(self):
        text = entry(body="see [[no-such-target]] for details")
        write(self.root, "learnings/operational.md", text)
        self.assertIn(("ERROR", "link-rot"), self.levels(self.run_check()))

    def test_wikilink_to_memory_file_resolves(self):
        write(self.root, "learnings/operational.md", entry(body="see [[ref-target]]"))
        write(self.root, "memory/ref-target.md",
              "---\nname: ref-target\ndescription: d\n---\nbody\n")
        self.assertNotIn("link-rot", [f.code for f in self.run_check()])

    def test_wikilink_to_learnings_key_resolves(self):
        write(self.root, "learnings/operational.md", entry(key="alpha", body="see [[beta]]"))
        write(self.root, "learnings/patterns.md", entry(key="beta"))
        self.assertNotIn("link-rot", [f.code for f in self.run_check()])

    def test_superseded_by_missing_target_is_error(self):
        text = entry(key="new-fact", extra="superseded_by: gone-key\n")
        write(self.root, "learnings/operational.md", text)
        self.assertIn(("ERROR", "orphan-supersede"), self.levels(self.run_check()))

    def test_superseded_by_existing_key_ok(self):
        write(self.root, "learnings/operational.md",
              entry(key="new-fact", extra="superseded_by: old-fact\n"))
        write(self.root, "learnings/patterns.md", entry(key="old-fact"))
        self.assertNotIn("orphan-supersede", [f.code for f in self.run_check()])

    def test_backlink_counts_as_indexing(self):
        # not in MEMORY.md, but reachable via [[link]] from another memory file
        write(self.root, "MEMORY.md", "# Memory Index\n\n- [Hub](hub.md) — hub\n")
        write(self.root, "memory/linked-note.md",
              "---\nname: linked-note\ndescription: d\n---\nbody\n")
        write(self.root, "memory/hub.md",
              "---\nname: hub\ndescription: d\n---\nsee [[linked-note]]\n")
        self.assertNotIn("index-missing", [f.code for f in self.run_check()])

    def test_template_only_file_warns_not_errors(self):
        write(self.root, "learnings/preferences.md",
              "# Preferences\n\n<!--\nExample:\n---\ntype: preference\n---\n-->\n")
        findings = self.run_check()
        self.assertIn(("WARN", "no-frontmatter"), self.levels(findings))
        self.assertEqual(sc.exit_code(findings), 0)

    def test_old_age_is_info_not_error(self):
        text = entry().replace("ts: 2026-10-14", "ts: 2020-01-01")
        write(self.root, "learnings/operational.md", text)
        findings = self.run_check()
        self.assertIn(("INFO", "age"), self.levels(findings))
        self.assertFalse(any(f.level == "ERROR" for f in findings))

    def test_html_comment_example_block_ignored(self):
        write(self.root, "decisions/decisions.active.md", textwrap.dedent("""\
            # decisions.active
            <!--
            Example:
            ---
            id: D-XXXX
            ---
            -->
            ---
            id: D-0001
            status: active
            decided: 2026-08-09
            ---
            body
            """))
        findings = self.run_check()
        self.assertNotIn("missing-field", [f.code for f in findings])

    # --- store-level ---

    def test_memory_file_without_index_line_warns(self):
        write(self.root, "memory/orphan-note.md",
              "---\nname: orphan-note\ndescription: d\n---\nbody\n")
        self.assertIn(("WARN", "index-missing"), self.levels(self.run_check()))

    def test_index_line_without_file_is_error(self):
        write(self.root, "MEMORY.md", "# Memory Index\n\n- [T](ghost-file.md) — hook\n")
        self.assertIn(("ERROR", "index-broken"), self.levels(self.run_check()))

    def test_index_line_with_file_ok(self):
        write(self.root, "MEMORY.md", "# Memory Index\n\n- [T](real.md) — hook\n")
        write(self.root, "memory/real.md", "---\nname: real\ndescription: d\n---\nbody\n")
        self.assertNotIn("index-broken", [f.code for f in self.run_check()])

    def test_budget_exceeded_warns_and_never_errors(self):
        lines = "\n".join(f"- [t{i}](f{i}.md) — h" for i in range(4))
        write(self.root, "MEMORY.md", "# Memory Index\n\n" + lines + "\n")
        for i in range(4):
            write(self.root, f"memory/f{i}.md", f"---\nname: f{i}\ndescription: d\n---\nb\n")
        findings = self.run_check(budgets={"MEMORY.md": 3})
        self.assertIn(("WARN", "budget"), self.levels(findings))
        self.assertFalse(any(f.level == "ERROR" for f in findings))

    def test_quick_mode_skips_store_level(self):
        write(self.root, "memory/orphan-note.md",
              "---\nname: orphan-note\ndescription: d\n---\nbody\n")  # would WARN index-missing
        findings = self.run_check(quick=True)
        self.assertNotIn("index-missing", [f.code for f in findings])

    def test_exit_code_zero_without_errors(self):
        write(self.root, "learnings/operational.md", entry())
        self.assertEqual(sc.exit_code(self.run_check()), 0)

    def test_exit_code_one_with_errors(self):
        write(self.root, "learnings/operational.md", "no frontmatter here\n")
        self.assertEqual(sc.exit_code(self.run_check()), 1)


if __name__ == "__main__":
    unittest.main()
