# dotfiles

This project contains the files I use to set up my personal environment.

Supports:

- Linux (tested with [Bluefin](https://projectbluefin.io/) and Ubuntu/WSL)
- macOS

Usage:

First, ensure [Homebrew](https://brew.sh/) is installed and PATH is configured.

Set up the dotfiles with:

```
brew install starship chezmoi
chezmoi init sargunv --apply
```

Finally, ensure the terminal uses some [Nerd Font](https://www.nerdfonts.com/). If
on macOS, one has been installed via `brew --cask`.

If Homebrew can't be used, install [chezmoi](https://www.chezmoi.io/) and
[starship](https://starship.rs/) some other way, and check
[packages.yml](./.chezmoidata/packages.yml) for a list of other optional packages to install.
