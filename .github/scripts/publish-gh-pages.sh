#!/usr/bin/env bash
# Publish a built site directory to the gh-pages branch root.
#
# The branch holds one production site and nothing else, so this replaces its
# whole contents on every run. That is deliberate: a file deleted from the site
# should disappear from the branch too, rather than lingering as an orphan that
# search engines keep serving.
#
# Usage: publish-gh-pages.sh <build-directory>
set -euo pipefail

BUILD_DIR="${1:?usage: publish-gh-pages.sh <build-directory>}"
BRANCH="${PUBLISH_BRANCH:-gh-pages}"
REMOTE="${PUBLISH_REMOTE:-https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git}"

if [ ! -d "$BUILD_DIR" ]; then
  echo "ERROR: build directory '$BUILD_DIR' does not exist. Run the build first." >&2
  exit 1
fi

if [ ! -f "$BUILD_DIR/index.html" ]; then
  echo "ERROR: '$BUILD_DIR' has no index.html; refusing to publish an empty site." >&2
  exit 1
fi

WORKTREE="$(mktemp -d)"
trap 'rm -rf "$WORKTREE"' EXIT

git config --global user.name "github-actions[bot]"
git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

# Fetch the existing branch so the publish is a normal commit with history,
# rather than an orphan that discards every previous deploy.
if git ls-remote --exit-code --heads "$REMOTE" "$BRANCH" >/dev/null 2>&1; then
  git clone --branch "$BRANCH" --depth 1 --single-branch "$REMOTE" "$WORKTREE"
else
  git clone --depth 1 "$REMOTE" "$WORKTREE"
  git -C "$WORKTREE" checkout --orphan "$BRANCH"
  git -C "$WORKTREE" rm -rf . >/dev/null 2>&1 || true
fi

# Replace the branch contents wholesale, preserving .git and .nojekyll.
find "$WORKTREE" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp -R "$BUILD_DIR"/. "$WORKTREE"/

# Without this, GitHub Pages runs Jekyll over the output and silently drops any
# path beginning with an underscore.
touch "$WORKTREE/.nojekyll"

cd "$WORKTREE"
git add --all

if git diff --cached --quiet; then
  echo "No change to publish; the built site matches what is already deployed."
  exit 0
fi

git commit --message "Deploy ${GITHUB_SHA:-local} to ${BRANCH}"
git push "$REMOTE" "HEAD:${BRANCH}"

echo "Published $(find . -name '*.html' | wc -l) pages to ${BRANCH}."
