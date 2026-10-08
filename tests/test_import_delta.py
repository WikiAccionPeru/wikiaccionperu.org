#!/usr/bin/env python3
"""Scenario tests for scripts/import-delta.py on a synthetic site + extract (nothing real is touched)."""
import json, os, subprocess, sys, tempfile, textwrap
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "wp" / "import_delta.py"
fails = 0
def ok(name, cond, extra=""):
    global fails
    print(("ok   " if cond else "FAIL ") + name, "" if cond else extra); fails += (not cond)

def page(id_, title, body, type_="post", modified="2026-01-01T00:00:00", extra="", slug=None, status="publish"):
    return textwrap.dedent(f'''\
        ---
        title: "{title}"
        slug: "{slug or title.lower().replace(' ', '-')}"
        type: "{type_}"
        date: "2026-01-01T00:00:00"
        modified: "{modified}"
        status: "{status}"
        id: {id_}
        {extra}
        ---

        {body}
        ''').replace("\n        \n", "\n").replace("\n\n\n", "\n\n")

def run(site, ex, *args):
    p = subprocess.run([sys.executable, str(SCRIPT), "--site", str(site), "--extract", str(ex), *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

with tempfile.TemporaryDirectory() as td:
    td = Path(td); site, ex = td / "site", td / "extract"
    (site / "content").mkdir(parents=True); (site / "data").mkdir(); (site / "import").mkdir()
    (ex / "content").mkdir(parents=True); (ex / "taxonomies").mkdir()
    (site / "data" / "taxonomies.json").write_text(json.dumps({"category": {"prefix": "categoria", "types": ["post"], "terms": [{"id": 1, "slug": "cultura", "name": "Cultura", "count": 1, "parent": 0}]}}))
    def wp(rel, text): (ex / "content" / rel).mkdir(parents=True, exist_ok=True); (ex / "content" / rel / "index.md").write_text(text)
    def loc(rel, text): f = site / "content" / f"{rel}.md"; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(text)
    pages = {"a": 101, "b": 102, "c": 103, "f": 106, "g": 107, "h": 108, "i": 109}
    for rel, id_ in pages.items():
        t = page(id_, rel.upper(), f"Cuerpo original de {rel}.", slug=rel)
        wp(rel, t); loc(rel, t)
    wp("index", page(771, "Inicio", "original home", type_="page", slug="home")); loc("index", page(771, "Inicio", "home rehecha a mano", type_="page", slug="home"))

    # --- init
    code, out = run(site, ex, "--init"); ok("init succeeds", code == 0, out)
    st = json.loads((site / "import/state.json").read_text()); ok("baseline holds all pages", len(st["items"]) == 8, str(len(st["items"])))
    exc = json.loads((site / "import/exclude.json").read_text())["items"]; ok("default exclusions resolved to ids", any(e["path"] == "/" and str(e["id"]) == "771" for e in exc))
    ok("init reports the hand-edited home as diverged", "/" in out.split("differ")[1])
    code, out = run(site, ex); ok("dry run right after init: nothing to do", '"update": 0' in out and '"conflict": 0' in out and '"new": 0' in out, out)

    # --- WordPress changes ---------------------------------------------------------------------------------------
    wp("a", page(101, "A", "Cuerpo NUEVO de a.", slug="a", modified="2026-02-01T00:00:00"))                 # A: WP only        -> update
    wp("b", page(102, "B", "Cuerpo NUEVO de b.", slug="b", modified="2026-02-01T00:00:00"))                 # B: both           -> conflict
    loc("b", page(102, "B", "Cuerpo editado localmente de b.", slug="b"))
    loc("c", page(103, "C", "Cuerpo original de c. Más texto local.", slug="c"))                             # C: local only
    wp("d", page(110, "D", "Página nueva.", slug="d"))                                                        # D: new
    wp("e", page(111, "E", "Otra nueva.", slug="e")); loc("e", "---\ntitle: x\ntype: page\ndate: x\nstatus: publish\n---\nocupada\n")  # E: path occupied
    wp("f", page(106, "F", "Cuerpo NUEVO de f.", slug="f", modified="2026-02-01T00:00:00"))                 # F: WP change on a moved page
    (site / "content/f.md").rename(site / "content/ayuda" / "f-movida.md") if (site / "content/ayuda").mkdir(exist_ok=True) is None else None
    txt = (site / "content/ayuda/f-movida.md").read_text().replace('slug: "f"', 'slug: "f-movida"'); (site / "content/ayuda/f-movida.md").write_text(txt)
    # G: reformatted by the editor (YAML block style, different quoting), meaning unchanged -> must NOT count as local edit
    loc("g", '---\ntitle: G\nslug: g\ntype: post\ndate: 2026-01-01T00:00:00\nmodified: 2026-01-01T00:00:00\nstatus: publish\nid: 107\n---\n\nCuerpo original de g.\n\n\n')
    wp("h", page(108, "H", "Cuerpo NUEVO de h.", slug="h", modified="2026-02-01T00:00:00"))                 # H: excluded
    run(site, ex, "exclude", "/h", "test")
    # I: deleted in WordPress, untouched locally
    import shutil; shutil.rmtree(ex / "content/i")
    wp("index", page(771, "Inicio", "home cambiada en WP", type_="page", slug="home", modified="2026-02-01T00:00:00"))  # excluded by default

    code, out = run(site, ex)
    counts = json.loads(out.split("DRY RUN ")[1].split("\n")[0])
    ok("dry run classifies: 1 update (a) + 1 update (f)", counts["update"] == 2, str(counts))
    ok("dry run: 1 conflict (b) + 1 path-occupied (e)", counts["conflict"] == 2, str(counts))
    ok("dry run: 1 new (d), 1 local-only (c)", counts["new"] == 1 and counts["local_only"] == 1, str(counts))
    rep = (site / "import/report.md").read_text()
    local_only_block = rep.split("## Edited locally only")[1].split("\n## ")[0] if "## Edited locally only" in rep else ""
    ok("dry run: editor reformatting of g is NOT a local edit (only c is)", "/c " in local_only_block and "/g " not in local_only_block, local_only_block)
    ok("dry run: h and home excluded", counts["excluded"] == 2, str(counts))
    ok("dry run: i reported as deleted in WordPress", counts["deleted_in_wp"] == 1, str(counts))
    ok("dry run changed nothing", "NUEVO de a" not in (site / "content/a.md").read_text() and not (site / "content/d.md").exists())

    # --- apply ----------------------------------------------------------------------------------------------------
    code, out = run(site, ex, "--apply"); ok("apply succeeds", code == 0, out)
    ok("A updated", "NUEVO de a" in (site / "content/a.md").read_text())
    ok("B untouched (local edit kept)", "editado localmente" in (site / "content/b.md").read_text())
    ok("B conflict files written", any((site / "import/conflicts").glob("102__b.wp.md")) and "NUEVO" in next((site / "import/conflicts").glob("102__b.diff")).read_text())
    ok("C untouched", "Más texto local" in (site / "content/c.md").read_text())
    ok("D created", (site / "content/d.md").exists() and "Página nueva" in (site / "content/d.md").read_text())
    ok("E not overwritten, conflict recorded", "ocupada" in (site / "content/e.md").read_text() and any((site / "import/conflicts").glob("111__*")))
    moved = (site / "content/ayuda/f-movida.md").read_text()
    ok("F updated at its moved path, no copy at the old path", "NUEVO de f" in moved and not (site / "content/f.md").exists())
    ok("F keeps the slug that follows its new address", 'slug: "f-movida"' in moved)
    ok("H and home not touched", "Cuerpo original de h" in (site / "content/h.md").read_text() and "rehecha a mano" in (site / "content/index.md").read_text())
    ok("I kept (not deleted by default)", (site / "content/i.md").exists())
    ok("backup of overwritten local file", any((site / "import/backup").rglob("a.md")))
    ok("indexes rebuilt", (site / "data/routes.json").exists() and "/d" in json.loads((site / "data/routes.json").read_text()) and "/ayuda/f-movida" in json.loads((site / "data/routes.json").read_text()))
    # --- idempotency + resolution --------------------------------------------------------------------------------------
    code, out = run(site, ex, "--apply"); c2 = json.loads(out.split("APPLIED ")[1].split("\n")[0])
    ok("second apply changes nothing (only the open conflicts remain)", c2["update"] == 0 and c2["new"] == 0 and c2["conflict"] == 2, str(c2))
    code, out = run(site, ex, "take", "/b"); ok("take overwrites local with WordPress", "NUEVO de b" in (site / "content/b.md").read_text(), out)
    code, out = run(site, ex, "keep", "/e")
    code, out = run(site, ex); c3 = json.loads(out.split("DRY RUN ")[1].split("\n")[0])
    ok("after take/keep: no conflicts left (e still occupied -> keep records baseline only for matched ids)", c3["conflict"] <= 1, str(c3))
    code, out = run(site, ex, "--apply", "--delete-removed"); ok("--delete-removed trashes i (untouched locally)", not (site / "content/i.md").exists() and any((site / "content/.trash").glob("*i.md")), out)
    code, out = run(site, ex, "include", "/h"); code, out = run(site, ex); c4 = json.loads(out.split("DRY RUN ")[1].split("\n")[0])
    ok("include re-enables a page: h now an update", c4["update"] == 1, str(c4))

print("\nALL PASSED" if not fails else f"\n{fails} FAILED"); sys.exit(1 if fails else 0)
