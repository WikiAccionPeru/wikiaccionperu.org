"""Shared WordPress -> site transformation. Used by the one-time import (sync-extract.py) and the delta importer
(import-delta.py), so both produce byte-identical pages from the same extract."""
import hashlib, json, re, unicodedata
from pathlib import Path
from urllib.parse import quote, unquote

import yaml

DIRECTIVE = re.compile(r"^::([a-z][\w-]*)\{.*\}\s*$")
MEDIA_SKIP = {"media-manifest.json"}


# ---- media names ---------------------------------------------------------------------------------------------
def safe_rel(rel):
    """ASCII-only, URL-safe media path (IPX and many static hosts choke on ¡, emoji, en-dashes, %…)."""
    base = unicodedata.normalize("NFKD", rel).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9._/-]+", "-", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return base or "file-" + hashlib.sha1(rel.encode()).hexdigest()[:8]


def media_files(media_dir):
    if not media_dir or not Path(media_dir).is_dir():
        return []
    return sorted(f.relative_to(media_dir).as_posix() for f in Path(media_dir).rglob("*") if f.is_file() and f.name not in MEDIA_SKIP)


def compute_renames(media_dir, existing=None):
    """original rel -> sanitised rel (only entries that differ). Names handed out before never change, so links stay valid
    when new files arrive; a new file that collides with a taken name gets a hash suffix."""
    renames = dict(existing or {})
    taken = {v: k for k, v in renames.items()}
    files = media_files(media_dir)
    for rel in files:
        if rel in renames:
            continue
        new = safe_rel(rel)
        if taken.get(new, rel) != rel:  # collision after sanitising
            stem, dot, ext = new.rpartition(".")
            new = f"{stem}-{hashlib.sha1(rel.encode()).hexdigest()[:6]}{dot}{ext}"
        taken[new] = rel
        if new != rel:
            renames[rel] = new
    return renames


# ---- body ------------------------------------------------------------------------------------------------------
def _safe_url(m):
    """Repair truncated percent-escapes (source typos) that make the MDC parser throw."""
    u = m.group(1)
    try:
        unquote(u, errors="strict")
        return m.group(0)
    except UnicodeDecodeError:
        u2 = re.sub(r"(?:%[0-9A-Fa-f]{2})*%(?![0-9A-Fa-f]{2}).*$|(?:%[0-9A-Fa-f]{2})+$", lambda x: quote(unquote(x.group(0), errors="ignore"), safe=""), u)
        return "](" + u2


def fix_body(body, renames, link_fixes=None):
    renames = renames or {}
    for old, new in (link_fixes or {}).items():  # known dead/renamed internal links (import/link-fixes.json)
        body = body.replace("(" + old + ")", "(" + new + ")")
    body = re.sub(r"(\(/media/[^)\s\"?]+)\?[^)\s\"]*", r"\1", body)  # drop ?w=…&resize=… image-proxy params
    body = re.sub(r"\(/media/([^)\s\"]+)", lambda m: "(/media/" + quote(renames.get(unquote(m.group(1))) or safe_rel(unquote(m.group(1))), safe="/._-~"), body)
    body = re.sub(r"\]\(([^)\s]*%[^)\s]*)", _safe_url, body)
    out = []
    for line in body.splitlines():
        out.append(line)
        if DIRECTIVE.match(line):
            out.append("::")  # leaf directives need an explicit close in MDC
    return "\n".join(out)


# ---- documents -------------------------------------------------------------------------------------------------
_SPLIT = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.S)


def split_doc(text):
    m = _SPLIT.match(text)
    return (m.group(1), m.group(2)) if m else ("", text)


def transform_text(text, renames, link_fixes=None):
    """One extract page -> the text written under content/."""
    fm, body = split_doc(text)
    fm = "\n".join(l for l in fm.splitlines() if not l.startswith("meta:"))  # `meta` is reserved by Nuxt Content
    return f"---\n{fm}\n---\n{fix_body(body, renames, link_fixes)}"


def frontmatter(text):
    """Frontmatter as {key: string-or-structure}. BaseLoader keeps every scalar a string, so formatting differences
    (quotes, unquoted timestamps, block vs flow style) between WordPress, this code and the editor never matter."""
    fm, _ = split_doc(text)
    try:
        d = yaml.load(fm, Loader=yaml.BaseLoader)
    except yaml.YAMLError:
        return {}
    return d if isinstance(d, dict) else {}


def sem_hash(text):
    """Hash of the *meaning* of a page: frontmatter (minus `slug`, which follows the address) + body, whitespace-normalised."""
    d = frontmatter(text)
    d.pop("slug", None)
    _, body = split_doc(text)
    body = "\n".join(l.rstrip() for l in body.replace("\r\n", "\n").split("\n")).strip()
    return hashlib.sha1((json.dumps(d, sort_keys=True, ensure_ascii=False) + "\n" + body).encode()).hexdigest()
