#!/bin/bash
# link.sh — connect agent-knowledge to Claude Code and other agents
# Usage: ./link.sh [--unlink]
#
# Deploys: skills/* -> ~/.claude/skills/, agents/* -> ~/.claude/agents/, and
# merges the infostyle-critic Stop hook into ~/.claude/settings.json (idempotent,
# preserves all existing keys). One command => skill + agent + hook everywhere.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION="${1:-link}"

LINKS_CLAUDE="$HOME/.claude/skills"
LINK_AGENTS="$HOME/.claude/agents"
TARGET_SKILLS="$REPO_DIR/skills"
TARGET_AGENTS="$REPO_DIR/agents"
TARGET_STANDARDS="$REPO_DIR/standards"
GATE="$REPO_DIR/hooks/infostyle_critic_gate.py"
HOOK_INSTALLER="$REPO_DIR/scripts/install_global_hook.py"
# Command the harness will run at Stop. python3 (PATH) keeps it portable across machines.
GATE_CMD="python3 \"$GATE\""

# install/remove the global Stop hook (merge into ~/.claude/settings.json)
sync_hook() {
  if [ ! -f "$GATE" ] || [ ! -f "$HOOK_INSTALLER" ]; then
    echo "  (gate or installer missing — hook sync skipped)"
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "  WARN: python3 not on PATH — Stop hook not synced (skill+agent still linked)."
    return 0
  fi
  python3 "$HOOK_INSTALLER" "$GATE_CMD" "$@"
}

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
  # Remove the global Stop hook
  sync_hook --remove
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

  # Merge the infostyle-critic Stop hook into ~/.claude/settings.json (global)
  sync_hook

  # Link standards as a whole directory
  link_standards="$LINKS_CLAUDE/standards"
  if [ -L "$link_standards" ]; then
    rm "$link_standards"
  fi
  ln -s "$TARGET_STANDARDS" "$link_standards"
  echo "  linked: standards/"

  echo ""
  echo "Done. Skills -> ~/.claude/skills/"
  echo "       Agents -> ~/.claude/agents/"
  echo "       Stop hook -> ~/.claude/settings.json"
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
