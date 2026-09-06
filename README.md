# dotfiles

Personal dotfiles managed with chezmoi.

## Git signing

On macOS, commits and tags use `~/.ssh/commit_signing_key.pub`, backed by a
non-exportable Secure Enclave key without biometric protection. Its private
counterpart is a local hardware reference, not an exported private key. Register
the public key with GitHub as a signing key only.

SSH authentication continues to use its separate key. Linux signing continues to
use the TPM setup. Hardware keys and their local references are provisioned on
each machine; they are not stored in this repository.

## Development

Repo tooling is pinned with mise. Python linting and type checking use locked uv
dependencies; formatting runs through dprint.

```sh
mise install
mise run check
mise run test
```

Use `mise run fix` to apply formatting and lint fixes.

## Bootstrap

On macOS, install Homebrew first:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Install chezmoi, then apply:

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin"
"$HOME/.local/bin/chezmoi" init sargunv --apply
```
