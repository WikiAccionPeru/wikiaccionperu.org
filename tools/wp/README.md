# tools/wp — rebuild the site's data from WordPress

GitHub holds **code, settings and a small sample** (45 pages, ~120 images). The rest of the content and all media are
rebuilt from the live WordPress on each machine, with plain scripts (no Claude skills needed). Everything goes through one command:

```bash
tools/wp/wp help          # (also: npm run wp -- help)
```

Needs: `git`, `python3` + `python3-venv` (Debian/Ubuntu: `sudo apt install python3-venv`), Node 22 for the site itself. Outbound HTTPS to the WordPress site.

## 1. After `git clone` (PC or wmcloud)

**Just look at the sample site** (seconds, no WordPress access needed):
```bash
npm ci && npm run dev          # `predev` seeds the generated data files from tools/wp/seed-data
```

**Rebuild the whole site from WordPress** (once, ~30–40 min, mostly images):
```bash
tools/wp/wp bootstrap          # setup → extract → baseline → import every page → fetch media
npm run generate               # static build → .output/public
tools/wp/wp backup             # see "Backups" — edits made on the server exist ONLY there
```
`bootstrap` is safe to interrupt and re-run the individual steps (`extract`, `import --apply`, `media`).
It refuses to run twice (use `update` afterwards, or `bootstrap --again` to redo the baseline).

What it does, step by step:

| Step | Command | Result |
|---|---|---|
| 1 | `wp extract` | `var/extract/`: every page, taxonomy and media *listing* from the WordPress REST API (content only, ~3 min) |
| 2 | `wp import --init` | baseline in `import/state.json`; the committed sample pages are adopted, the 3 hand-restructured pages (home, community, press) are protected by `import/exclude.json` |
| 3 | `wp import --apply` | creates the ~375 other pages in `content/`, builds `data/taxonomies.json`, `data/media-index.json`, `data/routes.json`, `data/taxonomy-index.json` |
| 4 | `wp media` | downloads only the images/PDFs that pages use, shrinking images to 1024 px as they arrive (originals are never stored) |

## 2. While WordPress is still live (delta)

```bash
tools/wp/wp update                 # re-extract + DRY RUN; read import/report.md; changes nothing
tools/wp/wp import --apply         # apply: new pages created, untouched pages updated, conflicts queued
tools/wp/wp media                  # fetch images the new/updated pages need
tools/wp/wp backup                 # before/after, your call
```
Rules, conflict handling and the exclusion list: **[import/README.md](../../import/README.md)**.
Run it when nobody is editing (a lock file stops two imports at once, but not an editor save in the same second).
`wp import --apply --fail-on-conflict` exits 3 if conflicts remain — handy in cron.

A cron/systemd timer may run `wp update` (dry run only) daily and mail `import/report.md`; applying stays a human decision.

## 3. Backups — important
`content/` and `data/` are **not on GitHub**, so pages edited in the site's editor exist only on that machine.
`wp backup` writes `var/backups/wp-YYYYmmdd-HHMMSS.tgz` (content, data, import state, admins.md; keeps 14). Suggested cron on wmcloud:
```
17 3 * * *  cd /srv/wikiaccion/site && tools/wp/wp backup >/dev/null
```
Copy `var/backups/` off the VM (or into a private repo/bucket) at least weekly.

## 4. Changing what is committed (the sample)
`tools/wp/sample.json` lists exactly the committed pages, media and data; `.gitignore` is generated from it.
After reshaping the main pages, on a machine with the full site:
```bash
python3 tools/wp/sample.py --media      # recompute list + .gitignore block + seed-data; recompress sample images (800 px)
git add -A && git status                # review, then commit
```
Committed sample = menu targets + footer link + home + press/community pages + the newest 9 news/resources/partners (page 1 of each
listing) + the home carousel partners + the images they use. Hand-edited data kept in git: `data/menu.json`, `data/medios.json`,
`data/partners-featured.json`, `data/redirects.json`. Generated data (`routes`, `taxonomies`, `taxonomy-index`, `media-index`) is **not** committed.

## 5. Layout
```
tools/wp/  wp (entry) extract.py import_delta.py fetch_media.py sample.py ensure-data.mjs wpimport/ seed-data/ config.json requirements.txt sample.json
import/    exclude.json link-fixes.json README.md   (committed)   state.json report.md conflicts/ backup/   (local)
var/       .venv  extract/  backups/  import.lock                (local, ignored; override with WP_VAR_DIR)
```
Config: `tools/wp/config.json` (`source_url`, `max_image_width`), env `WP_SOURCE_URL`, `WP_VAR_DIR`.

## 6. Troubleshooting
| Symptom | Fix |
|---|---|
| `python3-venv is missing` | `sudo apt install python3-venv`, re-run |
| `another import is running` | a previous run crashed: delete `var/import.lock` |
| `no baseline yet` | run `wp bootstrap` (first time) |
| Some images 404 in `wp media` | they are dead on WordPress too (listed at the end); fix or drop the link in the page |
| `wp media` slow | normal: ~1,500 files; re-run is incremental. `--workers 8` speeds it up |
| Page differs from WordPress and you want WordPress's version | `wp import take /path` |
| Tests | `wp test` (no network) |
