#!/usr/bin/env bash
# Commit everything and refresh the bundle, so the history survives the next snapshot.
set -euo pipefail
cd "$(dirname "$0")/.."
msg="${1:-chore: snapshot}"
# --- guard: snapshots silently delete files; never bake a deletion in by accident ---
DELETED=$(git ls-files --deleted)
if [ -n "$DELETED" ] && [ "${ALLOW_DELETE:-0}" != "1" ]; then
  echo "REFUSING: these tracked files vanished from disk (workspace snapshot strips them):"
  echo "$DELETED" | sed 's/^/  /'
  echo "Restore them:  git checkout HEAD -- <files>"
  echo "Really deleting on purpose?  ALLOW_DELETE=1 bash tools/git_snapshot.sh \"msg\""
  exit 1
fi

git add -A
git diff --cached --quiet || git -c core.quotepath=false commit -q -m "$msg"
out="../autoclip-$(git describe --tags --always).bundle"
git bundle create "$out" --all >/dev/null 2>&1
echo "committed: $(git log --oneline -1)"
echo "bundle:    $(realpath "$out")"
