#!/usr/bin/env bash
# link-nmt.sh — symlink Next Move Theory canon + Claude skills into a project.
# Mirror of ./link.sh, but for an EXTERNAL repo (Ivan Zamesin's NMT, CC BY-NC-SA).
# Re-run after every `git pull` in the NMT clone. Idempotent: re-creates symlinks,
# skips anything that isn't already a symlink (won't clobber real files), never
# copies SA-licensed content anywhere.
#
# Usage:
#   bash link-nmt.sh                     # link into Astra (default target)
#   bash link-nmt.sh --target <dir>      # link into another project root
#   bash link-nmt.sh --clone <dir>       # override the clone path
#   bash link-nmt.sh --unlink            # remove the symlinks it created
set -euo pipefail

CLONE=""
TARGET=""
ACTION="link"
while [ $# -gt 0 ]; do
  case "$1" in
    --clone)  CLONE="${2:?--clone needs a path}"; shift 2 ;;
    --target) TARGET="${2:?--target needs a path}"; shift 2 ;;
    --unlink) ACTION="unlink"; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

[ -z "$CLONE" ]  && CLONE="$HOME/Documents/Code_projects/Next-Move-Theory-Canon-and-Skills"
[ -z "$TARGET" ] && TARGET="$HOME/Documents/Code_projects/Astra"

[ -d "$CLONE/Next-Move-Theory-Canon" ] && [ -d "$CLONE/Skills/claude" ] || {
  echo "ERROR: $CLONE is not an NMT clone (missing Next-Move-Theory-Canon/ or Skills/claude/)" >&2
  exit 1
}
TARGET="$(cd "$TARGET" 2>/dev/null && pwd || { echo "ERROR: target not found: $TARGET" >&2; exit 1; })"

link_one() {  # $1 = symlink path, $2 = destination
  local link="$1" dest="$2"
  if [ -L "$link" ]; then rm "$link"
  elif [ -e "$link" ]; then echo "  SKIP (not a symlink, won't clobber): $link"; return; fi
  ln -s "$dest" "$link"
  echo "  linked: ${link#$TARGET/}"
}

case "$ACTION" in
  unlink)
    for d in "$CLONE"/Skills/claude/*/; do
      n=$(basename "$d"); [ -L "$TARGET/.claude/skills/$n" ] && rm "$TARGET/.claude/skills/$n" && echo "  removed: .claude/skills/$n"
    done
    for f in PRODUCER-CONTRACT.md READABILITY-CONTRACT.md; do
      [ -L "$TARGET/.claude/skills/$f" ] && rm "$TARGET/.claude/skills/$f" && echo "  removed: .claude/skills/$f"
    done
    [ -L "$TARGET/Next-Move-Theory-Canon" ] && rm "$TARGET/Next-Move-Theory-Canon" && echo "  removed: Next-Move-Theory-Canon"
    echo "unlinked from $TARGET"
    ;;
  link)
    mkdir -p "$TARGET/.claude/skills"
    echo "Linking NMT canon + skills into $TARGET (from $CLONE)"
    # 1. Canon — skills read it at runtime via a project-root-relative path.
    link_one "$TARGET/Next-Move-Theory-Canon" "$CLONE/Next-Move-Theory-Canon"
    # 2. Skills — each folder symlinked into .claude/skills/ (Claude Code follows symlinks).
    for d in "$CLONE"/Skills/claude/*/; do
      n=$(basename "$d"); link_one "$TARGET/.claude/skills/$n" "$d"
    done
    # 3. Shared contracts the skills reference by name.
    for f in PRODUCER-CONTRACT.md READABILITY-CONTRACT.md; do
      [ -f "$CLONE/Skills/claude/$f" ] && link_one "$TARGET/.claude/skills/$f" "$CLONE/Skills/claude/$f"
    done
    echo "done. Invoke /nmt-chat, /nmt-diagnose, ... from $TARGET."
    echo "pull updates:  cd \"$CLONE\" && git pull && bash \"$0\""
    ;;
esac
