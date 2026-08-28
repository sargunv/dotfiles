#!/bin/sh
set -eu

# Explicit PATH for launchd/systemd which don't inherit interactive shell PATH.
# Includes: chezmoi-managed bins, mise shims, opencode, kimi, homebrew, system.
export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$HOME/.opencode/bin:$HOME/.kimi-code/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_FILE="$LOG_DIR/update-agents.log"
mkdir -p "$LOG_DIR"

{
  echo "--- $(date -u +"%Y-%m-%dT%H:%M:%SZ") update-agents start ---"
  # Mise manages dev tools only; the agents below install via official curl installers.
  # Remaining manual/self-managed: kimi, cursor-agent, grok (muse launcher self-updates)
  # Run mise from $HOME with experimental flag to avoid scanning other worktrees with broken mise.toml
  if command -v mise >/dev/null 2>&1; then
    echo "Updating mise and mise-managed tools..."; (cd "$HOME" && MISE_EXPERIMENTAL=1 mise self-update --yes 2>&1) || echo "mise self-update failed: $?" >&2
    (cd "$HOME" && MISE_EXPERIMENTAL=1 mise upgrade --yes 2>&1) || echo "mise upgrade failed: $?" >&2
  fi
  # curl-installed agents: each installer is idempotent and installs/updates to latest
  echo "Updating claude (curl installer)..."; curl -fsSL https://claude.ai/install.sh | bash 2>&1 || echo "claude install failed: $?" >&2
  echo "Updating codex (curl installer)..."; curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh 2>&1 || echo "codex install failed: $?" >&2
  echo "Updating opencode (curl installer)..."; curl -fsSL https://opencode.ai/install | bash -s -- --no-modify-path 2>&1 || echo "opencode install failed: $?" >&2
  echo "Updating pi (curl installer)..."; curl -fsSL https://pi.dev/install.sh | sh 2>&1 || echo "pi install failed: $?" >&2
  echo "Updating oh-my-pi (curl installer)..."; curl -fsSL https://omp.sh/install | sh -s -- --binary 2>&1 || echo "oh-my-pi install failed: $?" >&2
  echo "Updating qwen (curl installer)..."; curl -fsSL https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.sh | bash -s -- --version latest --no-modify-path 2>&1 || echo "qwen install failed: $?" >&2
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
