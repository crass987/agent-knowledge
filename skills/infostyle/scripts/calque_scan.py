#!/usr/bin/env python3
"""Детерминированный сканер калек и канцелярита (скилл infostyle).

Ловит то, что стоп-сканер и локальный критик пропускают: кальки of-phrase,
кальки-оборотчики, канцелярит, EN-ru гибриды, оценки без меры. Паттерны живут
в calque_patterns.json рядом; заведение нового — references/pattern-admission.md.

Сканер предлагает — решает человек: находка не приговор (SKILL.md «Что такое сдано»).
"""
import argparse
import json
import re
import sys
from pathlib import Path

PATTERNS_FILE = Path(__file__).with_name("calque_patterns.json")
TIER_LABELS = {
    "calque": "калька",
    "officialese": "канцелярит",
    "hybrid": "гибрид",
    "stop": "стоп",
    "loose": "loose",
}


def load():
    data = json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
    patterns = []
    for p in data["patterns"]:
        patterns.append({
            "id": p["id"],
            "tier": p["tier"],
            "re": re.compile(p["check"], re.IGNORECASE),
            "fix": p.get("fix", ""),
            "source": p.get("source", ""),
        })
    return data, patterns


def mask_line(line):
    """Убирает то, где проза не проверяется: inline-код, URL, HTML-комментарии."""
    line = re.sub(r"`[^`]*`", " ", line)
    line = re.sub(r"\]\([^)]+\)", "]()", line)          # URL из markdown-ссылки
    line = re.sub(r"<!--.*?-->", " ", line)
    return line


def iter_prose_lines(text):
    """Yields (line_no, line) мимо frontmatter и ограждённых блоков кода."""
    in_fence = False
    in_front = text.startswith("---")
    for no, line in enumerate(text.splitlines(), 1):
        if in_front:
            if no > 1 and line.strip() == "---":
                in_front = False
            continue
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield no, line


def is_allowed_hybrid(m, allowlist, generic):
    en, ru = m.group(1).lower(), m.group(2).lower()
    return en in allowlist and any(ru.startswith(g) for g in generic)


def scan_text(text, patterns, cfg, use_loose=False):
    """Возвращает список находок: dict(file, line, tier, id, match, fix)."""
    allowlist = set(cfg.get("hybrid_allowlist", []))
    generic = cfg.get("hybrid_generic_ru", [])
    hits = []
    for no, raw in iter_prose_lines(text):
        line = mask_line(raw)
        for p in patterns:
            if p["tier"] == "loose" and not use_loose:
                continue
            for m in p["re"].finditer(line):
                if p["tier"] == "hybrid" and is_allowed_hybrid(m, allowlist, generic):
                    continue
                hits.append({
                    "line": no,
                    "tier": p["tier"],
                    "id": p["id"],
                    "match": m.group(0).strip(),
                    "fix": p["fix"],
                })
    return hits


def report(fname, hits, words):
    for h in hits:
        print(f"{fname}:{h['line']} [{TIER_LABELS[h['tier']]} {h['id']}] "
              f"«{h['match']}» → {h['fix']}")
    counts = {}
    for h in hits:
        counts[h["tier"]] = counts.get(h["tier"], 0) + 1
    parts = [f"{TIER_LABELS[t]} {counts[t]}" for t in
             ("calque", "officialese", "hybrid", "stop", "loose") if t in counts]
    density = (len(hits) / words * 1000) if words else 0.0
    print(f"— {fname}: {', '.join(parts) if parts else 'чисто'} · "
          f"{len(hits)} находок / {words} слов = {density:.1f} на 1000 слов")
    return counts


CLEAN = ("Агент собирает метрики раз в минуту и отправляет их в ClickHouse. "
         "Если запрос не дошёл, буфер хранит точки на диске: 10 МБ по умолчанию. "
         "Проверить доставку можно в разделе «Мониторы».")

ALLOWED = "API-ключ хранится в YAML-манифесте, а SaaS-решение проще в поддержке."


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="файлы .md для проверки")
    ap.add_argument("--loose", action="store_true",
                    help="показывать и шумный тир loose")
    ap.add_argument("--json", action="store_true", help="вывод в JSON")
    ap.add_argument("--selftest", action="store_true",
                    help="прогнать встроенные фикстуры")
    args = ap.parse_args()

    cfg, patterns = load()

    if args.selftest:
        inputs = {i["id"]: i["text"] for i in
                  json.loads(evals_path().read_text(encoding="utf-8"))["test_inputs"]}
        failures = 0
        for fid, floor in (("i1", 8), ("i2", 6)):
            n = len(scan_text(inputs[fid], patterns, cfg))
            ok = n >= floor
            failures += not ok
            print(f"selftest {fid}: {n} находок (ожидалось ≥{floor}) "
                  f"{'✓' if ok else '✗'}")
        for label, text, expect in (
                ("clean", CLEAN, 0), ("allowlist", ALLOWED, 0)):
            n = len(scan_text(text, patterns, cfg))
            ok = n == expect
            failures += not ok
            print(f"selftest {label}: {n} находок (ожидалось {expect}) "
                  f"{'✓' if ok else '✗'}")
        sys.exit(1 if failures else 0)

    if not args.paths:
        ap.error("укажите файлы или --selftest")

    all_hits = []
    for path in args.paths:
        text = Path(path).read_text(encoding="utf-8")
        hits = scan_text(text, patterns, cfg, use_loose=args.loose)
        words = len(re.findall(r"[А-Яа-яЁёA-Za-z0-9]+", mask_line(text)))
        if args.json:
            all_hits.extend({**h, "file": path} for h in hits)
        else:
            report(path, hits, words)

    if args.json:
        print(json.dumps(all_hits, ensure_ascii=False, indent=2))


def evals_path():
    return Path(__file__).parent.parent / "evals.json"


if __name__ == "__main__":
    main()
