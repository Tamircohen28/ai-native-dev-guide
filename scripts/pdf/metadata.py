#!/usr/bin/env python3
"""Write the book PDF's metadata with pypdf.

Usage: metadata.py <in.pdf> <out.pdf>      (called by scripts/pdf/build.mjs)
       metadata.py --show <file.pdf>       (print the metadata back)
       metadata.py --check <file.pdf>      (fail on missing metadata or a broken link)

The values come from environment variables set by build.mjs, so the build identity
(commit, version, build time) has one source.
"""

import os
import re
import sys
from datetime import datetime, timezone

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject


def pdf_date(iso):
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.strftime("D:%Y%m%d%H%M%S+00'00'")


def show(path):
    reader = PdfReader(path)
    print(f"{path}: {len(reader.pages)} pages")
    for key, value in sorted((reader.metadata or {}).items()):
        print(f"  {key}: {value}")


def write(src, dst):
    env = os.environ
    need = ["BOOK_TITLE", "BOOK_SUBTITLE", "BOOK_AUTHOR", "BOOK_KEYWORDS", "BOOK_REPO",
            "BOOK_LICENSE", "BOOK_LICENSE_URL", "BOOK_COMMIT_RESOLVED",
            "BOOK_VERSION_RESOLVED", "BOOK_BUILD_TIME_RESOLVED"]
    missing = [k for k in need if not env.get(k)]
    if missing:
        sys.exit(f"metadata.py: missing environment: {', '.join(missing)}")

    import pypdf

    # Copy pages, links, named destinations and the outline (bookmarks) into a fresh
    # file. Chromium only writes the outline for a tagged PDF, and its structure tree
    # (tens of thousands of span-level elements) doubles the file size, so it is left out.
    writer = PdfWriter()
    writer.append(PdfReader(src), import_outline=True)
    for page in writer.pages:
        if "/StructParents" in page:
            del page["/StructParents"]
        page.compress_content_streams()
    writer.compress_identical_objects()
    writer.root_object[NameObject("/Lang")] = TextStringObject("en")
    date = pdf_date(env["BOOK_BUILD_TIME_RESOLVED"])
    writer.add_metadata({
        "/Title": env["BOOK_TITLE"],
        "/Author": env["BOOK_AUTHOR"],
        "/Subject": env["BOOK_SUBTITLE"],
        "/Keywords": env["BOOK_KEYWORDS"],
        "/Creator": f"scripts/pdf/build.mjs: markdown-it, mermaid-cli, Paged.js, {env.get('BOOK_CHROME', 'Chromium')}",
        "/Producer": f"Chromium (Skia/PDF) via puppeteer; metadata by pypdf {pypdf.__version__}",
        "/CreationDate": date,
        "/ModDate": date,
        "/Repository": env["BOOK_REPO"],
        "/Commit": env["BOOK_COMMIT_RESOLVED"],
        "/Version": env["BOOK_VERSION_RESOLVED"],
        "/License": f"{env['BOOK_LICENSE']} ({env['BOOK_LICENSE_URL']})",
        "/BuildTimestamp": env["BOOK_BUILD_TIME_RESOLVED"],
    })
    writer.create_viewer_preferences()
    writer.viewer_preferences.display_doctitle = True
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    with open(dst, "wb") as fh:
        writer.write(fh)


REQUIRED_KEYS = ["/Title", "/Author", "/Subject", "/Keywords", "/Creator", "/Producer",
                 "/Repository", "/Commit", "/Version", "/License", "/BuildTimestamp"]


def check(path):
    """Every required metadata key is set, every internal link resolves to a page, and
    every link to a chapter lands on the page that starts with that chapter's title."""
    reader = PdfReader(path)
    meta = reader.metadata or {}
    errors = [f"metadata {k} is missing" for k in REQUIRED_KEYS if not meta.get(k)]
    dests = reader.named_destinations
    page_of = {name: reader.get_destination_page_number(d) for name, d in dests.items()}
    text_cache = {}

    def page_text(n):
        if n not in text_cache:
            text_cache[n] = reader.pages[n].extract_text() or ""
        return text_cache[n]

    internal = external = 0
    for n, page in enumerate(reader.pages):
        for annot in page.get("/Annots") or []:
            a = annot.get_object()
            if a.get("/Subtype") != "/Link":
                continue
            dest = a.get("/Dest")
            if dest is None and a.get("/A", {}).get("/S") == "/URI":
                external += 1
                continue
            internal += 1
            name = str(dest)
            if name not in page_of:
                errors.append(f"page {n + 1}: link to {name} has no destination")
                continue
            m = re.fullmatch(r"/?ch-([0-9]+|[A-E])", name)
            if m:
                # Extracted text is the page number, then the title, one word per line.
                head = re.sub(r"\s+", "", page_text(page_of[name]))[:40]
                want = f"Appendix{m[1]}—" if m[1].isalpha() else f"{m[1]}—"
                if want not in head:
                    errors.append(f"page {n + 1}: link to {name} lands on page "
                                  f"{page_of[name] + 1}, which starts {head[:40]!r}")
    print(f"{path}: {len(reader.pages)} pages, {internal} internal links "
          f"({len(dests)} destinations), {external} external links")
    for e in errors[:40]:
        print(f"  ERROR {e}")
    if errors:
        sys.exit(f"metadata.py --check: {len(errors)} problem(s)")
    print("  ok: metadata complete, every internal link resolves, chapter links land on their chapter")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--show":
        show(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--check":
        check(sys.argv[2])
    elif len(sys.argv) == 3:
        write(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
