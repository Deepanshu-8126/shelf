#!/usr/bin/env bash
# Workspace snapshots exclude .git/config, which makes git forget this is a repo.
# This rebuilds the repo from the bundle without touching your working files.
set -euo pipefail
cd "$(dirname "$0")/.."
BUNDLE="${1:-$(ls -t ../autoclip-*.bundle 2>/dev/null | head -1)}"
[ -f "$BUNDLE" ] || { echo "bundle not found; pass path as \$1"; exit 1; }
rm -rf .git
git init -q -b main
git config user.email "${GIT_EMAIL:-dkx@example.com}"
git config user.name  "${GIT_NAME:-DKX}"
git remote add bundle "$BUNDLE"
git fetch -q bundle main
git reset -q FETCH_HEAD
echo "restored: $(git log --oneline -1)"
git status --short
