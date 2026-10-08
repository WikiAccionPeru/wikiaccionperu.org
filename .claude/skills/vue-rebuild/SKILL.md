---
name: vue-rebuild
description: Work on the Nuxt 4 static site that replaces the WordPress at wikiaccionperu.org — components and styleguide, Markdown content with MDC directives, Wikimedia OAuth2 login, the in-browser page editor and admin screens, and deployment to wmcloud. Use when adding or changing site features; for pulling WordPress content use the wp-extract skill.
---

# vue-rebuild

The project is built (it started as stages 2a → 2c below). Content and media are **rebuilt from WordPress on each machine** (`tools/wp/wp bootstrap`, see the wp-extract skill); GitHub holds code, settings and a small sample. Work in small steps; stop for user review after each.

## Stack
Nuxt 4 · Nuxt Content (Markdown + MDC directives) · static generation (`nuxt generate`) · Nitro server routes only for login/admin · `@nuxt/image` (sharp) · `@nuxt/fonts` · CodeMirror 6 · Playwright UI tests · Python tools in `tools/wp`. Node 22 (`nvm use`). Hosting: wmcloud Cloud VPS, build on the server. See `references/`.

## Rules for components
- Atomic structure: `app/components/{atoms,molecules,organisms,content,styleguide}`; design tokens only in `app/assets/tokens.css`; no page-specific CSS.
- Editor-only components are prefixed `Editor…` (EditorMarkdown, EditorPageProperties, EditorPageFieldTree, EditorEditableSection, EditorEditLink, EditorCommonsFileInserter, EditorTermPicker).
- **Styleguide:** `/styleguide/` shows every token and component in a bounded `<SgSpecimen>` frame. A new component or token is not done until it has an entry; `node scripts/test-styleguide.mjs <url>` fails on a missing entry, an oversized demo or any console error.
- Images: use `<NuxtImg>` (width, webp, lazy); thumbnails are generated at build time, never stored.
- Cards/pages mirror the original look (pastel bands, 1px black lines, Source Code Pro + Ubuntu); compare with screenshots of the live site (`scripts/capture.mjs`).

## Content
- MDC directives in `app/components/content/`: `::video-embed`, `::split-hero`, `::centered-block`, `::media-mentions` (reads `data/medios.json`), `::partners-carousel` (reads `data/partners-featured.json`). Planned: `::buttons`, `::columns`, `::gallery`, `::commons-category`, `::article-card`, `::photo-bg`.
- The home page is data-driven (frontmatter `home`) and editable section by section; restructured pages are protected from imports in `import/exclude.json`.
- Listings (news, resources, partners, archives) are generated from frontmatter; drafts (`status: draft`) are hidden from listings and search. Redirects come from `data/redirects.json` (page moves) and `import/link-fixes.json` (dead or renamed links).

## Login and editor
Follow `references/security.md` and `references/editor.md`. Summary: Wikimedia OAuth 2.0 (code + PKCE, credentials in `.env`, see `.env.example`); editors listed in `admins.md` (`rely_on_username: true` → names resolved to ids through the Commons API; otherwise `Username | id`); httpOnly session; **every write route checks the editor server-side** and mutating requests also check the Origin; edit buttons are cosmetic.
Admin screens: `/admin/` (hub), `/admin/pages/` (create, move with redirect, soft-delete), `/admin/menu/`, `/admin/editors/` (+ username → id helper), `/admin/edit/?path=…&section=…` (properties form with closed choices, Markdown body, live preview, Commons image inserter).
The git-sync UI planned originally is **dropped**: content is not in git; use `tools/wp/wp backup`.

## Deploy (wmcloud)
`git pull --ff-only` → `npm ci` → `tools/wp/wp media` (only if pages need new images) → `npm run generate` → atomic symlink swap `current → releases/<sha>`, keep 3 releases (rollback = repoint the symlink). The Nitro server (login/admin API) runs under systemd behind nginx; TLS via the Cloud VPS proxy / Let's Encrypt. Production needs its **own** OAuth consumer (the local one only allows `http://localhost:8079/oauth/wikimedia/success`). Back up `content/`, `data/`, `import/`, `admins.md` with `tools/wp/wp backup` (cron) and copy `var/backups/` off the VM.

## Rules
- Do not invent answers (newsletter provider, missing URLs): leave a clearly marked placeholder and list it in the summary.
- No third-party trackers; CC BY-SA footer; keep dependencies minimal.
- Confirm before anything outward-facing (pushing to GitHub, deploying, changing the server).
- Never commit `.env`, `import/state.json`, `var/`, working content/media; the committed sample is managed by `python3 tools/wp/sample.py`.
- Do not run `nuxt generate` while a dev server is running (content database lock).
