"""
test_improve_runner_cli — CLI dispatcher tests for improve_runner.main().

Validates the thin CLI layer added in v2: each subcommand maps a JSON stdin
object → one JSON stdout object, matching the documented contract used by the
SKILL.md orchestrator (so the model can call these pure functions via Bash).

Two test layers:
  - Unit: call `_run_command(command, data)` directly (fast, full coverage of
    all 13 subcommands).
  - Boundary: invoke the real `python3 lib/improve_runner.py <cmd>` subprocess
    to exercise argparse + stdin parsing + exit codes (malformed stdin, unknown
    command, recovery via --skill-dir, plus a few happy-path wirings).

Run with: python3 -m pytest tests/test_improve_runner_cli.py -v
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from improve_runner import _run_command  # added alongside main()

LIB_DIR = os.path.join(os.path.dirname(__file__), "..", "lib")
RUNNER = os.path.join(LIB_DIR, "improve_runner.py")


# ── Helpers ───────────────────────────────────────────────────────────


def _cli(command, stdin_obj=None, skill_dir=None, raw=None):
    """Invoke the CLI via subprocess.

    Returns (returncode, parsed_stdout_or_None). If `raw` is given it is sent
    verbatim; otherwise stdin_obj is JSON-encoded (empty string when None).
    """
    cmd = [sys.executable, RUNNER, command]
    if skill_dir is not None:
        cmd += ["--skill-dir", str(skill_dir)]
    if raw is not None:
        input_text = raw
    elif stdin_obj is not None:
        input_text = json.dumps(stdin_obj)
    else:
        input_text = ""
    r = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        out = None
    return r.returncode, out


def _init_repo(tmp_path):
    """Create a real git repo with identity configured (mirrors test_improve_runner)."""
    d = tmp_path / "repo"
    d.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(d), check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=str(d), check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(d), check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=str(d), check=True)
    return d


# ── 1. Unit tests: each subcommand via _run_command ───────────────────


class TestParseArgs:
    def test_single_skill_and_flags(self):
        out = _run_command("parse-args", {"argv": ["tdd", "--regen"]})
        assert out == {
            "all_skills": False, "regen": True, "dry_run": False,
            "skill_names": ["tdd"],
        }

    def test_all_flag(self):
        out = _run_command("parse-args", {"argv": ["--all"]})
        assert out["all_skills"] is True
        assert out["skill_names"] == []


class TestMakeBranch:
    def test_no_collision(self):
        out = _run_command("make-branch", {"skill_name": "tdd", "taken": ["improve/x"]})
        assert out == {"name": "improve/tdd"}

    def test_collision_suffix(self):
        taken = ["improve/tdd"]
        out = _run_command("make-branch", {"skill_name": "tdd", "taken": taken})
        assert out == {"name": "improve/tdd-2"}

    def test_taken_as_list_accepted(self):
        # taken may arrive as a JSON list (sets are not JSON); dispatcher converts.
        out = _run_command("make-branch", {"skill_name": "jtbd", "taken": []})
        assert out == {"name": "improve/jtbd"}


class TestAggregate:
    def test_single_output(self):
        per = [{"total": 2, "passed": [{"id": "a01"}], "failed": [{"id": "a02"}]}]
        out = _run_command("aggregate", {"per_output": per})
        assert out["total"] == 2
        assert out["passed"] == ["a01"]
        assert out["failed"] == ["a02"]
        assert out["per_assertion"] == {"a01": [True], "a02": [False]}

    def test_intersection_across_outputs(self):
        # a01 passes on both, a02 passes only on first → a02 fails overall.
        per = [
            {"total": 2, "passed": [{"id": "a01"}, {"id": "a02"}], "failed": []},
            {"total": 2, "passed": [{"id": "a01"}], "failed": [{"id": "a02"}]},
        ]
        out = _run_command("aggregate", {"per_output": per})
        assert out["passed"] == ["a01"]
        assert out["failed"] == ["a02"]

    def test_empty(self):
        out = _run_command("aggregate", {"per_output": []})
        assert out == {"total": 0, "passed": [], "failed": [], "per_assertion": {}}


class TestPickTarget:
    def test_picks_lowest_failing(self):
        agg = {"total": 3, "passed": ["a01"], "failed": ["a03", "a02"],
               "per_assertion": {}}
        out = _run_command("pick-target", {"agg": agg})
        assert out == {"id": "a02"}

    def test_none_when_all_pass(self):
        agg = {"total": 2, "passed": ["a01", "a02"], "failed": [], "per_assertion": {}}
        out = _run_command("pick-target", {"agg": agg})
        assert out == {"target": None}


class TestResolveFile:
    def test_specific_source_file(self):
        out = _run_command("resolve-file", {"assertion": {"source_file": "references/x.md"}})
        assert out == {"file": "references/x.md"}

    def test_defaults_to_skill_md(self):
        out = _run_command("resolve-file", {"assertion": {"source_file": "SKILL.md"}})
        assert out == {"file": "SKILL.md"}

    def test_missing_source_file(self):
        out = _run_command("resolve-file", {"assertion": {}})
        assert out == {"file": "SKILL.md"}


class TestParseRule:
    def test_full_response(self):
        text = ("ANALYSIS: the output lacks a header\n"
                "RULE: start every output with an H1\n"
                "SECTION: Structure\n"
                'POSITION: after "## When to use"')
        out = _run_command("parse-rule", {"text": text})
        assert out["rule"] == "start every output with an H1"
        assert out["section"] == "Structure"
        assert out["analysis"] == "the output lacks a header"
        assert "after" in out["position"]

    def test_no_rule_returns_null(self):
        out = _run_command("parse-rule", {"text": "ANALYSIS: nothing useful here"})
        assert out == {"result": None}

    def test_empty_text(self):
        out = _run_command("parse-rule", {"text": ""})
        assert out == {"result": None}


class TestInject:
    def test_round_trip_into_section(self):
        content = "## Rules\n\n- existing rule\n"
        plan = {"analysis": "", "rule": "always write tests first",
                "section": "Rules", "position": ""}
        out = _run_command("inject", {"content": content, "plan": plan})
        # round-trip: new content preserves existing + adds the rule.
        assert "content" in out
        assert "always write tests first" in out["content"]
        assert "existing rule" in out["content"]
        assert out["content"].lstrip().startswith("## Rules")

    def test_explicit_block_overrides_default(self):
        content = "## Rules\n\n- a\n"
        plan = {"analysis": "", "rule": "X", "section": "Rules", "position": ""}
        out = _run_command("inject", {"content": content, "plan": plan,
                                       "block": "<!-- marker -->\n- CUSTOM\n<!-- /marker -->"})
        assert "CUSTOM" in out["content"]
        assert "<!-- marker -->" in out["content"]

    def test_frontmatter_preserved(self):
        content = "---\nname: tdd\n---\n\n## Rules\n\n- a\n"
        plan = {"analysis": "", "rule": "new", "section": "Rules", "position": ""}
        out = _run_command("inject", {"content": content, "plan": plan})
        assert out["content"].startswith("---")
        assert "name: tdd" in out["content"]


class TestDecide:
    def test_keep_on_strict_improvement(self):
        assert _run_command("decide", {"new": 5, "prev": 4}) == {"action": "keep"}

    def test_revert_on_equal(self):
        # boundary: new == prev → revert (no strict improvement).
        assert _run_command("decide", {"new": 4, "prev": 4}) == {"action": "revert"}

    def test_revert_on_lower(self):
        assert _run_command("decide", {"new": 3, "prev": 4}) == {"action": "revert"}


class TestStop:
    def test_all_pass(self):
        out = _run_command("stop", {"new": 3, "total": 3, "plateau": 0, "iteration": 1})
        assert out == {"stop": True, "reason": "ALL_PASS", "iteration": 1}

    def test_plateau(self):
        out = _run_command("stop", {"new": 1, "total": 3, "plateau": 3, "iteration": 4})
        assert out == {"stop": True, "reason": "PLATEAU", "iteration": 4}

    def test_cap(self):
        out = _run_command("stop", {"new": 1, "total": 3, "plateau": 0, "iteration": 10})
        assert out == {"stop": True, "reason": "CAP", "iteration": 10}

    def test_no_stop(self):
        out = _run_command("stop", {"new": 1, "total": 3, "plateau": 0, "iteration": 2})
        assert out == {"stop": False, "reason": "", "iteration": 2}

    def test_all_pass_beats_plateau(self):
        # priority: ALL_PASS before PLATEAU.
        out = _run_command("stop", {"new": 5, "total": 5, "plateau": 3, "iteration": 9})
        assert out["reason"] == "ALL_PASS"


class TestUpdateState:
    def _state(self, **kw):
        base = {"iteration": 2, "prev_score": 1, "plateau_count": 1,
                "agent_calls": 1, "llm_calls": 2, "test_inputs_evaluated": 2,
                "baseline_scores": {}}
        base.update(kw)
        return base

    def test_keep_advances_score_resets_plateau(self):
        out = _run_command("update-state", {
            "state": self._state(prev_score=1, plateau_count=2),
            "action": "keep", "delta": 1,
        })
        assert out["prev_score"] == 2
        assert out["plateau_count"] == 0

    def test_revert_increments_plateau(self):
        out = _run_command("update-state", {
            "state": self._state(prev_score=3, plateau_count=1),
            "action": "revert", "delta": 0,
        })
        assert out["prev_score"] == 3  # unchanged
        assert out["plateau_count"] == 2

    def test_original_state_not_mutated(self):
        # dispatcher must not mutate caller's input; result is a new state.
        state = self._state(prev_score=1, plateau_count=0)
        out = _run_command("update-state", {"state": state, "action": "keep", "delta": 1})
        assert out is not state
        assert state["prev_score"] == 1  # input untouched


class TestParseAudit:
    def test_full_response(self):
        text = ("QUALITY_SCORE: B\n"
                "DIMENSION: Clarity\n"
                "Score: 3\n"
                "Issues: headers missing\n"
                "Suggestions: add H1\n"
                "DIMENSION: Tone\n"
                "Score: 4\n"
                "Issues: ok\n"
                "Suggestions: none\n"
                "RECURRING_PROBLEMS:\n"
                "- vague wording\n"
                "- no examples")
        out = _run_command("parse-audit", {"text": text})
        assert out["quality_score"] == "B"
        assert "Clarity" in out["dimensions"]
        assert out["dimensions"]["Clarity"]["score"] == 3
        assert out["recurring_problems"] == ["vague wording", "no examples"]

    def test_empty_returns_default(self):
        out = _run_command("parse-audit", {"text": ""})
        assert out["quality_score"] == "F"
        assert out["dimensions"] == {}
        assert out["recurring_problems"] == []


class TestProblemsToAssertions:
    def test_converts_problems(self):
        out = _run_command("problems-to-assertions",
                           {"problems": ["missing header", "too many cliches"]})
        assert "result" in out
        assert isinstance(out["result"], list)
        assert len(out["result"]) == 2
        first = out["result"][0]
        assert first["id"] == "p01"
        assert first["status"] == "proposed"
        assert "type" in first

    def test_empty(self):
        out = _run_command("problems-to-assertions", {"problems": []})
        assert out == {"result": []}


# ── 2. Boundary tests: real subprocess ────────────────────────────────


class TestCLIBoundary:
    def test_parse_args_via_subprocess(self):
        rc, out = _cli("parse-args", {"argv": ["infostyle", "--dry-run"]})
        assert rc == 0
        assert out["skill_names"] == ["infostyle"]
        assert out["dry_run"] is True

    def test_decide_via_subprocess(self):
        rc, out = _cli("decide", {"new": 5, "prev": 4})
        assert rc == 0
        assert out == {"action": "keep"}

    def test_malformed_stdin_returns_error_and_nonzero(self):
        rc, out = _cli("decide", raw="{not valid json")
        assert rc != 0
        assert out is not None
        assert "error" in out

    def test_malformed_stdin_error_is_descriptive(self):
        rc, out = _cli("aggregate", raw="")
        # empty stdin is not valid input for a command needing data → error.
        assert rc != 0
        assert "error" in out

    def test_unknown_command_returns_error_and_nonzero(self):
        rc, out = _cli("bogus-command", stdin_obj={}, )
        assert rc != 0
        assert out == {"error": "unknown command: bogus-command"}

    def test_aggregate_via_subprocess(self):
        per = [{"total": 1, "passed": [{"id": "a01"}], "failed": []}]
        rc, out = _cli("aggregate", {"per_output": per})
        assert rc == 0
        assert out["total"] == 1
        assert out["passed"] == ["a01"]


class TestRecoveryCLI:
    def test_recovery_empty_repo(self, tmp_path):
        d = _init_repo(tmp_path)
        (d / "SKILL.md").write_text("# x\n")
        subprocess.run(["git", "add", "."], cwd=str(d), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(d), check=True)

        rc, out = _cli("recovery", skill_dir=str(d))
        assert rc == 0
        assert out["iteration"] == 1
        assert out["last_assertion_id"] is None
        assert out["last_action"] == "unknown"

    def test_recovery_with_improve_commits(self, tmp_path):
        d = _init_repo(tmp_path)
        (d / "SKILL.md").write_text("# x\n")
        subprocess.run(["git", "add", "."], cwd=str(d), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(d), check=True)
        # simulate an improve keep commit (score 2→3)
        subprocess.run(["git", "commit", "--allow-empty", "-qm",
                        "improve: [a02] some rule (score 2→3)"], cwd=str(d), check=True)

        rc, out = _cli("recovery", skill_dir=str(d))
        assert rc == 0
        assert out["iteration"] == 2  # one improve commit → next is iteration 2
        assert out["last_assertion_id"] == "a02"
        assert out["last_action"] == "keep"

    def test_recovery_via_run_command(self, tmp_path):
        # the dispatch function also accepts skill_dir positionally.
        d = _init_repo(tmp_path)
        (d / "SKILL.md").write_text("# x\n")
        subprocess.run(["git", "add", "."], cwd=str(d), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(d), check=True)
        out = _run_command("recovery", {}, skill_dir=str(d))
        assert out["iteration"] == 1
