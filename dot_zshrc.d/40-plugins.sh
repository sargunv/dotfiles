#!/bin/zsh

function auto-zsh-plugin() {
  local prefix='/usr'
  [ -n "$HOMEBREW_PREFIX" ] && prefix="$HOMEBREW_PREFIX"
  [ -f "$prefix/share/$1" ] && . "$prefix/share/$1"
  return $?
}

auto-zsh-plugin zsh-fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh \
    || auto-zsh-plugin zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
auto-zsh-plugin zsh-autosuggestions/zsh-autosuggestions.zsh || true
auto-zsh-plugin zsh-autopair/autopair.zsh || true
