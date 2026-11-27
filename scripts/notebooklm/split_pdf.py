#!/usr/bin/env python3
"""Split the book PDF into one PDF per table-of-contents entry, grouped by part.

Usage: split_pdf.py <book.pdf> <out-dir> [--readme <README.md>]   (called by make notebookLM)
       split_pdf.py --check <book.pdf> <out-dir>                 (re-verify an existing split)

The structure comes from the PDF itself: its top-level outline (bookmarks), cross-checked
against the named destinations the contents page links to. Nothing is hard-coded.

  00-front-matter/NN-<slug>.pdf   everything before the first part, one file per outline
                                  entry; pages before the first entry (the cover) join it
  NN-<part-slug>/00-part-<slug>.pdf   the part's divider page(s)
  NN-<part-slug>/NN-<chapter>.pdf     one file per chapter, named by its book number
  99-back-matter/NN-<slug>.pdf    anything after the last chapter (only when present)

Completeness invariant, checked after writing (the run fails when it breaks): the page
ranges are contiguous and cover the book exactly once, and concatenating every split file
in sorted path order gives the book's page count with every page identical (a hash of its
extracted text plus the length of its content stream).

With --readme, a section describing the split is added to (or replaced in) that README.
"""

import hashlib
import os
import re
import shutil
import sys
import unicodedata

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, FloatObject, NameObject, NullObject, TextStringObject
except ImportError:
    sys.exit("pypdf is missing: python3 -m pip install -r requirements-pdf.txt")

BOOK_TITLE_FALLBACK = "AI-Native Development"
COPY_KEYS = ["/Author", "/Subject", "/Keywords", "/Repository", "/Commit", "/Version",
             "/License", "/BuildTimestamp"]
README_HEADING = "## Book PDF split (`pdf-split/`)"

PART_RE = re.compile(r"^Part\s+([IVXLC]+)\s*[—–-]\s*(.+)$")
CHAPTER_RE = re.compile(r"^(\d+)\s*[—–-]\s*(.+)$")


def fail(msg):
    sys.exit(f"pdf-split: FAIL: {msg}")


def slugify(s, max_words=None):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", s.lower())
    if max_words:
        words = words[:max_words]
    return "-".join(words) or "untitled"


def short_slug(title):
    """'Inside the harness: architecture and …' -> 'inside-the-harness'. A one-word lead
    ('Guide: write a subagent', 'MCP: how the protocol works') keeps the whole title."""
    lead = title.split(":", 1)[0]
    if ":" in title and len(lead.split()) >= 2:
        return slugify(lead)
    return slugify(title, max_words=8)


def page_tokens(reader, n):
    """The page's extracted text as words, without the leading page number."""
    words = (reader.pages[n].extract_text() or "").split()
    if words and words[0].isdigit():
        words = words[1:]
    return words


def repair_title(reader, title, n):
    """Outline titles lose the space at a line break ('whathappens'). Rebuild the title
    from the words that start its page when they spell the same characters."""
    want = re.sub(r"\s+", "", title)
    got, words = "", []
    for w in page_tokens(reader, n)[:60]:
        if not want.startswith(got + w):
            break
        got += w
        words.append(w)
        if got == want:
            return re.sub(r"\s+([,:;.])", r"\1", " ".join(words))
    return title


def top_level_entries(reader):
    entries = []
    for item in reader.outline:
        if isinstance(item, list):
            continue  # children of the previous entry
        entries.append((reader.get_destination_page_number(item), str(item.title).strip()))
    if not entries:
        fail("the PDF has no outline (bookmarks); rebuild it with make pdf")
    for (a, ta), (b, tb) in zip(entries, entries[1:]):
        if b <= a:
            fail(f"outline is not in page order: {ta!r} p{a + 1} then {tb!r} p{b + 1}")
    return entries


