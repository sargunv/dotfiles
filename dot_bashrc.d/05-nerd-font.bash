#!/bin/bash
[ -n "$NO_FANCY_SHELL" ] && return

command -v has-nerd-font > /dev/null && has-nerd-font && HAS_NERD_FONT=1
