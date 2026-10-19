#!/bin/sh
set -eu

# Runs on every apply but only acts until the first successful build; the daily
# update-agents job keeps it current afterwards. A failed build (e.g. offline) is a
# warning, so bootstrap still finishes.

export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"

if [ -f "$HOME/.local/share/workflow-cli/dist/.built-from" ]; then
  exit 0
fi

update-workflow-cli || echo "workflow-cli install failed; rerun update-workflow-cli." >&2
