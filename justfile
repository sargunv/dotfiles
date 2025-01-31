default:
    @just --list

# Apply changes manually
apply:
    chezmoi apply --verbose

# Edit a file in the source state
edit *PATHS:
    chezmoi edit {{PATHS}}

# Add a file to source state
add *PATHS:
    chezmoi add {{PATHS}}

# Show diff between source state and destination state
diff:
    chezmoi diff

watch:
    #!/usr/bin/env bash
    export CHEZMOI_SOURCE_PATH="$(chezmoi source-path)"
    watchman watch "${CHEZMOI_SOURCE_PATH}"
    jq -n \
        --arg path "${CHEZMOI_SOURCE_PATH}" \
        '[
            "trigger",
            $path,
            {
                name: "chezmoi-apply",
                command: ["chezmoi", "apply", "--force"]
            }
        ]' | watchman -j

# Stop watching and remove triggers
unwatch:
    #!/usr/bin/env bash
    CHEZMOI_SOURCE_PATH="$(chezmoi source-path)"
    watchman trigger-del "${CHEZMOI_SOURCE_PATH}" chezmoi-apply
    watchman watch-del "${CHEZMOI_SOURCE_PATH}"
