#!/usr/bin/env python3
"""Валидатор любой .excalidraw-деки: python3 validate_deck.py file.excalidraw.

Проверяет: уникальность id, существование контейнеров и фреймов, bound-текст
внутри контейнера, оценку переноса (теснота), выход элементов за фрейм.
Код возврата 1 — есть FAIL. Импортирует est_wrapped_height из excalidraw_deck.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from excalidraw_deck import est_wrapped_height, contrast  # noqa: E402


def validate(path):
    problems = []
    d = json.load(open(path, encoding="utf-8"))
    els = d["elements"]
    paper = d.get("appState", {}).get("viewBackgroundColor", "#ffffff")
    ids = [e["id"] for e in els]
    if len(ids) != len(set(ids)):
        problems.append("FAIL: дубликаты id")
    by_id = {e["id"]: e for e in els}
    frames = {e["id"]: e for e in els if e["type"] == "frame"}
    for e in els:
        cid = e.get("containerId")
        if cid:
            c = by_id.get(cid)
            if not c:
                problems.append(f"FAIL: текст {e['id']} без контейнера")
                continue
            if not (c["x"] <= e["x"] and c["y"] <= e["y"] and
                    e["x"] + e["width"] <= c["x"] + c["width"] and
                    e["y"] + e["height"] <= c["y"] + c["height"]):
                problems.append(f"FAIL: bound-текст вне контейнера {cid}")
            th = est_wrapped_height(e["text"], e["width"],
                                    e["fontSize"], e.get("fontFamily", 2))
            if th > c["height"] - 4:
                problems.append(
                    f"WARN: тесно в {cid} (~{th:.0f} > {c['height']:.0f}): "
                    f"{e['text'][:40]!r}")
        fid = e.get("frameId")
        if fid and fid not in frames:
            problems.append(f"FAIL: {e['id']} ссылается на чужой фрейм")
    for e in els:
        if e["type"] != "text":
            continue
        key = (e.get("customData") or {}).get("deck-key") or ""
        keyed = bool(key) and not key.startswith("panel/")
        c = by_id.get(e.get("containerId"))
        bg = c["backgroundColor"] if c and c.get("backgroundColor") not in (None, "transparent") else paper
        r = contrast(e["strokeColor"], bg)
        fs = e.get("fontSize", 0)
        fail_at = 3.0 if fs >= 40 else 4.5
        warn_at = 4.5 if fs >= 40 else (7.0 if fs >= 22 else None)
        if r < fail_at:
            lvl = "FAIL" if keyed else "WARN"
            problems.append(f"{lvl}: контраст {r:.1f}:1 < {fail_at} — {e['text'][:40]!r} на {bg}")
        elif warn_at and r < warn_at:
            problems.append(f"WARN: контраст {r:.1f}:1 < {warn_at} — {e['text'][:40]!r} на {bg}")
    for f in frames.values():
        kids = [e for e in els if e.get("frameId") == f["id"]]
        for e in kids:
            if e["type"] == "arrow":
                continue
            if (e["x"] < f["x"] - 1 or e["y"] < f["y"] - 1 or
                    e["x"] + e["width"] > f["x"] + f["width"] + 1 or
                    e["y"] + e["height"] > f["y"] + f["height"] + 1):
                problems.append(
                    f"WARN: вылезает из фрейма {f.get('name')}: "
                    f"{e.get('text', e['id'])[:40]!r}")
    return problems


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    issues = validate(sys.argv[1])
    fails = [p for p in issues if p.startswith("FAIL")]
    for p in issues:
        print(p)
    print(f"--- {len(fails)} FAIL, {len(issues) - len(fails)} WARN")
    sys.exit(1 if fails else 0)
