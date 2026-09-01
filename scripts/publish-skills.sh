#!/bin/bash
# publish-skills.sh — publish agent-knowledge/skills → am-skills (team GitLab repo)
#
# ADDITIVE publish: am-skills is a TEAM repo — colleagues add their own skills
# (e.g. tempo-fill, jira-task) directly there. This script syncs ONLY the skills
# that exist in agent-knowledge and never deletes anything else:
#   - per-skill rsync --delete (scoped to my own skill dirs)
#   - _INDEX.md merged via scripts/merge-index.py (team rows preserved)
#   - safety net: aborts if the staged diff deletes files outside my skills
#
# NEVER copied (personal): learnings/, decisions/, state/, standards/, docs/.
# NMT skills live in a separate zamesin clone and are NOT here (self-install, CC BY-NC-SA).
#
# Usage:
#   ./scripts/publish-skills.sh [--dry-run]   # default clone path
#   AM_SKILLS_DIR=/path/to/am-skills ./scripts/publish-skills.sh
#
# First time: clone the repo (astra-monitoring-icl/workspace/am-skills), point
# AM_SKILLS_DIR at it (or use the default below), run this script.

set -euo pipefail

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

SRC="$(cd "$(dirname "$0")/.." && pwd)"                       # agent-knowledge root
AM_SKILLS_DIR="${AM_SKILLS_DIR:-$HOME/Documents/Code_projects/am-skills}"
PUBLISH_DIR="$SRC/scripts/publish"                            # templates for the published repo

if [ ! -d "$AM_SKILLS_DIR/.git" ]; then
  echo "ERROR: $AM_SKILLS_DIR is not a git clone of am-skills."
  echo ""
  echo "First-time setup:"
  echo "  1. Clone the repo:  git clone <am-skills-url> $AM_SKILLS_DIR"
  echo "  2. Re-run:          ./scripts/publish-skills.sh"
  exit 1
fi

# Maintainer-only skills (not for end-users): dropped from the publish + index.
#  Override:  EXCLUDE_SKILLS="prune improve-skill" ./publish-skills.sh
EXCLUDE_SKILLS="${EXCLUDE_SKILLS:-prune}"

# The skill dirs this publish owns (canon = agent-knowledge). Everything else
# in am-skills/skills/ is team territory and is never touched.
MY_SKILL_DIRS=()
for d in "$SRC/skills"/*/; do
  name="$(basename "$d")"
  case " $EXCLUDE_SKILLS " in *" $name "*) continue;; esac
  MY_SKILL_DIRS+=("skills/$name")
done

echo "Publishing agent-knowledge/skills → $AM_SKILLS_DIR (additive; team skills untouched)"
SRC_SHA="$(cd "$SRC" && git rev-parse --short HEAD)"

# 0. Freshness: the clone must be up to date with the server BEFORE we layer
#    anything on top. Refuse to run on a stale/divergent clone — that is how
#    team skills got wiped historically (2026-08-11).
if [ "$DRY_RUN" -eq 0 ]; then
  git -C "$AM_SKILLS_DIR" pull --ff-only
fi

# 0a. Foreign edits guard: if teammates committed changes to MY skill dirs
#     since the last publish, this publish would silently overwrite them.
#     Refuse: the changes must first be folded back into agent-knowledge
#     (the canon) — or be consciously discarded with FORCE_PUBLISH=1.
LAST_PUBLISH="$(git -C "$AM_SKILLS_DIR" log --grep='^publish skills from agent-knowledge' -1 --format=%H 2>/dev/null || true)"
MY_EMAIL="$(git -C "$AM_SKILLS_DIR" config user.email 2>/dev/null || git config user.email)"
if [ -n "$LAST_PUBLISH" ] && [ "${FORCE_PUBLISH:-0}" != "1" ]; then
  # Own commits (my committer email) and publish commits are fine; anything
  # else touching my skill dirs is a foreign edit the publish would overwrite.
  FOREIGN="$(git -C "$AM_SKILLS_DIR" log "$LAST_PUBLISH"..HEAD --format='%h|%ce|%an — %s' \
    -- "${MY_SKILL_DIRS[@]}" 2>/dev/null \
    | grep -v 'publish skills from agent-knowledge' \
    | grep -v "$MY_EMAIL" \
    | cut -d'|' -f1,3 || true)"
  if [ -n "$FOREIGN" ]; then
    echo "ABORT: commits touching agent-knowledge-owned skills since last publish:"
    echo "$FOREIGN"
    echo ""
    echo "Fold these changes back into agent-knowledge (canon), then re-publish."
    echo "To consciously overwrite them instead: FORCE_PUBLISH=1 ./scripts/publish-skills.sh"
    exit 1
  fi
fi

# 1. Sync my skills — per-skill, scoped. rsync --delete inside MY dir only
#    (my files removed upstream disappear; other dirs are never touched).
for d in "$SRC/skills"/*/; do
  name="$(basename "$d")"
  case " $EXCLUDE_SKILLS " in *" $name "*) continue;; esac
  mkdir -p "$AM_SKILLS_DIR/skills/$name"
  rsync -a --delete "$d" "$AM_SKILLS_DIR/skills/$name/"
