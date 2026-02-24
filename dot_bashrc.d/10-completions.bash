#!/bin/bash
[ -n "$NO_FANCY_SHELL" ] && return

[ "$(command -v starship)" ] && source <(starship completions bash)
[ "$(command -v chezmoi)" ] && source <(chezmoi completion bash)
[ "$(command -v mise)" ] && source <(mise completion bash)
