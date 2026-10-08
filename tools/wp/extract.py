#!/usr/bin/env python3
"""wp-extract: extract a WordPress site via its REST API into Markdown + media + JSON.

Usage:
  extract.py probe  <url>
  extract.py run    <url> [--out var/extract] [--no-media]
  extract.py verify [--out extract]
  extract.py downscale [--out extract] [--max 1024] [--dry-run]
"""
import argparse, hashlib, json, re, sys, time
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup, NavigableString, Comment

UA = "wp-extract/1.0 (site migration by owner)"
DELAY = 0.2
S = requests.Session()
S.headers["User-Agent"] = UA
SKIP_TYPES = {"attachment", "wp_block", "wp_template", "wp_template_part", "wp_navigation",
              "wp_font_family", "wp_font_face", "wp_global_styles", "nav_menu_item"}


def get(url, **kw):
    for attempt in range(4):
        try:
            r = S.get(url, timeout=30, **kw)
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            time.sleep(DELAY)
            return r
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None


def api(base, route, **params):
    return get(f"{base}/wp-json/wp/v2/{route}", params=params)


def paginate(base, route, **params):
    items, page = [], 1
    while True:
        r = api(base, route, per_page=100, page=page, **params)
        if r is None or r.status_code != 200:
            break
        data = r.json()
        if not isinstance(data, list) or not data:
            break
        items += data
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    return items


def discover(base):
    types = (api(base, "types").json() or {})
    taxes = (api(base, "taxonomies").json() or {})
    ptypes = {k: v for k, v in types.items() if k not in SKIP_TYPES and v.get("rest_base")}
    return ptypes, taxes


def sitemap_urls(base):
    urls, queue, seen = set(), [f"{base}/wp-sitemap.xml", f"{base}/sitemap.xml"], set()
    while queue:
        u = queue.pop()
        if u in seen:
            continue
        seen.add(u)
        r = get(u)
        if not r or r.status_code != 200:
            continue
        soup = BeautifulSoup(r.text, "xml")
        for sm in soup.find_all("sitemap"):
            queue.append(sm.loc.text.strip())
        for url in soup.find_all("url"):
            urls.add(url.loc.text.strip())
    return urls


