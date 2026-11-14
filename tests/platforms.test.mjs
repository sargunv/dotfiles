import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  realpathSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve, sep } from "node:path";
import { after, test } from "node:test";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const temporary = mkdtempSync(join(tmpdir(), "dotfiles-test-"));
const home = join(temporary, "Home with 'quotes' $cash #%");
const config = join(temporary, "chezmoi.json");
mkdirSync(home);
writeFileSync(config, "{}");

after(() => {
  assert.ok(realpathSync(temporary).startsWith(realpathSync(tmpdir()) + sep));
  rmSync(temporary, { recursive: true, force: true });
});

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    timeout: 30000,
    ...options,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return result.stdout.trim();
}

function chezmoi(os, args, input = "", distribution = "ubuntu") {
  return run(
    process.env.CHEZMOI || "chezmoi",
    [
      "--source",
      repository,
      "--destination",
      home,
      "--config",
      config,
      "--cache",
      join(temporary, "cache"),
      "--persistent-state",
      join(temporary, "state.boltdb"),
      "--override-data",
      JSON.stringify({
        chezmoi: {
          os,
          arch: "arm64",
          homeDir: home,
          uid: "1000",
          osRelease: { id: os === "linux" ? distribution : "" },
        },
      }),
      ...args,
    ],
    { input },
  );
}

