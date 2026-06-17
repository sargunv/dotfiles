# TypeScript

## Mise and deps

[pnpm](https://pnpm.io) via [corepack](https://nodejs.org/api/corepack.html) —
pin the version in `packageManager`, not as a separate mise tool.

```toml
# mise.toml
[settings.node]
corepack = true

[tools]
"core:node" = "…"

[deps.pnpm]
auto = true
```

```json
// package.json
{
  "packageManager": "pnpm@X.Y.Z"
}
```

```yaml
# pnpm-workspace.yaml — monorepos only
packages:
  - "apps/*"
  - "packages/*"
catalog:
  typescript: "…"
  vite-plus: "…"
catalogMode: strict
cleanupUnusedCatalogs: true
minimumReleaseAge: 4320
```

```json
// package.json — monorepo packages
{
  "devDependencies": {
    "typescript": "catalog:",
    "vite-plus": "catalog:"
  }
}
```

Single-package repos pin versions directly in `devDependencies` instead of a
catalog.

Do not install `oxlint` or `oxfmt` — [oxfmt](#formatter) is the dprint oxc
plugin; [oxlint](#linter) comes through vite-plus (`pnpm exec vp check`).

Commit `pnpm-lock.yaml`.

## Formatter

[dprint oxc plugin](https://dprint.dev/plugins/) (oxfmt) in `dprint.jsonc`. Do
not add prettier, eslint, or biome as parallel formatters.

```jsonc
"plugins": [
  "https://plugins.dprint.dev/oxc-X.Y.Z.wasm",
],
"oxc": {
  "experimentalSortImports": { "newlinesBetween": true },
}
```

## Linter

[vite-plus](https://www.npmjs.com/package/vite-plus) in hk. For web UIs see
[web-apps.md](web-apps.md).

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "verbatimModuleSyntax": true
  }
}
```

```pkl
["vp-check"] {
  glob = List("**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx")
  workspace_indicator = "vite.config.ts"
  check = "cd {{workspace}} && pnpm exec vp check --no-fmt"
  fix = "cd {{workspace}} && pnpm exec vp check --no-fmt --fix"
}
```
