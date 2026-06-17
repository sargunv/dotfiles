# Web apps

## TypeSpec

For cross-language full stack apps. The formatter doesn't support stdin/out, so
use `hk`:

```pkl
["tsp-format"] {
  glob = List("api/**/*.tsp")
  check = "cd api && pnpm exec tsp format . --check"
  fix = "cd api && pnpm exec tsp format ."
}
```

Backend codegen from OpenAPI — [ogen-go](https://github.com/ogen-go/ogen) for
Go. Client — [openapi-typescript](https://openapi-ts.dev/) + TanStack Query in
`lib/queries.ts`.

## tRPC

Types from the tRPC router — no OpenAPI codegen. See
[tRPC](https://trpc.io/docs/server/introduction).

## React UI

Vite + vite-plus, Tailwind v4, daisyUI v5, TanStack Router, TanStack Query,
valibot, Radix UI, Ark UI.

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
  root: ":root";
}
```

```
src/ui/          # primitives
src/components/
src/routes/
src/lib/         # queries, mutations, hooks
```

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    host: true,
    proxy: { "/api": "http://localhost:8080" },
  },
});
```
