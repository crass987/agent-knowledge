#!/bin/bash
# link.sh — install am-skills into Claude Code (global, via symlinks)
# Usage: ./link.sh [--unlink]
# After linking, skills fire in every project via ~/.claude/skills/

set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION="${1:-link}"
LINKS_CLAUDE="$HOME/.claude/skills"
TARGET_SKILLS="$REPO_DIR/skills"

unlink_all() {
  echo "Removing am-skills symlinks..."
  for dir in "$TARGET_SKILLS"/*/; do
    name=$(basename "$dir")
    [ "$name" = "_shared" ] && continue
    link="$LINKS_CLAUDE/$name"
    if [ -L "$link" ]; then rm "$link"; echo "  removed: $name"; fi
  done
  echo "Done."
}

# Recreate per-skill _shared symlinks so skill-root-relative refs like
# `_shared/infostyle-core.md` resolve under deploy. Idempotent.
ensure_shared_links() {
  for dir in "$TARGET_SKILLS"/*/; do
    name=$(basename "$dir")
    [ "$name" = "_shared" ] && continue
    grep -rq "_shared/" "$dir" --include="*.md" 2>/dev/null || continue
    link="$dir/_shared"
    if [ -L "$link" ]; then
      [ "$(readlink "$link")" = "../_shared" ] && continue
      rm "$link"
    elif [ -e "$link" ]; then
      echo "  WARNING: $link exists and is not a symlink — skipping."
      continue
    fi
    ln -s ../_shared "$link"
  done
}

link_all() {
  echo "Installing am-skills → ~/.claude/skills/"
  mkdir -p "$LINKS_CLAUDE"
  for dir in "$TARGET_SKILLS"/*/; do
    name=$(basename "$dir")
    [ "$name" = "_shared" ] && continue
    link="$LINKS_CLAUDE/$name"
    if [ -L "$link" ]; then
      rm "$link"
    elif [ -e "$link" ]; then
      echo "  WARNING: $link exists and is not a symlink — skipping. Remove it manually."
      continue
    fi
    ln -s "$dir" "$link"
    echo "  linked: $name"
  done
  ensure_shared_links
  echo ""
  echo "Done. Skills fire as slash commands in any project: /am-research, /jtbd, /infostyle ..."
  echo "Full list with triggers: _INDEX.md"
}

if [ "$ACTION" = "--unlink" ]; then
  unlink_all
else
  link_all
fi
