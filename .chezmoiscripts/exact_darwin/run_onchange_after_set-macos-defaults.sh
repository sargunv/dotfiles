#!/bin/sh
set -eu

defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false
defaults write NSGlobalDomain InitialKeyRepeat -int 15
defaults write NSGlobalDomain KeyRepeat -int 2

defaults write NSGlobalDomain AppleICUForce24HourTime -bool true
defaults write com.apple.menuextra.clock Show24Hour -bool true

defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write com.apple.finder ShowPathbar -bool true
defaults write com.apple.finder ShowStatusBar -bool true

defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock show-recents -bool false
defaults write com.apple.dock mru-spaces -bool false

killall Finder >/dev/null 2>&1 || true
killall Dock >/dev/null 2>&1 || true