# ---------- HTML -> Markdown ----------
class Conv:
    def __init__(self, base, gaps):
        self.base, self.gaps, self.raw_blocks = base, gaps, 0

    def url(self, u):
        if not u:
            return u
        if re.search(r"/wp-content/uploads/", u):
            return "/media/" + resolve(u.split("/wp-content/uploads/", 1)[1].split("?", 1)[0])
        if u.startswith(self.base):
            return u[len(self.base):] or "/"
        return u

    def raw(self, el, why):
        self.raw_blocks += 1
        self.gaps.append(why)
        return f'\n\n<div data-wp-raw="{why}">\n{el}\n</div>\n\n'

    def inline(self, el):
        return "".join(self.node(c, inline=True) for c in el.children).strip()

    def node(self, el, inline=False, depth=0):
        if isinstance(el, Comment):
            return ""
        if isinstance(el, NavigableString):
            return re.sub(r"\s+", " ", str(el)) if inline else str(el).strip()
        n = el.name
        if n in ("script", "style"):
            return self.raw(el, n) if n == "script" else ""
        if n == "object" and el.get("hidden") is not None:
            return ""
        if n == "iframe":
            src, title = el.get("src", ""), el.get("title", "")
            if re.search(r"youtube(-nocookie)?\.com|youtu\.be|vimeo\.com|commons\.wikimedia\.org", src):
                self.gaps.append("embed")  # mapped to a directive, listed for awareness
                return f'\n\n::video-embed{{src="{src}" title="{title}"}}\n\n'
            return self.raw(el, n)
        if n in ("form", "video", "audio", "svg", "button", "select", "input", "object"):
            return self.raw(el, n)
        if n in ("i", "span") and not el.get_text(strip=True) and not el.find("img"):
            return ""  # icon fonts (Font Awesome) carry no content
        if re.fullmatch(r"h[1-6]", n):
            return f"\n\n{'#' * int(n[1])} {self.inline(el)}\n\n"
        if n == "p":
            t = self.inline(el)
            return f"\n\n{t}\n\n" if t else ""
        if n in ("strong", "b"):
            t = self.inline(el)
            return f"**{t}**" if t else ""
        if n in ("em", "i"):
            t = self.inline(el)
            return f"*{t}*" if t else ""
        if n in ("time", "cite", "abbr", "figcaption", "label", "dl", "dt", "dd"):
            return self.inline(el) if inline else f"\n\n{self.inline(el)}\n\n"
        if n == "br":
            return "  \n"
        if n == "hr":
            return "\n\n---\n\n"
        if n == "code":
            return f"`{el.get_text()}`"
        if n == "pre":
            return f"\n\n```\n{el.get_text()}\n```\n\n"
        if n == "a":
            return f"[{self.inline(el) or el.get('href','')}]({self.url(el.get('href',''))})"
        if n == "img":
            src = el.get("data-src") or el.get("src", "")
            return f"![{el.get('alt','')}]({self.url(src)})"
        if n == "blockquote":
            body = "\n".join("> " + l for l in self.children(el).strip().splitlines())
            return f"\n\n{body}\n\n"
        if n in ("ul", "ol"):
            out = []
            for i, li in enumerate(el.find_all("li", recursive=False), 1):
                mark = f"{i}." if n == "ol" else "-"
                body = self.children(li, inline_li=True).strip().replace("\n", "\n" + "  " * (depth + 1))
                out.append("  " * depth + f"{mark} {body}")
            return "\n\n" + "\n".join(out) + "\n\n"
        if n == "figure":
            if el.find(["ul", "li"]) and "gallery" in " ".join(el.get("class", [])):
                self.gaps.append("gallery")
                return self.raw(el, "gallery")
            img, cap = el.find("img"), el.find("figcaption")
            if img and not el.find(["iframe", "video"]):
                alt = img.get("alt", "")
                src = self.url(img.get("data-src") or img.get("src", ""))
                title = f' "{cap.get_text(strip=True)}"' if cap else ""
                return f"\n\n![{alt}]({src}{title})\n\n"
            if el.find("iframe") or el.find("table"):
                return self.children(el)
            u = el.get_text(strip=True)
            if u.startswith("http"):  # WordPress oEmbed of another page
                return f"\n\n[{u}]({self.url(u)})\n\n"
            return self.raw(el, "figure")
        if n == "table":
            rows = [[re.sub(r"\s+", " ", c.get_text(" ", strip=True)).replace("|", "\\|") for c in r.find_all(["th", "td"])]
                    for r in el.find_all("tr")]
            if rows and not el.find(["table"]) and not any(c.get("colspan") or c.get("rowspan") for c in el.find_all(["td", "th"])) \
                    and len({len(r) for r in rows}) == 1:
                head = rows[0] if el.find("th") else [""] * len(rows[0])
                body = rows[1:] if el.find("th") else rows
                lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)] + ["| " + " | ".join(r) + " |" for r in body]
                return "\n\n" + "\n".join(lines) + "\n\n"
            return self.raw(el, "table")
        if n in ("div", "span", "section", "article", "main", "header", "footer", "aside", "li", "center",
                 "small", "u", "mark", "sup", "sub", "details", "summary", "noscript", "font"):
            classes = " ".join(el.get("class", []))
            if n == "div" and re.search(r"wp-block-(columns|buttons|cover|group|gallery|embed)|elementor|et_pb|vc_", classes):
                self.gaps.append("layout:" + (re.search(r"wp-block-[a-z\-]+|elementor|et_pb|vc_", classes).group(0)))
            return self.children(el) if not inline else self.inline(el)
        return self.raw(el, "unknown:" + n)

    def children(self, el, inline_li=False):
        out = "".join(self.node(c, depth=1 if inline_li else 0) for c in el.children)
        return re.sub(r"\n{3,}", "\n\n", out)

    def convert(self, html):
        soup = BeautifulSoup(html or "", "html.parser")
        md = self.children(soup)
        return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


SIZE_RE = re.compile(r"-\d+x\d+(?=\.[A-Za-z0-9]+$)")


def original(path):
    """WordPress resized copy (foo-1024x1024.png) -> original (foo.png)."""
    return SIZE_RE.sub("", path)


ALIAS = {}  # normalised upload path -> real library path (WP "-scaled", "-scaled-1", "-edited" renames)
SCALED_RE = re.compile(r"-scaled(-\d+)?(?=\.[A-Za-z0-9]+$)")


def resolve(path):
    """Content path (maybe a resized copy) -> the library file that really exists."""
    o = original(path)
    return ALIAS.get(o, o)


def yaml_val(v):
    return json.dumps(v, ensure_ascii=False)


def frontmatter(d):
    lines = ["---"] + [f"{k}: {yaml_val(v)}" for k, v in d.items() if v not in (None, "", [], {})] + ["---", ""]
    return "\n".join(lines)


