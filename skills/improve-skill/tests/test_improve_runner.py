"""
Tests for improve_runner — deterministic helper library for improve-skill v2.

The model stays the orchestrator; these pure functions hold state + decisions.
Run with: python3 -m pytest tests/test_improve_runner.py -v
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from improve_runner import (
    LoopState,
    ParsedArgs,
    AggScore,
    RulePlan,
    StopDecision,
    AuditFindings,
    RecoveryState,
    parse_args,
    discover_all_skills,
    load_or_regenerate_evals,
    make_branch_name,
    create_branch,
    aggregate_scores,
    pick_target_assertion,
    resolve_target_file,
    parse_rule_response,
    format_rule_marker,
    inject_rule,
    decide_action,
    commit_keep,
    revert_change,
    check_stop,
    parse_audit_response,
    problems_to_proposed_assertions,
    append_proposed_assertions,
    format_baseline_report,
    format_iteration_report,
    format_final_report,
    format_batch_summary,
    parse_git_log_recovery,
    update_state_from_action,
)


# ── Helpers ───────────────────────────────────────────────────────────


def make_result(passed_ids, failed_ids, total=None):
    """Build a run_assertions-style result dict from id lists."""
    passed = [{"id": i, "description": f"desc {i}"} for i in passed_ids]
    failed = [{"id": i, "description": f"desc {i}", "actual": "x"} for i in failed_ids]
    all_ids = list(passed_ids) + list(failed_ids)
    if total is None:
        total = len(all_ids)
    return {"total": total, "passed": passed, "failed": failed}


# ── 1. parse_args ─────────────────────────────────────────────────────


class TestParseArgs:
    def test_single_skill_name(self):
        r = parse_args(["tdd"])
        assert r.skill_names == ["tdd"]
        assert r.all_skills is False
        assert r.regen is False
        assert r.dry_run is False

    def test_all_flag(self):
        r = parse_args(["--all"])
        assert r.all_skills is True
        assert r.skill_names == []

    def test_regen_flag(self):
        r = parse_args(["tdd", "--regen"])
        assert r.regen is True
        assert r.skill_names == ["tdd"]

    def test_dry_run_flag(self):
        r = parse_args(["tdd", "--dry-run"])
        assert r.dry_run is True

    def test_combined_flags_and_names(self):
        r = parse_args(["--all", "--regen", "--dry-run"])
        assert r.all_skills and r.regen and r.dry_run

    def test_named_list(self):
        r = parse_args(["tdd", "code-review", "infostyle"])
        assert r.skill_names == ["tdd", "code-review", "infostyle"]
        assert r.all_skills is False

    def test_empty_argv(self):
        r = parse_args([])
        assert r.skill_names == []
        assert r.all_skills is False

    def test_unknown_flag_ignored(self):
        r = parse_args(["tdd", "--unknown"])
        assert r.skill_names == ["tdd"]

    def test_flags_before_names(self):
        r = parse_args(["--regen", "tdd"])
        assert r.regen is True
        assert r.skill_names == ["tdd"]


# ── 2. discover_all_skills ────────────────────────────────────────────


class TestDiscoverAllSkills:
    def test_discovers_skills_with_skill_md(self, tmp_path):
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "SKILL.md").write_text("# alpha\n")
        (tmp_path / "beta").mkdir()
        (tmp_path / "beta" / "SKILL.md").write_text("# beta\n")
        (tmp_path / "no-skill-md").mkdir()  # no SKILL.md → excluded
        result = discover_all_skills([str(tmp_path)])
        assert "alpha" in result
        assert "beta" in result
        assert "no-skill-md" not in result

    def test_excludes_improve_skill_itself(self, tmp_path):
        (tmp_path / "improve-skill").mkdir()
        (tmp_path / "improve-skill" / "SKILL.md").write_text("# improver\n")
        (tmp_path / "tdd").mkdir()
        (tmp_path / "tdd" / "SKILL.md").write_text("# tdd\n")
        result = discover_all_skills([str(tmp_path)])
        assert "improve-skill" not in result
        assert "tdd" in result

    def test_dedup_across_dirs(self, tmp_path):
        d1 = tmp_path / "d1"
        d2 = tmp_path / "d2"
        d1.mkdir()
        d2.mkdir()
        for d in (d1, d2):
            (d / "shared").mkdir()
            (d / "shared" / "SKILL.md").write_text("# shared\n")
        result = discover_all_skills([str(d1), str(d2)])
        assert result.count("shared") == 1

    def test_nonexistent_dir_skipped(self):
        result = discover_all_skills(["/nonexistent/path/xyz"])
        assert result == []

    def test_sorted_output(self, tmp_path):
        for name in ["zeta", "alpha", "mango"]:
            (tmp_path / name).mkdir()
            (tmp_path / name / "SKILL.md").write_text(f"# {name}\n")
        result = discover_all_skills([str(tmp_path)])
        assert result == sorted(result)


# ── 3. make_branch_name ───────────────────────────────────────────────


class TestMakeBranchName:
    def test_base_when_not_taken(self):
        assert make_branch_name("tdd", set()) == "improve/tdd"

    def test_suffix_2_on_collision(self):
        assert make_branch_name("tdd", {"improve/tdd"}) == "improve/tdd-2"

    def test_suffix_3_on_double_collision(self):
        assert make_branch_name("tdd", {"improve/tdd", "improve/tdd-2"}) == "improve/tdd-3"

    def test_no_collision_with_unrelated(self):
        assert make_branch_name("tdd", {"improve/other"}) == "improve/tdd"

    def test_high_collision_count(self):
        taken = {"improve/tdd"} | {f"improve/tdd-{n}" for n in range(2, 6)}
        assert make_branch_name("tdd", taken) == "improve/tdd-6"


# ── 4. aggregate_scores ───────────────────────────────────────────────


class TestAggregateScores:
    def test_pass_on_all_outputs(self):
        per_output = [
            make_result(["a01", "a02"], ["a03"]),
            make_result(["a01", "a02"], ["a03"]),
        ]
        agg = aggregate_scores(per_output)
        assert agg.total == 3
        assert set(agg.passed) == {"a01", "a02"}
        assert set(agg.failed) == {"a03"}

    def test_fail_if_fails_on_any_output(self):
        # a02 passes on output 1 but fails on output 2 → failing
        per_output = [
            make_result(["a01", "a02"], ["a03"]),
            make_result(["a01"], ["a02", "a03"]),
        ]
        agg = aggregate_scores(per_output)
        assert "a02" in agg.failed
        assert "a01" in agg.passed

    def test_per_assertion_matrix(self):
        per_output = [
            make_result(["a01", "a02"], ["a03"]),
            make_result(["a01"], ["a02", "a03"]),
        ]
        agg = aggregate_scores(per_output)
        assert agg.per_assertion["a01"] == [True, True]
        assert agg.per_assertion["a02"] == [True, False]
        assert agg.per_assertion["a03"] == [False, False]

    def test_single_output(self):
        per_output = [make_result(["a01"], ["a02", "a03"])]
        agg = aggregate_scores(per_output)
        assert agg.total == 3
        assert set(agg.passed) == {"a01"}
        assert set(agg.failed) == {"a02", "a03"}

    def test_empty_outputs(self):
        agg = aggregate_scores([])
        assert agg.total == 0
        assert agg.passed == []
        assert agg.failed == []

    def test_all_pass(self):
        per_output = [make_result(["a01", "a02"], []), make_result(["a01", "a02"], [])]
        agg = aggregate_scores(per_output)
        assert agg.failed == []
        assert set(agg.passed) == {"a01", "a02"}


# ── 5. pick_target_assertion ──────────────────────────────────────────


class TestPickTargetAssertion:
    def test_first_failing_by_id(self):
        agg = AggScore(total=4, passed=["a01", "a04"], failed=["a03", "a02"])
        target = pick_target_assertion(agg)
        assert target["id"] == "a02"  # lowest id among failing

    def test_none_when_all_pass(self):
        agg = AggScore(total=2, passed=["a01", "a02"], failed=[])
        target = pick_target_assertion(agg)
        assert target == {} or target is None

    def test_single_failure(self):
        agg = AggScore(total=3, passed=["a01", "a03"], failed=["a02"])
        assert pick_target_assertion(agg)["id"] == "a02"

    def test_picks_lowest_alpha(self):
        agg = AggScore(total=5, passed=["a01"], failed=["a10", "a02", "a05"])
        assert pick_target_assertion(agg)["id"] == "a02"


# ── 6. resolve_target_file ────────────────────────────────────────────


class TestResolveTargetFile:
    def test_specific_reference_file(self):
        a = {"source_file": "references/templates.md"}
        assert resolve_target_file(a) == "references/templates.md"

    def test_skill_md_falls_back_to_skill_md(self):
        a = {"source_file": "SKILL.md"}
        assert resolve_target_file(a) == "SKILL.md"

    def test_missing_source_file(self):
        a = {}
        assert resolve_target_file(a) == "SKILL.md"

    def test_empty_source_file(self):
        a = {"source_file": ""}
        assert resolve_target_file(a) == "SKILL.md"

    def test_nested_reference(self):
        a = {"source_file": "references/checklist.md"}
        assert resolve_target_file(a) == "references/checklist.md"


# ── 7. parse_rule_response ────────────────────────────────────────────


class TestParseRuleResponse:
    GOOD = """ANALYSIS: The output lacks a summary section because the skill never mandates one.
