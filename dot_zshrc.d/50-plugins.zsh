#!/bin/zsh
[ -n "$NO_FANCY_SHELL" ] && return

[ -n "$HOMEBREW_PREFIX" ] && [ -d "$HOMEBREW_PREFIX/opt/antidote/share/antidote" ] && {
  source $HOMEBREW_PREFIX/opt/antidote/share/antidote/antidote.zsh
  antidote load
}
