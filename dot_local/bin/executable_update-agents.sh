#!/bin/sh
set -eu

# Explicit PATH for launchd/systemd which don't inherit interactive shell PATH.
# Includes: chezmoi-managed bins, mise shims, kimi, homebrew, system.
export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$HOME/.kimi-code/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_FILE="$LOG_DIR/update-agents.log"
mkdir -p "$LOG_DIR"

{
  echo "--- $(date -u +"%Y-%m-%dT%H:%M:%SZ") update-agents start ---"
  # Mise now manages: claude, codex, opencode, pi, oh-my-pi (omp), qwen
  # Remaining manual/self-managed: kimi, cursor-agent, grok (muse launcher self-updates)
  # Run mise from $HOME with experimental flag to avoid scanning other worktrees with broken mise.toml
  if command -v mise >/dev/null 2>&1; then
    echo "Updating mise and mise-managed tools..."; (cd "$HOME" && MISE_EXPERIMENTAL=1 mise self-update --yes 2>&1) || echo "mise self-update failed: $?" >&2
    (cd "$HOME" && MISE_EXPERIMENTAL=1 mise upgrade --yes 2>&1) || echo "mise upgrade failed: $?" >&2
  fi
  if command -v kimi >/dev/null 2>&1; then
    echo "Updating kimi (manual)..."
    # kimi's updater requires a TTY (without it, it mis-detects as windows and exits);
    # mimic interactive shell by driving its TUI via expect
    if command -v expect >/dev/null 2>&1; then
      expect 2>&1 <<'EXPECT_EOF' || echo "kimi upgrade (expect) failed: $?" >&2
set timeout 120
spawn kimi upgrade
expect {
  "Install update now" { send "\r"; exp_continue }
  eof
}
EXPECT_EOF
    else
      kimi upgrade 2>&1 || echo "kimi upgrade failed: $?" >&2
    fi
  fi
  if command -v cursor-agent >/dev/null 2>&1; then
    echo "Updating cursor-agent (manual)..."; cursor-agent update 2>&1 || echo "cursor-agent update failed: $?" >&2
  elif command -v agent >/dev/null 2>&1; then
    echo "Updating agent (cursor, manual)..."; agent update 2>&1 || echo "agent update failed: $?" >&2
  fi
  if command -v grok >/dev/null 2>&1; then
    echo "Updating grok (manual, no mise backend)..."; grok update 2>&1 || echo "grok update failed: $?" >&2
  fi
  echo "--- $(date -u +"%Y-%m-%dT%H:%M:%SZ") update-agents done ---"
} >>"$LOG_FILE" 2>&1
