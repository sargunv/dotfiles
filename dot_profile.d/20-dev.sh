#!/bin/sh

# cargo / rust
export PATH="$HOME/.cargo/bin:$PATH"

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
export PIPENV_PYTHON="$PYENV_ROOT/shims/python"
if command -v pyenv > /dev/null; then
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
fi

# fnm
command -v fnm > /dev/null && eval "$(fnm env --use-on-cd)"
