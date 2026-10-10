#!/bin/sh
set -eu

# Explicit PATH for launchd/systemd which don't inherit interactive shell PATH.
# Includes: chezmoi-managed bins, mise shims, opencode, homebrew, system.
export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$HOME/.opencode/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_FILE="$LOG_DIR/update-agents.log"
mkdir -p "$LOG_DIR"

{
  echo "--- $(date -u +"%Y-%m-%dT%H:%M:%SZ") update-agents start ---"
  # Mise manages dev tools only; the agents below install via official curl installers.
  # Run mise from $HOME with experimental flag to avoid scanning other worktrees with broken mise.toml
  if command -v mise >/dev/null 2>&1; then
    echo "Updating mise and mise-managed tools..."; (cd "$HOME" && MISE_EXPERIMENTAL=1 mise self-update --yes 2>&1) || echo "mise self-update failed: $?" >&2
    (cd "$HOME" && MISE_EXPERIMENTAL=1 mise upgrade --yes 2>&1) || echo "mise upgrade failed: $?" >&2
  fi
  # curl-installed agents: each installer is idempotent and installs/updates to latest
  echo "Updating claude (curl installer)..."; curl -fsSL https://claude.ai/install.sh | bash 2>&1 || echo "claude install failed: $?" >&2
  echo "Updating codex (curl installer)..."; curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh 2>&1 || echo "codex install failed: $?" >&2
  echo "Updating opencode (curl installer)..."; curl -fsSL https://opencode.ai/install | bash -s -- --no-modify-path 2>&1 || echo "opencode install failed: $?" >&2
  echo "--- $(date -u +"%Y-%m-%dT%H:%M:%SZ") update-agents done ---"
} >>"$LOG_FILE" 2>&1
