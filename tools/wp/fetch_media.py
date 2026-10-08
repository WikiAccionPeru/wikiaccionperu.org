#!/usr/bin/env python3
"""Fetch the media that pages actually use, straight from WordPress, shrinking images while they arrive.

  fetch_media.py [--max-width 1024] [--dry-run] [--limit N] [--workers 4] [--strict]

What is "used": every /media/… reference in content/**/*.md, data/*.json and app/ sources, plus the featured image
of every page. Files already in public/media are left alone (so a re-run only fetches what is new/missing).
The full-size originals are never stored: ~1 GB of 1024-px files instead of ~2 GB+ of originals.
"""
import argparse, errno, io, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, unquote

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from wpimport import indexes, transform as T  # noqa: E402

UA = "wikiaccionperu-tools/1.0 (media fetch for the site owner)"
RASTER = (".jpg", ".jpeg", ".png", ".webp")


def config():
    c = json.loads((HERE / "config.json").read_text()) if (HERE / "config.json").exists() else {}
    c["source_url"] = os.environ.get("WP_SOURCE_URL", c.get("source_url", "https://wikiaccionperu.org")).rstrip("/")
    return c


def referenced(root):
    refs = set()
    text = []
    for route, f, fm in indexes.local_pages(root / "content"):
        text.append(f.read_text(encoding="utf-8"))
    for f in (root / "data").glob("*.json"):
        if f.name not in ("media-index.json", "taxonomy-index.json", "routes.json"):
            text.append(f.read_text(encoding="utf-8"))
    for f in [*(root / "app").rglob("*"), root / "nuxt.config.ts"]:
        if f.is_file() and f.suffix in (".vue", ".ts"):
            text.append(f.read_text(encoding="utf-8"))
    for t in text:
        refs |= {unquote(m) for m in re.findall(r"/media/([\w.%~/-]+\.[A-Za-z0-9]{2,5})", t)}
    mi = {}
    try:
        mi = json.loads((root / "data" / "media-index.json").read_text())
    except (OSError, ValueError):
        pass
    for route, f, fm in indexes.local_pages(root / "content"):
        fid = fm.get("featured_media")
        if fid and str(fid) in mi:
            refs.add(mi[str(fid)][len("/media/"):])
    return refs


def shrink(data, name, max_w):
    if not name.lower().endswith(RASTER):
        return data
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(data))
        if getattr(im, "is_animated", False) or max(im.size) <= max_w:
            return data
        fmt = im.format
        from PIL import ImageOps
        im = ImageOps.exif_transpose(im)
        im.thumbnail((max_w, max_w), Image.LANCZOS)
        out = io.BytesIO()
        kw = {"quality": 85, "optimize": True} if fmt == "JPEG" else {"optimize": True}
        if fmt == "JPEG" and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.save(out, format=fmt, **kw)
        return out.getvalue() if out.tell() < len(data) else data
    except Exception:
        return data  # not decodable: keep the original bytes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default=str(ROOT))
    ap.add_argument("--extract", default=str(Path(os.environ.get("WP_VAR_DIR", ROOT / "var")) / "extract"))
    ap.add_argument("--max-width", type=int, default=config().get("max_image_width", 1024))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--strict", action="store_true", help="exit 2 if any file could not be fetched")
    a = ap.parse_args()
    root, ex, base = Path(a.site), Path(a.extract), config()["source_url"]
    state = {}
    try:
        state = json.loads((root / "import" / "state.json").read_text())
    except (OSError, ValueError):
        pass
    renames = dict(state.get("renames", {}))
    # sanitised name -> original WordPress path (names that were never changed map to themselves)
    inverse = {v: k for k, v in renames.items()}
    # also learn originals from the media library listing, when an extract is at hand
    raw = []
    try:
        raw = json.loads((ex / "raw" / "media.json").read_text())
    except (OSError, ValueError):
        pass
    mark = "/wp-content/uploads/"
    for m in raw:
        if mark in m.get("source_url", ""):
            o = unquote(m["source_url"].split(mark, 1)[1])
            inverse.setdefault(renames.get(o) or T.safe_rel(o), o)

    todo = sorted(r for r in referenced(root) if not (root / "public" / "media" / r).exists())
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(todo)} referenced media file(s) missing from public/media" + (" (dry run)" if a.dry_run else ""))
    if a.dry_run or not todo:
        for r in todo[:10]: print("  ", r)
        return

    sess = requests.Session()
    sess.headers["User-Agent"] = UA
    stats = {"ok": 0, "bytes_in": 0, "bytes_out": 0, "failed": [], "disk_full": False}

    def work(rel):
        if stats["disk_full"]:
            return
        orig = inverse.get(rel, rel)
        local = ex / "media" / orig
        try:
            if local.is_file():  # an earlier full extraction: no download needed
                data = local.read_bytes()
            else:
                for attempt in range(3):
                    r = sess.get(f"{base}{mark}{quote(orig)}", timeout=60)
                    if r.status_code == 200:
                        data = r.content; break
                    if r.status_code in (404, 410):
                        stats["failed"].append((rel, r.status_code)); return
                    time.sleep(2 ** attempt)
                else:
                    stats["failed"].append((rel, "retries")); return
                time.sleep(0.1)
            out = shrink(data, rel, a.max_width)
            dest = root / "public" / "media" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".part")
            tmp.write_bytes(out); tmp.replace(dest)
            stats["ok"] += 1; stats["bytes_in"] += len(data); stats["bytes_out"] += len(out)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                stats["disk_full"] = True  # stop everything: continuing would only fill the disk with partial files
            stats["failed"].append((rel, "disk full" if e.errno == errno.ENOSPC else type(e).__name__))
        except Exception as e:  # network problem: report, keep going
            stats["failed"].append((rel, type(e).__name__))

    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as pool:
        for i, _ in enumerate(pool.map(work, todo), 1):
            if i % 200 == 0:
                print(f"  {i}/{len(todo)}", flush=True)
    for part in (root / "public" / "media").rglob("*.part"):
        part.unlink(missing_ok=True)
    if stats["disk_full"]:
        print("STOPPED: the disk is full. Free some space and run `wp media` again (it continues where it stopped).")
        sys.exit(4)
    print(f"fetched {stats['ok']} file(s): {stats['bytes_in'] / 1e6:.0f} MB downloaded -> {stats['bytes_out'] / 1e6:.0f} MB stored")
    if stats["failed"]:
        print(f"{len(stats['failed'])} could not be fetched (dead on WordPress too, or network error):")
        for rel, why in stats["failed"][:15]:
            print(f"   {why}  {rel}")
        if len(stats["failed"]) > 15: print("   …")
        if a.strict: sys.exit(2)


if __name__ == "__main__":
    main()