def plan(reader):
    """Return [(rel_path, title, first_page, last_page)] (0-based, inclusive), in order."""
    total = len(reader.pages)
    entries = top_level_entries(reader)
    dests = {}
    for name, d in reader.named_destinations.items():
        try:
            dests[str(name).lstrip("/")] = reader.get_destination_page_number(d)
        except Exception:
            pass

    starts = [p for p, _ in entries]
    ends = [s - 1 for s in starts[1:]] + [total - 1]
    items = []  # (kind, number, title, first, last)
    for (p, raw), last in zip(entries, ends):
        title = repair_title(reader, raw, p)
        m_part, m_ch = PART_RE.match(title), CHAPTER_RE.match(title)
        if m_part:
            items.append(("part", title, m_part[2].strip(), p, last))
        elif m_ch:
            items.append(("chapter", int(m_ch[1]), title, p, last))
        else:
            items.append(("other", None, title, p, last))

    # Pages before the first outline entry (the cover) belong to the first entry.
    if items and items[0][3] > 0:
        k, num, title, _, last = items[0]
        items[0] = (k, num, f"Cover and {title[:1].lower()}{title[1:]}", 0, last)

    first_part = next((i for i, it in enumerate(items) if it[0] == "part"), None)
    if first_part is None:
        fail("no 'Part N — Title' entry in the PDF outline")
    last_ch = max((i for i, it in enumerate(items) if it[0] == "chapter"), default=None)
    if last_ch is None:
        fail("no 'NN — Title' chapter entry in the PDF outline")

    out, part_no, part_dir, part_title, front_no, back_no = [], 0, None, None, 0, 0
    for i, (kind, num, title, a, b) in enumerate(items):
        if i < first_part:
            front_no += 1
            out.append((f"00-front-matter/{front_no:02d}-{slugify(title, 8)}.pdf", title, a, b))
        elif kind == "part":
            part_no += 1
            part_title = title
            part_dir = f"{part_no:02d}-{slugify(title)}"
            if part_no >= 99:
                fail("more than 98 parts")
            out.append((f"{part_dir}/00-part-{slugify(title)}.pdf", num, a, b))
            dest = dests.get(f"part-{part_no - 1}")
            if dest is not None and dest != a:
                fail(f"part {title!r} starts on page {a + 1}, its destination on page {dest + 1}")
        elif kind == "chapter":
            dest = dests.get(f"ch-{num:02d}")
            if dest is not None and dest != a:
                fail(f"chapter {num} starts on page {a + 1}, its destination on page {dest + 1}")
            name = CHAPTER_RE.match(title)[2]
            out.append((f"{part_dir}/{num:02d}-{short_slug(name)}.pdf", title, a, b))
        elif i > last_ch:
            back_no += 1
            out.append((f"99-back-matter/{back_no:02d}-{slugify(title, 8)}.pdf", title, a, b))
        else:
            fail(f"outline entry {title!r} (page {a + 1}) inside part {part_title!r} is "
                 "neither a part nor a numbered chapter")
    paths = [o[0] for o in out]
    if len(set(paths)) != len(paths):
        fail("two split files would get the same name")
    if paths != sorted(paths):
        fail("split file names do not sort in page order")
    return out


def check_ranges(ranges, total):
    expect = 0
    for path, _, a, b in ranges:
        if a != expect:
            kind = "gap" if a > expect else "overlap"
            fail(f"page ranges have a {kind} before {path}: expected page {expect + 1}, "
                 f"range starts at page {a + 1}")
        if b < a:
            fail(f"empty page range for {path}")
        expect = b + 1
    if expect != total:
        fail(f"page ranges end at page {expect}, the book has {total} pages")


def page_fingerprint(page):
    text = page.extract_text() or ""
    contents = page.get_contents()
    length = len(contents.get_data()) if contents is not None else 0
    return hashlib.sha256(f"{length}\0{text}".encode()).hexdigest()


def split_files(out_dir):
    files = []
    for dirpath, _, names in os.walk(out_dir):
        files += [os.path.join(dirpath, n) for n in names if n.endswith(".pdf")]
    return sorted(files, key=lambda f: os.path.relpath(f, out_dir))


def verify(book, out_dir):
    """Concatenate every split file in sorted path order and compare it page by page."""
    reader = PdfReader(book)
    total = len(reader.pages)
    files = split_files(out_dir)
    if not files:
        fail(f"no split PDFs in {out_dir}")
    pages = []
    for f in files:
        pages += [(f, p) for p in PdfReader(f).pages]
    if len(pages) != total:
        fail(f"{len(files)} files hold {len(pages)} pages, the book has {total} pages")
    for n, (f, p) in enumerate(pages):
        if page_fingerprint(p) != page_fingerprint(reader.pages[n]):
            fail(f"page {n + 1} of the concatenation ({os.path.relpath(f, out_dir)}) differs "
                 f"from page {n + 1} of the book")
    # Every named destination must land, at the same page offset, in the file that holds
    # its target page; otherwise links inside that file break.
    by_page = named_destinations_by_page(reader)
    start = ndest = 0
    for f in files:
        r = PdfReader(f)
        have = {}
        for name, d in r.named_destinations.items():
            try:
                have[str(name)] = r.get_destination_page_number(d)
            except Exception:
                pass
        for book_page in range(start, start + len(r.pages)):
            for name, _ in by_page.get(book_page, []):
                if have.get(name) != book_page - start:
                    fail(f"named destination {name} is missing from {os.path.relpath(f, out_dir)} "
                         f"or points at the wrong page")
                ndest += 1
        start += len(r.pages)
    print(f"pdf-split: {len(files)} files, {len(pages)} pages = full book ({total} pages), "
          f"{ndest} named destinations kept ✓")
    return files


DEST_PARAMS = {  # the parameters each destination type carries after the page, in PDF order
    "/XYZ": ("left", "top", "zoom"), "/Fit": (), "/FitB": (),
    "/FitH": ("top",), "/FitBH": ("top",), "/FitV": ("left",), "/FitBV": ("left",),
    "/FitR": ("left", "bottom", "right", "top"),
}


