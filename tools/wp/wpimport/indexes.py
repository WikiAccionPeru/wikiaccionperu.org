"""Derived data rebuilt from the real content (so editor changes count too): taxonomy index and the prerender route list."""
import json, math
from pathlib import Path

from .transform import frontmatter

PER_PAGE = 9
SYSTEM_ROUTES = {"/admin", "/admin/pages", "/admin/menu", "/admin/editors", "/admin/edit"}  # client-rendered admin screens


def local_pages(content_dir):
    """[(route, file, frontmatter)] for every page under content/ (dot folders such as .trash are ignored)."""
    out = []
    for f in sorted(Path(content_dir).rglob("*.md")):
        rel = f.relative_to(content_dir)
        if any(p.startswith(".") for p in rel.parts):
            continue
        r = rel.with_suffix("").as_posix()
        route = "/" if r == "index" else "/" + (r[:-6] if r.endswith("/index") else r)
        out.append((route, f, frontmatter(f.read_text(encoding="utf-8"))))
    return out


def rebuild(site_root):
    root = Path(site_root)
    data = root / "data"
    pages = local_pages(root / "content")
    tax = json.loads((data / "taxonomies.json").read_text()) if (data / "taxonomies.json").exists() else {}
    index, per_type = {}, {}
    for route, _, fm in pages:
        if fm.get("status", "publish") != "publish":
            continue
        per_type[fm.get("type", "")] = per_type.get(fm.get("type", ""), 0) + 1
        for tname, slugs in (fm.get("taxonomies") or {}).items():
            for s in slugs or []:
                index.setdefault(f"{tname}/{s}", []).append(route)
    routes = {"/", "/styleguide", "/buscar", "/noticias", "/recursos", "/alianza"} | SYSTEM_ROUTES
    routes |= {r for r, _, _ in pages}
    n = lambda c: max(0, math.ceil(c / PER_PAGE))
    routes |= {f"/noticias/page/{i}" for i in range(2, n(per_type.get("post", 0)) + 1)}
    routes |= {f"/recursos/page/{i}" for i in range(2, n(per_type.get("recurso", 0)) + 1)}
    routes |= {f"/alianza/page/{i}" for i in range(2, n(per_type.get("alianza", 0)) + 1)}
    for tname, t in tax.items():
        for term in t["terms"]:
            c = len(index.get(f"{tname}/{term['slug']}", []))
            if c:
                routes.add(f"/{t['prefix']}/{term['slug']}")
                routes |= {f"/{t['prefix']}/{term['slug']}/page/{i}" for i in range(2, n(c) + 1)}
    (data / "taxonomy-index.json").write_text(json.dumps(index, ensure_ascii=False))
    (data / "routes.json").write_text(json.dumps(sorted(routes), indent=1))
    return {"pages": len(pages), "routes": len(routes), "archives": len(index)}
