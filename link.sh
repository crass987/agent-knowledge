#!/bin/bash
# link.sh — connect agent-knowledge to Claude Code and other agents
# Usage: ./link.sh [--unlink]

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION="${1:-link}"

LINKS_CLAUDE="$HOME/.claude/skills"
LINK_AGENTS="$HOME/.claude/agents"
TARGET_SKILLS="$REPO_DIR/skills"
TARGET_AGENTS="$REPO_DIR/agents"
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
  # Remove agent-definition symlinks
  if [ -d "$TARGET_AGENTS" ]; then
    for f in "$TARGET_AGENTS"/*.md; do
      [ -e "$f" ] || continue
      name=$(basename "$f")
      link="$LINK_AGENTS/$name"
      if [ -L "$link" ]; then
        rm "$link"
        echo "  removed: $link"
      fi
    done
  fi
  echo "Done."
}

# Ensure each skill that references _shared/ carries a relative _shared symlink,
# so skill-root-relative refs like `_shared/infostyle-core.md` resolve both in-repo
# and under deploy (where each skill is itself a symlink into this dir). Idempotent.
ensure_shared_links() {
  for dir in "$TARGET_SKILLS"/*/; do
    name=$(basename "$dir")
    if [ "$name" = "_shared" ]; then continue; fi
    if ! grep -rq "_shared/" "$dir" --include="*.md" 2>/dev/null; then continue; fi
    link="$dir/_shared"
    if [ -L "$link" ]; then
      if [ "$(readlink "$link")" = "../_shared" ]; then continue; fi
      rm "$link"
    elif [ -e "$link" ]; then
      echo "  WARNING: $link exists and is not a symlink — skipping."
      continue
    fi
    ln -s ../_shared "$link"
    echo "  _shared link: $name"
  done
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

  # Self-heal _shared symlinks for skills that reference shared content
  ensure_shared_links

  # Link agent definitions (agents/*.md -> ~/.claude/agents/)
  if [ -d "$TARGET_AGENTS" ]; then
    mkdir -p "$LINK_AGENTS"
    for f in "$TARGET_AGENTS"/*.md; do
      [ -e "$f" ] || continue
      name=$(basename "$f")
      link="$LINK_AGENTS/$name"
      if [ -L "$link" ]; then
        rm "$link"
      elif [ -e "$link" ]; then
        echo "  WARNING: $link exists and is not a symlink — skipping. Remove it manually."
        continue
      fi
      ln -s "$f" "$link"
      echo "  linked agent: $name"
    done
  fi

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
  echo "       Agents linked to ~/.claude/agents/"
  echo "To connect a specific project, add to its .gitignore:"
  echo "  .claude/skills"
  echo "  .claude/agents"
  echo ""
  echo "To make AGENTS.md available in a project:"
  echo "  ln -s $REPO_DIR/AGENTS.md <project-root>/AGENTS.md"
}

if [ "$ACTION" = "--unlink" ]; then
  unlink_all
else
  link_all
fi
