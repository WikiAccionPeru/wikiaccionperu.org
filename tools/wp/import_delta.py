#!/usr/bin/env python3
"""Delta importer: bring WordPress changes (a fresh var/extract) into content/ without clobbering local work.

  import-delta.py                    dry run: classify every page and write import/report.md (changes nothing else)
  import-delta.py --apply            write new pages, update untouched ones, queue conflicts
  import-delta.py --init             adopt the current state as the baseline (run ONCE, before re-extracting WordPress)
  import-delta.py exclude PATH [WHY] never import this page again (restructured by hand)
  import-delta.py include PATH       remove it from the exclusion list
  import-delta.py take PATH          overwrite the local page with the WordPress version (resolves a conflict)
  import-delta.py keep PATH          keep the local page and mark the current WordPress version as seen
  import-delta.py reindex            rebuild data/routes.json and data/taxonomy-index.json from the real content

Pages are matched by their WordPress `id` (frontmatter), not by path, so pages moved in the editor stay matched.
Per page, comparing three versions — baseline (last imported), WordPress (now), local (now):
  WP same,    local same     -> unchanged
  WP changed, local same     -> UPDATE (applied with --apply, at the page's current local path)
  WP same,    local changed  -> local-only edit (left alone)
  WP changed, local changed  -> CONFLICT (never overwritten; WP version + diff go to import/conflicts/)
Options: --extract DIR --site DIR (testing), --delete-removed (trash pages deleted in WordPress and untouched locally).
"""
import argparse, difflib, json, os, re, shutil, sys, time
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from wpimport import transform as T  # noqa: E402
from wpimport import indexes  # noqa: E402

DEFAULT_EXCLUDES = [
    {"path": "/", "reason": "Rebuilt as data-driven home (frontmatter `home`) with editable sections"},
    {"path": "/comunidad-en-expansion", "reason": "Rebuilt with ::split-hero / ::centered-block directives"},
    {"path": "/wikiaccion-peru-en-medios", "reason": "JS grid replaced by ::media-mentions + data/medios.json"},
]


