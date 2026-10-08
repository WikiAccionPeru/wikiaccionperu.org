# WikiAcción Perú — site

Nuxt 4 static site (Markdown content, Wikimedia-login editor for a list of admins) that replaces the WordPress at wikiaccionperu.org.

```bash
npm ci
npm run dev            # sample site (45 pages, ~120 images) — no WordPress access needed
npm run dev:oauth      # same, on :8079 for the Wikimedia login (credentials in .env, see .env.example)
tools/wp/wp bootstrap  # rebuild ALL pages and images from WordPress (once, ~30–40 min)
npm run generate       # static build → .output/public
```

GitHub holds code + settings + a small sample; content and media are rebuilt from WordPress on each machine.
**Read [tools/wp/README.md](tools/wp/README.md)** (clone → wmcloud, updates, backups) and [import/README.md](import/README.md) (delta rules).

Tests: `tools/wp/wp test` (tools, no network) · with a dev server running: `node scripts/test-admin.mjs <url>` (admin UI), `node scripts/test-styleguide.mjs <url>` (styleguide).
**Styleguide rule:** `/styleguide/` shows the design tokens and *every* component in a bounded frame. A new component or token is not done until it has an entry there; `test-styleguide.mjs` fails otherwise (and if any demo is oversized or throws).
Node: `nvm use` (see `.nvmrc`). Don't run `nuxt generate` while a dev server is running (content database lock).
