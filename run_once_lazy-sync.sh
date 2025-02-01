#!/bin/bash

if command -v nvim > /dev/null; then
  nvim --headless "+Lazy! sync" +qa
fi