function render(source, os = "windows", input = "") {
  return chezmoi(
    os,
    ["execute-template", "--with-stdin", "--file", join(repository, source)],
    input,
  ).replace(/^# chezmoi:modify-template\r?\n/, "");
}

function parse(contents, format, os = "windows") {
  return JSON.parse(
    chezmoi(
      os,
      [
        "execute-template",
        "--with-stdin",
        `{{ .chezmoi.stdin | from${format} | toJson }}`,
      ],
      contents,
    ),
  );
}

for (const os of ["windows", "darwin", "linux"]) {
  test(`${os} selects only its own platform integration`, () => {
    const managed = chezmoi(os, ["managed", "--exclude", "externals"]);
    const paths = managed.split(/\r?\n/);
    assert.equal(
      paths.includes("AppData/Local/nvim/init.lua"),
      os === "windows",
    );
    assert.equal(
      paths.includes(".local/bin/litellm-key.cmd"),
      os === "windows",
    );
    assert.equal(
      paths.includes(".config/powershell/profile.ps1"),
      os === "windows",
    );
    assert.equal(
      paths.includes(".config/systemd/user/update-agents.timer"),
      os === "linux",
    );
    assert.equal(paths.includes(".local/bin/setup-tpm-key"), os === "linux");
    assert.equal(paths.includes(".zshenv"), os !== "windows");
    assert.equal(
      paths.includes(".local/bin/update-agents.sh"),
      os !== "windows",
    );
    assert.equal(
      paths.includes(".local/bin/update-agents.ps1"),
      os === "windows",
    );
    const scripts = paths.filter((path) => path.startsWith(".chezmoiscripts/"));
    if (os === "windows") {
      assert.ok(scripts.length > 0);
      assert.ok(
        scripts.every(
          (path) =>
            path.startsWith(".chezmoiscripts/windows/") &&
            path.endsWith(".ps1"),
        ),
      );
    } else {
      assert.ok(
        scripts.every((path) => !path.startsWith(".chezmoiscripts/windows/")),
      );
    }
    assert.equal(
      scripts.some((path) => path.startsWith(".chezmoiscripts/darwin/")),
      os === "darwin",
    );
    assert.equal(
      scripts.some((path) => path.includes("install-apt-packages")),
      os === "linux",
    );
    assert.ok(!scripts.some((path) => path.includes("install-dnf-packages")));

    const externals = parse(
      render(".chezmoiexternal.toml.tmpl", os),
      "Toml",
      os,
    );
    const lazy =
      os === "windows"
        ? "AppData/Local/nvim-data/chezmoi/lazy.nvim"
        : ".local/share/nvim/chezmoi/lazy.nvim";
    assert.ok(externals[lazy]);
    assert.equal(Boolean(externals[".config/zsh/antidote"]), os !== "windows");
    assert.equal(
      Boolean(externals[".config/tmux/plugins/tpm"]),
      os !== "windows",
    );

    const mise = parse(
      render("dot_config/mise/config.toml.tmpl", os),
      "Toml",
      os,
    );
    assert.equal(
      Boolean(mise.tools["github:sargunv/starship-multi-config"]),
      os !== "windows",
    );
    assert.deepEqual(mise.settings.lockfile_platforms, [
      `${os === "darwin" ? "macos" : os}-arm64`,
    ]);
  });

  test(`${os} agent settings merge preferences and render valid gateway commands`, () => {
    const claude = JSON.parse(
      render(
        "dot_claude/modify_settings.json",
        os,
        '{"model":"saved-model","theme":"dark"}',
      ),
    );
    assert.equal(claude.model, "saved-model");
    assert.equal(claude.theme, "dark");
    assert.equal(
      claude.apiKeyHelper,
      os === "windows"
        ? "litellm-key.cmd"
        : `cat ${JSON.stringify(join(home, ".config/litellm/api-key"))}`,
    );
    const codex = parse(
      render("dot_codex/modify_config.toml", os, 'model = "saved-model"'),
      "Toml",
      os,
    );
    assert.equal(codex.model, "saved-model");
    const auth = codex.model_providers.litellm.auth;
    assert.equal(auth.command, os === "windows" ? "pwsh" : "/bin/cat");
    if (os === "windows")
      assert.deepEqual(auth.args, [
        "-NoProfile",
        "-File",
        join(home, ".local/bin/litellm-key.ps1"),
      ]);
    const omp = parse(
      render("dot_omp/private_agent/modify_models.yml", os),
      "Yaml",
      os,
    );
    assert.equal(omp.providers.openai.apiKey, `!${claude.apiKeyHelper}`);
    const grok = parse(render("dot_grok/modify_config.toml", os), "Toml", os);
    if (os === "windows")
      assert.equal(grok.auth.auth_provider_command, claude.apiKeyHelper);
  });
}

test("Fedora selects dnf instead of apt", () => {
  const managed = chezmoi(
    "linux",
    ["managed", "--exclude", "externals"],
    "",
    "fedora",
  );
  assert.match(managed, /install-dnf-packages/);
  assert.doesNotMatch(managed, /install-apt-packages/);
});

test("agent module imports load through escaped file URLs", async () => {
  const modulePath = join(home, ".local/lib/coding-agents/litellm.mjs");
  mkdirSync(dirname(modulePath), { recursive: true });
  writeFileSync(
    modulePath,
    readFileSync(join(repository, "dot_local/lib/coding-agents/litellm.mjs")),
  );
  for (const source of [
    "dot_config/opencode/plugins/litellm.js.tmpl",
    "dot_pi/agent/extensions/litellm.ts.tmpl",
    "dot_omp/private_agent/extensions/litellm.ts.tmpl",
  ]) {
    const contents = render(source);
    const url = JSON.parse(contents.match(/from ("file:[^\n]+");/)[1]);
    assert.equal(fileURLToPath(url), modulePath);
    assert.equal(typeof (await import(url)).routeFilter, "function");
  }
});

const windows = process.platform === "win32";

test(
  "Windows credential helpers read a key through both native and shell commands",
  { skip: !windows },
  () => {
    const bin = join(home, ".local/bin");
    mkdirSync(bin, { recursive: true });
    mkdirSync(join(home, ".config/litellm"), { recursive: true });
    writeFileSync(
      join(home, ".config/litellm/api-key"),
      "test-gateway-key\r\n",
    );
    writeFileSync(
      join(bin, "litellm-key.ps1"),
      render("dot_local/bin/executable_litellm-key.ps1.tmpl"),
    );
    writeFileSync(
      join(bin, "litellm-key.cmd"),
      readFileSync(
        join(repository, "dot_local/bin/executable_litellm-key.cmd"),
      ),
    );
    const codex = parse(render("dot_codex/modify_config.toml"), "Toml");
    const auth = codex.model_providers.litellm.auth;
    assert.equal(run(auth.command, auth.args), "test-gateway-key");
    assert.equal(
      run("cmd.exe", ["/d", "/c", "litellm-key.cmd"], {
        env: { ...process.env, PATH: `${bin};${process.env.PATH}` },
      }),
      "test-gateway-key",
    );
  },
);

test(
  "Windows scripts parse without executing system setup",
  { skip: !windows },
  () => {
    const sources = run(
      "git",
      ["ls-files", "--cached", "--others", "--exclude-standard"],
      { cwd: repository },
    )
      .split(/\r?\n/)
      .filter((path) => /\.ps1(?:\.tmpl)?$/.test(path));
    const directory = join(temporary, "scripts");
    mkdirSync(directory);
    for (const [index, source] of sources.entries()) {
      writeFileSync(join(directory, `${index}.ps1`), render(source));
    }
    const parser = join(temporary, "parse.ps1");
    writeFileSync(
      parser,
      `param($Directory)
$ErrorActionPreference = 'Stop'
foreach ($file in Get-ChildItem -LiteralPath $Directory -Filter '*.ps1') {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count) { throw "$($file.Name): $errors" }
}
`,
    );
    run("pwsh", ["-NoProfile", "-File", parser, directory]);
  },
);

test(
  "Windows SSH bootstrap creates a usable key and preserves it on reapply",
  { skip: !windows },
  () => {
    const script = join(temporary, "ssh-key.ps1");
    writeFileSync(
      script,
      render(
        ".chezmoiscripts/exact_windows/run_onchange_before_05-generate-ed25519-ssh-key.ps1.tmpl",
      ),
    );
    run("pwsh", ["-NoProfile", "-File", script]);
    const key = join(home, ".ssh/id_ed25519");
    const contents = readFileSync(key, "utf8");
    const publicKey = run("ssh-keygen", ["-y", "-f", key]);
    assert.ok(readFileSync(`${key}.pub`, "utf8").startsWith(publicKey));
    run("pwsh", ["-NoProfile", "-File", script]);
    assert.equal(readFileSync(key, "utf8"), contents);
  },
);

test(
  "Windows package bootstrap skips installed tools and propagates failures",
  { skip: !windows },
  () => {
    const script = join(temporary, "winget.ps1");
    writeFileSync(
      script,
      render(
        ".chezmoiscripts/exact_windows/run_onchange_after_05-install-winget-packages.ps1.tmpl",
      ),
    );
    const harness = join(temporary, "winget-test.ps1");
    writeFileSync(
      harness,
      `param($Script)
$ErrorActionPreference = 'Stop'
$script:installed = @()
function winget {
    $id = $args[[array]::IndexOf($args, '--id') + 1]
    if ($args[0] -eq 'list') {
        $global:LASTEXITCODE = if ($id -eq 'Microsoft.PowerShell') { 0 } else { 1 }
    } else {
        $script:installed += $id
        $global:LASTEXITCODE = if ($id -eq 'Git.Git') { 3010 } else { 42 }
    }
}
try {
    . $Script
    throw 'Expected installation to fail.'
} catch {
    if ($_ -notmatch 'WinGet failed to install GitHub.cli') { throw }
}
if (($script:installed -join ',') -ne 'Git.Git,GitHub.cli') {
    throw "Unexpected installs: $script:installed"
}
`,
    );
    run("pwsh", ["-NoProfile", "-File", harness, script]);
  },
);