def local_path(base, link):
    p = unquote(urlparse(link).path).strip("/")
    return p or "index"


# ---------- commands ----------
def cmd_probe(a):
    base = a.url.rstrip("/")
    r = get(f"{base}/wp-json/")
    if not r or r.status_code != 200:
        sys.exit("REST API not reachable: fall back to HTML crawling (not implemented in this script).")
    info = r.json()
    print(f"Site: {info.get('name')} | plugins/namespaces: {', '.join(info.get('namespaces', []))}")
    ptypes, taxes = discover(base)
    for k, v in ptypes.items():
        rr = api(base, v["rest_base"], per_page=1)
        print(f"  type {k:12} rest_base={v['rest_base']:12} count={rr.headers.get('X-WP-Total','?') if rr else '?'}")
    for k, v in taxes.items():
        rr = api(base, v["rest_base"], per_page=1)
        print(f"  tax  {k:20} types={v.get('types')} count={rr.headers.get('X-WP-Total','?') if rr else '?'}")
    print(f"  sitemap urls: {len(sitemap_urls(base))}")


def fetch_menus(base, home_html):
    menus = []
    r = api(base, "menus")
    if r is not None and r.status_code == 200:
        for m in r.json():
            items = paginate(base, "menu-items", menus=m["id"])
            menus.append({"id": m["id"], "name": m["name"], "slug": m["slug"], "items": [
                {"id": i["id"], "title": i["title"]["rendered"], "url": i["url"], "parent": i["parent"],
                 "order": i["menu_order"]} for i in items]})
        if menus:
            return menus, "rest"
    soup = BeautifulSoup(home_html, "html.parser")
    for i, nav in enumerate(soup.find_all("nav")):
        items = [{"title": a.get_text(strip=True), "url": a["href"], "depth": len(a.find_parents("ul")) - 1}
                 for a in nav.find_all("a", href=True)]
        if items:
            menus.append({"id": i, "name": nav.get("aria-label") or f"nav-{i}", "items": items})
    return menus, "html-scrape (REST menus require auth)"


