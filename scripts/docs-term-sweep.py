#!/usr/bin/env python3
"""docs-term-sweep — mechanical grounding check for Astra Monitoring public docs.

Extracts inline-code tokens (`` `...` `` spans) from a docs .md page and greps each
against the CODE of the Astra meta-repo (go/ts/tsx/py/yaml/json/sh/sql/j2 — markdown
is excluded on purpose). A token that exists only in docs and nowhere in code is the
"fabricated term" smell: e.g. a NoData mode "Evaluate as zero" that the enum never
defined (found in production, MON-4708 follow-up).

This is an ADVISOR, not a hard gate: unmatched does not mean wrong (SNMP trap names,
third-party products, RU UI labels). Unmatched tokens go to a human/agent review table;
each must end up grounded (code:line, live probe) or allowlisted.

Usage:
  docs-term-sweep.py docs/source/monitors_and_notifications/monitors-guide.md
  docs-term-sweep.py page.md --strict            # exit 1 if unactioned UNMATCHED remain
  docs-term-sweep.py page.md --allow allow.json  # allowlist: {"linkDown": "SNMP trap name"}
  docs-term-sweep.py page.md --alias "Нет данных=No data"   # RU label -> code string

Roots default to the meta-repo found by walking up from the input file
(<meta>/docs/source/... -> <meta>). Override with --roots dir1 dir2.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Inline code span: one line, non-empty, no backticks inside.
SPAN_RE = re.compile(r"`([^`\n]+)`")

# Skip spans that are paths, URLs, template expressions, refs, or punctuation noise.
SKIP_RE = re.compile(
    r"(^/|\.\w{1,5}$|://"           # /path, file.ext, scheme://
    r"|\{\{|\}\}|^\s*<|>\s*$"       # {{.Var}}, <tag>
    r"|^\d+(\.\d+)*$"               # bare numbers
    r"|^(S|N|X)\d*$)"               # placeholders
)

# Rule examples and math are not product terms: `Critical >= 50`, `a>0`, `30°C`.
# Their truth lives in the rule editor, not in the codebase.
RULE_EXAMPLE_RE = re.compile(r"[<>=°]")

MIN_TOKEN_LEN = 3  # kills `a`, `b`, `-1`, `>=` — sub-term noise

CODE_GLOBS = [
    "*.go", "*.ts", "*.tsx", "*.py", "*.yaml", "*.yml",
    "*.json", "*.sh", "*.sql", "*.tpl", "*.j2",
]

EXCLUDE_DIRS = ["node_modules", ".venv", "vendor", "build", "dist", "__pycache__"]

# rg globs applied on top of roots: harness leftovers that mirror docs/pages back
# at the scan (playwright page snapshots, worktrees, session stores) — matches there
# are self-confirming echoes, not code evidence.
EXCLUDE_GLOBS = ["!.playwright-mcp/**", "!.claude/**", "!**/worktrees/**", "!**/tmp/**"]


def collect_spans(text: str) -> list[str]:
    seen, out = set(), []
    for m in SPAN_RE.finditer(text):
        tok = m.group(1).strip()
        if (
            not tok
            or len(tok) < MIN_TOKEN_LEN
            or SKIP_RE.search(tok)
            or RULE_EXAMPLE_RE.search(tok)
            or tok in seen
        ):
            continue
        seen.add(tok)
        out.append(tok)
    return out


def repos_yml_roots(md_path: Path) -> list[Path]:
    """Canonical code roots: repo names from <meta>/repos.yml (`core: - name: x`).

    Searching only registry repos keeps PM/, meta/, ai-agent/ and one-off dumps out —
    a match in a customer folder or a page snapshot is not code evidence.
    """
    for p in md_path.resolve().parents:
        if p.name == "source" and p.parent.name == "docs":
            registry = p.parent.parent / "repos.yml"
            if registry.is_file():
                names = re.findall(r"^\s*-\s*name:\s*([\w-]+)", registry.read_text(), re.M)
                meta = p.parent.parent
                return [meta / n for n in names if (meta / n).is_dir()]
    return []


def meta_roots_from(md_path: Path) -> list[Path]:
    """Fallback when repos.yml is absent: walk up to the meta dir."""
    for p in md_path.resolve().parents:
        if p.name == "source" and p.parent.name == "docs":
            return [p.parent.parent]
    return [Path.cwd()]


def find_rg() -> tuple[str | None, str | None]:
    """Locate a usable ripgrep engine. Returns (argv, executable_or_None).

    `rg` is often a shell-function shim (e.g. Claude Code's bundled rg via
    `exec -a rg <claude binary>`), invisible to PATH lookup. Resolution order:
    real binary on PATH -> common brew locations -> the shim's target binary
    (run with argv0="rg", which is how the shim itself invokes it) -> None (grep).
    """
    if shutil.which("rg"):
        return "rg", None
    for cand in ("/opt/homebrew/bin/rg", "/usr/local/bin/rg"):
        if Path(cand).is_file() and Path(cand).stat().st_mode & 0o111:
            return cand, None
    shim = Path("~/bin/claude").expanduser()
    if not shim.is_file():
        shim = Path("~/").expanduser() / ".local/bin/claude"
    if shim.is_file() and shim.stat().st_mode & 0o111:
        return str(shim), "rg"  # args[0]="rg" becomes argv0, executable=shim
    return None, None


def scan_once(patterns: list[str], roots: list[Path]) -> dict[str, str]:
    """One search pass over all roots; map pattern -> first `file:line` hit.

    Single rg process with -e per pattern — one full tree walk for the whole page,
    instead of one per token (a meta-repo walk is seconds; a hundred of them are not).
    Falls back to plain grep (one pass per pattern, slower but rare).
    """
    hits: dict[str, str] = {}
    argv, exe = find_rg()
    if argv:
        base = [argv, "-S", "-n", "--no-heading", "--no-messages"]
        for g in CODE_GLOBS + EXCLUDE_GLOBS:
            base += ["-g", g]
        for d in EXCLUDE_DIRS:
            base += ["-g", f"!{d}/**"]
        for p in patterns:
            base += ["-e", p]
        base += [str(r) for r in roots]
        try:
            r = subprocess.run(base, capture_output=True, text=True, timeout=600,
                               executable=exe)  # None -> normal exec
        except (subprocess.TimeoutExpired, OSError):
            return {p: "TIMEOUT" for p in patterns}
        for line in r.stdout.splitlines():
            if ":" not in line:
                continue
            for p in patterns:
                if p not in hits and p in line:
                    hits[p] = line.strip()
                    break
        return hits
    # plain grep fallback — prune heavy dirs explicitly or the walk never ends
    inc: list[str] = []
    for g in CODE_GLOBS:
        inc += ["--include", g]
    for d in EXCLUDE_DIRS:
        inc += ["--exclude-dir", d]
    for p in patterns:
        r = subprocess.run(
            ["grep", "-rInF", "-S", *inc, "-e", p, "--", *[str(x) for x in roots]],
            capture_output=True, text=True, timeout=600,
        )
        first = next((l for l in r.stdout.splitlines() if l.strip()), None)
        if first:
            hits[p] = first.strip()
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("md_file", type=Path)
    ap.add_argument("--roots", nargs="*", type=Path)
    ap.add_argument("--allow", type=Path, help="JSON: {token|regex: reason}")
    ap.add_argument("--alias", action="append", default=[],
                    help="RU label -> code string, 'label=code' (repeatable)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any token is UNMATCHED and not allowlisted")
    args = ap.parse_args()

    text = args.md_file.read_text(encoding="utf-8")
    tokens = collect_spans(text)
    aliases = dict(a.split("=", 1) for a in args.alias)
    allow = json.loads(args.allow.read_text()) if args.allow else {}

    roots = args.roots or repos_yml_roots(args.md_file) or meta_roots_from(args.md_file)
    print(f"# docs-term-sweep: {args.md_file}")
    print(f"# roots: {', '.join(str(r) for r in roots)}; tokens: {len(tokens)}\n")

    alias_targets = [v for v in aliases.values() if v not in tokens]
    scan = scan_once(tokens + alias_targets, roots)

    rows, unmatched = [], []
    for tok in tokens:
        hit = scan.get(tok)
        if hit:
            status = hit
        elif tok in aliases:
            hit2 = scan.get(aliases[tok])
            status = f"ALIAS→{aliases[tok]}: {hit2}" if hit2 else f"ALIAS FAIL ({aliases[tok]})"
        elif any(re.fullmatch(a, tok) for a in allow):
            status = "ALLOWED"
        else:
            status = "UNMATCHED"
            unmatched.append(tok)
        rows.append((tok, status))

    w = max(len(t) for t, _ in rows) + 2
    HIT_CAP = 200  # seed yaml / test fixtures carry kilobyte lines — cap keeps the table readable
    for tok, status in rows:
        if len(status) > HIT_CAP:
            status = status[:HIT_CAP] + " …"
        print(f"{tok.ljust(w)} {status}")
    print(f"\n# total {len(rows)} | unmatched {len(unmatched)}: {', '.join(unmatched) or '—'}")
    print("# UNMATCHED = advisor flag, not a verdict: ground it (code:line / live probe) or allowlist it.")
    return 1 if args.strict and unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
