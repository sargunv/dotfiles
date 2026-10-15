import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import {
  loadRouteFilter,
  piGatewayProvider,
  piUnprefixResponseModel,
  routeFilter,
} from "../dot_local/lib/coding-agents/litellm.mjs";

const goPrefix = "opencode-go/";
const routes = ["gpt-6-sol", "claude-*", "chatgpt/gpt-6-sol", "opencode-go/kimi-k3", "opencode-go/claude-haiku", "opencode-go/literal.v*"];

async function withKeyFile(contents, run) {
  const directory = await mkdtemp(join(tmpdir(), "litellm-test-"));
  try {
    const keyFile = join(directory, "key");
    if (contents !== undefined) await writeFile(keyFile, contents);
    return await run(keyFile);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

test("route filter offers routed models and prefers dedicated routes over Go copies", () => {
  const visible = routeFilter(routes, goPrefix);
  assert.equal(visible("openai", "gpt-6-sol"), true);
  assert.equal(visible("openai", "gpt-4o"), false);
  assert.equal(visible("opencode-go", "kimi-k3"), true);
  assert.equal(visible("opencode-go", "claude-haiku"), false);
  assert.equal(visible("opencode-go", "gpt-6-sol"), false);
});

test("route wildcards do not interpret regex metacharacters", () => {
  const visible = routeFilter(routes, goPrefix);
  assert.equal(visible("opencode-go", "literal.v1"), true);
  assert.equal(visible("opencode-go", "literalXv1"), false);
});

test("route listing failures offer every model", async () => {
  const originalWarn = console.warn;
  console.warn = () => {};
  try {
    await withKeyFile(undefined, async (keyFile) => {
      const visible = await loadRouteFilter({ origin: "https://gateway.invalid", keyFile, goPrefix });
      assert.equal(visible("openai", "anything"), true);
    });
  } finally {
    console.warn = originalWarn;
  }
});

const baseProvider = (id, models) => {
  const calls = [];
  return {
    calls,
    id,
    name: id.toUpperCase(),
    getModels: () => models,
    stream: (...args) => calls.push(["stream", ...args]),
    streamSimple: (...args) => calls.push(["streamSimple", ...args]),
  };
};

test("Pi providers keep model metadata and change only endpoint and auth", async () => {
  await withKeyFile("gateway-key\n", async (keyFile) => {
    const gateway = { origin: "https://gateway.example", keyFile, goPrefix };
    const base = baseProvider("opencode-go", [
      { id: "kimi-k3", api: "openai-completions", baseUrl: "https://opencode.ai/zen/go/v1", thinkingLevelMap: { max: "max" } },
      { id: "qwen", api: "anthropic-messages", baseUrl: "https://opencode.ai/zen/go", compat: { supportsTemperature: false } },
      { id: "grok", api: "openai-responses", baseUrl: "https://opencode.ai/zen/go/v1" },
      { id: "unrouted", api: "openai-completions", baseUrl: "https://opencode.ai/zen/go/v1" },
      { id: "gemini", api: "google-generative-ai", baseUrl: "https://opencode.ai/zen/go/v1" },
    ]);
    const provider = piGatewayProvider(base, gateway, (_, id) => id !== "unrouted");
    assert.equal(provider.id, "opencode-go");
    assert.deepEqual(provider.getModels().map((model) => [model.id, model.baseUrl]), [
      ["kimi-k3", "https://gateway.example/v1"],
      ["qwen", "https://gateway.example"],
      ["grok", "https://gateway.example/v1"],
    ]);
    const [kimi, qwen] = provider.getModels();
    assert.deepEqual(kimi.thinkingLevelMap, { max: "max" });
    assert.deepEqual(qwen.compat, { supportsTemperature: false });

    const stored = { type: "api_key", key: "saved-login" };
    assert.deepEqual(await provider.auth.apiKey.resolve({ credential: stored }), {
      auth: { apiKey: "gateway-key" },
      source: keyFile,
    });
    await writeFile(keyFile, "rotated-key\n");
    assert.equal((await provider.auth.apiKey.resolve({})).auth.apiKey, "rotated-key");
  });
});

test("Pi Go requests send the gateway model id after Pi's own payload hooks", async () => {
  await withKeyFile("key", async (keyFile) => {
    const gateway = { origin: "https://gateway.example", keyFile, goPrefix };
    const go = baseProvider("opencode-go", [{ id: "kimi-k3", api: "openai-completions" }]);
    const provider = piGatewayProvider(go, gateway, () => true);
    const model = provider.getModels()[0];
    const seen = [];
    provider.streamSimple(model, "context", {
      sessionId: "session-1",
      onPayload: (payload, payloadModel) => {
        seen.push([payload.model, payloadModel.id]);
        return { ...payload, temperature: 0 };
      },
    });
    const [kind, sentModel, context, options] = go.calls[0];
    assert.equal(kind, "streamSimple");
    assert.equal(sentModel, model);
    assert.equal(context, "context");
    assert.equal(options.sessionId, "session-1");
    assert.deepEqual(await options.onPayload({ model: "kimi-k3" }, model), {
      model: "opencode-go/kimi-k3",
      temperature: 0,
    });
    assert.deepEqual(seen, [["kimi-k3", "kimi-k3"]]);

    provider.stream(model, "context");
    assert.deepEqual(await go.calls[1][3].onPayload({ model: "kimi-k3" }, model), { model: "opencode-go/kimi-k3" });

    const openai = baseProvider("openai", [{ id: "gpt-6-sol", api: "openai-responses" }]);
    const openaiOptions = { sessionId: "session-1" };
    piGatewayProvider(openai, gateway, () => true).streamSimple(openai.getModels()[0], "context", openaiOptions);
    assert.equal(openai.calls[0][3], openaiOptions);
  });
});

test("Pi providers are unconfigured without a key file", async () => {
  await withKeyFile(undefined, async (keyFile) => {
    const provider = piGatewayProvider(baseProvider("openai", []), { origin: "https://gateway.example", keyFile, goPrefix }, () => true);
    assert.equal(await provider.auth.apiKey.resolve({}), undefined);
  });
});

test("Go response model names lose the gateway prefix", () => {
  const message = { role: "assistant", provider: "opencode-go", model: "qwen", responseModel: "opencode-go/qwen" };
  assert.deepEqual(piUnprefixResponseModel(message, goPrefix), { role: "assistant", provider: "opencode-go", model: "qwen" });
  assert.equal(
    piUnprefixResponseModel({ ...message, responseModel: "opencode-go/qwen-fallback" }, goPrefix).responseModel,
    "qwen-fallback",
  );
  assert.equal(piUnprefixResponseModel({ ...message, responseModel: undefined }, goPrefix), undefined);
  assert.equal(piUnprefixResponseModel({ ...message, provider: "openai" }, goPrefix), undefined);
});

test("Pi Go chat requests pass vendor thinking controls through LiteLLM's extra_body", async () => {
  await withKeyFile("key", async (keyFile) => {
    const gateway = { origin: "https://gateway.example", keyFile, goPrefix };
    const go = baseProvider("opencode-go", [
      { id: "deepseek", api: "openai-completions" },
      { id: "qwen", api: "anthropic-messages" },
    ]);
    const provider = piGatewayProvider(go, gateway, () => true);
    const [deepseek, qwen] = provider.getModels();
    provider.streamSimple(deepseek, "context");
    provider.streamSimple(qwen, "context");
    const thinking = { type: "enabled" };
    assert.deepEqual(await go.calls[0][3].onPayload({ model: "deepseek", thinking, extra_body: { a: 1 } }, deepseek), {
      model: "opencode-go/deepseek",
      extra_body: { a: 1, thinking },
    });
    assert.deepEqual(await go.calls[1][3].onPayload({ model: "qwen", thinking }, qwen), {
      model: "opencode-go/qwen",
      thinking,
    });
  });
});
