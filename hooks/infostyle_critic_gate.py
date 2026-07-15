#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stop-hook gate for infostyle acceptance.

Wired into a project's .claude/settings.json as a Stop hook. Blocks the agent from
stopping if, IN THE CURRENT TURN, it invoked the `infostyle` skill but did NOT dispatch
the `infostyle-critic` agent. The critic is the acceptance gate; this hook stops the
writing agent from self-certifying via scanners and declaring "done" without an
independent cold read.

FAILS OPEN: any parse error, missing field, unreadable transcript, or uncertainty ->
allow the stop (never block on error). The 8-block harness hard cap + the
stop_hook_active check prevent infinite loops.

Stdin:  Claude Code Stop-hook JSON (uses transcript_path, stop_hook_active).
Stdout: {"decision":"block","reason":"..."} to block; nothing (exit 0) to allow.

Detection (current turn = entries after the last genuine human message):
  used_infostyle = a Skill tool_use with input.skill == "infostyle"
  ran_critic     = an Agent tool_use with input.subagent_type == "infostyle-critic"
  block iff used_infostyle and not ran_critic

Caveat (honest): only the canonical dispatch (Agent tool, subagent_type=infostyle-critic)
and the canonical skill load (Skill tool) are detected. Infostyle applied from
already-loaded context without a Skill call this turn is not caught -- the skill's own
instruction to dispatch the critic covers the common path; this hook is a backstop.
"""
import json
import sys


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.write("\n")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return  # malformed stdin -> allow

    # Loop guard: already blocked once this turn -> let it stop.
    if payload.get("stop_hook_active"):
        return

    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        return

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except Exception:
        return  # can't read transcript -> allow

    entries = []          # list of parsed JSON objects, in order
    last_human_idx = -1   # index into `entries`
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        entries.append(obj)
        if obj.get("type") == "user":
            msg = obj.get("message") or {}
            content = msg.get("content")
            is_tool_result = False
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        is_tool_result = True
                        break
            # genuine human message = a user entry that is NOT a tool_result
            if not is_tool_result:
                last_human_idx = len(entries) - 1

    start = last_human_idx + 1 if last_human_idx >= 0 else 0
    turn = entries[start:]

    used_infostyle = False
    ran_critic = False
    for obj in turn:
        if obj.get("type") != "assistant":
            continue
        msg = obj.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "tool_use":
                continue
            name = item.get("name")
            inp = item.get("input") or {}
            if name == "Skill" and inp.get("skill") == "infostyle":
                used_infostyle = True
            elif name == "Agent" and inp.get("subagent_type") == "infostyle-critic":
                ran_critic = True

    if used_infostyle and not ran_critic:
        emit({
            "decision": "block",
            "reason": (
                "В этом ходе использован скилл infostyle, но не запущен независимый "
                "критик. Перед сдачей диспатчи: "
                "Agent(subagent_type=\"infostyle-critic\", prompt=\"<текст на проверку>\"). "
                "Его вердикт (ЖИВОЙ/НА ГРАНИ/МЁРТВЫЙ) — финальный гейт приёмки; "
                "сдавать по самоотчёту сканеров нельзя."
            ),
        })
    # else: emit nothing -> allow


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open, always
