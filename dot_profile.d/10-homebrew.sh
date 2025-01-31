#!/bin/sh

case "$(uname -s)" in
  Darwin)
    if [ -f /opt/homebrew/bin/brew ]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
      export FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"

      # gnu tooling
      GNU_PATH=$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin
      GNU_PATH=$GNU_PATH:$HOMEBREW_PREFIX/opt/gnu-sed/libexec/gnubin
      GNU_PATH=$GNU_PATH:$HOMEBREW_PREFIX/opt/gnu-tar/libexec/gnubin
      export PATH=$GNU_PATH:$PATH

      GNU_MANPATH=$HOMEBREW_PREFIX/opt/coreutils/libexec/gnuman
      GNU_MANPATH=$GNU_MANPATH:$HOMEBREW_PREFIX/opt/gnu-sed/libexec/gnuman
      GNU_MANPATH=$GNU_MANPATH:$HOMEBREW_PREFIX/opt/gnu-tar/libexec/gnuman
      export MANPATH=$GNU_MANPATH:$MANPATH

      # trash-cli is keg only
      export PATH="/opt/homebrew/opt/trash/bin:$PATH"
    fi
    ;;
esac
