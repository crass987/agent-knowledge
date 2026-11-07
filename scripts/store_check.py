#!/usr/bin/env python3
"""store_check.py — mechanical hygiene checks for harness knowledge stores.

Read-only. Never fixes anything — fixes happen through prune decisions.
Exit code: 1 if any ERROR (gate-worthy), 0 otherwise (WARN/INFO don't block).

Checks:
  entry:  missing/invalid frontmatter, duplicate keys, stale `files:` paths,
          broken [[wikilinks]] (LINK-ROT), superseded_by pointing nowhere (ORPHAN),
          entry age (INFO only — age never fails)
  memory: optional `stale_after` (expired or bad format) and `refs:` (broken paths)
          fields — WARN-level freshness pointers, never block
  store:  MEMORY.md <-> memory/ index sync, memory files missing from index,
          size budgets (WARN — never blocks)

Usage:
  store_check.py [--root PATH] [--memory PATH] [--quick] [--json]
"""
import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

DEFAULT_BUDGETS = {"MEMORY.md": 200}  # lines; vendor guidance for auto-memory index
AGE_INFO_DAYS = 365
HOME_PROJECTS = Path.home() / "Documents" / "Code_projects"
WORKSPACE_ROOTS = (HOME_PROJECTS / "Astra",)  # sibling repos the stores reference

REQUIRED_LEARNINGS = ("type", "key", "insight", "confidence", "source", "ts", "scope")
REQUIRED_DECISIONS = ("id", "status", "decided")


@dataclass
class Finding:
    level: str  # ERROR | WARN | INFO
    code: str
    file: str
    line: int
    message: str


@dataclass
class Entry:
    file: Path
    line_start: int
    fm: dict
    body: str


def parse_blocks(text: str):
    """Split a store file into (frontmatter_lines, body_lines, line_start) blocks.

    `---` opens frontmatter, next `---` closes it, body runs to the next `---`.
    HTML comments are skipped entirely (decisions files embed an example block).
    """
    blocks, in_comment = [], False
    state, cur_start, cur_fm, cur_body = "idle", 0, [], []

    def finalize():
        if state in ("fm", "body") and cur_start:
            blocks.append((list(cur_fm), list(cur_body), cur_start))

    for i, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped == "<!--":
            in_comment = True
            continue
        if in_comment:
            if stripped == "-->":
                in_comment = False
            continue
        if stripped == "---":
            if state == "fm":
                state = "body"
            elif state == "body":
                finalize()
                state, cur_start, cur_fm, cur_body = "fm", i, [], []
            else:
                state, cur_start, cur_fm, cur_body = "fm", i, [], []
        elif state == "fm":
            cur_fm.append(raw)
        elif state == "body":
            cur_body.append(raw)
    finalize()
    return blocks


def parse_fm(fm_lines):
    """Top-level `key: value` pairs; indented lines (nested maps) are ignored."""
    fm = {}
    for line in fm_lines:
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip("'\"")
    return fm


def collect_entries(paths):
    """Entries from store files; a learnings file with content but no blocks is an error."""
    entries, no_fm = [], []
    for path in paths:
        if path.name == "README.md" or not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        blocks = parse_blocks(text)
        if not blocks and text.strip():
            no_fm.append(path)
            continue
        for fm_lines, body_lines, line_start in blocks:
            entries.append(Entry(path, line_start, parse_fm(fm_lines), "\n".join(body_lines)))
    return entries, no_fm


def parse_file_list(value):
    if not value or value.strip() in ("[]", ""):
        return []
    return [p.strip().strip("'\"") for p in value.strip().strip("[]").split(",") if p.strip()]


def files_ref_exists(path: str, root: Path, extra_roots: tuple = WORKSPACE_ROOTS) -> bool:
    candidates = [Path(path).expanduser(), root / path, HOME_PROJECTS / path]
    candidates += [ws / path for ws in extra_roots]
    return any(c.exists() for c in candidates)


WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
# repo-path mentions in skill/prompt files: `repo/dir/file.md` in backticks or after "→ "
SKILL_PATH = re.compile(r"`([A-Za-z0-9_.-]+/[\w./\-]+?\.[A-Za-z]{1,5})`")
INDEX_LINE = re.compile(r"^- \[.*?\]\((.+?)\)")


