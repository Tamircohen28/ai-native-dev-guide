# Troubleshooting

Problems with reading or checking the book. For problems with coding agents themselves, the book has its own catalogue: [chapter 27](../../book/27-troubleshooting-common-problems.md).

## Quick lookup

| Symptom | Likely cause | Fix |
|---|---|---|
| A diagram shows as a block of code | The viewer does not render Mermaid | [Mermaid not rendering](#mermaid-not-rendering) |
| A link between chapters goes nowhere | A file was moved or renamed out of `book/` | [Broken relative links](#broken-relative-links-after-moving-files) |
| An image is missing | `book/assets/` was not copied with the chapters | [Broken relative links](#broken-relative-links-after-moving-files) |
| `make check-book` prints `FAIL` | A length, fence, link, image or Mermaid error | [Checker failures](#checker-failures) |
| The summary says `NOT rendered` | The Mermaid CLI is not on `PATH` | [Mermaid CLI missing](#the-mermaid-cli-is-missing) |
| `check-doc-standards.sh` reports violations | A page under `docs/` lacks the footer or a themed diagram | [Documentation standard failures](#documentation-standard-failures) |

## Mermaid not rendering

**In a viewer.** The diagrams are fenced code blocks tagged `mermaid`. A viewer that does not know Mermaid shows the source text.

| Viewer | What to do |
|---|---|
| GitHub | Nothing; it renders Mermaid. If one diagram shows an error box, the diagram itself is broken: please open an issue |
| VS Code | Install a Mermaid preview extension, then reopen the Markdown preview |
| Obsidian | Renders by default; check that you are in reading view or live preview, not source mode |
| Other | Look for a Mermaid plugin, or read that chapter on GitHub |

**In the checker.** A line such as `ERROR: mermaid block 2 failed: ...` means the Mermaid CLI could not render the second diagram in that file. Common causes:

| Cause | Fix |
|---|---|
| A node label contains brackets, a colon or a quote and is not wrapped in double quotes | Write the label as `A["text (with brackets)"]` |
| An edge label is not quoted | Write it as `-->|"label"|` |
| A reserved word such as `end` is used as a node id | Rename the node |
| The CLI cannot start its browser | Set `MMDC_PUPPETEER_CONFIG` to a Puppeteer config file; the checker passes it to `mmdc` with `-p` |

To isolate one diagram, check only its file:

```bash
python3 scripts/check-book.py book/10-mcp-how-it-works.md
```

### The Mermaid CLI is missing

The checker's last line says whether diagrams were rendered:

```text
check-book: 35 files, 0 failed, 53 Mermaid blocks NOT rendered (mmdc missing or --no-mermaid)
```

`NOT rendered` means the diagrams were counted but not checked. Install the CLI and run again:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc --version
make check-book
```

To make a missing CLI an error instead of a notice, pass `--require-mermaid`; the script then exits with status 2.

## Broken relative links after moving files

Every link between chapters and every image path is relative to the `book/` folder. They break when the folder's shape changes.

| What happened | Why it breaks | Fix |
|---|---|---|
| One chapter was copied somewhere else | Its links point at sibling files that are not there | Copy the whole `book/` folder |
| `book/` was copied without `book/assets/` | Images resolve to missing files | Copy `assets/` too |
| A chapter was renamed | Other chapters, the contents page and Appendix D still use the old name | Search for the old name and update every reference |
| A chapter was moved into a subfolder | Its own relative links are now one level off, and inbound links are stale | Keep chapters flat in `book/`; the checker and the footer navigation assume it |

Find every broken link and image in one pass, without rendering diagrams:

```bash
python3 scripts/check-book.py --no-mermaid
```

Each problem is printed under its file as `ERROR: broken link: <target>` or `ERROR: broken image: <target>`. The checker tests that the target file exists; it does not test `#anchor` fragments or external URLs.

After renaming a chapter, find the stale references:

```bash
grep -rn "old-file-name.md" book/ README.md docs/
```

## Checker failures

`make check-book` prints `ok` or `FAIL` for each file, the errors under each failing file, then a summary line. Its exit status is 0 when every file passes, 1 when at least one file has an error, and 2 for a usage or environment problem.

| Error text | Meaning | Fix |
|---|---|---|
| `NNN lines (limit 399)` | The file has 400 lines or more | Tighten the chapter or split the topic; see the [authoring rules](../CONTRIBUTING.md#authoring-rules) |
| ``odd number of ``` fences`` | A code block was opened and never closed, or closed twice | Find the unmatched fence; a quick way is to look for the first place where prose is rendered as code |
| `broken link: <target>` | A relative link points at a missing file | Fix the path or restore the file |
| `broken image: <target>` | A relative image path points at a missing file | Fix the path or regenerate the figure |
| `mermaid block N failed: ...` | Diagram number N in that file did not render | See [Mermaid not rendering](#mermaid-not-rendering) |
| `no Markdown files found under book/` | The script was run from a copy without `book/` | Run it from a full clone |
| `mmdc not found` | `--require-mermaid` was given and the CLI is missing | Install the CLI, or drop the flag |

The fence check counts every occurrence of three backticks in the file, so a stray run of three inside a sentence trips it as surely as an unclosed block.

## Documentation standard failures

Pages under `docs/` and the root `README.md` are held to the repository's [documentation standard](../agent-guidelines/documentation-standards.md). The checker prints one line per violation as `path:line kind: detail`.

| Kind | Meaning | Fix |
|---|---|---|
| `footer-missing`, `footer-wrong` | The page does not end with the shared two-link footer | Run the fixer |
| `mermaid-init-missing`, `mermaid-init-wrong` | A Mermaid block does not start with the shared theme line | Run the fixer |
| `mermaid-style` | A diagram sets its own colours with `classDef`, `class`, `style` or `fill:` | Remove the styling by hand; the fixer does not rewrite diagrams |

```bash
bash scripts/check-doc-standards.sh --fix .
```

This standard does not apply to `book/`. Book diagrams are plain Mermaid with no theme line.

## Still stuck

[Open an issue](https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose) with the command you ran and the last lines of its output.

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
