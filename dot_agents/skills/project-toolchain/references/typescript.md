# TypeScript

## Mise and deps

[pnpm](https://pnpm.io) is a mise tool (`aqua:pnpm/pnpm`) — pin it in
`mise.toml`, not via corepack (Node no longer ships corepack). Pinning pnpm with
mise keeps the version locked next to the rest of the toolchain.

```toml
# mise.toml
[tools]
"core:node" = "…"
"aqua:pnpm/pnpm" = "…"

[deps.pnpm]
auto = true
```

Keep `packageManager` in `package.json` matched to the mise-pinned version as
metadata (Renovate and editors read it); it is not what activates pnpm.

```json
// package.json
{
  "packageManager": "pnpm@X.Y.Z"
}
```

Every repo gets a `pnpm-workspace.yaml` — pnpm v10+ reads its config from there
even for single-package repos. Monorepos add `packages` and `catalog`;
single-package repos omit them. Set `minimumReleaseAge` (minutes) for the npm
release cooldown so it mirrors mise's `minimum_release_age`.

```yaml
# pnpm-workspace.yaml
minimumReleaseAge: 4320 # 3-day release cooldown
# packages: # monorepos only
#   - "apps/*"
#   - "packages/*"
# catalog: # monorepos only
#   typescript: "…"
#   vite-plus: "…"
# catalogMode: strict
# cleanupUnusedCatalogs: true
```

```json
// package.json — monorepo packages use the catalog
{
  "devDependencies": {
    "typescript": "catalog:",
    "vite-plus": "catalog:"
  }
}
```

Single-package repos pin versions directly in `devDependencies` (caret ranges by
default; the committed lockfile is the source of truth).

Use dprint's oxc plugin for formatting and vite-plus for lint checks
(`pnpm exec vp check`).

Commit `pnpm-lock.yaml`.

## Formatter

Dprint plugin: `oxc`.

```jsonc
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
