#!/bin/zsh

if [ -d ~/.aliases.d ]; then
  for alias_file in ~/.aliases.d/*; do
    if [ -f "$alias_file" ]; then
      . "$alias_file"
    fi
  done
fi
