#!/bin/bash
# link.sh — connect agent-knowledge to Claude Code and other agents
# Usage: ./link.sh [--unlink]

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION="${1:-link}"

LINKS_CLAUDE="$HOME/.claude/skills"
TARGET_SKILLS="$REPO_DIR/skills"
TARGET_STANDARDS="$REPO_DIR/standards"

unlink_all() {
  echo "Removing symlinks..."
  for dir in "$TARGET_SKILLS"/*/; do
    name=$(basename "$dir")
    link="$LINKS_CLAUDE/$name"
    if [ -L "$link" ]; then
      rm "$link"
      echo "  removed: $link"
    fi
  done
  echo "Done."
}

link_all() {
  echo "Linking agent-knowledge to Claude Code..."

  # Ensure target directory exists
  mkdir -p "$LINKS_CLAUDE"

  # Link each skill
  for dir in "$TARGET_SKILLS"/*/; do
    name=$(basename "$dir")
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

  # Link standards as a whole directory
  link_standards="$LINKS_CLAUDE/standards"
  if [ -L "$link_standards" ]; then
    rm "$link_standards"
  fi
  ln -s "$TARGET_STANDARDS" "$link_standards"
  echo "  linked: standards/"

  # Copy AGENTS.md to project roots if requested
  echo ""
  echo "Done. Skills linked to ~/.claude/skills/"
  echo "To connect a specific project, add to its .gitignore:"
  echo "  .claude/skills"
  echo ""
  echo "To make AGENTS.md available in a project:"
  echo "  ln -s $REPO_DIR/AGENTS.md <project-root>/AGENTS.md"
}

if [ "$ACTION" = "--unlink" ]; then
  unlink_all
else
  link_all
fi