RULE: Always include a ## Summary section at the end of the output.
SECTION: ## Output Format
POSITION: after "## Output Format"
"""

    def test_parses_all_fields(self):
        plan = parse_rule_response(self.GOOD)
        assert plan is not None
        assert "## Summary" in plan.rule
        assert plan.section == "## Output Format"
        assert plan.position == 'after "## Output Format"'
        assert "summary section" in plan.analysis

    def test_multiline_analysis(self):
        text = """ANALYSIS: First line of analysis.
Second line continues here.
Third line.
RULE: The rule.
SECTION: ## S
POSITION: end of section ## S
"""
        plan = parse_rule_response(text)
        assert plan is not None
        assert "First line" in plan.analysis
        assert "Third line." in plan.analysis
        assert plan.rule == "The rule."

    def test_missing_rule_returns_none(self):
        text = "ANALYSIS: x\nSECTION: ## S\nPOSITION: end\n"
        assert parse_rule_response(text) is None

    def test_empty_text_returns_none(self):
        assert parse_rule_response("") is None
        assert parse_rule_response(None) is None

    def test_garbage_returns_none(self):
        assert parse_rule_response("blah blah no structure") is None

    def test_partial_missing_section(self):
        text = "RULE: do a thing\nPOSITION: end of file\n"
        plan = parse_rule_response(text)
        assert plan is not None
        assert plan.rule == "do a thing"
        assert plan.section == ""
        assert plan.position == "end of file"

    def test_no_raise_on_malformed(self):
        # must never raise
        for bad in ["RULE:", "RULE", "RULE:\nRULE:", ":::", "RULE: \nSECTION:\n"]:
            plan = parse_rule_response(bad)
            # either None or a RulePlan — never an exception
            assert plan is None or isinstance(plan, RulePlan)


# ── 8. format_rule_marker ─────────────────────────────────────────────


class TestFormatRuleMarker:
    def test_basic_format(self):
        m = format_rule_marker(3, "a02", "Always include a summary.")
        assert "<!-- improve-skill: iteration 3, assertion a02 -->" in m
        assert "- Always include a summary." in m
        assert "<!-- /improve-skill -->" in m

    def test_marker_order(self):
        m = format_rule_marker(1, "a01", "rule text")
        assert m.index("<!-- improve-skill:") < m.index("- rule text")
        assert m.index("- rule text") < m.index("<!-- /improve-skill -->")


# ── 9. inject_rule ────────────────────────────────────────────────────


class TestInjectRule:
    def test_after_heading(self):
        body = "# Title\n\n## Section A\nsome content\n"
        plan = RulePlan(analysis="", rule="new rule", section="## Section A",
                        position='after "## Section A"')
        out = inject_rule(body, plan)
        # new content appears right after the heading, before "some content"
        assert out.index("- new rule") > out.index("## Section A")
        assert out.index("- new rule") < out.index("some content")

    def test_before_heading(self):
        body = "## A\nx\n\n## B\ny\n"
        plan = RulePlan("", "rb", "## B", 'before "## B"')
        out = inject_rule(body, plan)
        assert out.index("- rb") < out.index("## B")
        assert out.index("- rb") > out.index("x")  # after section A content "x"

    def test_end_of_section(self):
        body = "## A\nfirst\nsecond\n\n## B\nx\n"
        plan = RulePlan("", "rend", "## A", 'end of section "## A"')
        out = inject_rule(body, plan)
        assert out.index("- rend") > out.index("second")
        assert out.index("- rend") < out.index("## B")

    def test_frontmatter_preserved(self):
        body = "---\nname: x\ndescription: y\n---\n# Title\n\n## S\ncontent\n"
        plan = RulePlan("", "r", "## S", 'after "## S"')
        out = inject_rule(body, plan)
        assert out.startswith("---\nname: x\ndescription: y\n---")
        assert "- r" in out
        # marker not inserted inside frontmatter
        assert out.index("- r") > out.index("## S")

    def test_code_fence_headings_ignored(self):
        body = "## Real\n\n```\n## NotAHeading\n```\nmore\n\n## Next\nz\n"
        plan = RulePlan("", "rf", "## Real", 'end of section "## Real"')
        out = inject_rule(body, plan)
        # injected after "more" (real section end), not inside fence
        assert out.index("- rf") > out.index("more")
        assert out.index("- rf") < out.index("## Next")

    def test_empty_file(self):
        plan = RulePlan("", "ronly", "", "")
        out = inject_rule("", plan)
        assert "- ronly" in out

    def test_last_section_no_trailing_newline(self):
        body = "## Solo\ncontent"  # no trailing newline
        plan = RulePlan("", "rlast", "## Solo", 'end of section "## Solo"')
        out = inject_rule(body, plan)
        assert "- rlast" in out
        # original content preserved
        assert "content" in out

    def test_section_not_found_appends(self):
        body = "## A\nx\n"
        plan = RulePlan("", "rappend", "## Nonexistent", 'end of section "## Nonexistent"')
        out = inject_rule(body, plan)
        assert "- rappend" in out
        # appended at end
        assert out.index("- rappend") > out.index("x")

    def test_custom_block_used(self):
        body = "## S\nc\n"
        plan = RulePlan("", "r", "## S", 'after "## S"')
        marker = "<!-- improve-skill: iteration 1, assertion a01 -->\n- marked\n<!-- /improve-skill -->"
        out = inject_rule(body, plan, block=marker)
        assert "marked" in out
        assert "improve-skill" in out

    def test_no_position_uses_section(self):
        body = "## S\nfirst\n\n## T\nx\n"
        plan = RulePlan("", "r", "## S", "")
        out = inject_rule(body, plan)
        assert out.index("- r") > out.index("first")
        assert out.index("- r") < out.index("## T")


# ── 10. decide_action ─────────────────────────────────────────────────


class TestDecideAction:
    @pytest.mark.parametrize("new,prev,expected", [
        (5, 3, "keep"),
        (3, 3, "revert"),   # equal → revert
        (2, 3, "revert"),   # lower → revert
        (4, 0, "keep"),
        (10, 9, "keep"),
    ])
    def test_action_matrix(self, new, prev, expected):
        assert decide_action(new, prev) == expected


# ── 11. check_stop ────────────────────────────────────────────────────


class TestCheckStop:
    def test_all_pass_stops(self):
        d = check_stop(5, 5, 0, 1)
        assert d.stop is True
        assert d.reason == "ALL_PASS"

    def test_continue_when_not_all_pass(self):
        d = check_stop(3, 5, 0, 1)
        assert d.stop is False
        assert d.reason == ""

    def test_plateau_stops(self):
        d = check_stop(3, 5, 3, 5)
        assert d.stop is True
        assert d.reason == "PLATEAU"

    def test_below_plateau_continues(self):
        d = check_stop(3, 5, 2, 5)
        assert d.stop is False

    def test_cap_stops(self):
        d = check_stop(3, 5, 0, 10)
        assert d.stop is True
        assert d.reason == "CAP"

    def test_all_pass_takes_priority_over_plateau(self):
        d = check_stop(5, 5, 3, 10)
        assert d.stop is True
        assert d.reason == "ALL_PASS"

    def test_zero_total_does_not_all_pass(self):
        d = check_stop(0, 0, 0, 1)
        assert d.stop is False  # no assertions → don't claim ALL_PASS


# ── 12. parse_audit_response ──────────────────────────────────────────


class TestParseAuditResponse:
    GOOD = """QUALITY_SCORE: B

