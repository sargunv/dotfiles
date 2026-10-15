import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { buildCatalogs, registerGateway } from "../dot_local/lib/coding-agents/litellm.mjs";

const model = (id, overrides = {}) => ({
  id, name: id, tool_call: true, reasoning: true,
  modalities: { input: ["text", "image", "audio"] },
  limit: { context: 100000, output: 10000 },
  cost: { input: 1, output: 2, cache_read: 0.1 },
  ...overrides,
});
const catalog = {
  openai: { models: { sol: model("sol"), image: model("image", { tool_call: false }) } },
  "opencode-go": { models: Object.fromEntries([
    "mimo-v2.6-flash", "kimi-k3", "claude-haiku", "literal.v1", "literalXv1", "unserved",
  ].map((id) => [id, model(id)])) },
  anthropic: { models: { claude: model("claude") } },
};
const routes = ["sol", "claude-*", "kimi-*", "opencode-go/*"];

test("only OpenAI and Go catalogs, excluding dedicated-route duplicates", () => {
  const result = buildCatalogs(catalog, routes, "opencode-go/");
  assert.deepEqual(Object.keys(result), ["openai", "opencode-go"]);
  assert.deepEqual(result.openai.map((m) => m.id), ["sol"]);
  assert.deepEqual(result["opencode-go"].map((m) => m.id), [
    "mimo-v2.6-flash", "literal.v1", "literalXv1", "unserved",
  ]);
  assert.deepEqual(result.openai[0].input, ["text", "image"]);
  assert.equal(result.openai[0].contextWindow, 100000);
  assert.equal(result.openai[0].cost.cacheRead, 0.1);
});

test("wildcards do not interpret regex metacharacters", () => {
  const result = buildCatalogs(catalog, ["opencode-go/literal.v*"], "opencode-go/");
  assert.deepEqual(result["opencode-go"].map((m) => m.id), ["literal.v1"]);
});

test("missing catalogs fail rather than silently widening discovery", () => {
  assert.throws(() => buildCatalogs({}, routes, "opencode-go/"), /Missing openai catalog/);
});

test("gateway dispatch overrides native credentials and adds Go routing/session headers", async () => {
  const directory = await mkdtemp(join(tmpdir(), "litellm-test-"));
  const originalFetch = globalThis.fetch;
  try {
    const config = { origin: "https://gateway.example", keyFile: join(directory, "key"), goPrefix: "opencode-go/", cacheDir: directory };
    await writeFile(config.keyFile, "gateway-key\n");
    globalThis.fetch = async (url, options) => {
      if (String(url).startsWith(config.origin)) {
        assert.equal(options.headers.Authorization, "Bearer gateway-key");
        return Response.json({ data: routes.map((id) => ({ id })) });
      }
      assert.equal(url, "https://models.dev/api.json");
      assert.equal(options.headers, undefined);
      return Response.json(catalog);
    };
    const registered = new Map();
    const calls = [];
    const stream = (...args) => { calls.push(args); return "stream"; };
    const pi = { registerProvider: (name, definition) => registered.set(name, definition) };
    await registerGateway(pi, config, { openai: stream, "opencode-go": stream });
    assert.deepEqual([...registered.keys()], ["openai", "opencode-go"]);
    const go = registered.get("opencode-go");
    const goModel = { ...go.models[0], provider: "opencode-go" };
    assert.equal(go.streamSimple(goModel, {}, { apiKey: "native-oauth", headers: { authorization: "Bearer native-oauth" }, sessionId: "session-1" }), "stream");
    assert.equal(calls[0][0].id, "opencode-go/mimo-v2.6-flash");
    assert.equal(calls[0][0].baseUrl, "https://gateway.example/v1");
    assert.equal(calls[0][0].api, "openai-completions");
    assert.equal(calls[0][2].apiKey, "gateway-key");
    assert.equal(calls[0][2].headers.authorization, "Bearer gateway-key");
    assert.equal(calls[0][2].headers["x-opencode-session"], "session-1");
    assert.equal(goModel.id, "mimo-v2.6-flash");
    const openai = registered.get("openai");
    openai.streamSimple({ ...openai.models[0], provider: "openai" }, {}, {});
    assert.equal(calls[1][0].id, "sol");
    assert.equal(calls[1][0].api, "openai-responses");
    // Previously filtered snapshots can be used offline; credentials are not cached.
    globalThis.fetch = async () => { throw new Error("offline"); };
    await registerGateway(pi, config, { openai: stream, "opencode-go": stream });
    await writeFile(config.keyFile, "rotated-key\n");
    registered.get("openai").streamSimple(openai.models[0], {}, {});
    assert.equal(calls[2][2].apiKey, "rotated-key");
    await assert.rejects(registerGateway(pi, { ...config, origin: "https://other.example" }, {}), /offline/);
  } finally {
    globalThis.fetch = originalFetch;
    await rm(directory, { recursive: true, force: true });
  }
});
