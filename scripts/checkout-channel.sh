#!/usr/bin/env bash
# Prepare a fresh local channel working copy; a missing ref is valid only for first publication.
set -euo pipefail
origin=${1:?repository URL}
dest=${2:?new checkout directory}
branch=rolling-channel
if refs=$(git ls-remote --exit-code --heads "$origin" "refs/heads/$branch"); then
  git clone --single-branch --branch "$branch" "$origin" "$dest"
  [[ $(git -C "$dest" rev-parse HEAD) == "${refs%%[[:space:]]*}" ]]
else
  code=$?
  [[ $code == 2 ]] || exit "$code"
  mkdir "$dest"
  git -C "$dest" init -b "$branch"
  git -C "$dest" remote add origin "$origin"
fi