def check(root: Path, memory: Path = None, quick: bool = False, budgets: dict = None,
          resolve_roots: tuple = WORKSPACE_ROOTS):
    root = Path(root)
    findings = []

    def add(level, code, file, line, message):
        findings.append(Finding(level, code, str(file), line, message))

    learnings_files = sorted((root / "learnings").glob("*.md")) if (root / "learnings").is_dir() else []
    decisions_file = root / "decisions" / "decisions.active.md"
    memory_dir = Path(memory) if memory else (root / "memory" if (root / "memory").is_dir() else None)

    entries, no_fm = collect_entries(learnings_files + [decisions_file])
    for path in no_fm:
        level = "WARN" if "<!--" in path.read_text(encoding="utf-8") else "ERROR"
        add(level, "no-frontmatter", path, 1, "store file has content but no frontmatter blocks")

    # global key space: learnings keys + decision ids + memory names
    key_owner = {}
    known_keys = set()

    def register(key, file, line):
        if key in key_owner:
            add("ERROR", "dup-key", file, line, f"key '{key}' already in {key_owner[key]}")
        else:
            key_owner[key] = str(file)
        known_keys.add(key)

    for e in entries:
        if "id" in e.fm:
            key, required = e.fm["id"], REQUIRED_DECISIONS
        else:
            key, required = e.fm.get("key"), REQUIRED_LEARNINGS
        if key:
            register(key, e.file, e.line_start)

    memory_names = {p.stem for p in sorted(memory_dir.glob("*.md")) if p.name != "MEMORY.md"} \
        if memory_dir else set()
    known_keys |= memory_names

    today = date.today()
    for e in entries:
        is_decision = "id" in e.fm
        required = REQUIRED_DECISIONS if is_decision else REQUIRED_LEARNINGS
        key = e.fm.get("id") if is_decision else e.fm.get("key")
        for field in required:
            if not e.fm.get(field):
                add("ERROR", "missing-field", e.file, e.line_start, f"missing '{field}'")

        conf = e.fm.get("confidence")
        if conf and not (conf.isdigit() and 1 <= int(conf) <= 10):
            add("ERROR", "bad-confidence", e.file, e.line_start, f"confidence '{conf}' not 1-10")

        ts = e.fm.get("ts", "")
        try:
            entry_date = datetime.strptime(ts, "%Y-%m-%d").date()
            if (today - entry_date).days > AGE_INFO_DAYS:
                add("INFO", "age", e.file, e.line_start,
                    f"last confirmed {ts} ({(today - entry_date).days}d ago)")
        except ValueError:
            if ts:
                add("ERROR", "bad-ts", e.file, e.line_start, f"ts '{ts}' not YYYY-MM-DD")

        for ref in parse_file_list(e.fm.get("files", "")):
            if not files_ref_exists(ref, root, resolve_roots):
                add("ERROR", "stale-files-ref", e.file, e.line_start, f"files: '{ref}' not found")

        text = e.body + "\n" + e.fm.get("insight", "")
        for target in WIKILINK.findall(text):
            if target.strip() not in known_keys:
                add("ERROR", "link-rot", e.file, e.line_start, f"[[{target}]] resolves to nothing")

        sup = e.fm.get("superseded_by", "")
        for target in [s.strip() for s in re.split(r"[,\[\]]", sup) if s.strip()]:
            if target not in known_keys:
                add("ERROR", "orphan-supersede", e.file, e.line_start,
                    f"superseded_by '{target}' resolves to nothing")

    # memory entry freshness — optional fields, WARN-level only (age never blocks)
    if memory_dir:
        for mpath in sorted(memory_dir.glob("*.md")):
            if mpath.name == "MEMORY.md":
                continue
            for fm_lines, _body, line_start in parse_blocks(mpath.read_text(encoding="utf-8")):
                fm = parse_fm(fm_lines)
                sa = fm.get("stale_after", "")
                if sa:
                    try:
                        expired = (today - datetime.strptime(sa, "%Y-%m-%d").date()).days
                        if expired > 0:
                            add("WARN", "stale-after", mpath, line_start,
                                f"stale_after {sa} expired {expired}d ago")
                    except ValueError:
                        add("WARN", "bad-stale-after", mpath, line_start,
                            f"stale_after '{sa}' not YYYY-MM-DD")
                for ref in parse_file_list(fm.get("refs", "")):
                    if not files_ref_exists(ref, root, resolve_roots):
                        add("WARN", "stale-refs", mpath, line_start, f"refs: '{ref}' not found")

    link_targets = set()  # [[wikilink]] targets across all stores — backlinks count as indexing

    if not quick:
        # paths referenced from skills must resolve — catches doc-trees that moved
        # (класс «C2 переехал из master_docs в internal_docs, скиллы молча указывают
        # в старое место»). Только «якорные» ссылки: первый сегмент — реальный
        # топ-уровень каталога одного из корней (путь притворяется корневым).
        # Фрагменты (references/…, lib/…, ../…) — проза-относительные, пропускаем.
        # WARN-уровень: виден в prune/traverse, коммиты не блокирует (чужие репо
        # двигаются без нас — гейт не должен падать от чужого переезда).
        anchors = set()
        for r in [root, *resolve_roots, HOME_PROJECTS]:
            if r.is_dir():
                anchors |= {p.name for p in r.iterdir() if p.is_dir()}
        PLACEHOLDER = re.compile(r"YYYY|NN|XXX|<[^>]*>|\.\w+/\.\w+")  # примеры и <шаблоны>
        # только SKILL.md: вложенные дизайн-доки (issues/, references/) описывают
        # будущие/контекстные файлы — проза, не операционные ссылки
        harness_files = [p for p in (root / "skills").rglob("SKILL.md")] if (root / "skills").is_dir() else []
        # операционные промпты скиллов (skills/*/prompts/*.md) — они же брифы
        # сабагентов: живые пути, под той же проверкой
        harness_files += [p for p in (root / "skills").glob("*/prompts/*.md")]
        for hf in harness_files:
            for line in hf.read_text(encoding="utf-8").splitlines():
                # «create lazily»-пути: файл создаётся самим скиллом при первом
                # использовании — отложенный, не мёртвый
                if "create lazily" in line or "создаёт*ся при первом" in line:
                    continue
                for ref in SKILL_PATH.findall(line):
                    if ref.startswith(("http", "mcp__")) or PLACEHOLDER.search(ref):
                        continue
                    if ref.split("/")[0] not in anchors:
                        continue
                    candidates = [Path(ref).expanduser(), root / ref, hf.parent / ref,
                                  hf.parent.parent / ref]
                    candidates += [ws / ref for ws in resolve_roots + (HOME_PROJECTS,)]
                    if not any(c.exists() for c in candidates):
                        add("WARN", "dead-path", hf, 1,
                            f"referenced path '{ref}' not found (repo moved?)")
        # MEMORY.md lives inside the memory dir (auto-memory layout); tests use root/
        if memory_dir and (memory_dir / "MEMORY.md").exists():
            index_file = memory_dir / "MEMORY.md"
        else:
            index_file = root / "MEMORY.md"
        indexed = set()
        expected_dir = memory_dir or (root / "memory")
        if index_file.exists():
            n_lines = 0
            for line in index_file.read_text(encoding="utf-8").splitlines():
                n_lines += 1
                # любая (file.md)-ссылка в строке индексирует файл — и своя строка,
                # и инлайн-упоминание в чужой строке; [^()] — не съедать вложенные скобки
                for target in re.findall(r"\(([^()]+\.md)\)", line):
                    indexed.add(Path(target).stem)
                    if not (expected_dir / target).exists():
                        add("ERROR", "index-broken", index_file, n_lines,
                            f"index points to missing {target}")
            if budgets is None:
                budgets = DEFAULT_BUDGETS
            limit = (budgets or {}).get("MEMORY.md")
            if limit and n_lines > limit:
                add("WARN", "budget", index_file, n_lines,
                    f"MEMORY.md has {n_lines} lines (budget {limit})")
        if memory_dir:
            # backlinks index too: a file reachable via [[name]] from any store body is not an orphan
            for e in entries:
                link_targets.update(t.strip() for t in WIKILINK.findall(e.body))
            for mpath in memory_dir.glob("*.md"):
                for fm_lines, body_lines, _ in parse_blocks(mpath.read_text(encoding="utf-8")):
                    link_targets.update(t.strip() for t in WIKILINK.findall("\n".join(body_lines)))
            for name in sorted(memory_names - indexed - link_targets):
                add("WARN", "index-missing", memory_dir / f"{name}.md", 1,
                    "memory file has no index line and no [[backlinks]]")

    return findings


def exit_code(findings) -> int:
    return 1 if any(f.level == "ERROR" for f in findings) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--memory", default=None, help="path to auto-memory dir (index sync + freshness checks)")
    ap.add_argument("--quick", action="store_true", help="entry-level checks only")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    findings = check(Path(args.root), memory=Path(args.memory) if args.memory else None,
                     quick=args.quick)
    if args.json:
        print(json.dumps([f.__dict__ for f in findings], ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f"{f.level:5} {f.code:16} {f.file}:{f.line} {f.message}")
        n_err = sum(1 for f in findings if f.level == "ERROR")
        n_warn = sum(1 for f in findings if f.level == "WARN")
        print(f"--- {len(findings)} findings: {n_err} error, {n_warn} warn, "
              f"{len(findings) - n_err - n_warn} info")
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