DIMENSION: completeness
Score: 4
Issues: missing summary section
Suggestions: add a summary

DIMENSION: specificity
Score: 3
Issues: vague advice
Suggestions: add concrete numbers

RECURRING_PROBLEMS:
- outputs are too vague
- missing conclusion
"""

    def test_quality_score(self):
        f = parse_audit_response(self.GOOD)
        assert f.quality_score == "B"

    def test_dimensions_parsed(self):
        f = parse_audit_response(self.GOOD)
        assert "completeness" in f.dimensions
        assert f.dimensions["completeness"]["score"] == 4
        assert "specificity" in f.dimensions
        assert f.dimensions["specificity"]["score"] == 3

    def test_recurring_problems(self):
        f = parse_audit_response(self.GOOD)
        assert len(f.recurring_problems) == 2
        assert "too vague" in f.recurring_problems[0]

    def test_empty_text_no_raise(self):
        f = parse_audit_response("")
        assert isinstance(f, AuditFindings)
        assert f.dimensions == {}
        assert f.recurring_problems == []

    def test_garbage_no_raise(self):
        f = parse_audit_response("totally unstructured text without markers")
        assert isinstance(f, AuditFindings)

    def test_none_text_no_raise(self):
        f = parse_audit_response(None)
        assert isinstance(f, AuditFindings)

    def test_partial_dimensions(self):
        text = """QUALITY_SCORE: C
