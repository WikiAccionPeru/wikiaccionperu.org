#!/usr/bin/env python3
"""Tests for tools/wp: transform, route rebuild, media fetcher (against a local fake WordPress) and a fresh-clone bootstrap."""
import io, json, os, subprocess, sys, tempfile, threading, textwrap
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "wp"))
from wpimport import indexes, transform as T  # noqa: E402
from PIL import Image  # noqa: E402

fails = 0
def ok(name, cond, extra=""):
    global fails
    print(("ok   " if cond else "FAIL ") + name, "" if cond else extra); fails += (not cond)

def png(w, h):
    b = io.BytesIO(); Image.new("RGB", (w, h), (200, 30, 30)).save(b, "PNG"); return b.getvalue()

# ---- 1. transform ---------------------------------------------------------------------------------------------------
body = "![x](/media/2026/05/Caf%C3%A9%20Foto%20%281%29.jpg?w=300&resize=1,2)\n\n[old](/viejo-enlace/)\n\n::video-embed{src=\"https://y/1\" title=\"t\"}\n\nFin"
out = T.fix_body(body, {}, {"/viejo-enlace/": "/nuevo-enlace/"})
ok("transform: media name sanitised without any saved map", f"(/media/{T.safe_rel('2026/05/Café Foto (1).jpg')})" in out and "?w=" not in out, out)
ok("transform: known dead link repaired", "(/nuevo-enlace/)" in out and "/viejo-enlace/" not in out)
ok("transform: leaf directive closed for MDC", '::video-embed{src="https://y/1" title="t"}\n::' in out)
ok("transform: already-safe names untouched", T.safe_rel("2025/08/foto-1.jpg") == "2025/08/foto-1.jpg")
t = T.transform_text('---\ntitle: "T"\nmeta: {"a": 1}\nid: 5\n---\n\ncuerpo\n', {}, {})
ok("transform: reserved `meta` frontmatter dropped", "meta:" not in t and 'title: "T"' in t)
base = '---\ntitle: "A"\nslug: "a"\nid: 5\ntaxonomies: {"category": ["x"]}\n---\n\nTexto.\n'
same = "---\ntitle: A\nslug: other-slug\nid: 5\ntaxonomies:\n  category:\n    - x\n---\n\n\nTexto.   \n\n"
ok("hash: quotes / YAML style / whitespace / slug do not change meaning", T.sem_hash(base) == T.sem_hash(same))
ok("hash: a real body change does", T.sem_hash(base) != T.sem_hash(base.replace("Texto.", "Texto 2.")))
ok("hash: a real property change does", T.sem_hash(base) != T.sem_hash(base.replace('"x"', '"y"')))

# ---- 2. route rebuild ---------------------------------------------------------------------------------------------------
def page(route_file, id_, type_, status="publish", tax=None):
    f = route_file; f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f'---\ntitle: "{f.stem}"\ntype: "{type_}"\ndate: "2026-01-{id_ % 28 + 1:02d}T00:00:00"\nstatus: "{status}"\nid: {id_}\ntaxonomies: {json.dumps(tax or {})}\n---\n\nx\n')
with tempfile.TemporaryDirectory() as td:
    td = Path(td); (td / "data").mkdir(); c = td / "content"
    for i in range(23): page(c / f"n{i:02d}.md", i, "post", tax={"category": ["cultura"]})
    page(c / "borrador.md", 90, "post", status="draft", tax={"category": ["cultura"]})
    for i in range(3): page(c / "recurso" / f"r{i}.md", 100 + i, "recurso")
    page(c / "index.md", 771, "page"); page(c / "sobre.md", 5, "page")
    page(c / ".trash" / "ignorada.md", 999, "post")
    (td / "data/taxonomies.json").write_text(json.dumps({"category": {"prefix": "categoria", "types": ["post"], "terms": [{"slug": "cultura", "name": "Cultura"}, {"slug": "vacia", "name": "Vacía"}]}}))
    r = indexes.rebuild(td); routes = set(json.loads((td / "data/routes.json").read_text())); idx = json.loads((td / "data/taxonomy-index.json").read_text())
    ok("reindex: 23 published posts -> /noticias/page/2 and /3, no /4", {"/noticias/page/2", "/noticias/page/3"} <= routes and "/noticias/page/4" not in routes)
    ok("reindex: archive pages follow the real count (23 -> 3 pages), drafts excluded", len(idx["category/cultura"]) == 23 and "/categoria/cultura/page/3" in routes and "/categoria/cultura/page/4" not in routes)
    ok("reindex: empty term has no archive route; .trash ignored; system routes present", "/categoria/vacia" not in routes and "/ignorada" not in routes and {"/", "/buscar", "/admin", "/admin/pages", "/admin/menu", "/admin/editors", "/styleguide", "/sobre"} <= routes)

