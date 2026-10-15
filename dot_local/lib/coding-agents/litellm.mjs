// Shared by the Pi and oh-my-pi LiteLLM extensions. Like the OpenCode plugin,
// they keep each harness's own OpenAI and OpenCode Go models and only offer
// the ones LiteLLM routes. LiteLLM serves Go models under a route prefix.
import { readFileSync } from "node:fs";

export const providers = ["openai", "opencode-go"];
// Protocols LiteLLM serves these providers' chat models over. It has no
// Google route, and can't serve OpenAI's Decisions or image APIs from the
// ChatGPT subscription.
export const gatewayApis = ["openai-completions", "openai-responses", "anthropic-messages"];

const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const routePattern = (route) => new RegExp(`^${route.split("*").map(escapeRegExp).join(".*")}$`);

/** Reads the gateway key; undefined when the key file does not exist. */
export function readKey(keyFile) {
  let key;
  try {
    key = readFileSync(keyFile, "utf8").trim();
  } catch (error) {
    if (error.code === "ENOENT") return undefined;
    throw error;
  }
  if (!key) throw new Error(`LiteLLM key file is empty: ${keyFile}`);
  return key;
}

/**
 * Decides whether LiteLLM routes a provider's model, given its route ids
 * (including wildcard patterns like `kimi-*`). Go routes use the Go prefix; any
 * other route is a dedicated subscription, which wins over the Go copy.
 */
export function routeFilter(routes, goPrefix) {
  const go = routes.filter((id) => id.startsWith(goPrefix)).map((id) => routePattern(id.slice(goPrefix.length)));
  const dedicated = routes.filter((id) => !id.startsWith(goPrefix)).map(routePattern);
  const isDedicated = (id) => dedicated.some((route) => route.test(id));
  return (provider, id) =>
    provider === "opencode-go" ? go.some((route) => route.test(id)) && !isDedicated(id) : isDedicated(id);
}

export async function loadRouteFilter({ origin, keyFile, goPrefix }) {
  try {
    const key = readKey(keyFile);
    if (!key) throw new Error(`missing ${keyFile}`);
    const response = await fetch(`${origin}/v1/models?return_wildcard_routes=true`, {
      headers: { Authorization: `Bearer ${key}` },
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const { data } = await response.json();
    return routeFilter(data.map((model) => model.id), goPrefix);
  } catch (error) {
    console.warn(`LiteLLM: showing all models; couldn't list routes: ${error.message}`);
    return () => true;
  }
}

/**
 * Points one of Pi's built-in providers at the gateway. Models keep their
 * protocol, limits, and compatibility settings; only the endpoint, the key, and
 * the Go model id sent upstream change, so sessions keep Pi's model identity.
 */
export function piGatewayProvider(base, { origin, keyFile, goPrefix }, visible) {
  // Chat models only; see gatewayApis.
  const models = base.getModels()
    .filter((model) => gatewayApis.includes(model.api) && visible(base.id, model.id))
    // Pi's Anthropic client appends /v1/messages itself.
    .map((model) => ({ ...model, baseUrl: model.api === "anthropic-messages" ? origin : `${origin}/v1` }));
  const upstream = (model, options) =>
    base.id === "opencode-go"
      ? {
        ...options,
        // Runs after Pi's own payload hooks, which see the model's Pi id.
        onPayload: async (payload, payloadModel) => {
          const { thinking, ...next } = (await options?.onPayload?.(payload, payloadModel)) ?? payload;
          next.model = goPrefix + model.id;
          if (thinking === undefined) return next;
          // LiteLLM's OpenAI route rejects vendor fields like DeepSeek's
          // `thinking` unless they arrive through its extra_body passthrough.
          if (model.api !== "openai-completions") return { ...next, thinking };
          return { ...next, extra_body: { ...next.extra_body, thinking } };
        },
      }
      : options;
  return {
    id: base.id,
    name: base.name,
    baseUrl: `${origin}/v1`,
    auth: {
      // Saved logins and environment keys never apply; the key file is read per request.
      apiKey: {
        name: "LiteLLM key",
        resolve: async () => {
          const apiKey = readKey(keyFile);
          return apiKey ? { auth: { apiKey }, source: keyFile } : undefined;
        },
      },
    },
    getModels: () => models,
    stream: (model, context, options) => base.stream(model, context, upstream(model, options)),
    streamSimple: (model, context, options) => base.streamSimple(model, context, upstream(model, options)),
  };
}

/** Undoes the Go prefix in the model name LiteLLM echoes back. */
export function piUnprefixResponseModel(message, goPrefix) {
  if (message.role !== "assistant" || message.provider !== "opencode-go") return undefined;
  if (!message.responseModel?.startsWith(goPrefix)) return undefined;
  const { responseModel, ...rest } = message;
  const unprefixed = responseModel.slice(goPrefix.length);
  return unprefixed === message.model ? rest : { ...rest, responseModel: unprefixed };
}