DIMENSION: accuracy
Score: 2
Issues: wrong
"""
        f = parse_audit_response(text)
        assert f.quality_score == "C"
        assert "accuracy" in f.dimensions


# ── 13. problems_to_proposed_assertions ───────────────────────────────


class TestProblemsToProposed:
    def test_id_schema_sequential(self):
        props = problems_to_proposed_assertions(["prob a", "prob b", "prob c"])
        ids = [p["id"] for p in props]
        assert ids == ["p01", "p02", "p03"]

    def test_required_fields(self):
        props = problems_to_proposed_assertions(["a problem"])
        p = props[0]
        for field in ("id", "description", "source_rule", "type", "source_file", "generator", "status"):
            assert field in p, f"missing {field}"
        assert p["source_file"] == "SKILL.md"
        assert p["generator"] == "audit"
        assert p["status"] == "proposed"

    def test_source_rule_preserved(self):
        props = problems_to_proposed_assertions(["the full problem text here"])
        assert props[0]["source_rule"] == "the full problem text here"

    def test_empty_list(self):
        assert problems_to_proposed_assertions([]) == []

    def test_check_type_is_valid(self):
        props = problems_to_proposed_assertions(["x", "y"])
        for p in props:
            assert p["type"] in ("contains", "not_contains", "regex", "not_regex")


# ── 14. append_proposed_assertions (JSON round-trip) ──────────────────


class TestAppendProposed:
    def test_round_trip_creates_array(self, tmp_path):
        evals_path = tmp_path / "evals.json"
        original = {"version": 2, "skill": "x", "assertions": []}
        evals_path.write_text(json.dumps(original))
        proposed = [{"id": "p01", "description": "d"}]
        append_proposed_assertions(str(evals_path), proposed)
        with open(evals_path) as f:
            loaded = json.load(f)
        assert loaded["proposed_assertions"] == proposed
        # original fields preserved
        assert loaded["version"] == 2
        assert loaded["skill"] == "x"

    def test_appends_to_existing_array(self, tmp_path):
        evals_path = tmp_path / "evals.json"
        original = {"version": 2, "skill": "x", "assertions": [],
                    "proposed_assertions": [{"id": "p01", "description": "old"}]}
        evals_path.write_text(json.dumps(original))
        append_proposed_assertions(str(evals_path), [{"id": "p02", "description": "new"}])
        with open(evals_path) as f:
            loaded = json.load(f)
        ids = [p["id"] for p in loaded["proposed_assertions"]]
        assert ids == ["p01", "p02"]

    def test_idempotent_structure(self, tmp_path):
        evals_path = tmp_path / "evals.json"
        original = {"version": 2, "skill": "x", "assertions": []}
        evals_path.write_text(json.dumps(original))
        append_proposed_assertions(str(evals_path), [])
        with open(evals_path) as f:
            loaded = json.load(f)
        assert loaded["proposed_assertions"] == []


# ── 15. update_state_from_action ──────────────────────────────────────


class TestUpdateStateFromAction:
    def test_keep_resets_plateau(self):
        s = LoopState(iteration=3, prev_score=2, plateau_count=2)
        new = update_state_from_action(s, "keep", delta=2)
        assert new.plateau_count == 0
        assert new.prev_score == 4

    def test_revert_increments_plateau(self):
        s = LoopState(iteration=3, prev_score=2, plateau_count=1)
        new = update_state_from_action(s, "revert", delta=0)
        assert new.plateau_count == 2
        assert new.prev_score == 2  # unchanged

    def test_does_not_mutate_original(self):
        s = LoopState(iteration=3, prev_score=2, plateau_count=1)
        new = update_state_from_action(s, "revert", delta=0)
        assert s.plateau_count == 1  # original untouched
        assert new is not s

    def test_keep_zero_delta(self):
        # keep with delta 0 shouldn't happen (decide_action would revert), but handle gracefully
        s = LoopState(prev_score=3, plateau_count=1)
        new = update_state_from_action(s, "keep", delta=0)
        assert new.prev_score == 3
        assert new.plateau_count == 0

    def test_three_reverts_reach_plateau(self):
        s = LoopState(prev_score=2, plateau_count=0)
        for _ in range(3):
            s = update_state_from_action(s, "revert", delta=0)
        assert s.plateau_count == 3  # triggers plateau stop


# ── 16. parse_git_log_recovery (pure parser) ──────────────────────────


class TestParseGitLogRecovery:
    def test_counts_commits(self):
        log = """abc123 improve(tdd): [a02] some rule (score 2→3)