def cmd_run(a):
    base, out = a.url.rstrip("/"), Path(a.out)
    for d in ("content", "media", "raw", "taxonomies"):
        (out / d).mkdir(parents=True, exist_ok=True)
    ptypes, taxes = discover(base)
    info = get(f"{base}/wp-json/").json()
    gaps_log, redirects, media_used, report = {}, {}, {}, []

    # taxonomies
    tax_terms = {}
    for tname, t in taxes.items():
        terms = paginate(base, t["rest_base"])
        tax_terms[tname] = {x["id"]: x for x in terms}
        (out / "taxonomies" / f"{tname}.json").write_text(json.dumps(
            [{k: x.get(k) for k in ("id", "slug", "name", "parent", "count", "link", "description")} for x in terms],
            ensure_ascii=False, indent=1))
        report.append(f"taxonomy {tname}: {len(terms)} terms")

    # media library
    media = paginate(base, "media")
    (out / "raw" / "media.json").write_text(json.dumps(media, ensure_ascii=False))
    by_url = {}
    for m in media:
        by_url[m["source_url"]] = m
        for sz in (m.get("media_details", {}).get("sizes") or {}).values():
            by_url[sz["source_url"]] = m
    lib = {m["source_url"].split("/wp-content/uploads/", 1)[-1] for m in media}
    for rel in lib:
        norm = SCALED_RE.sub("", rel)
        if norm != rel and norm not in lib:
            ALIAS[norm] = rel
    report.append(f"media library: {len(media)} items ({len(ALIAS)} aliased from -scaled names)")

    # content
    total = 0
    for tname, t in ptypes.items():
        items = paginate(base, t["rest_base"], context="view")
        (out / "raw" / f"{tname}.json").write_text(json.dumps(items, ensure_ascii=False))
        for it in items:
            gaps = []
            conv = Conv(base, gaps)
            html = it.get("content", {}).get("rendered", "")
            body = conv.convert(html)
            for m in re.findall(r"\[[a-z_\-]+[^\]]*\]", re.sub(r"<[^>]+>", "", html)):
                gaps.append("shortcode:" + m[:40])
            for u in re.findall(r"/wp-content/uploads/[^\s\"')]+", html):
                media_used.setdefault(u.split("/wp-content/uploads/", 1)[1], set()).add(it["link"])
            fm = {
                "title": it.get("title", {}).get("rendered"), "slug": it.get("slug"), "type": tname,
                "date": it.get("date"), "modified": it.get("modified"), "status": it.get("status"),
                "source_url": it.get("link"), "id": it.get("id"), "parent": it.get("parent"),
                "template": it.get("template"), "menu_order": it.get("menu_order"), "author": it.get("author"),
                "excerpt": re.sub(r"\s*…?Read more.*$", "", BeautifulSoup(it.get("excerpt", {}).get("rendered", ""), "html.parser").get_text(" ", strip=True)).strip(),
                "featured_media": it.get("featured_media"),
                "taxonomies": {tx: [tax_terms[tx][i]["slug"] for i in it.get(tx_rest, []) if i in tax_terms[tx]]
                               for tx, tdef in taxes.items() if tname in tdef.get("types", [])
                               for tx_rest in [tdef["rest_base"]] if it.get(tx_rest)},
                "meta": it.get("meta") if it.get("meta") else None,
            }
            rel = local_path(base, it["link"])
            path = out / "content" / rel / "index.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(frontmatter(fm) + "\n" + body)
            redirects["/" + rel + "/" if rel != "index" else "/"] = "/" + rel + "/" if rel != "index" else "/"
            if gaps:
                gaps_log[it["link"]] = sorted(set(gaps))
            total += 1
        report.append(f"type {tname}: {len(items)} items")

    # manual body overrides (e.g. JS-driven pages resolved by hand): data/overrides.json {"<content rel>": "<body>"}
    ov = out / "data" / "overrides.json"
    if ov.exists():
        for rel, new_body in json.loads(ov.read_text()).items():
            f = out / "content" / rel / "index.md"
            if f.exists():
                head = f.read_text().split("---\n", 2)
                f.write_text("---\n" + head[1] + "---\n\n" + new_body)

    # media download
    downloaded = skipped = failed = 0
    manifest = []
    targets = {m["source_url"]: m for m in media}
    known = {u.split("/wp-content/uploads/", 1)[-1] for u in targets}
    for rel in media_used:  # referenced but not in library; resized copies are mapped to originals
        rel = resolve(rel)
        if rel not in known:
            known.add(rel)
            targets[f"{base}/wp-content/uploads/{rel}"] = None
    if not a.no_media:
        for u, m in targets.items():
            rel = u.split("/wp-content/uploads/", 1)[-1]
            dest = out / "media" / rel
            ok = dest.exists()
            if not ok:
                r = get(u)
                if r is not None and r.status_code == 200:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(r.content)
                    downloaded += 1
                    ok = True
                else:
                    failed += 1
            else:
                skipped += 1
            manifest.append({
                "id": m["id"] if m else None, "source_url": u, "local": "/media/" + rel,
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest() if ok else None,
                "alt": m.get("alt_text") if m else None,
                "caption": BeautifulSoup(m["caption"]["rendered"], "html.parser").get_text(strip=True) if m else None,
                "mime": m.get("mime_type") if m else None,
                "width": (m.get("media_details") or {}).get("width") if m else None,
                "height": (m.get("media_details") or {}).get("height") if m else None,
                "used_by": sorted(set().union(*[v for k, v in media_used.items() if resolve(k) == rel])),
            })
    (out / "media" / "media-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    report.append(f"media files: downloaded={downloaded} existing={skipped} failed={failed}")

    # site.json, menus
    home_html = get(base + "/").text
    menus, how = fetch_menus(base, home_html)
    site = {"title": info.get("name"), "description": info.get("description"), "home": info.get("home"),
            "page_on_front": info.get("page_on_front"), "page_for_posts": info.get("page_for_posts"),
            "timezone": info.get("timezone_string"), "namespaces": info.get("namespaces"),
            "menus": menus, "menus_source": how,
            "post_types": {k: {"rest_base": v["rest_base"], "name": v["name"]} for k, v in ptypes.items()},
            "taxonomies": {k: {"rest_base": v["rest_base"], "types": v["types"]} for k, v in taxes.items()}}
    (out / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=1))
    (out / "redirects.json").write_text(json.dumps(redirects, ensure_ascii=False, indent=1, sort_keys=True))

    # gaps + report
    g = ["# Gaps (content that did not convert cleanly)\n"]
    for link, items in sorted(gaps_log.items()):
        g.append(f"- {link}\n  - " + "\n  - ".join(items))
    (out / "gaps.md").write_text("\n".join(g) + "\n")
    report += [f"content items written: {total}", f"pages with gaps: {len(gaps_log)}", f"menus via: {how}"]
    (out / "REPORT.md").write_text("# Extraction report\n\n" + "\n".join(f"- {x}" for x in report) + "\n")
    print("\n".join(report))


