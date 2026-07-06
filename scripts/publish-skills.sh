#!/bin/bash
# publish-skills.sh — publish agent-knowledge/skills → am-skills (team GitLab repo)
#
# One-way mirror: copies the skills layer (+ _shared, _INDEX, link.sh, README/USAGE)
# from agent-knowledge into the am-skills repo and pushes. Colleagues clone am-skills.
#
# NEVER copied (personal): learnings/, decisions/, state/, standards/, docs/.
# NMT skills live in a separate zamesin clone and are NOT here (self-install, CC BY-NC-SA).
#
# Usage:
#   ./scripts/publish-skills.sh                                     # default clone path
#   AM_SKILLS_DIR=/path/to/am-skills ./scripts/publish-skills.sh   # custom path
#
# First time: create the empty repo in GitLab (astra-monitoring-icl/am-skills),
# clone it locally, point AM_SKILLS_DIR at it (or use the default below), run this script.

set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"                       # agent-knowledge root
AM_SKILLS_DIR="${AM_SKILLS_DIR:-$HOME/Documents/Code_projects/am-skills}"
PUBLISH_DIR="$SRC/scripts/publish"                            # templates for the published repo

if [ ! -d "$AM_SKILLS_DIR/.git" ]; then
  echo "ERROR: $AM_SKILLS_DIR is not a git clone of am-skills."
  echo ""
  echo "First-time setup:"
  echo "  1. Create the repo in GitLab: astra-monitoring-icl/am-skills (private)"
  echo "  2. Clone it:   git clone <am-skills-url> $AM_SKILLS_DIR"
  echo "  3. Re-run:     ./scripts/publish-skills.sh"
  exit 1
fi

echo "Publishing agent-knowledge/skills → $AM_SKILLS_DIR"
SRC_SHA="$(cd "$SRC" && git rev-parse --short HEAD)"

# 1. Mirror skills/
rm -rf "$AM_SKILLS_DIR/skills"
cp -R "$SRC/skills" "$AM_SKILLS_DIR/skills"

# 1a. Strip embedded git repos inside skills/ (e.g. a nested local clone) so they
#     publish as files, not as submodule pointers (which would be empty for colleagues).
find "$AM_SKILLS_DIR/skills" -name .git -prune -exec rm -rf {} +

# 1b. Strip per-skill _shared symlinks (link.sh recreates them at install time)
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

# 2. Copy the skill router (catalog with triggers)
cp "$SRC/skills/_INDEX.md" "$AM_SKILLS_DIR/_INDEX.md"

# 2a. Exclude maintainer-only skills (not for end-users): drop the dir + its _INDEX row.
#      Override the list via env, e.g.  EXCLUDE_SKILLS="prune improve-skill" ./publish-skills.sh
EXCLUDE_SKILLS="${EXCLUDE_SKILLS:-prune}"
for ex in $EXCLUDE_SKILLS; do
  rm -rf "$AM_SKILLS_DIR/skills/$ex"
  find "$AM_SKILLS_DIR" -maxdepth 2 -name "_INDEX.md" -type f -print0 2>/dev/null \
    | while IFS= read -r -d '' idx; do
        sed "\#${ex}/SKILL\.md#d" "$idx" > "$idx.tmp" && mv "$idx.tmp" "$idx"
      done
done

# 3. Substitute the clone's remote URL into README/USAGE, then write templates
REMOTE_URL="$(cd "$AM_SKILLS_DIR" && git remote get-url origin 2>/dev/null || echo '<am-skills-url>')"
sed "s|%%AM_SKILLS_URL%%|$REMOTE_URL|g" "$PUBLISH_DIR/README.md"  > "$AM_SKILLS_DIR/README.md"
sed "s|%%AM_SKILLS_URL%%|$REMOTE_URL|g" "$PUBLISH_DIR/USAGE.md"   > "$AM_SKILLS_DIR/USAGE.md"
cp "$PUBLISH_DIR/link.sh"     "$AM_SKILLS_DIR/link.sh"
cp "$PUBLISH_DIR/.gitignore"  "$AM_SKILLS_DIR/.gitignore"
chmod +x "$AM_SKILLS_DIR/link.sh"

# 4. Commit + push — only if something changed
cd "$AM_SKILLS_DIR"
# Clear cached skills/ entries first: kills stale submodule gitlinks left by any
# embedded repo (git won't replace a gitlink with files on plain `git add`).
git rm -r --cached --quiet --ignore-unmatch skills/ >/dev/null 2>&1 || true
git add -A
if git diff --cached --quiet; then
  echo "Already up to date — no changes to publish (agent-knowledge@${SRC_SHA})."
else
  git commit -m "publish skills from agent-knowledge@${SRC_SHA}"
  git push -u origin HEAD
  echo "Published agent-knowledge@${SRC_SHA} → am-skills."
fi
