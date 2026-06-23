# Go

## Mise and deps

```toml
# mise.toml
[tools]
"core:go" = "…"
"golangci-lint" = "…"

[deps.go]
auto = true
```

Commit `go.sum`.

## Formatter

Dprint plugin: `jakebailey/gofumpt`.

```jsonc
"gofumpt": {
  "langVersion": "go1.XX",
  "modulePath": "github.com/org/project",
}
```

## Linter

Formatting belongs to dprint; keep golangci focused on lint checks.

```pkl
["gomod-tidy"] = (Builtins.gomod_tidy) {
  glob = List("**/go.mod")
  workspace_indicator = "go.mod"
  check_diff = "cd {{workspace}} && go mod tidy -diff"
  fix = "cd {{workspace}} && go mod tidy"
}
["golangci-lint"] {
  glob = List("**/*.go")
  workspace_indicator = "go.mod"
  check = "cd {{workspace}} && golangci-lint run --allow-parallel-runners ./..."
  fix = "cd {{workspace}} && golangci-lint run --allow-parallel-runners --fix ./..."
}
```