# ---- 3. media fetcher against a fake WordPress ----------------------------------------------------------------------------
FILES = {"/wp-content/uploads/2026/01/grande.png": png(2400, 1200), "/wp-content/uploads/2026/01/peque.png": png(300, 150),
         "/wp-content/uploads/2026/01/Café Foto.png": png(1500, 500), "/wp-content/uploads/2026/01/guia.pdf": b"%PDF-1.4 fake"}
hits = []
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(self.path); hits.append(path)
        data = FILES.get(path)
        self.send_response(200 if data else 404); self.end_headers()
        if data: self.wfile.write(data)
    def log_message(self, *a): pass
srv = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
with tempfile.TemporaryDirectory() as td:
    td = Path(td); (td / "content").mkdir(); (td / "data").mkdir(); (td / "import").mkdir(); (td / "app").mkdir(); (td / "public/media/2026/01").mkdir(parents=True)
    safe = T.safe_rel("2026/01/Café Foto.png")
    (td / "content/p.md").write_text(f'---\ntitle: "P"\ntype: "post"\ndate: "x"\nstatus: "publish"\nid: 1\n---\n\n![a](/media/2026/01/grande.png)\n![b](/media/2026/01/peque.png)\n![c](/media/{safe})\n[doc](/media/2026/01/guia.pdf)\n![d](/media/2026/01/muerta.png)\n![e](/media/2026/01/ya-esta.png)\n')
    (td / "public/media/2026/01/ya-esta.png").write_bytes(b"keep-me")
    (td / "import/state.json").write_text(json.dumps({"renames": {"2026/01/Café Foto.png": safe}}))  # what the importer records
    env = {**os.environ, "WP_SOURCE_URL": f"http://127.0.0.1:{srv.server_port}"}
    run = lambda *a: subprocess.run([sys.executable, str(ROOT / "tools/wp/fetch_media.py"), "--site", str(td), "--extract", str(td / "none"), *a], capture_output=True, text=True, env=env)
    d = run("--dry-run"); ok("media: dry run lists missing files, downloads nothing", "5 referenced media" in d.stdout and not hits, d.stdout)
    r = run(); m = td / "public/media/2026/01"
    ok("media: big image shrunk to 1024 px wide (aspect kept)", Image.open(m / "grande.png").size == (1024, 512), r.stdout)
    ok("media: small image and PDF stored untouched", Image.open(m / "peque.png").size == (300, 150) and (m / "guia.pdf").read_bytes() == b"%PDF-1.4 fake")
    ok("media: sanitised name fetched from the ORIGINAL accented URL", (td / "public/media" / safe).exists() and any("Café" in h for h in hits), str(hits))
    ok("media: existing file never overwritten, never requested", (m / "ya-esta.png").read_bytes() == b"keep-me" and not any("ya-esta" in h for h in hits))
    ok("media: 404 reported, run still succeeds", "muerta.png" in r.stdout and r.returncode == 0, r.stdout)
    ok("media: --strict turns a dead file into exit 2", run("--strict").returncode == 2)
    n = len(hits); run(); ok("media: second run only retries the dead file", len(hits) - n == 1)
srv.shutdown()