def456 improve(tdd): [a01] first rule (score 1→2)
ghi789 unrelated commit
"""
        from improve_runner import _parse_recovery_from_log
        r = _parse_recovery_from_log(log)
        assert r.iteration == 3  # 2 improve commits + 1
        assert r.last_assertion_id == "a02"
        assert r.last_action == "keep"

    def test_no_commits(self):
        from improve_runner import _parse_recovery_from_log
        r = _parse_recovery_from_log("some unrelated\ncommits only\n")
        assert r.iteration == 1
        assert r.last_assertion_id is None

    def test_revert_detected_when_no_score_change(self):
        log = "abc improve(x): [a03] tried something"
        from improve_runner import _parse_recovery_from_log
        r = _parse_recovery_from_log(log)
        assert r.iteration == 2
        assert r.last_action != "keep"  # no score arrow → not a keep

    def test_empty_log(self):
        from improve_runner import _parse_recovery_from_log
        r = _parse_recovery_from_log("")
        assert r.iteration == 1


# ── 17. Git smoke tests (tmp_path repo) ───────────────────────────────


def _init_repo(tmp_path):
    """Create a real git repo with identity configured."""
    d = tmp_path / "repo"
    d.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(d), check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=str(d), check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(d), check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=str(d), check=True)
    return d


class TestGitSmoke:
    def test_create_branch(self, tmp_path):
        d = _init_repo(tmp_path)
        (d / "SKILL.md").write_text("# x\n")
        subprocess.run(["git", "add", "."], cwd=str(d), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(d), check=True)
        name = create_branch(str(d), "improve/x")
        assert name == "improve/x"
        # verify branch checked out
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           cwd=str(d), capture_output=True, text=True)
        assert r.stdout.strip() == "improve/x"

    def test_commit_keep(self, tmp_path):
        d = _init_repo(tmp_path)
        target = "SKILL.md"
        (d / target).write_text("# x\n")
        subprocess.run(["git", "add", "."], cwd=str(d), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(d), check=True)
        subprocess.run(["git", "checkout", "-qb", "improve/x"], cwd=str(d), check=True)
        (d / target).write_text("# x\n- new rule\n")
        msg = commit_keep(str(d), target, "new rule", 2, 3, assertion_id="a02")
        log = subprocess.run(["git", "log", "--oneline"], cwd=str(d),
                             capture_output=True, text=True).stdout
        assert "improve" in log
        assert "2→3" in msg

    def test_revert_change(self, tmp_path):
        d = _init_repo(tmp_path)
        target = "SKILL.md"
        (d / target).write_text("# original\n")
        subprocess.run(["git", "add", "."], cwd=str(d), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(d), check=True)
        (d / target).write_text("# modified\n")
        revert_change(str(d), target)
        assert (d / target).read_text() == "# original\n"


# ── 18. load_or_regenerate_evals ──────────────────────────────────────


class TestLoadOrRegenerate:
    def _make_skill(self, tmp_path):
        sd = tmp_path / "myskill"
        sd.mkdir()
        (sd / "SKILL.md").write_text("---\nname: myskill\ndescription: test\n---\n# Rules\n\n1. Never skip.\n")
        return sd

    def test_loads_existing(self, tmp_path):
        sd = self._make_skill(tmp_path)
        existing = {"version": 2, "skill": "myskill", "test_inputs": [],
                    "assertions": [{"id": "a01", "type": "contains", "value": "x"}]}
        (sd / "evals.json").write_text(json.dumps(existing))
        result = load_or_regenerate_evals(str(sd), str(tmp_path), regen=False)
        assert result["skill"] == "myskill"

    def test_regen_deletes_and_regenerates(self, tmp_path):
        sd = self._make_skill(tmp_path)
        existing = {"version": 2, "skill": "OLD", "assertions": []}
        (sd / "evals.json").write_text(json.dumps(existing))

        def fake_generate(path):
            return {"version": 2, "skill": "myskill", "test_inputs": [],
                    "assertions": [{"id": "a01", "type": "contains", "value": "y"}]}

        result = load_or_regenerate_evals(str(sd), str(tmp_path), regen=True, _generate=fake_generate)
        assert result["skill"] == "myskill"
        assert "OLD" not in str(result)

    def test_generates_when_missing(self, tmp_path):
        sd = self._make_skill(tmp_path)

        def fake_generate(path):
            return {"version": 2, "skill": "fresh", "assertions": []}

        result = load_or_regenerate_evals(str(sd), str(tmp_path), regen=False, _generate=fake_generate)
        assert result["skill"] == "fresh"


# ── 19. format_baseline_report ────────────────────────────────────────


class TestFormatBaselineReport:
    def test_includes_counts(self):
        report = format_baseline_report(
            "tdd", total=4,
            passing=["a01", "a02"],
            failing=[("a03", "desc a03"), ("a04", "desc a04")],
        )
        assert "2/4" in report
        assert "a03" in report
        assert "a01" in report

    def test_no_failing(self):
        report = format_baseline_report("tdd", total=2,
                                        passing=["a01", "a02"], failing=[])
        assert "2/2" in report


# ── 20. format_iteration_report ───────────────────────────────────────


class TestFormatIterationReport:
    def test_keep_report(self):
        s = LoopState(iteration=2, prev_score=3)
        delta = {"new": 4, "prev": 3, "total": 5, "action": "keep"}
        report = format_iteration_report(s, delta)
        assert "2/10" in report or "2" in report
        assert "KEEP" in report.upper()

    def test_revert_report(self):
        s = LoopState(iteration=3, prev_score=3)
        delta = {"new": 3, "prev": 3, "total": 5, "action": "revert"}
        report = format_iteration_report(s, delta)
        assert "REVERT" in report.upper()


# ── 21. format_final_report ───────────────────────────────────────────


class TestFormatFinalReport:
    def test_contains_baseline_and_final(self):
        s = LoopState(iteration=4, prev_score=3, agent_calls=8, llm_calls=2)
        baseline = {"passed": 2, "total": 5}
        final = {"passed": 3, "total": 5,
                 "per_assertion": {"a01": (True, True, "d1"), ("a03"): (False, True, "d3")}}
        audit = AuditFindings(quality_score="B", dimensions={"completeness": {"score": 4}},
                              recurring_problems=["vague"])
        proposed = [{"id": "p01", "description": "pd"}]
        report = format_final_report(s, baseline, final, audit, proposed)
        assert "2/5" in report
        assert "3/5" in report
        assert "B" in report
        assert "p01" in report

    def test_no_proposed(self):
        s = LoopState(iteration=1, prev_score=5)
        baseline = {"passed": 5, "total": 5}
        final = {"passed": 5, "total": 5, "per_assertion": {}}
        audit = AuditFindings(quality_score="A", dimensions={}, recurring_problems=[])
        report = format_final_report(s, baseline, final, audit, [])
        assert "A" in report


# ── 22. format_batch_summary ──────────────────────────────────────────


class TestFormatBatchSummary:
    def test_lists_success_and_failure(self):
        results = [
            {"skill": "tdd", "status": "success"},
            {"skill": "code-review", "status": "failed", "error": "boom"},
        ]
        report = format_batch_summary(results)
        assert "tdd" in report
        assert "code-review" in report
        assert "2" in report  # total

    def test_all_success(self):
        results = [{"skill": "a", "status": "success"}, {"skill": "b", "status": "success"}]
        report = format_batch_summary(results)
        assert "a" in report and "b" in report
