# Kotlin

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

Dprint plugin: `https://plugins.dprint.dev/sargunv/ktfmt-<ver>.json`. No ktfmt
mise tool or task.

```jsonc
"ktfmt": {
  "style": "google", // or "kotlinlang" | "meta"
  "lineWidth": 100,
}
```

## Linter

I haven't yet explored suitable linters for Kotlin. Feel free to suggest one to
add.
