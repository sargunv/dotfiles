# dotfiles

Personal dotfiles managed with chezmoi.

## AI gateway

Claude Code, Codex, OpenCode, and Pi use the LiteLLM gateway. Save its key on
each machine; chezmoi does not manage it:

```sh
install -d -m 700 ~/.config/litellm
install -m 600 /dev/null ~/.config/litellm/api-key
$EDITOR ~/.config/litellm/api-key
```

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
node --test tests/litellm.test.mjs
```

Use `mise run fix` to apply formatting and lint fixes.

## Bootstrap

On macOS, install Homebrew first:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Debian and Ubuntu, the first apply installs the apt packages with `sudo`.
Make zsh the login shell afterwards with `chsh -s "$(command -v zsh)"`. SSH
hosts that belong to one machine go in `~/.ssh/config.local`.

Install chezmoi, then apply:

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin"
"$HOME/.local/bin/chezmoi" init sargunv --apply
```
