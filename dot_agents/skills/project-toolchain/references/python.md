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

Dprint plugin: `ruff`.

## Linter

Formatting belongs to dprint; use hk for ruff lint checks and ty type checks.

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
