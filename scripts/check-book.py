#!/usr/bin/env python3
"""Check the book's Markdown files: length, code fences, local links, images, Mermaid syntax.

Usage:
  scripts/check-book.py                  check every .md file under book/
  scripts/check-book.py FILE.md ...      check the named files
  scripts/check-book.py --no-mermaid     skip rendering Mermaid blocks
  scripts/check-book.py --require-mermaid  fail when the Mermaid CLI (mmdc) is missing

Mermaid blocks are rendered with `mmdc` (npm: @mermaid-js/mermaid-cli) when it is on PATH.
Without it they are skipped with a notice, unless --require-mermaid is given.
Exit status: 0 all files ok, 1 at least one error, 2 usage or environment problem.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

MAX_LINES = 400
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BOOK = os.path.join(ROOT, "book")


def render_mermaid(block):
    with tempfile.TemporaryDirectory() as d:
        src, out = os.path.join(d, "d.mmd"), os.path.join(d, "d.svg")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(block)
        cmd = ["mmdc", "-i", src, "-o", out, "-q"]
        cfg = os.environ.get("MMDC_PUPPETEER_CONFIG")
        if cfg:
            cmd += ["-p", cfg]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            msg = (r.stderr or r.stdout).strip().splitlines()
            return " | ".join(msg[:3])[:300] or "mmdc failed"
    return None


def check(path, mermaid):
    errors = []
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    here = os.path.dirname(os.path.abspath(path))
    lines = text.splitlines()
    if len(lines) >= MAX_LINES:
        errors.append(f"{len(lines)} lines (limit {MAX_LINES - 1})")
    if text.count("```") % 2:
        errors.append("odd number of ``` fences")
    blocks = re.findall(r"```mermaid\n(.*?)```", text, flags=re.S)
    if mermaid:
        for i, block in enumerate(blocks, 1):
            problem = render_mermaid(block)
            if problem:
                errors.append(f"mermaid block {i} failed: {problem}")
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    body = re.sub(r"`[^`\n]*`", "", body)
    targets = re.findall(r"(!?)\[[^\]]*\]\(([^)\s]+)", body)
    targets += [("", t) for t in re.findall(r"^\[[^\]]+\]:\s+(\S+)", body, flags=re.M)]
    for is_img, target in targets:
        if re.match(r"^(https?:|mailto:|#)", target):
            continue
        rel = target.split("#")[0]
        if rel and not os.path.exists(os.path.join(here, rel)):
            errors.append(f"broken {'image' if is_img else 'link'}: {target}")
    return errors, len(blocks)


def main(argv):
    flags = {a for a in argv if a.startswith("--")}
    files = [a for a in argv if not a.startswith("--")]
    unknown = flags - {"--no-mermaid", "--require-mermaid", "--help"}
    if unknown or "--help" in flags:
        print(__doc__)
        return 2 if unknown else 0
    if not files:
        files = sorted(glob.glob(os.path.join(BOOK, "*.md")))
    if not files:
        print("check-book: no Markdown files found under book/", file=sys.stderr)
        return 2
    have_mmdc = shutil.which("mmdc") is not None
    mermaid = "--no-mermaid" not in flags and have_mmdc
    if "--require-mermaid" in flags and not have_mmdc:
        print("check-book: mmdc not found (npm install -g @mermaid-js/mermaid-cli)", file=sys.stderr)
        return 2
    failed = diagrams = 0
    for path in files:
        errors, n = check(path, mermaid)
        diagrams += n
        print(f"{'FAIL' if errors else 'ok  '} {os.path.relpath(path, ROOT)}")
        for e in errors:
            print("   ERROR:", e)
        failed += bool(errors)
    state = "rendered" if mermaid else "NOT rendered (mmdc missing or --no-mermaid)"
    print(f"check-book: {len(files)} files, {failed} failed, {diagrams} Mermaid blocks {state}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
