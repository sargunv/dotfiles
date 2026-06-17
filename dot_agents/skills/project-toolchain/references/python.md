# Python

## Mise and deps

```toml
# mise.toml
[settings.python]
uv_venv_auto = "create|source"

[tools]
"core:python" = "…"
"aqua:astral-sh/uv" = "…"

[deps.uv]
auto = true
```

```toml
# pyproject.toml
[dependency-groups]
dev = [
  "ruff==…",
  "ty==…",
]
```

Commit `uv.lock`.

## Formatter

[dprint ruff WASM plugin](https://dprint.dev/plugins/) in `dprint.jsonc`.

```jsonc
"plugins": [
  "https://plugins.dprint.dev/ruff-X.Y.Z.wasm",
],
```

## Linter

Do not also run `ruff format` in hk when dprint owns formatting.

```pkl
["ruff"] {
  glob = List("**/*.py")
  check = "uv run ruff check {{files}}"
  fix = "uv run ruff check --fix {{files}}"
}
["ty"] {
  glob = List("**/*.py")
  check = "uv run ty check --error-on-warning ."
}
```
