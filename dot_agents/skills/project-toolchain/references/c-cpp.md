# C / C++

## Mise

```toml
# mise.toml
[tools]
"conda:clang-format" = "…"
"conda:clang-tools" = "…"
"github:cmakefmt/cmakefmt" = "…"
```

## Formatter

```jsonc
"exec": {
  "commands": [
    {
      "command": "clang-format --assume-filename={{file_path}}",
      "exts": ["c", "cc", "cpp", "cxx", "h", "hh", "hpp", "hxx", "m", "mm"],
    },
    {
      "command": "cmakefmt --line-width {{line_width}} --tab-size {{indent_width}} -",
      "exts": ["cmake"],
    },
  ]
}
```

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
