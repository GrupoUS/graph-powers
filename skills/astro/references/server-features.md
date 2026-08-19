# Astro Server Features — endpoints, middleware, on-demand rendering

Astro mechanics for server-rendered surfaces. Tenancy, PII and data-protection rules do **not** live
here — see `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` items 9 and 12, plus the project's own
rules in `${rulesDir}/`.

## On-demand rendering (per route)

Static is the global default (`output: "hybrid"` has not existed since Astro 5). A route becomes server-rendered by declaring:

```astro
---
export const prerender = false;
---
```

This requires an adapter. **Which routes are allowed to declare it is the project's decision, not
this skill's** — read the project's own route doctrine in `${rulesDir}/` before flipping a route to
either side. Many projects keep the set deliberately small and treat the rest as a hard static
floor.

**The invariant for a new server route:** update the sitemap filter and the indexing policy in the same change. A server route that leaks into the sitemap is indexed content nobody meant to publish.

## API endpoints

A `.ts` file under the pages directory exporting HTTP handlers:

```ts
// <pages>/api/items.ts
import type { APIRoute } from "astro";

export const prerender = false;

export const POST: APIRoute = async ({ request, locals }) => {
  const body = await request.json();
  // validate with a schema; take identity ONLY from locals, never from the body or query string
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};
```

- One export per method (`GET`, `POST`, …); `ALL` as the fallback.
- Catch-all routes delegate to external handlers — the common shape is `<pages>/api/<domain>/[...all].ts` passing `request` straight to a library's handler.
- On static routes, `GET` runs at build time and produces a static file.

## Middleware + `Astro.locals`

```ts
// <src>/middleware.ts
import { defineMiddleware } from "astro:middleware";

export const onRequest = defineMiddleware(async (context, next) => {
  // resolve the session/user and expose it through typed locals (env.d.ts / App.Locals)
  context.locals.user = await resolveUser(context.request);
  return next();
});
```

- Runs on every request served by the adapter — and at build time for static pages, so guard side effects.
- `locals` is the single source of identity in routes (`locals.user`); type it through `App.Locals`.
- Chaining middleware: `sequence()` from `astro:middleware`.

## `astro:env` — typed environment variables

```js
// astro.config.mjs
import { envField } from "astro/config";
export default defineConfig({
  env: {
    schema: {
      DATABASE_URL: envField.string({ context: "server", access: "secret" }),
    },
  },
});
```

```ts
import { DATABASE_URL } from "astro:env/server";
```

Stable since 5.0. Validates at build/start and separates client from server, secret from public. Better than raw `import.meta.env`, which in 6 is inlined with no type coercion.

## Astro Actions

Type-safe RPC between client and server (stable since 5.0):

```ts
// <src>/actions/index.ts
import { defineAction } from "astro:actions";
import { z } from "astro/zod";

export const server = {
  subscribe: defineAction({
    input: z.object({ email: z.email() }),
    handler: async (input, context) => ({ ok: true }),
  }),
};
```

Client: `import { actions } from "astro:actions"; await actions.subscribe({ email })`. Built-in Zod validation and typed errors (`ActionError`). Where a project already has REST endpoints doing this job, adopt Actions only on a new surface, with approval — two ways to call the server is one too many.

## Sessions

Per-user state on server routes (`Astro.session.get/set`). Astro 6 configures it through the `sessionDrivers` object (the string driver is deprecated; the `test` driver was removed). If the project's auth library already owns the session, do not run `Astro.session` alongside it.

## CSP (stable in 6.0)

```js
export default defineConfig({ csp: true });
```

Generates hashes for inline scripts and styles; a per-page runtime API through `Astro`/`APIContext` (`insertDirective`, `insertScriptHash`, …) that merges and de-duplicates against the config. Responsive images in 6 already emit CSP-safe styles (`data-*` plus a hash class). Turning it on means editing `astro.config.mjs` — usually a protected file, so ask first.

## Live Content Collections (stable in 6.0)

`defineLiveCollection` plus a live loader → `getLiveCollection`/`getLiveEntry` fetch **at runtime** on server routes, with no rebuild. Useful for data that changes per request; build-time collections stay the default for versioned content.

## Adapter majors — worked example: `@astrojs/vercel` v10

Adapters move on their own release cadence, and an Astro major usually forces a new adapter major.
The v10 changes below are illustrative of the kind of break to expect; check the release notes for
whichever adapter the project actually uses.


- Import from the root: `import vercel from "@astrojs/vercel"` (the `/serverless` and `/static` subpaths were removed).
- Static by default, with `prerender = false` per page — the usual shape when only part of a site needs a server.
- `edgeMiddleware: true` deprecated → `middlewareMode: "edge"`.
- Requires Node 22.12+. Astro 7 will need a new adapter major.

## Container API (experimental)

Isolated rendering of Astro components in tests. Still experimental as of 2026 — do not build a suite on it.
