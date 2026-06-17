# Rust

## Mise and deps

```toml
# mise.toml
[tools]
"core:rust" = { version = "…", profile = "minimal", components = "rustfmt,clippy" }
```

Commit `Cargo.lock`.

## Formatter

[rustfmt](https://github.com/rust-lang/rustfmt) via dprint exec.

```jsonc
"exec": {
  "commands": [
    { "command": "rustfmt --edition 2024", "exts": ["rs"] }
  ]
}
```

## Linter

```pkl
["cargo-clippy"] {
  glob = List("**/*.rs")
  check = "cargo clippy -- -D warnings"
  fix = "cargo clippy --fix --allow-dirty --allow-staged"
}
```
