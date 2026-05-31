---
name: improve-skill
description: Use when the user wants to improve a Claude Code skill's output quality — "improve the tdd skill", "improve-skill video-knowledge-extraction", "auto-improve my skills", "improve all skills", "run improve-skill on X". Triggers on skill improvement and skill quality requests. Does NOT trigger on general code improvement ("improve this code") or skill writing ("write a skill").
---

# improve-skill — Autonomous Skill Improvement (v2)

Improve a skill's output quality using a Karpathy-style loop: change → test → keep or revert.

## When to Use

- User says "improve the X skill" or "/improve-skill X"
- User says "improve all skills" or "/improve-skill --all"
- User says "auto-improve my skills"
- User wants to systematically verify or improve skill output quality

## When NOT to Use

- General code improvement requests ("improve this code", "refactor this function")
- Writing a new skill from scratch (that's `/write-a-skill`)
- Editing skill descriptions (that's Anthropic's Skill Creator)

## Invocation

```
/improve-skill <skill-name>
```

Batch mode, --dry-run, --regen, and named lists are NOT in this version.

## Architecture

This skill is self-contained orchestration. Python handles deterministic evaluation;
this SKILL.md handles all reasoning.

| Component | Location | Role |
|-----------|----------|------|
| Eval generation | `lib/eval_generator.py` | Hybrid heuristic + LLM seam → evals.json |
| Assertion scoring | `lib/assertion_runner.py` | Deterministic: text + evals → pass/fail JSON |
| Improvement loop | This SKILL.md | Diagnosis, rule generation, file targeting, git |

The lib/ path is relative to this skill's directory:
```
SKILL_DIR/lib/
```

Search paths for skill directories:
```
~/.claude/skills/
~/Documents/Code_projects/agent-knowledge/skills/
```

## Tool Interfaces

### eval_generator.py

```bash
python3 <skill_dir>/lib/eval_generator.py <target_skill_dir>
# → prints evals JSON to stdout
```

### assertion_runner.py

```bash
python3 <skill_dir>/lib/assertion_runner.py --evals <evals.json> --output <output.txt>
# → prints {"total": N, "passed": [...], "failed": [...]} to stdout
# → exit code: 0 = all pass, 1 = any fail
```

## Safety Constraints

These rules are ABSOLUTE. Violating them breaks the improvement loop's trustworthiness.

1. **Only edit `*.md` files and `evals.json`** in the target skill directory.
2. **Never modify** `*.py`, `*.sh`, `*.js`, `scripts/*`, or any executable file.
3. **Never modify files outside** the target skill directory.
4. **One file change per iteration** — atomic, traceable.
5. **Always use `git checkout -- <file>` to revert** bad changes. Never leave a regression.
6. **Hard cap of 10 iterations** per skill. Stop when reached.

## Workflow

Follow these phases in order. Print phase headers as shown — the user relies on them.

---

### PHASE 1: SETUP

Print:
```
══════════════════════════════════════════════
PHASE 1: SETUP — <skill-name>
══════════════════════════════════════════════
```

#### 1a. Parse arguments

The skill name is the argument after `/improve-skill`.
- If no argument provided: ask the user which skill to improve, then continue.
- If argument is `--all`: not supported in this version. Tell the user to use single-skill mode.

#### 1b. Discover skill directory

Search for `<skill-name>/SKILL.md` in these directories (in order):
1. `~/.claude/skills/`
2. `~/Documents/Code_projects/agent-knowledge/skills/`

If not found, ask the user for the correct path. Store the found directory as `SKILL_DIR`.

Also determine `THIS_DIR` — the directory containing this improve-skill SKILL.md:
```
THIS_DIR = ~/.claude/skills/improve-skill  (or the resolved symlink target)
```

Print:
```
Skill:      <skill-name>
Directory:  <SKILL_DIR>
```

#### 1c. Create git branch

Create an improvement branch for traceability:

```bash
cd <SKILL_DIR>
BRANCH="improve/<skill-name>-$(date +%Y-%m-%d)"
git checkout -b "$BRANCH"
```

If the branch already exists, append a numeric suffix: `-2`, `-3`, etc.

Print:
```
Branch:     <branch-name>
```

#### 1d. Read all skill files

Read every `.md` file in the skill directory:
- `SKILL.md` (always)
- `references/*.md` (if references/ directory exists)

Store the content for later diagnosis. Also note the file list — these are the only editable targets.

Print:
```
Files:      SKILL.md, references/X.md, references/Y.md, ...
```

#### 1e. Generate or load evals.json

Check if `<SKILL_DIR>/evals.json` already exists.

**If exists:** load it. Validate it's v2 schema (has `test_inputs` array, `version: 2`).
If schema is v1 or invalid, regenerate.

**If not exists:** generate:

```bash
python3 <THIS_DIR>/lib/eval_generator.py <SKILL_DIR> > <SKILL_DIR>/evals.json
```

After loading/generating, parse the evals.json to extract:
- `test_inputs` array (for baseline phase)
- `assertions` array with their `id`, `description`, `source_file`, `type`

Print:
```
Evals:      <N> assertions, <M> test inputs
Assert:     a01: <description>
            a02: <description>
            ...
Inputs:     1. <label> (type)
            2. <label> (type)
```

---

### PHASE 2: BASELINE

Print:
```
══════════════════════════════════════════════
PHASE 2: BASELINE
══════════════════════════════════════════════
```

#### 2a. Execute skill on each test input

For each `test_input` in `evals.json.test_inputs`:

**If type is "prompt":**
Use the Agent tool to run the target skill. The Agent prompt is:
```
You are running the <skill-name> skill. Process the following request:
<test_input.text>
```

**If type is "file":**
Use the Agent tool to run the target skill with the file. The Agent prompt is:
```
You are running the <skill-name> skill. Process the following file:
<test_input.path>
```

Save each Agent's output to a temp file:
```
/tmp/improve-skill-output-<skill-name>-input<N>.txt
```

Print per input:
```
── Input <N>: <label> ──
Agent completed. Output saved (<X> words).
```

#### 2b. Score outputs

For each output file, run assertion_runner:

```bash
python3 <THIS_DIR>/lib/assertion_runner.py --evals <SKILL_DIR>/evals.json --output /tmp/improve-skill-output-<skill-name>-input<N>.txt
```

The runner prints JSON: `{"total": N, "passed": [...], "failed": [...]}`.

#### 2c. Aggregate scores

Combine results across all test inputs:
- Count total assertions (from evals.json)
- Count how many pass across ALL outputs (an assertion passes if it passes on ALL outputs)
- List which assertions fail on at least one output

Print:
```
Baseline:   <PASSED>/<TOTAL> passed
Failing:    a03: <description>
            a07: <description>
            ...
Passing:    a01, a02, a04, a05, a06, ...
```

If baseline is perfect (all pass), print:
```
All assertions pass. No improvement needed.
```
Then skip to reporting.

---

### PHASE 3: IMPROVEMENT LOOP

Print:
```
══════════════════════════════════════════════
PHASE 3: IMPROVEMENT LOOP (max 10 iterations)
══════════════════════════════════════════════
```

Track these state variables across iterations:
- `ITERATION`: starts at 1, increments each loop
- `PREV_SCORE`: the passing count from the previous iteration (baseline score for iteration 1)
- `PLATEAU_COUNT`: consecutive iterations with no improvement, starts at 0
- `AGENT_CALLS`: cumulative Agent tool invocations
- `LLM_CALLS`: cumulative LLM diagnosis/rule-generation calls

#### 3a. DIAGNOSE

Print:
```
── Iteration <N>/10 ──
Step 3a: DIAGNOSE
```

**Identify first failing assertion:**
From the aggregated score, pick the first failing assertion (lowest `id` sort).

**Resolve target file:**
1. Check the assertion's `source_file` field in evals.json
2. If `source_file` is a specific file (e.g., `"references/templates.md"`): use it as target
3. If `source_file` is `"SKILL.md"` or unclear: use SKILL.md as target
4. If `source_file` is missing: use SKILL.md as target (last resort)

Print:
```
Target assertion: a<XX> — <description>
Source file:      <source_file>
Target file:      <resolved_target_file>
```

#### 3b. GENERATE RULE

Print:
```
Step 3b: GENERATE RULE
```

Use the Agent tool (this counts as an LLM call) with this prompt:

```
You are a skill improvement assistant. Your job is to write a single rule that,
when added to a skill's instructions, will fix a failing assertion.

## Failing assertion
- ID: <assertion_id>
- Description: <assertion_description>
- Source rule: <assertion_source_rule>
- Type: <assertion_type>
- Expected: <assertion_check or assertion_value>

## Recent skill output (snippet — last 500 words of output that failed this assertion)
<snippet_from_latest_output>

## Target file content
<full_content_of_target_file>

## Your task
1. Analyze WHY the assertion fails — what is the skill missing or doing wrong?
2. Write a SINGLE rule that fixes this. The rule must:
   - Be in the same language and style as the existing skill content
   - Be specific and actionable (not vague like "provide better output")
   - Target the specific gap that causes the assertion failure
3. Decide WHERE to place the rule:
   - Specify the section heading it should go under
   - Specify if it goes BEFORE or AFTER a specific existing line/heading
   - Prefer inserting into the most relevant section

Return your answer in this EXACT format:
```
ANALYSIS: <one paragraph explaining why the assertion fails>
RULE: <the rule text, in the skill's language and style>
SECTION: <heading of the section to insert into>
POSITION: <after "## Some Heading" or before "## Another Heading" or "end of section X">
```
```

Increment `LLM_CALLS`.

Parse the Agent's response to extract: `RULE`, `SECTION`, `POSITION`.

Print:
```
Analysis:   <ANALYSIS summary>
Rule:       <RULE text>
Section:    <SECTION>
Position:   <POSITION>
```

#### 3c. INJECT

Print:
```
Step 3c: INJECT
```

Use the Edit tool to inject the rule into the target file at the specified position.

The rule must be wrapped in marker comments for traceability:

```
<!-- improve-skill: iteration <N>, assertion a<XX> -->
- <RULE text>
<!-- /improve-skill -->
```

**Placement logic:**
- Read the target file
- Find the section specified by `SECTION`
- Apply the `POSITION`:
  - If "after X": insert after the line containing X
  - If "before X": insert before the line containing X
  - If "end of section X": insert after the last content line in that section (before the next heading or end of file)
- If the section doesn't exist, append to the end of the file before the last heading

**IMPORTANT:** Only use Edit tool. Only modify the single target file. This must be an atomic change.

Print:
```
Injected rule into <target_file> at <position>
```

#### 3d. RE-SCORE

Print:
```
Step 3d: RE-SCORE
```

1. Re-run the skill via Agent on ALL test_inputs (same as Phase 2a)
   - Save new outputs, overwriting the previous temp files
   - Increment `AGENT_CALLS` per test_input

2. Score each new output via assertion_runner.py (same as Phase 2b)

3. Aggregate scores (same logic as Phase 2c)

4. Compare with `PREV_SCORE`:
   - `NEW_SCORE` = number of assertions now passing
   - `DELTA` = `NEW_SCORE - PREV_SCORE`

Print:
```
Score:      <NEW_SCORE>/<TOTAL> (was <PREV_SCORE>, delta <+/-><DELTA>)
```

#### 3e. DECIDE

Print:
```
Step 3e: DECIDE
```

**If score improved** (NEW_SCORE > PREV_SCORE):
```bash
cd <SKILL_DIR>
git add <target_file>
git commit -m "improve(<skill-name>): <RULE text truncated to 60 chars> (score <PREV_SCORE>→<NEW_SCORE>)"
```
Update `PREV_SCORE = NEW_SCORE`.
Reset `PLATEAU_COUNT = 0`.

Print:
```
Action:     KEEP — score improved
Commit:     improve(<skill-name>): <truncated rule>
```

**If score same or lower** (NEW_SCORE <= PREV_SCORE):
```bash
cd <SKILL_DIR>
git checkout -- <target_file>
```
Keep `PREV_SCORE` unchanged.
Increment `PLATEAU_COUNT += 1`.

Print:
```
Action:     REVERT — score did not improve
Reverted:   <target_file>
```

#### 3f. STOP CHECK

Print:
```
Step 3f: STOP CHECK
```

Check stopping conditions in order:
1. **All pass**: `NEW_SCORE == TOTAL` → stop (success)
2. **Plateau**: `PLATEAU_COUNT >= 3` → stop (no progress for 3 iterations)
3. **Cap**: `ITERATION >= 10` → stop (hard cap)

If none apply: increment `ITERATION += 1` and go back to **Step 3a**.

Print:
```
Status:     <CONTINUE | ALL PASS | PLATEAU (3 iterations) | CAP (10 iterations)>
```

If stopping, print summary:
```
Stopping reason: <reason>
Total iterations: <N>
Agent calls: <AGENT_CALLS>
LLM calls: <LLM_CALLS>
```

---

### PHASE 4: REPORT

Print:
```
══════════════════════════════════════════════
PHASE 4: REPORT
══════════════════════════════════════════════
```

#### 4a. Score comparison

Show baseline vs final, per assertion:

```
Baseline:   <BASELINE_PASSED>/<TOTAL>
Final:      <FINAL_PASSED>/<TOTAL>
Improved:   <+N> assertions fixed

Per-assertion:
  a01: ✅ → ✅  (<description>)
  a02: ✅ → ✅  (<description>)
  a03: ❌ → ✅  (<description>)  ← FIXED
  a04: ✅ → ✅  (<description>)
  a05: ❌ → ❌  (<description>)  ← STILL FAILING
  ...
```

#### 4b. Git commits

```bash
cd <SKILL_DIR>
git log --oneline <original-branch>..HEAD
```

Print the commit list.

#### 4c. Summary

```
Skill:          <skill-name>
Iterations:     <N>
Agent calls:    <N>
LLM calls:      <N>
Commits:        <N>
Baseline:       <B>/<T>
Final:          <F>/<T>
Status:         <SUCCESS | PARTIAL | PLATEAU | CAP>
```

If there are still-failing assertions, note them:
```
Remaining failures:
  a<XX>: <description>
  a<YY>: <description>

These may require:
- LLM-based assertions (run with --regen after adding LLM phase)
- Manual skill review
- Multiple improvement sessions
```

## Cost Tracking

After each iteration in Phase 3, display:
```
[COST] Iteration <N>: <AGENT_CALLS> agent calls, <LLM_CALLS> LLM calls cumulative
```