def jload(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def jsave(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


class Site:
    def __init__(self, root, extract):
        self.root, self.ex = Path(root), Path(extract)
        self.content, self.imp = self.root / "content", self.root / "import"
        self.state = jload(self.imp / "state.json", {"version": 1, "items": {}, "renames": {}})
        self.exclude = jload(self.imp / "exclude.json", {"items": []})
        self.link_fixes = jload(self.imp / "link-fixes.json", {})
        self.renames = T.compute_renames(self.ex / "media", self.state.get("renames"))

    # -- extract side ------------------------------------------------------------------------------------------
    def extract_items(self):
        items = {}
        for f in sorted((self.ex / "content").rglob("index.md")):
            rel = f.parent.relative_to(self.ex / "content").as_posix()
            text = f.read_text(encoding="utf-8")
            fm = T.frontmatter(text)
            if not fm.get("id"):
                continue
            for ref in re.findall(r"\]\(/media/([^)\s\"?]+)", T.split_doc(text)[1]):
                orig = unquote(ref)
                safe = T.safe_rel(orig)
                if safe != orig and orig not in self.renames:
                    self.renames[orig] = safe  # remembered in state.json: the media fetcher needs the original WordPress name
            imported = T.transform_text(text, self.renames, self.link_fixes)
            items[str(fm["id"])] = {"id": str(fm["id"]), "rel": rel, "route": "/" if rel == "index" else "/" + rel, "fm": fm, "text": imported, "hash": T.sem_hash(imported)}
        return items

    # -- local side ---------------------------------------------------------------------------------------------
    def local_items(self):
        out = {}
        for route, f, fm in indexes.local_pages(self.content):
            text = f.read_text(encoding="utf-8")
            out[str(fm.get("id", "")) or f"path:{route}"] = {"route": route, "file": f, "text": text, "hash": T.sem_hash(text), "fm": fm}
        return out

    def dest_for(self, rel):
        return self.content / ("index.md" if rel == "index" else f"{rel}.md")

    def excluded(self, item):
        for e in self.exclude["items"]:
            if (e.get("id") and str(e["id"]) == item["id"]) or e.get("path") in (item["route"],):
                return e
        return None


def classify(site):
    ex, loc = site.extract_items(), site.local_items()
    st = site.state["items"]
    r = {k: [] for k in ["new", "update", "conflict", "local_only", "unchanged", "excluded", "deleted_locally", "deleted_in_wp", "converged", "adopted"]}
    for id_, it in ex.items():
        e = site.excluded(it)
        if e:
            r["excluded"].append({"item": it, "why": e.get("reason", "")})
            continue
        l = loc.get(id_)
        if not l:
            if id_ in st:
                r["deleted_locally"].append({"item": it})
            else:
                dest = site.dest_for(it["rel"])
                occupied = dest.exists()
                (r["conflict"] if occupied else r["new"]).append({"item": it, "dest": dest, "kind": "path-occupied" if occupied else "new"})
            continue
        base = st.get(id_, {}).get("hash")
        if base is None:
            (r["adopted"] if l["hash"] == it["hash"] else r["conflict"]).append({"item": it, "local": l, "kind": "unknown-history"})
            continue
        wp_changed, local_changed = it["hash"] != base, l["hash"] != base
        if wp_changed and local_changed and l["hash"] == it["hash"]:
            r["converged"].append({"item": it, "local": l})
        elif wp_changed and local_changed:
            r["conflict"].append({"item": it, "local": l, "kind": "both-changed"})
        elif wp_changed:
            r["update"].append({"item": it, "local": l})
        elif local_changed:
            r["local_only"].append({"item": it, "local": l})
        else:
            r["unchanged"].append({"item": it, "local": l})
    for id_, s in st.items():
        if id_ not in ex and id_ in loc and not site.excluded({"id": id_, "route": loc[id_]["route"]}):
            r["deleted_in_wp"].append({"id": id_, "local": loc[id_], "unchanged_locally": loc[id_]["hash"] == s["hash"]})
    return r, ex, loc


def html_text(s):
    return re.sub(r"<[^>]+>|&[#\w]+;", "", s)


def title(it):
    return str(it["fm"].get("title", it["route"]))


def write_report(site, r, applied, notes):
    L = [f"# Import report — {time.strftime('%Y-%m-%d %H:%M')} — {'APPLIED' if applied else 'dry run (nothing written)'}", ""]
    L.append("| Class | Pages |\n|---|---|")
    for k, label in [("new", "New in WordPress"), ("update", "Updated in WordPress, untouched locally"), ("conflict", "CONFLICT (needs a human)"), ("local_only", "Edited locally only"), ("converged", "Same change on both sides"), ("unchanged", "Unchanged"), ("excluded", "Excluded (restructured)"), ("deleted_locally", "Deleted locally"), ("deleted_in_wp", "Deleted in WordPress"), ("adopted", "Adopted")]:
        L.append(f"| {label} | {len(r[k])} |")
    def section(name, rows, fmt):
        if rows:
            L.extend(["", f"## {name}", *[f"- {fmt(x)}" for x in rows]])
    section("New", r["new"], lambda x: f"{x['item']['route']} — {title(x['item'])}")
    section("Will be updated" if not applied else "Updated", r["update"], lambda x: f"{x['local']['route']} — {title(x['item'])}")
    section("Conflicts (resolve with `take PATH` or `keep PATH`; WP version and diff in import/conflicts/)", r["conflict"], lambda x: f"{x.get('local', {}).get('route', x['item']['route'])} — {x['kind']}")
    section("Edited locally only (not touched)", r["local_only"], lambda x: f"{x['local']['route']} — {title(x['item'])}")
    section("Excluded", r["excluded"], lambda x: f"{x['item']['route']} — {x['why']}")
    section("Deleted locally (not re-imported)", r["deleted_locally"], lambda x: f"{x['item']['route']}")
    section("Deleted in WordPress (kept locally unless --delete-removed)", r["deleted_in_wp"], lambda x: f"{x['local']['route']} ({'untouched locally' if x['unchanged_locally'] else 'edited locally'})")
    if notes:
        L.extend(["", "## To do by hand", *[f"- {n}" for n in notes]])
    (site.imp).mkdir(exist_ok=True)
    (site.imp / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def notes_for(r, site):
    notes = []
    first_run = not site.state.get("last_apply")  # bootstrap: everything is "new"; curated data already covers the known items
    known = {re.sub(r"\W+", "", str(m.get("title", "")).lower()) for m in jload(site.root / "data" / "medios.json", [])}
    news = [x for x in r["new"] if x["item"]["fm"].get("type") == "nota" and re.sub(r"\W+", "", html_text(title(x["item"])).lower()) not in known]
    if news:
        notes.append(f"{len(news)} «nota» (press) item(s) not in data/medios.json: add their external links there (WordPress does not expose that field): " + ", ".join(title(x['item']) for x in news))
    al = [x for x in r["new"] if x["item"]["fm"].get("type") == "alianza"]
    if al and not first_run:
        notes.append(f"{len(al)} new partner page(s) created; add to data/partners-featured.json if they should appear in the home carousel.")
    # media referenced by new/updated pages but absent from public/media
    missing = set()
    for x in r["new"] + r["update"]:
        for ref in re.findall(r"\]\((/media/[^)\s\"]+)", x["item"]["text"]):
            from urllib.parse import unquote
            if not (site.root / "public" / unquote(ref).lstrip("/")).exists():
                missing.add(ref)
    if missing:
        notes.append(f"{len(missing)} media file(s) referenced by imported pages are not in public/media yet (run `wp media`): " + ", ".join(sorted(missing)[:5]) + ("…" if len(missing) > 5 else ""))
    return notes


def sync_media(site, apply):
    """Hardlink (or copy) media from the extract into public/media under their sanitised names; returns how many are new."""
    src_dir, dst_dir = site.ex / "media", site.root / "public" / "media"
    n = 0
    for rel in T.media_files(src_dir):
        dest = dst_dir / site.renames.get(rel, rel)
        if dest.exists():
            continue
        n += 1
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(src_dir / rel, dest)
            except OSError:
                shutil.copy2(src_dir / rel, dest)
    if apply:
        write_media_index(site)
    return n


def write_media_index(site):
    """id -> /media/<name>, from the WordPress media library listing (raw/media.json): no downloaded files needed."""
    raw = jload(site.ex / "raw" / "media.json", None)
    if not raw:
        return
    mark = "/wp-content/uploads/"
    idx = {str(m["id"]): "/media/" + (site.renames.get(rel := unquote(m["source_url"].split(mark, 1)[1])) or T.safe_rel(rel)) for m in raw if mark in m.get("source_url", "")}
    f = site.root / "data" / "media-index.json"
    old = jload(f, {})
    jsave(f, {**old, **idx})


def merge_taxonomies(site):
    """data/taxonomies.json: built from the extract when absent; otherwise new terms are added (existing prefix/types/names kept)."""
    from urllib.parse import urlparse
    f = site.root / "data" / "taxonomies.json"
    tax = jload(f, {})
    sj = jload(site.ex / "site.json", {"taxonomies": {}})
    added = 0
    for tf in sorted((site.ex / "taxonomies").glob("*.json")) if (site.ex / "taxonomies").is_dir() else []:
        terms = json.loads(tf.read_text())
        if not terms:
            continue
        if tf.stem not in tax:
            tax[tf.stem] = {"prefix": urlparse(terms[0]["link"]).path.strip("/").split("/")[0], "types": sj["taxonomies"].get(tf.stem, {}).get("types", []), "terms": []}
        have = {t["slug"]: t for t in tax[tf.stem]["terms"]}
        for t in terms:
            if t["slug"] in have:
                have[t["slug"]]["count"] = t["count"]
            else:
                tax[tf.stem]["terms"].append({k: t[k] for k in ("id", "slug", "name", "count", "parent")})
                added += 1
    f.write_text(json.dumps(tax, ensure_ascii=False))
    return added


def set_slug(text, route):
    seg = route.rstrip("/").split("/")[-1] or "home"
    return re.sub(r"^slug:.*$", f'slug: "{seg}"', text, count=1, flags=re.M)


def trash(site, path):
    t = site.content / ".trash"
    t.mkdir(exist_ok=True)
    dest = t / f"{time.strftime('%Y%m%dT%H%M%S')}__{path.relative_to(site.content).as_posix().replace('/', '__')}"
    shutil.move(str(path), str(dest))


def apply_changes(site, r, delete_removed):
    st, ts = site.state["items"], time.strftime("%Y%m%dT%H%M%S")
    backup = site.imp / "backup" / ts
    def record(it):
        st[it["id"]] = {"hash": it["hash"], "wp_modified": it["fm"].get("modified", ""), "type": it["fm"].get("type", ""), "rel": it["rel"]}
    for x in r["new"]:
        x["dest"].parent.mkdir(parents=True, exist_ok=True)
        x["dest"].write_text(x["item"]["text"], encoding="utf-8")
        record(x["item"])
    for x in r["update"]:
        f = x["local"]["file"]
        (backup / f.relative_to(site.content)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, backup / f.relative_to(site.content))
        f.write_text(set_slug(x["item"]["text"], x["local"]["route"]), encoding="utf-8")
        record(x["item"])
    for x in r["converged"] + r["adopted"]:
        record(x["item"])
    (site.imp / "conflicts").mkdir(parents=True, exist_ok=True)
    for x in r["conflict"]:
        it = x["item"]
        stem = f"{it['id']}__{it['route'].strip('/').replace('/', '_') or 'home'}"
        (site.imp / "conflicts" / f"{stem}.wp.md").write_text(it["text"], encoding="utf-8")
        mine = x.get("local", {}).get("text", "")
        (site.imp / "conflicts" / f"{stem}.diff").write_text("".join(difflib.unified_diff(mine.splitlines(True), it["text"].splitlines(True), "local", "wordpress")), encoding="utf-8")
    removed = 0
    if delete_removed:
        for x in r["deleted_in_wp"]:
            if x["unchanged_locally"]:
                trash(site, x["local"]["file"]); st.pop(x["id"], None); removed += 1
    site.state["renames"] = site.renames
    site.state["last_apply"] = ts
    jsave(site.imp / "state.json", site.state)
    return removed


def acquire_lock(site):
    """One apply at a time (and not while another import/bootstrap is running)."""
    lock = Path(os.environ.get("WP_VAR_DIR", site.root / "var")) / "import.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.write(fd, str(os.getpid()).encode()); os.close(fd)
    except FileExistsError:
        sys.exit(f"another import is running (lock {lock}). If it crashed, delete the lock file.")
    return lock


def release_lock(lock):
    try: lock.unlink()
    except OSError: pass


def find_by_path(site, key):
    ex, loc = site.extract_items(), site.local_items()
    key = key if key.startswith("/") or key.isdigit() else "/" + key
    key = "/" + key.strip("/") if key != "/" and not key.isdigit() else key
    for id_, l in loc.items():
        if id_ == key or l["route"] == key:
            return id_, ex.get(id_), l
    for id_, it in ex.items():
        if id_ == key or it["route"] == key:
            return id_, it, loc.get(id_)
    return None, None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="run", choices=["run", "exclude", "include", "take", "keep", "reindex"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--delete-removed", action="store_true")
    ap.add_argument("--fail-on-conflict", action="store_true", help="exit 3 when conflicts remain (for scripts)")
    ap.add_argument("--extract", default=str(Path(os.environ.get("WP_VAR_DIR", ROOT / "var")) / "extract"))
    ap.add_argument("--site", default=str(ROOT))
    a = ap.parse_args()
    site = Site(a.site, a.extract)

    if a.cmd == "reindex":
        print(indexes.rebuild(site.root)); return
    if a.cmd in ("exclude", "include"):
        if not a.args: sys.exit("give a page path, e.g. /comunidad-en-expansion")
        path = "/" + a.args[0].strip("/") if a.args[0] != "/" else "/"
        items = site.exclude["items"]
        _, it, l = find_by_path(site, path)
        wp_id = str((it or {}).get("id") or ((l or {}).get("fm", {}).get("id") or ""))
        items[:] = [e for e in items if e.get("path") != path and (not wp_id or str(e.get("id")) != wp_id)]
        if a.cmd == "exclude":
            items.append({"id": wp_id or None, "path": path, "reason": " ".join(a.args[1:]) or "restructured by hand"})
        jsave(site.imp / "exclude.json", site.exclude); print(f"{a.cmd}d {path}"); return
    if a.cmd in ("take", "keep"):
        id_, it, l = find_by_path(site, a.args[0] if a.args else "")
        if not it: sys.exit("page not found in the extract")
        if a.cmd == "take":
            if not l: sys.exit("no local page to overwrite")
            (site.imp / "backup").mkdir(parents=True, exist_ok=True)
            shutil.copy2(l["file"], site.imp / "backup" / f"{time.strftime('%Y%m%dT%H%M%S')}__{l['file'].name}")
            l["file"].write_text(set_slug(it["text"], l["route"]), encoding="utf-8")
        site.state["items"][id_] = {"hash": it["hash"], "wp_modified": it["fm"].get("modified", ""), "type": it["fm"].get("type", ""), "rel": it["rel"]}
        site.state["renames"] = site.renames; jsave(site.imp / "state.json", site.state); print(f"{a.cmd}: {l['route'] if l else it['route']}"); return

    if not (site.ex / "content").is_dir(): sys.exit(f"no extract at {site.ex}")
    if a.init:
        if not site.exclude["items"]:
            site.exclude["items"] = [dict(e) for e in DEFAULT_EXCLUDES]
            jsave(site.imp / "exclude.json", site.exclude)
        ex, loc = site.extract_items(), site.local_items()
        site.state["items"] = {i: {"hash": it["hash"], "wp_modified": it["fm"].get("modified", ""), "type": it["fm"].get("type", ""), "rel": it["rel"]} for i, it in ex.items() if i in loc}
        site.state["renames"] = site.renames
        # resolve excluded paths to ids now, so later moves cannot unprotect them
        for e in site.exclude["items"]:
            for it in ex.values():
                if it["route"] == e.get("path"): e["id"] = it["id"]
        jsave(site.imp / "exclude.json", site.exclude); jsave(site.imp / "state.json", site.state)
        diverged = [loc[i]["route"] for i, it in ex.items() if i in loc and loc[i]["hash"] != it["hash"]]
        print(f"baseline set for {len(site.state['items'])} pages; {len(diverged)} differ from what a fresh import would produce (will be treated as local edits):")
        for d in diverged: print("   ", d)
        return

    if not site.state["items"]: sys.exit("no baseline yet: run `import-delta.py --init` BEFORE re-extracting WordPress")
    r, ex, loc = classify(site)
    notes = notes_for(r, site)
    new_media = sync_media(site, a.apply)
    lock = acquire_lock(site) if a.apply else None
    counts = {k: len(v) for k, v in r.items()}
    if a.apply:
        removed = apply_changes(site, r, a.delete_removed)
        terms = merge_taxonomies(site)
        idx = indexes.rebuild(site.root)
        notes.append(f"{new_media} media file(s) linked; {terms} new taxonomy term(s); {removed} page(s) trashed; indexes rebuilt ({idx['routes']} routes).")
    if lock: release_lock(lock)
    write_report(site, r, a.apply, notes)
    print(("APPLIED " if a.apply else "DRY RUN ") + json.dumps(counts))
    if a.fail_on_conflict and counts["conflict"]:
        print(f"{counts['conflict']} conflict(s): see {site.imp / 'report.md'}"); sys.exit(3)
    if new_media and not a.apply: print(f"{new_media} new media file(s) would be linked")
    for n in notes: print(" •", n)
    print(f"report: {site.imp / 'report.md'}")


if __name__ == "__main__":
    main()
