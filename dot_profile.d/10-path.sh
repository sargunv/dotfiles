#!/bin/sh

# gnu tooling (macOS only, requires $HOMEBREW_PREFIX)
if [ -n "$HOMEBREW_PREFIX" ]; then
  GNU_PATH=$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin
  GNU_PATH=$GNU_PATH:$HOMEBREW_PREFIX/opt/gnu-sed/libexec/gnubin
  GNU_PATH=$GNU_PATH:$HOMEBREW_PREFIX/opt/gnu-tar/libexec/gnubin
  export PATH=$GNU_PATH:$PATH

  GNU_MANPATH=$HOMEBREW_PREFIX/opt/coreutils/libexec/gnuman
  GNU_MANPATH=$GNU_MANPATH:$HOMEBREW_PREFIX/opt/gnu-sed/libexec/gnuman
  GNU_MANPATH=$GNU_MANPATH:$HOMEBREW_PREFIX/opt/gnu-tar/libexec/gnuman
  export MANPATH=$GNU_MANPATH:$MANPATH
fi

# Jetbrains
export PATH="$PATH:$HOME/.local/share/JetBrains/Toolbox/scripts"

# Claude
export PATH="$PATH:$HOME/.claude/local"

# mise shims
export PATH="$HOME/.local/share/mise/shims:$PATH"

# local bin
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"
