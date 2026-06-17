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

[dprint gofumpt plugin](https://dprint.dev/plugins/) in `dprint.jsonc`.

```jsonc
"plugins": [
  "https://plugins.dprint.dev/jakebailey/gofumpt-vX.Y.Z.wasm",
],
"gofumpt": {
  "langVersion": "go1.XX",
  "modulePath": "github.com/org/project",
}
```

## Linter

Do not enable gofumpt under golangci `formatters` — dprint owns formatting.

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
