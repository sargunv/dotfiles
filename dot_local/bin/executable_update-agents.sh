#!/bin/sh
set -eu

# Explicit PATH for launchd/systemd which don't inherit interactive shell PATH.
# Includes: chezmoi-managed bins, mise shims, opencode, homebrew, system.
export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$HOME/.opencode/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_FILE="$LOG_DIR/update-agents.log"
mkdir -p "$LOG_DIR"

prune_aged_worktrees() {
  wt_root="$1"
  [ -d "$wt_root" ] || return 0
  for repo_dir in "$wt_root"/*; do
    [ -d "$repo_dir" ] || continue
    for wt in "$repo_dir"/*; do
      [ -d "$wt" ] || continue
      [ -f "$wt/.git" ] || continue
      # Keep any worktree with files modified in the last 3 days.
      if [ -n "$(find "$wt" -maxdepth 4 -not -path '*/.git*' -mtime -3 -print -quit 2>/dev/null || true)" ]; then
        continue
      fi
      gitdir_line="$(head -n 1 "$wt/.git" 2>/dev/null || true)"
      parent_git=""
      case "$gitdir_line" in
        gitdir:\ */.git/worktrees/*)
          gitdir_path="${gitdir_line#gitdir: }"
          parent_repo="${gitdir_path%%/.git/worktrees/*}"
          [ -d "$parent_repo/.git" ] && parent_git="$parent_repo"
          ;;
      esac
      echo "Pruning aged worktree (>3d): $wt"
      if [ -n "$parent_git" ]; then
        git -C "$parent_git" worktree remove --force "$wt" 2>&1 || rm -rf "$wt"
        git -C "$parent_git" worktree prune 2>&1 || true
      else
        rm -rf "$wt"
      fi
    done
  done
}

{
  echo "--- $(date -u +"%Y-%m-%dT%H:%M:%SZ") update-agents start ---"
  # Mise manages dev tools only; the agents below install via official curl installers.
  # Run mise from $HOME with experimental flag to avoid scanning other worktrees with broken mise.toml
  if command -v mise >/dev/null 2>&1; then
    echo "Updating mise and mise-managed tools..."
    (cd "$HOME" && MISE_EXPERIMENTAL=1 mise self-update --yes 2>&1) || echo "mise self-update failed: $?" >&2
    (cd "$HOME" && MISE_EXPERIMENTAL=1 mise upgrade --yes 2>&1) || echo "mise upgrade failed: $?" >&2
    echo "Pruning unused mise tool versions..."
    (cd "$HOME" && MISE_EXPERIMENTAL=1 mise prune --yes 2>&1) || echo "mise prune failed: $?" >&2
  fi
  # curl-installed agents: each installer is idempotent and installs/updates to latest
  echo "Updating claude (curl installer)..."; curl -fsSL https://claude.ai/install.sh | bash 2>&1 || echo "claude install failed: $?" >&2
  echo "Updating codex (curl installer)..."; curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh 2>&1 || echo "codex install failed: $?" >&2
  echo "Updating opencode (curl installer)..."; curl -fsSL https://opencode.ai/v2/install | bash -s -- --no-modify-path 2>&1 || echo "opencode install failed: $?" >&2
  echo "Updating pi (curl installer)..."; curl -fsSL https://pi.dev/install.sh | sh 2>&1 || echo "pi install failed: $?" >&2
  echo "Updating omp (curl installer)..."; curl -fsSL https://omp.sh/install | sh -s -- --binary 2>&1 || echo "omp install failed: $?" >&2
  # An unrecognized SHELL stops Grok's installer from editing ~/.zshrc or ~/.bashrc.
  echo "Updating grok (curl installer)..."; curl -fsSL https://x.ai/cli/install.sh | SHELL=/bin/sh bash 2>&1 || echo "grok install failed: $?" >&2
  echo "Updating workflow-cli (git checkout)..."; git -C "$HOME/.local/share/workflow-cli" pull --ff-only --quiet 2>&1 || echo "workflow-cli update failed: $?" >&2

  # Light daily storage pruning: aged T3 worktrees (>3d, including dirty ones), Cargo targets (>2d), and T3 cache tmp.
  prune_aged_worktrees "$HOME/.t3/worktrees"
  if [ -n "${T3CODE_HOME:-}" ] && [ "$T3CODE_HOME/worktrees" != "$HOME/.t3/worktrees" ]; then
    prune_aged_worktrees "$T3CODE_HOME/worktrees"
  fi
  if command -v cargo-sweep >/dev/null 2>&1; then
    echo "Running cargo-sweep (--time 2)..."
    for sweep_dir in "$HOME/.t3/worktrees" "${T3CODE_HOME:-}/worktrees" "$HOME/Projects" "$HOME/Code" "$HOME/projects"; do
      [ -n "$sweep_dir" ] && [ -d "$sweep_dir" ] || continue
      cargo-sweep sweep --time 2 --recursive "$sweep_dir" 2>&1 || echo "cargo-sweep failed for $sweep_dir: $?" >&2
    done
  fi
  if [ -d /srv/homelab/cache/t3-code/tmp ]; then
    echo "Pruning aged files in /srv/homelab/cache/t3-code/tmp (>2d)..."
    find /srv/homelab/cache/t3-code/tmp -mindepth 1 -maxdepth 1 -mtime +2 -exec rm -rf -- {} + 2>&1 || true
  fi

  echo "--- $(date -u +"%Y-%m-%dT%H:%M:%SZ") update-agents done ---"
} >>"$LOG_FILE" 2>&1
