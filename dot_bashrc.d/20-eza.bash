#!/bin/bash
[ -n "$NO_FANCY_SHELL" ] && return

if [ "$(command -v eza)" ]; then
  alias ls='eza --hyperlink --icons=auto'
  alias ll='ls -l --group-directories-first --git'
  alias lt='ls --tree'
  alias llt='ll --tree'
fi
