# C / C++

## Mise

```toml
# mise.toml
[tools]
"conda:clang-tools" = "…"
```

## Formatter

Dprint plugins:

- `sargunv/dprint-clang-format`
- `sargunv/dprint-cmakefmt`

The clang-format plugin formats `c`, `cc`, `cpp`, `cxx`, `h`, `hh`, `hpp`,
`hxx`, `m`, and `mm`. The cmakefmt plugin formats `CMakeLists.txt`,
`CMakeLists.txt.in`, and `*.cmake`.

```jsonc
"clangFormat": {
  "BasedOnStyle": "Google",
  "ColumnLimit": 80,
  "IndentWidth": 2,
  "ContinuationIndentWidth": 2,
  "UseCRLF": false,
  "UseTab": "Never",
  "AlignAfterOpenBracket": "BlockIndent",
  "IncludeBlocks": "Regroup",
  "IncludeCategories": [
    { "Regex": "^<[a-zA-Z0-9_]+>$", "Priority": -100 },
    // Add a bucket here for a heavily used dependency namespace when it should
    // stay grouped before other C++/system-style includes.
    // { "Regex": "^<dependency/.*>$", "Priority": -60 },
    { "Regex": "^<.*>$", "Priority": -50 },
    { "Regex": ".*", "Priority": 1 },
  ]
}
```

Use the optional dependency bucket for consumers that include a lot from one
library namespace and benefit from keeping that library grouped separately.

Leave cmakefmt on plugin defaults unless the project needs otherwise.

## Linter

[clang-tidy](https://clang.llvm.org/extra/clang-tidy/) in hk. CMake must export
`compile_commands.json`. Keep clang-tidy out of `pre-commit` — too slow.

```yaml
# .clang-tidy
Checks: "-*,bugprone-*,clang-analyzer-*,modernize-*,performance-*,readability-*"
WarningsAsErrors: "*"
HeaderFilterRegex: ".*"
```

```cmake
# CMakeLists.txt
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```

```pkl
local fastSteps = new Mapping<String, Step> {
  ["dprint"] = Builtins.dprint
  // …other fast steps
}

local slowSteps = new Mapping<String, Step> {
  ["clang-tidy"] {
    glob = List("**/*.cpp", "**/*.cc", "**/*.cxx", "**/*.c", "**/*.h", "**/*.hpp", "**/*.m", "**/*.mm")
    workspace_indicator = "compile_commands.json"
    check = "clang-tidy -p {{workspace}} {{files}}"
    fix = "clang-tidy -p {{workspace}} --fix {{files}}"
    exclusive = true
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    stash = "git"
    steps { ...fastSteps }
  }
  ["check"] {
    steps {
      ...fastSteps
      ...slowSteps
    }
  }
  ["fix"] {
    fix = true
    steps {
      ...fastSteps
      ...slowSteps
    }
  }
}
```
