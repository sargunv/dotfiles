# Java

## Mise

Commit a Gradle wrapper. Don't enable Gradle dependency locking
(`dependencyLocking`, `gradle.lockfile`); Gradle handles it poorly. Pin
dependency versions explicitly instead.

```toml
# mise.toml
[tools]
"core:java" = "zulu-…"
```

## Formatter

Dprint plugin: `sargunv/google-java-format`
(`https://plugins.dprint.dev/sargunv/google-java-format-<ver>.json`).

```jsonc
"googleJavaFormat": {
  "lineWidth": 100,
}
```

## Linter

I haven't yet explored suitable linters for Java. Feel free to suggest one to
add.
