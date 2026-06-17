# Java

## Mise

Commit a Gradle wrapper.

```toml
# mise.toml
[tools]
"core:java" = "zulu-…"
"github:google/google-java-format" = "…"
```

## Formatter

```jsonc
"exec": {
  "commands": [
    {
      "command": "google-java-format - --assume-filename {{file_path}}",
      "exts": ["java"],
    },
  ]
}
```

## Linter

I haven't yet explored suitable linters for Java. Feel free to suggest one to
add.
