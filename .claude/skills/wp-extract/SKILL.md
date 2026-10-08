---
name: wp-extract
description: Rebuild the site's content and media from the live WordPress (bootstrap after git clone, or delta updates while WordPress is still live). Thin wrapper over the scripts in tools/wp — the same commands work on wmcloud, where Claude skills do not exist.
---

# wp-extract (wrapper)

All logic lives in the repository (`tools/wp/`), so everything below also works on wmcloud without skills.
Run from the repository root:

```bash
tools/wp/wp help        # all commands
tools/wp/wp bootstrap   # first time after git clone: extract → baseline → import → media
tools/wp/wp update      # later: re-extract + DRY-RUN delta import (read import/report.md)
tools/wp/wp import --apply && tools/wp/wp media
```
Docs: `tools/wp/README.md` (setup, wmcloud, backups, troubleshooting) and `import/README.md` (delta rules, conflicts, exclusions).

## How to use this skill
- Always dry-run first (`wp update` / `wp import`), show the user `import/report.md`, and ask before `--apply` when there are conflicts.
- Never run anything that overwrites `content/` wholesale; the importer only creates new pages, updates pages untouched locally, and queues conflicts in `import/conflicts/`.
- Content and media are **not on GitHub**: remind the user to run `tools/wp/wp backup` (edits made in the site's editor exist only on that machine).
- Check free disk space first (`bootstrap` needs ~3.5 GB; the root partition of this PC is nearly full — keep scratch on /home).

## Extraction notes (for changing the tools)
- REST API first (`/wp-json/wp/v2/…`); scrape HTML only where REST lacks data (menus when 401, theme-built grids).
- JS-driven grids: the data is usually a custom post type whose key fields (ACF/meta) REST does not expose; match by title, take the missing fields from the rendered HTML, store them in `data/*.json`, replace the page body with a directive, and protect the page with `import/exclude.json`.
- Polite crawl: ≥ 0.2 s between requests, descriptive User-Agent, retries with backoff.
- Tests: `tools/wp/wp test` (no network).
