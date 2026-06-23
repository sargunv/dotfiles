---
name: project-toolchain
description: >-
  Describes my approach to selecting a tech stack or spinning up new projects.
  Apply when setting up a repo or when the user asks to align an existing repo
  with these recommendations. Do not retrofit repos unprompted.
---

# Project toolchain

## General guidance

Projects should keep host tooling expectations minimal. Every machine should
have [mise](https://mise.jdx.dev) installed; projects bootstrap toolchains via
`mise.toml`. Mise pins host-level tools, and ecosystem package managers (pnpm,
uv, cargo, and so on) install the rest.

Use lockfiles and frozen or locked installs everywhere the ecosystem supports
them. Avoid package managers that lack lockfiles or release-cooldown support.

For repos we own (new or existing), apply all relevant setup sections below. In
someone else's repo, defer to upstream conventions but use mise to set up a
local environment — see [Third-party repos](#third-party-repos).

I have opinions about what languages to use for different scenarios. Generally,
I prefer languages with compile time safety, modern tooling, and the ability to
produce a self contained static binary (if relevant).

- Go suits straightforward CLIs and services. Nil safety is the main pitfall, so
  avoid Go for large, complex projects.
- Rust fits complex or performance-sensitive work, but is harder to
  cross-compile and requires assembling a larger tooling ecosystem.
- Zig is excellent for interfacing with C or when exact memory layout matters,
  but avoid if memory safety is a concern and the project is large or complex.
- TypeScript/React/Node is the default for full-stack web apps. Swap in Go,
  Java, Rust, or Python for the backend when it fits the domain better than Node
  does.
- Modern Java (25+) is great for JVM work. Prefer Kotlin when supporting Android
  or when Kotlin Multiplatform is needed.
- C++ is reserved for interfacing with existing C++ codebases.
- Python is typically reserved for scripting and orchestration.

These are guidance, not hard rules. Please pick the right tool for the job
rather than going out of your way to stick to my preferred tools; I'm happy to
learn a new language or tool.

Prefer modern strict linters and opinionated AST-rewriting formatters (Prettier,
oxfmt, ktfmt, ruff, gofumpt) over classic linter-style formatters. Ban `any`,
avoid type casts, and use strict modes where the language allows. Prefer static
languages when the problem fits.

For API contracts, when the stack spans languages and communicates over a
serialized medium (like a network), use [TypeSpec](https://typespec.io/) to emit
JSON Schema and/or OpenAPI for the contract. When both frontend and backend are
TypeScript, use [tRPC](https://trpc.io/) with TanStack Query instead. Web app
layout, codegen, and UI stack details are in
[references/web-apps.md](references/web-apps.md).

## Native dependencies

When a project needs portable native libraries, prefer [pixi](https://pixi.sh)
with [conda-forge](https://conda-forge.org/) over documenting `apt install` or
`brew install`. If just acquiring tools from conda-forge, use the mise `conda:`
backend rather than adding `pixi` to the project. The same applies in
third-party repos if they ask you to install host packages.

In owned repos, commit `pixi.lock` and wire `pixi install --locked` via a custom
`[deps.*]` provider or a dedicated mise task — see
[Mise setup → Owned repos](#owned-repos) for the deps pattern.

In third-party repos, keep mise and/or pixi pins in gitignored local config —
`mise.local.toml` and a local `pixi.toml`, listed in `.git/info/exclude` with
their lockfiles — so you satisfy upstream build docs without committing personal
environment setup.

## Extension references

Before configuring mise, hk, or dprint, identify which languages and patterns
the project uses and open the matching references. Then apply the baseline
sections in this file.

Language toolchains (each includes minimal default config snippets):

- [typescript.md](references/typescript.md)
- [python.md](references/python.md)
- [go.md](references/go.md)
- [rust.md](references/rust.md)
- [kotlin.md](references/kotlin.md)
- [java.md](references/java.md)
- [c-cpp.md](references/c-cpp.md)
- [zig.md](references/zig.md)

Stack patterns (additive; pair with the language refs above):

- [web-apps.md](references/web-apps.md)

## Mise setup

Mise is the primary toolchain manager. Reference docs:

- [mise](https://mise.jdx.dev),
- [tools](https://mise.jdx.dev/dev-tools/),
- [tasks](https://mise.jdx.dev/tasks/),
- [deps](https://mise.jdx.dev/dev-tools/deps.html),
- [hooks](https://mise.jdx.dev/hooks.html).

### Owned repos

Almost every owned project starts from this `mise.toml`:

```toml
[settings]
experimental = true
pin = true
install_before = "3d"
lockfile = true

[tools]
"aqua:jdx/hk" = "…"
"aqua:dprint/dprint" = "…"

[tasks.check]
run = "hk check --all"

[tasks.fix]
run = "hk fix --all"

[hooks]
postinstall = ["hk install --mise"]
```

Use [mise deps](https://mise.jdx.dev/dev-tools/deps.html) to integrate ecosystem
installs. Deps hashes lockfiles and auto-runs before `mise run` or `mise x` when
`auto = true`:

```toml
[deps.pnpm]
auto = true

[deps.uv]
auto = true
```

Use explicit backends (`core:node`, `core:rust`, `aqua:jdx/hk`) rather than bare
(`node`, `rust`, `hk`). Backend priority is core, then aqua, then github; then
conda, npm, or pipx. Avoid asdf and vfox unless they're the only choice for the
tool. Mise bootstraps the toolchain; ecosystem tools live inside it (mise → node
→ corepack → pnpm, and so on).

For monorepos with multiple package roots that each have their own `mise.toml`,
set `experimental_monorepo_root = true` and list roots under
`[monorepo]
config_roots`. See the
[mise monorepo docs](https://mise.jdx.dev/monorepo.html).

### Third-party repos

In someone else's repo, develop locally without reshaping the project to your
preferences. Match upstream's package manager, CI, layout, and conventions. Do
not mass-add hk, dprint, or package managers, and do not rewrite their linter or
formatter stack unless you are proposing it explicitly. Use gitignored overrides
for personal workflow gaps instead.

Create a `mise.local.toml` (gitignored via `.git/info/exclude`, never committed)
for tools upstream docs require but you do not want on the host:

```toml
[tools]
"core:…" = "…"
```

Before `apt install` or `brew install`, see
[Native dependencies](#native-dependencies) and check whether mise aqua/github
backends can pin a portable binary. Fall back to host packages only when nothing
else works, and only after getting the user's permission. Document any such
manual installs in `mise.local.toml` comment blocks.

The difference between owned and third-party mode is what gets committed: owned
repos commit the full hk/dprint/mise toolchain; upstream repos do not unless you
are proposing it.

## hk and dprint setup

Hk is the linter and pre-commit orchestrator. Dprint is the formatter
orchestrator. Reference docs:

- [hk](https://hk.jdx.dev),
- [Builtins](https://hk.jdx.dev/builtins),
- [dprint](https://dprint.dev),
- [config](https://dprint.dev/config/),
- [exec plugin](https://dprint.dev/plugins/exec/),
- [plugin hub](https://dprint.dev/plugins/).

Pin hk and dprint in `mise.toml`. The `hk.pkl` `amends` URL must match the mise
hk pin. Hk includes the Pkl runtime for its configuration.

```pkl
amends "package://github.com/jdx/hk/releases/download/vX.Y.Z/hk@X.Y.Z#/Config.pkl"
import "package://github.com/jdx/hk/releases/download/vX.Y.Z/hk@X.Y.Z#/Builtins.pkl"

local lintSteps = new Mapping<String, Step> {
  ["dprint"] = (Builtins.dprint)
  // …language-specific steps — see extension references
}

hooks {
  ["pre-commit"] { fix = true; stash = "git"; steps { ...lintSteps } }
  ["check"]      { steps { ...lintSteps } }
  ["fix"]        { fix = true; steps { ...lintSteps } }
}
```

The baseline `dprint.jsonc` below covers json, toml, markdown, and yaml. Add
language plugins and exec formatters from the
[extension references](#extension-references).

```jsonc
{
  "$schema": "https://dprint.dev/schemas/v0.json",
  "lineWidth": 80,
  "indentWidth": 2,
  "useTabs": false,
  "newLineKind": "lf",
  "json": { "preferSingleLine": true },
  "markdown": { "textWrap": "always" },
  "exec": { "commands": [] },
  "plugins": [
    "https://plugins.dprint.dev/exec-X.Y.Z.json@…",
    "https://plugins.dprint.dev/json-X.Y.Z.wasm",
    "https://plugins.dprint.dev/toml-X.Y.Z.wasm",
    "https://plugins.dprint.dev/markdown-X.Y.Z.wasm",
    "https://plugins.dprint.dev/g-plane/pretty_yaml-vX.Y.Z.wasm",
  ],
}
```

Dprint owns formatting wherever possible, linters should be configured with
formatting disabled if relevant. Put generated files in dprint `excludes`. Do
not add gitignored files to excludes; those are excluded by default.

Refer WASM plugins from the [plugin hub](https://dprint.dev/plugins/). When you
add `"exec": { "commands": … }`, include the
[exec plugin](https://dprint.dev/plugins/exec/) in `"plugins"` with its pinned
checksum. Exec formatters read stdin and write stdout; pass `--assume-filename`
or `--stdin-name` when rules depend on path. WASM plugins ignore external config
like `.prettierrc` — put all necessary settings in `dprint.jsonc`, though it's
usually best to stick close to defaults.

If a formatter cannot do stdin/stdout, run it as an hk linter step instead of
dprint exec.

## Editor config

Wire dprint in editors so format-on-save matches `hk fix` and CI. Commit
`.vscode/settings.json` and `.zed/settings.json` on owned repos; use user-level
settings on third-party repos.

Install the
[dprint extension](https://marketplace.visualstudio.com/items?itemName=dprint.dprint)
(`dprint.dprint`) in VS Code or Cursor:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "dprint.dprint",
  "json.schemaDownload.trustedDomains": {
    "https://dprint.dev": true
  }
}
```

In Zed, use an
[external formatter](https://zed.dev/docs/languages#external-formatter) via mise
so the editor runs the pinned dprint from `mise.toml`:

```json
{
  "format_on_save": "on",
  "formatter": {
    "external": {
      "command": "mise",
      "arguments": ["x", "--", "dprint", "fmt", "--stdin", "{buffer_path}"]
    }
  }
}
```

## AGENTS.md

Every owned repo gets a root `AGENTS.md` with agent context for the project.
Symlink `CLAUDE.md` to `AGENTS.md` so Claude Code reads the same file. Leave
Project invariants empty at setup and fill it in as non-negotiable rules emerge.

```markdown
# Project name

<!-- One-line description of what this repo is. -->

## Project map

<!-- Tree of key directories and what they contain -->

## Dev tool commands

<!--
Document the project's mise tasks and any other common commands here. If there
are many tasks, list only the important ones and reference `mise tasks ls --all`
for the full list.
-->

## Project invariants

<!-- List non-negotiable rules for this project -->
```
