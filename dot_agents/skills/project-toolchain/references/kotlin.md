# Kotlin

## Mise

Commit a Gradle wrapper.

```toml
# mise.toml
[tools]
"core:java" = "zulu-…"
"aqua:facebook/ktfmt" = "…"
```

## Formatter

ktfmt **google-style** via dprint exec:

```toml
# mise.toml
[tasks._ktfmt]
hide = true
run = 'java -jar {{ tools["aqua:facebook/ktfmt"].path }}/ktfmt'
```

```jsonc
// dprint.jsonc
"exec": {
  "commands": [
    {
      "command": "mise run _ktfmt --google-style - --stdin-name={{file_path}}",
      "exts": ["kt", "kts"],
    },
  ]
}
```

## Linter

I haven't yet explored suitable linters for Kotlin. Feel free to suggest one to
add.
