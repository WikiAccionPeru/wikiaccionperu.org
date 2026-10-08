# Security checklist (login, admin API, editor)
- OAuth 2.0 auth-code + PKCE with `state`; callback validates `state`; tokens never sent to the browser; session = signed httpOnly, SameSite=Lax, Secure cookie; CSRF token (or SameSite + Origin check) on all POST/PUT/DELETE.
- Admin = session user id ∈ ids in `admins.md`. Re-read the file on each request (small, cached by mtime). Anyone who can push to the repo can change `admins.md`: enable branch protection + CODEOWNERS on it.
- Write routes: allowlist roots (`content/`, `data/menu.json`, `admins.md`), reject `..`, encoded dots, absolute paths, dot-folders; new/moved addresses must match `[a-z0-9-]` words (≤ 4 levels, reserved names refused); max body size; (still to add: rate limit per user).
- A save that would remove the saving editor from the editor list is refused (no lockout); menu links must be `/path` or `https://…` (no `javascript:`).
- Render Markdown with raw HTML disabled except allowlisted MDC components; sanitize any HTML in preview.
- `.env` never committed; secrets only in `.env` on the server. Tool scripts run `git`/shell only with fixed argv (no string commands); imports take a lock file.
- Log who changed what: `[admin] <user> saved|created|moved|deleted …` lines in the server log (content is not in git, so keep `tools/wp/wp backup`).
