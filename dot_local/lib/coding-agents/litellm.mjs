import { readFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const providers = ["openai", "opencode-go"];
const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const routePattern = (route) => new RegExp(`^${route.split("*").map(escapeRegExp).join(".*")}$`);

export function buildCatalogs(catalog, routes, goPrefix) {
  const go = routes.filter((id) => id.startsWith(goPrefix)).map((id) => routePattern(id.slice(goPrefix.length)));
  const dedicated = routes.filter((id) => !id.startsWith(goPrefix)).map(routePattern);
  return Object.fromEntries(providers.map((provider) => {
    if (!catalog[provider]?.models) throw new Error(`Missing ${provider} catalog`);
    const models = Object.values(catalog[provider].models)
      // These harnesses need chat/tool models, not image, audio, or embedding runners.
      .filter((model) => model.tool_call && model.limit?.context > 0 && model.limit?.output > 0)
      .filter((model) => provider !== "opencode-go" || (
        go.some((route) => route.test(model.id)) && !dedicated.some((route) => route.test(model.id))
      ))
      .map((model) => ({
        id: model.id,
        name: model.name,
        reasoning: model.reasoning === true,
        input: model.modalities.input.filter((type) => type === "text" || type === "image"),
        contextWindow: model.limit.context,
        maxTokens: model.limit.output,
        cost: {
          input: model.cost?.input ?? 0,
          output: model.cost?.output ?? 0,
          cacheRead: model.cost?.cache_read ?? 0,
          cacheWrite: model.cost?.cache_write ?? 0,
        },
      }));
    return [provider, models];
  }));
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(`Catalog request failed: HTTP ${response.status}`);
  return response.json();
}

export async function loadCatalogs({ origin, keyFile, goPrefix, cacheDir }) {
  const cacheFile = join(cacheDir, "catalogs.json");
  let cached;
  try {
    cached = JSON.parse(await readFile(cacheFile, "utf8"));
  } catch {
    // A first run or invalid cache must obtain a fresh catalog.
  }
  const validCache = cached?.origin === origin && cached?.goPrefix === goPrefix
    && providers.every((provider) => Array.isArray(cached?.catalogs?.[provider]));
  try {
    const key = readFileSync(keyFile, "utf8").trim();
    const [catalog, routes] = await Promise.all([
      fetchJson("https://models.dev/api.json"),
      fetchJson(`${origin}/v1/models?return_wildcard_routes=true`, {
        headers: { Authorization: `Bearer ${key}` },
      }),
    ]);
    const catalogs = buildCatalogs(catalog, routes.data.map((model) => model.id), goPrefix);
    const snapshot = { origin, goPrefix, catalogs };
    await mkdir(dirname(cacheFile), { recursive: true });
    const temporary = `${cacheFile}.${process.pid}.tmp`;
    await writeFile(temporary, JSON.stringify(snapshot), { mode: 0o600 });
    await rename(temporary, cacheFile);
    return catalogs;
  } catch (error) {
    if (!validCache) throw error;
    console.warn(`LiteLLM: using cached catalogs (${error.message})`);
    return cached.catalogs;
  }
}

export async function registerGateway(pi, config, streams) {
  const catalogs = await loadCatalogs(config);
  const sessionId = randomUUID();
  for (const provider of providers) {
    const api = `chezmoi-${provider}`;
    const nativeApi = provider === "openai" ? "openai-responses" : "openai-completions";
    pi.registerProvider(provider, {
      baseUrl: `${config.origin}/v1`,
      api,
      apiKey: `!cat ${JSON.stringify(config.keyFile)}`,
      models: catalogs[provider].map((model) => ({ ...model, api })),
      streamSimple(model, context, options) {
        const key = readFileSync(config.keyFile, "utf8").trim();
        if (!key) throw new Error("LiteLLM key file is empty");
        const headers = new Headers({ ...model.headers, ...options?.headers });
        headers.set("Authorization", `Bearer ${key}`);
        if (provider === "opencode-go") headers.set("x-opencode-session", options?.sessionId ?? sessionId);
        const wireModel = {
          ...model,
          provider: "chezmoi-litellm",
          api: nativeApi,
          baseUrl: `${config.origin}/v1`,
          id: provider === "opencode-go" ? config.goPrefix + model.id : model.id,
          headers: Object.fromEntries(headers),
        };
        // Use the native serializers, but never forward a saved provider/OAuth key.
        return streams[provider](wireModel, context, {
          ...options,
          apiKey: key,
          headers: Object.fromEntries(headers),
        });
      },
    });
  }
}