done
_shared_src="$SRC/skills/_shared"
if [ -d "$_shared_src" ]; then
  rsync -a --delete "$_shared_src/" "$AM_SKILLS_DIR/skills/_shared/"
fi

# 1a. Strip embedded git repos inside my skills (publish as files, not gitlinks).
find "$AM_SKILLS_DIR/skills" -name .git -prune -exec rm -rf {} +

# 1b. Strip per-skill _shared symlinks (link.sh recreates them at install time).
find "$AM_SKILLS_DIR/skills" -maxdepth 2 -type l -name _shared -delete

# 1c. am-research depends on scripts/auto-retrieve.py, which in agent-knowledge is a
#     symlink (skills/am-research/scripts → repo-root scripts/). Publish it as a REAL
#     file so the skill runs without agent-knowledge's repo root. auto-retrieve.py
#     degrades gracefully when learnings/ is absent — colleagues have none.
AMR="$AM_SKILLS_DIR/skills/am-research"
if [ -e "$AMR" ] && [ -e "$SRC/scripts/auto-retrieve.py" ]; then
  rm -rf "$AMR/scripts"
  mkdir -p "$AMR/scripts"
  cp "$SRC/scripts/auto-retrieve.py" "$AMR/scripts/auto-retrieve.py"
fi

# 2. Index: MERGE, never overwrite. My rows come from SRC (canon), team rows
#    (skills not in agent-knowledge) are preserved into a dedicated section.
MERGE_EXCLUDE="$EXCLUDE_SKILLS" python3 "$SRC/scripts/merge-index.py" \
  "$SRC/skills/_INDEX.md" "$AM_SKILLS_DIR/_INDEX.md" "$AM_SKILLS_DIR/_INDEX.md"

# 3. Substitute the clone's remote URL into README/USAGE, then write templates.
#    (Repo infrastructure — my layer. Team skills/ content is untouched by this.)
REMOTE_URL="$(cd "$AM_SKILLS_DIR" && git remote get-url origin 2>/dev/null | sed 's|//[^@]*@|//|')"
REMOTE_URL="${REMOTE_URL:-https://gitlab.astra-monitoring.astralinux.ru/astra-monitoring-icl/workspace/am-skills.git}"
sed "s|%%AM_SKILLS_URL%%|$REMOTE_URL|g" "$PUBLISH_DIR/README.md"  > "$AM_SKILLS_DIR/README.md"
sed "s|%%AM_SKILLS_URL%%|$REMOTE_URL|g" "$PUBLISH_DIR/USAGE.md"   > "$AM_SKILLS_DIR/USAGE.md"
cp "$PUBLISH_DIR/link.sh"     "$AM_SKILLS_DIR/link.sh"
cp "$PUBLISH_DIR/.gitignore"  "$AM_SKILLS_DIR/.gitignore"
chmod +x "$AM_SKILLS_DIR/link.sh"

# 4. Commit + push — only if something changed.
cd "$AM_SKILLS_DIR"
git rm -r --cached --quiet --ignore-unmatch skills/ >/dev/null 2>&1 || true
git add -A

# Safety net: if the staged diff deletes anything in skills/ that is NOT one of
# my published skills, stop. Team content must never disappear in a publish.
DELETIONS="$(git diff --cached --name-only --diff-filter=D | sed -n 's|^skills/||; s|/.*||p' | sort -u)"
for del in $DELETIONS; do
  if [ ! -d "$SRC/skills/$del" ]; then
    echo "ABORT: publish would delete '$del' which is not from agent-knowledge."
    echo "Restore it (git checkout -- skills/$del) and investigate before publishing."
    exit 1
  fi
done

if git diff --cached --quiet; then
  echo "Already up to date — no changes to publish (agent-knowledge@${SRC_SHA})."
else
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[DRY-RUN] Would commit + push. Staged changes:"
    git diff --cached --stat | tail -5
    git diff --cached --name-status | head -30
  else
    git commit -m "publish skills from agent-knowledge@${SRC_SHA} (additive — team skills preserved)"
    git push -u origin HEAD
    echo "Published agent-knowledge@${SRC_SHA} → am-skills."
  fi
fi