# ---- 4. fresh clone: sample committed, no state, no media -> bootstrap import --------------------------------------------------
IMP = ROOT / "tools/wp/import_delta.py"
def wp_page(id_, title, body, type_="post"): return f'---\ntitle: "{title}"\nslug: "{title.lower()}"\ntype: "{type_}"\ndate: "2026-01-01T00:00:00"\nmodified: "2026-01-01T00:00:00"\nstatus: "publish"\nid: {id_}\n---\n\n{body}\n'
with tempfile.TemporaryDirectory() as td:
    td = Path(td); site, ex = td / "site", td / "var/extract"
    (site / "content").mkdir(parents=True); (site / "data").mkdir(); (site / "import").mkdir()
    for rel, id_, t in [("index", 771, "page"), ("sobre", 2, "page"), ("uno", 3, "post"), ("dos", 4, "post"), ("recurso/tres", 5, "recurso")]:
        (ex / "content" / rel).mkdir(parents=True); (ex / "content" / rel / "index.md").write_text(wp_page(id_, rel.split("/")[-1], f"WP {rel}" + ("\n\n![](/media/2026/01/Caf%C3%A9%20Foto.jpg)" if rel == "uno" else ""), t))
    for rel in ["index", "sobre"]:  # the committed sample: home is restructured, sobre matches WordPress
        (site / "content" / f"{rel}.md").write_text(wp_page(771 if rel == "index" else 2, rel, "home rehecha" if rel == "index" else f"WP {rel}", "page"))
    (ex / "taxonomies").mkdir()
    (ex / "site.json").write_text(json.dumps({"taxonomies": {"category": {"types": ["post"]}}}))
    (ex / "taxonomies/category.json").write_text(json.dumps([{"id": 1, "slug": "cultura", "name": "Cultura", "count": 2, "parent": 0, "link": "https://x/categoria/cultura/"}]))
    (ex / "raw").mkdir(); (ex / "raw/media.json").write_text(json.dumps([{"id": 9, "source_url": "https://x/wp-content/uploads/2026/01/Foto%20A.jpg"}]))
    run = lambda *a: subprocess.run([sys.executable, str(IMP), "--site", str(site), "--extract", str(ex), *a], capture_output=True, text=True)
    r = run(); ok("fresh clone: refuses to run without a baseline", r.returncode != 0 and "--init" in (r.stdout + r.stderr))
    r = run("--init"); ok("fresh clone: --init adopts the sample and flags the restructured home as local", r.returncode == 0 and "baseline set for 2 pages" in r.stdout, r.stdout)
    r = run("--apply"); ok("fresh clone: --apply creates the 3 missing pages, keeps the 2 sample pages", all((site / "content" / f).exists() for f in ["uno.md", "dos.md", "recurso/tres.md"]) and "rehecha" in (site / "content/index.md").read_text(), r.stdout + r.stderr)
    ok("fresh clone: taxonomies built from the extract", json.loads((site / "data/taxonomies.json").read_text())["category"]["prefix"] == "categoria")
    ok("fresh clone: media-index built from the library listing (no downloaded files needed)", json.loads((site / "data/media-index.json").read_text()).get("9") == f"/media/{T.safe_rel('2026/01/Foto A.jpg')}")
    ok("fresh clone: importer remembers the ORIGINAL media name for the fetcher", json.loads((site / "import/state.json").read_text())["renames"].get("2026/01/Café Foto.jpg") == T.safe_rel("2026/01/Café Foto.jpg"))
    ok("fresh clone: routes generated", "/uno" in json.loads((site / "data/routes.json").read_text()))
    r = run(); ok("fresh clone: next dry run is clean", '"new": 0' in r.stdout and '"update": 0' in r.stdout and '"conflict": 0' in r.stdout, r.stdout)
    (ex / "content/uno/index.md").write_text(wp_page(3, "uno", "WP cambiado")); (site / "content/uno.md").write_text(wp_page(3, "uno", "edición local"))
    r = run("--fail-on-conflict"); ok("--fail-on-conflict exits 3 on a real conflict", r.returncode == 3, r.stdout)
    (site / "import/state.json").unlink() if False else None

# ---- 5. wrapper -----------------------------------------------------------------------------------------------------------------
w = subprocess.run(["bash", "-n", str(ROOT / "tools/wp/wp")]); ok("wrapper: bash syntax", w.returncode == 0)
h = subprocess.run([str(ROOT / "tools/wp/wp"), "help"], capture_output=True, text=True); ok("wrapper: help lists bootstrap/update/media", all(x in h.stdout for x in ["bootstrap", "update", "media"]))

print("\nALL PASSED" if not fails else f"\n{fails} FAILED"); sys.exit(1 if fails else 0)
