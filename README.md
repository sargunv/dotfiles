# dotfiles

This project contains the files I use to set up my personal environment.

Supports:

- macOS (arm64 and x86_64)

Usage:

First, ensure [Homebrew](https://brew.sh/) is installed and PATH is configured.

Set up the dotfiles with:

```sh
brew install starship chezmoi
chezmoi init sargunv --apply
```

If Homebrew can't be used, install [chezmoi](https://www.chezmoi.io/) and
[starship](https://starship.rs/) some other way, and check
[packages.yml](./.chezmoidata/packages.yml) for a list of other optional packages to install.
