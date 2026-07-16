#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idempotently install (or remove) the infostyle-critic Stop hook in the GLOBAL
~/.claude/settings.json. Merge-only: preserves every existing key (env, tokens,
mcpServers, plugins...). Safe to re-run; makes `clone agent-knowledge && ./link.sh`
deploy the skill + agent + hook together.

Usage:
  install_global_hook.py "<command string>"           # install
  install_global_hook.py "<command string>" --remove  # remove

Never crashes the deploy: on any parse/write error it prints a warning and exits 0.
Creates ~/.claude/settings.json.bak before the first write (belt-and-suspenders for
a file that may carry secrets).
"""
import json
import os
import shutil
import sys

SETTINGS = os.path.expanduser("~/.claude/settings.json")
BAK = SETTINGS + ".bak"


def _load():
    try:
        with open(SETTINGS, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return {}, None
    except Exception as e:
        return None, str(e)


def _has(stop, command):
    for grp in stop:
        if isinstance(grp, dict):
            for h in grp.get("hooks") or []:
                if isinstance(h, dict) and h.get("command") == command:
                    return True
    return False


def main():
    if len(sys.argv) < 2:
        print("usage: install_global_hook.py <command> [--remove]", file=sys.stderr)
        sys.exit(0)
    command = sys.argv[1]
    remove = "--remove" in sys.argv[2:]

    cfg, err = _load()
    if err is not None:
        print(f"  WARN: cannot parse {SETTINGS} ({err}); hook not "
              f"{'removed' if remove else 'installed'}.", file=sys.stderr)
        sys.exit(0)

    hooks = cfg.get("hooks")
    if not isinstance(hooks, dict):
        if remove:
            print("  no hooks block; nothing to remove.")
            sys.exit(0)
        hooks = {}
        cfg["hooks"] = hooks

    stop = hooks.get("Stop")
    if not isinstance(stop, list):
        if remove:
            print("  no Stop hook; nothing to remove.")
            sys.exit(0)
        stop = []
        hooks["Stop"] = stop

    if remove:
        if not _has(stop, command):
            print("  hook not present; nothing to remove.")
            sys.exit(0)
        for grp in stop:
            if isinstance(grp, dict):
                grp["hooks"] = [h for h in (grp.get("hooks") or [])
                                if not (isinstance(h, dict) and h.get("command") == command)]
        stop[:] = [grp for grp in stop if isinstance(grp, dict) and (grp.get("hooks"))]
        if not stop:
            del hooks["Stop"]
        if not hooks:
            del cfg["hooks"]
        msg = "removed"
    else:
        if _has(stop, command):
            print("  hook already present (infostyle-critic gate).")
            sys.exit(0)
        stop.append({"hooks": [{"type": "command", "command": command}]})
        hooks["Stop"] = stop
        cfg["hooks"] = hooks
        msg = "installed"

    # backup (reflects last-known-good), then write — preserve key order, 2-space indent
    try:
        if os.path.exists(SETTINGS):
            shutil.copyfile(SETTINGS, BAK)
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  {msg} Stop hook (infostyle-critic gate) -> {SETTINGS}")
        if os.path.exists(BAK):
            print(f"  backup: {BAK}")
    except Exception as e:
        print(f"  WARN: write failed ({e}); settings.json untouched.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"  WARN: {e}", file=sys.stderr)
