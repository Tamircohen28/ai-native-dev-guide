---
name: run-ai-native-dev-guide
description: Use when asked to run, open, preview or validate the book in this repo. Trigger phrases - "run the book", "preview the book", "open the guide", "validate the book", "check the book", "make check-book failed", "does this Mermaid diagram render", "check the links", "is this chapter too long", "render the diagrams in chapter N".
---

# Run, preview and validate the book

This repo is a book, not an app: there is no build and nothing to start. "Running" it means
reading the Markdown and passing the checker.

## Open it

Start at `book/README.md` (cover, preface, contents). Chapters are `book/NN-slug.md`,
appendices `book/A-*.md` to `book/E-*.md`, figures `book/assets/*.svg`. Any Markdown preview
that renders Mermaid (GitHub, VS Code) shows it as readers see it.

## Validate it

```bash
make check-book                                  # every file under book/
python3 scripts/check-book.py book/13-skills.md  # one chapter
python3 scripts/check-book.py --require-mermaid  # exit 2 if mmdc is missing
```

Each file prints `ok` or `FAIL` with one `ERROR:` line per problem, then a summary such as
`check-book: 35 files, 0 failed, 53 Mermaid blocks rendered`. Exit 0 is clean, 1 means at
least one file failed, 2 is a usage or environment problem. If the summary says
`NOT rendered`, `mmdc` is not on PATH and the diagrams were skipped, so the run proves
nothing about them: `npm install -g @mermaid-js/mermaid-cli`, then run it again.

## Fix the common failures

| Error line | Cause | Fix |
|---|---|---|
| `mermaid block N failed: ...` | Block N (counted from the top of the file) has a syntax error | Quote every label that contains punctuation (`A["text (x)"]`), then render the chapter as shown below |
| `broken link: ...` / `broken image: ...` | A relative target does not exist next to the file | Fix the path or the filename; chapters link to each other as `NN-slug.md`, images as `assets/name.svg` |
| `NNN lines (limit 399)` | The file is at or over 400 lines | Cut or move content to an appendix; never join lines to fit |
| `odd number of` triple-backtick `fences` | A code fence is not closed | Close it; Mermaid and link errors reported for the same file usually go with it |

## Render one chapter's Mermaid blocks

```bash
out="$(mktemp -d)"
mmdc -i book/01-what-is-ai-native-development.md -o "$out/ch.md" -q
ls "$out"    # ch-1.svg, ch-2.svg ... one per block, in file order
```

Open the SVGs to check layout as well as syntax. If Chromium will not launch (sandbox, CI),
set `MMDC_PUPPETEER_CONFIG` to a puppeteer JSON config; the checker passes it to `mmdc -p`.
Hard rules for editing the book: `.claude/rules/constraints.md`.
