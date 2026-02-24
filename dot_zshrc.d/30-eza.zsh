#!/bin/zsh
[ -n "$NO_FANCY_SHELL" ] && return

if [ "$(command -v eza)" ]; then
  EZA_ICONS="never"
  [ -n "$HAS_NERD_FONT" ] && EZA_ICONS="auto"
  alias ls="eza --hyperlink --icons=$EZA_ICONS"
  alias ll='ls -l --group-directories-first --git'
  alias lt='ls --tree'
  alias llt='ll --tree'
fi
