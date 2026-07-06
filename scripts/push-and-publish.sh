#!/bin/bash
# push-and-publish.sh — push agent-knowledge to GitHub, then mirror skills → am-skills.
# One-command replacement for:  git push && ./scripts/publish-skills.sh
#
# Usage:
#   ./scripts/push-and-publish.sh        # from agent-knowledge root
#   git pushup                           # if the alias is set (see below)
#
# Set the alias once (local to this repo):
#   git config alias.pushup '!./scripts/push-and-publish.sh'
#
# Note: the publish half pushes to GitLab (am-skills) — run while on VPN.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"   # agent-knowledge root
cd "$ROOT"

echo "=== 1/2  git push  (agent-knowledge → GitHub) ==="
git push

echo ""
echo "=== 2/2  publish skills  (agent-knowledge → am-skills) ==="
./scripts/publish-skills.sh
