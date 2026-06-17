# Zig

## Mise

```toml
# mise.toml
[tools]
"core:zig" = "…"
```

## Formatter

```jsonc
"exec": {
  "commands": [
    { "command": "zig fmt --stdin", "exts": ["zig"] },
    { "command": "zig fmt --stdin --zon", "exts": ["zon"] },
  ]
}
```

## Linter

None, to my knowledge.