def named_destinations_by_page(reader):
    """Map each book page index to the named destinations that point at it.

    Links in the book use named /Dest entries that live in the document catalog, which
    add_page() does not copy; without re-adding them, even same-chapter links break."""
    by_page = {}
    for name, dest in reader.named_destinations.items():
        try:
            page = reader.get_destination_page_number(dest)
        except Exception:
            continue
        if page is not None and page >= 0:
            by_page.setdefault(page, []).append((str(name), dest))
    return by_page


def copy_destinations(writer, by_page, a, b):
    """Re-create, in writer, every named destination whose target lies on book pages a..b."""
    n = 0
    for book_page in range(a, b + 1):
        for name, dest in by_page.get(book_page, []):
            typ = str(dest.typ) if dest.typ in DEST_PARAMS else "/XYZ"
            arr = ArrayObject([writer.pages[book_page - a].indirect_reference, NameObject(typ)])
            for attr in DEST_PARAMS[typ]:
                v = getattr(dest, attr, None)
                arr.append(NullObject() if v is None else FloatObject(v))
            writer.add_named_destination_array(TextStringObject(name), arr)
            n += 1
    return n


def write(book, out_dir):
    reader = PdfReader(book)
    total = len(reader.pages)
    meta = reader.metadata or {}
    book_title = str(meta.get("/Title") or BOOK_TITLE_FALLBACK)
    ranges = plan(reader)
    check_ranges(ranges, total)
    dests_by_page = named_destinations_by_page(reader)

    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    for rel, title, a, b in ranges:
        dst = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        w = PdfWriter()
        for n in range(a, b + 1):
            w.add_page(reader.pages[n])
        copy_destinations(w, dests_by_page, a, b)
        info = {"/Title": f"{book_title} — {title}"}
        for k in COPY_KEYS:
            if meta.get(k):
                info[k] = str(meta[k])
        info["/Creator"] = "scripts/notebooklm/split_pdf.py"
        w.add_metadata(info)
        w.create_viewer_preferences()
        w.viewer_preferences.display_doctitle = True
        with open(dst, "wb") as fh:
            w.write(fh)
    return ranges


def readme_section(ranges, out_dir):
    groups = []
    for rel, title, a, b in ranges:
        d = rel.split("/", 1)[0]
        if not groups or groups[-1][0] != d:
            groups.append([d, 0, 0, a, b])
        groups[-1][1] += 1
        groups[-1][2] += b - a + 1
        groups[-1][4] = b
    total = sum(g[2] for g in groups)
    r = [README_HEADING, ""]
    r += [f"`{os.path.basename(out_dir.rstrip('/'))}/` holds the book PDF (`make pdf`) cut along its table "
             "of contents: one folder per part, with the part's title page as `00-part-<slug>.pdf` "
             "and one PDF per chapter, `NN-<chapter>.pdf`, named by the chapter's number in the book. "
             "`00-front-matter/` holds the cover, contents and \"About this book\". The appendices are "
             "online only, so they are not in the PDF and not in the split.", ""]
    r += ["Joined in sorted path order, the files are the whole book, page for page; the build "
             "checks this and fails otherwise. Each file carries the book's metadata with its own "
             "title. External links work; a link to a page in another file does not.", ""]
    r += ["| Folder | Files | Pages | Book pages |", "|---|---|---|---|"]
    for d, nfiles, npages, a, b in groups:
        r.append(f"| `{d}/` | {nfiles} | {npages} | {a + 1}–{b + 1} |")
    r.append(f"| **Total** | **{len(ranges)}** | **{total}** | 1–{total} |")
    return "\n".join(r) + "\n"


def update_readme(path, section):
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if README_HEADING in text:
        head, rest = text.split(README_HEADING, 1)
        nxt = re.search(r"^## ", rest, re.M)
        text = head + section + ("\n" + rest[nxt.start():] if nxt else "")
    else:
        # Before "## Regenerate" when there is one, else at the end.
        m = re.search(r"^## Regenerate", text, re.M)
        text = text[:m.start()] + section + "\n" + text[m.start():] if m else text.rstrip("\n") + "\n\n" + section
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main(argv):
    if len(argv) == 3 and argv[0] == "--check":
        verify(argv[1], argv[2])
        return
    readme = None
    if len(argv) == 4 and argv[2] == "--readme":
        readme = argv[3]
        argv = argv[:2]
    if len(argv) != 2:
        sys.exit(__doc__)
    book, out_dir = argv
    if not os.path.isfile(book):
        fail(f"{book} not found; run make pdf first")
    ranges = write(book, out_dir)
    for rel, title, a, b in ranges:
        print(f"  {rel:<60} {b - a + 1:>4} pages  (book pages {a + 1}–{b + 1})")
    verify(book, out_dir)
    if readme:
        update_readme(readme, readme_section(ranges, out_dir))


if __name__ == "__main__":
    main(sys.argv[1:])
