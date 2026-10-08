# Importing WordPress changes (delta import)

`content/` is the source of truth now (edited in the site's editor, committed to git). WordPress changes still arrive
through the same two steps as the first import, but they are **merged**, never overwritten.

## Routine
```bash
# 1+2. Pull the live WordPress again and look first (dry run: writes import/report.md, changes nothing)
tools/wp/wp update
# 3. Apply, then fetch the images the changed pages need
tools/wp/wp import --apply
tools/wp/wp media
# 4. Resolve conflicts one by one (see below). Content is not on GitHub: run tools/wp/wp backup
```

## How a page is classified
Pages are matched by their WordPress **`id`** (frontmatter), so pages you moved in the editor are still found.
`import/state.json` (local to each machine, not in git) remembers what was imported last (a hash of its meaning, not its formatting).

| WordPress | Local | Result |
|---|---|---|
| same | same | unchanged |
| changed | untouched | **updated**, at the page's *current* local path (old file saved in `import/backup/`) |
| same | edited | left alone |
| changed | edited | **conflict**: nothing overwritten; the WordPress version and a diff go to `import/conflicts/` |
| new | — | **created** (if its address is taken by another page: conflict) |
| gone | untouched | reported; trashed only with `--delete-removed` |
| — | deleted by you | not re-imported |

Reformatting by the editor (quotes, YAML style, whitespace, the `slug` that follows a move) is **not** an edit.

## Exclusion list — pages restructured by hand
`import/exclude.json` (matched by WordPress id, so moves cannot unprotect a page). Currently: the home page,
`/comunidad-en-expansion`, `/wikiaccion-peru-en-medios`.
```bash
tools/wp/wp import exclude /some/page "why it is protected"
tools/wp/wp import include /some/page
```

## Resolving a conflict
Open `import/conflicts/<id>__<page>.diff`, merge what you want into the page in the editor, then either
`tools/wp/wp import keep /page` (keep local, mark the WordPress version as seen) or
`tools/wp/wp import take /page` (overwrite local with the WordPress version).

## Also handled / not handled
- Media are fetched by `tools/wp/wp media` (only what pages use, shrunk to 1024 px) under sanitised names; `state.json` remembers the original WordPress name of each.
- New taxonomy terms are added; `data/routes.json` and `data/taxonomy-index.json` are rebuilt from the real content (`tools/wp/wp reindex` does only that).
- **By hand:** a new «nota» (press) item needs its external link in `data/medios.json`, a new partner may need adding to `data/partners-featured.json`; the menu is never imported (it is edited in /admin/menu).
- Known dead or renamed internal links are repaired from `import/link-fixes.json` (add entries there).
- The first baseline is made by `tools/wp/wp bootstrap` (see tools/wp/README.md).