def cmd_verify(a):
    out = Path(a.out)
    site = json.loads((out / "site.json").read_text())
    base = site["home"].rstrip("/")
    problems = []
    written = {json.loads(l.split(": ", 1)[1]) for p in (out / "content").rglob("index.md")
               for l in p.read_text().splitlines()[:30] if l.startswith("source_url:")}
    sm = {u for u in sitemap_urls(base) if not re.search(r"\.(jpe?g|png|webp|gif|pdf)$", u, re.I)}
    derived = {t["link"] for f in (out / "taxonomies").glob("*.json") for t in json.loads(f.read_text()) if t.get("link")}
    derived |= {u for u in sm if re.search(r"/(author|page)/", u)}
    missing = sorted(sm - written - derived - {base + "/"})
    problems.append(f"sitemap URLs without content file: {len(missing)}")
    problems += [f"  - {u}" for u in missing[:30]]
    man = json.loads((out / "media" / "media-manifest.json").read_text()) if (out / "media" / "media-manifest.json").exists() else []
    bad = [m["source_url"] for m in man if not m["sha256"]]
    problems.append(f"media not downloaded: {len(bad)}")
    problems += [f"  - {u}" for u in bad[:30]]
    broken = 0
    for p in (out / "content").rglob("index.md"):
        for ref in re.findall(r"\]\((/media/[^)\s\"]+)", p.read_text()):
            if not (out / ref.lstrip("/")).exists():
                broken += 1
                problems.append(f"  broken media ref {ref} in {p}")
    problems.append(f"broken media refs: {broken}")
    txt = "\n".join(problems)
    with open(out / "REPORT.md", "a") as f:
        f.write("\n## Verification\n\n```\n" + txt + "\n```\n")
    print(txt)


def cmd_downscale(a):
    """Shrink raster images whose longest side exceeds --max, overwriting the file in place."""
    from PIL import Image, ImageOps
    out = Path(a.out)
    mpath = out / "media" / "media-manifest.json"
    manifest = {m["local"]: m for m in json.loads(mpath.read_text())} if mpath.exists() else {}
    done = saved = 0
    for f in sorted((out / "media").rglob("*")):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp") or not f.is_file():
            continue
        try:
            with Image.open(f) as im:
                m0 = manifest.get("/media/" + f.relative_to(out / "media").as_posix())
                if m0 and not a.dry_run:  # keep manifest dimensions truthful even for untouched/already-shrunk files
                    m0.update(width=im.size[0], height=im.size[1])
                if getattr(im, "is_animated", False) or max(im.size) <= a.max:
                    continue
                before, old = f.stat().st_size, im.size
                if a.dry_run:
                    print(f"would shrink {f} {old}")
                    done += 1
                    continue
                fmt = im.format
                icc = im.info.get("icc_profile")
                im = ImageOps.exif_transpose(im)
                im.thumbnail((a.max, a.max), Image.LANCZOS)
                tmp = f.with_name(f.name + ".tmp")
                kw = {"quality": 85, "optimize": True} if fmt == "JPEG" else {"optimize": True}
                if icc:
                    kw["icc_profile"] = icc
                im.save(tmp, format=fmt, **kw)
                new = im.size
            if tmp.stat().st_size >= before:  # never make a file bigger
                tmp.unlink()
                continue
            tmp.replace(f)
            saved += before - f.stat().st_size
            done += 1
            m = manifest.get("/media/" + f.relative_to(out / "media").as_posix())
            if m:
                m.update(width=new[0], height=new[1], downscaled_from=list(old),
                         sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        except Exception as e:
            print(f"skip {f}: {e}")
    if manifest and not a.dry_run:
        mpath.write_text(json.dumps(list(manifest.values()), ensure_ascii=False, indent=1))
    print(f"{'would downscale' if a.dry_run else 'downscaled'} {done} images; saved {saved / 1e6:.0f} MB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe"); p.add_argument("url"); p.set_defaults(f=cmd_probe)
    p = sub.add_parser("run"); p.add_argument("url"); p.add_argument("--out", default="extract")
    p.add_argument("--no-media", action="store_true"); p.set_defaults(f=cmd_run)
    p = sub.add_parser("verify"); p.add_argument("--out", default="extract"); p.set_defaults(f=cmd_verify)
    p = sub.add_parser("downscale"); p.add_argument("--out", default="extract")
    p.add_argument("--max", type=int, default=1024); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(f=cmd_downscale)
    a = ap.parse_args()
    a.f(a)
