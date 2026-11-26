# Command reference

Every command this repository offers. There is no runtime: the commands set up optional tools, check the text and build the optional PDF edition.

Run `make help` for the list as the Makefile itself reports it; the Makefile is the source of truth if this page and it ever disagree.

## make targets

### Lifecycle

Nothing is compiled and no package manager is involved, so these targets do the honest equivalent for a documentation repository.

| Target | What it does | When to run it |
|---|---|---|
| `make help` | Lists every target with a one-line description. It is the default target | Any time |
| `make install` | Checks that `python3`, `jq` and `git` are present and reports whether the optional `mmdc` is. Installs nothing; exits non-zero if a required tool is missing | Once, after cloning |
| `make update` | Fast-forwards the checkout to the latest published edition (`git pull --ff-only`) | To get a newer edition |
| `make uninstall` | Runs `make clean`. Nothing else is ever installed, so there is nothing else to remove | To tidy up |
| `make build` | Does nothing, and says so: the book is read as Markdown | Never needed |
| `make dev` | Prints how to preview the book. There is no dev server | When you want a reminder |
| `make clean` | Removes scratch render output, `dist/`, `notebookLM/` and Python caches. It never touches `book/` or `assets/` | After local rendering experiments |

Reading the book needs none of these.

### Checks

| Target | What it does | Needs |
|---|---|---|
| `make agent:check` | The repository gate, and the command CI runs. It runs `check-agent-drift`, `check-feature-equivalence`, `check-platform-targets`, `check-action-pinning` and the book check without Mermaid rendering | bash, Python 3, jq, git |
| `make check-book` | The full book check: length, code fences, local links, images, and a render of every Mermaid block when `mmdc` is on `PATH` | Python 3; the Mermaid CLI to render |
| `make check-book-no-mermaid` | The book check without rendering. This is the form CI uses | Python 3 |
| `make test` | An alias for `make check-book` | As above |
| `make check-doc-standards` | Checks that `README.md` and `docs/` follow the documentation standard: shared footer and themed Mermaid | bash, jq |
| `make check-action-pinning` | Fails if any workflow refers to an action or container by a movable reference instead of a commit | bash |
| `make lint` | Runs `check-doc-standards` and `check-action-pinning` | bash, jq |

### PDF edition

| Target | What it does | Needs |
|---|---|---|
| `make pdf` | Builds the whole book as one PDF, `dist/AI-Native Development.pdf`: a cover with the version, commit, license and build time, a clickable table of contents with page numbers, the 34 chapters, page numbers at the bottom of every page, and PDF metadata. The appendices are not printed: the contents lists them as links to their files on GitHub, and every link to an appendix opens it there. In each chapter, external links carry a numbered citation marker, `[n]`, and the Sources section is printed as the matching numbered reference list. It then checks the metadata and that every internal link resolves | Node.js 22.12 or later, Python 3 with `pypdf` |
| `make clean` | Also removes `dist/`, where the PDF is written | Nothing |

Run `make agent:check` and `make check-book` before every pull request. The first is what CI will run; the second is the only one that proves the diagrams render. `make agent:check` does not include the documentation standard, so run `make lint` as well when you change `README.md` or `docs/`.

### NotebookLM packages

| Target | What it does | Needs |
|---|---|---|
| `make notebookLM` | Packages the book for NotebookLM, one notebook and one Video Overview per section, in `notebookLM/` at the repository root. `make notebooklm` is the same target | Node.js 22.12 or later |
| `make clean` | Also removes `notebookLM/` | Nothing |

`notebookLM/` is a build output, like `dist/`: it is git-ignored and every run wipes and rebuilds it. Regenerate it after the book changes, then upload a section's files to its notebook. The generator is `scripts/notebooklm/build.mjs`; `make notebookLM` runs `npm ci` first when `node_modules/` is missing and uses the same pinned Mermaid CLI and puppeteer as `make pdf`.

It reads the reading order from the Contents tables in `book/README.md`. Each part is a section, and a sub-heading inside a part (the Workshop) is a section of its own, so a new chapter lands in the right package when it is added to the contents. The appendices are left out: they are reference tables that narrate poorly, and every package links to them on GitHub instead.

Each section folder, `notebookLM/NN-<section>/`, holds:

| File | What it is |
|---|---|
| `01-video-outline.md` | Narrative guidance built only from the chapters' own text: learning objectives from each opener, then per chapter the core concept (from `## Mental model`), key sections, suggested visuals and key takeaways (from `## Checklist`), and narration guidance |
| `NN-chNN-<slug>.md` | Each chapter, cleaned for NotebookLM: no footer navigation, links to other book files rewritten to GitHub URLs, images pointed at `media/*.png`, and a `Diagram: media/…png — caption` line after every Mermaid block, which is kept as text |
| `visual-references.pdf` | Every figure and Mermaid diagram in the section, one per page with a caption |
| `media/` | PNG versions of the section's figures and Mermaid diagrams at 2x on white. NotebookLM does not accept SVG sources |
| `README.md` | Not a source: which files to upload, the source count against NotebookLM's per-notebook limit, Video Overview settings and a steering prompt |

`notebookLM/README.md` lists the sections with their chapters, source files, images and word counts. The Markdown output is deterministic for a given commit; `BOOK_COMMIT` and `BOOK_VERSION` override the commit and version it records, as for `make pdf`. A Mermaid block that does not render, an image that does not exist or a section without chapters fails the run.

### Agent and platform targets

These keep the agent instruction files consistent across the coding tools the repository declares. Most contributors only meet them through `make agent:check`.

| Target | What it does |
|---|---|
| `make check-agent-drift` | Checks that the thin adapters (`CLAUDE.md`, the Cursor rule) still point at `AGENTS.md` |
| `make check-feature-equivalence` | Checks cross-tool parity against the capability registry in `core/capabilities/platforms.json` |
| `make check-platform-targets` | Checks declared tool versions against the README |
| `make check-capability-registry` | Checks the capability registry; skipped while the repository ships no checker for it |
| `make check-manifest-declares MANIFEST=<file> KEYS="<key> ..."` | Asserts that a manifest declares the given keys |
| `make platform-targets-sync`, `platform-targets-sync-capabilities`, `platform-targets-assert`, `platform-targets-cochange` | Maintain `docs/engineering/build-and-release/platform-targets.json` |
| `make agent-polish-gate` | Syncs and asserts the platform targets, then runs `agent:check` and `check-doc-standards` |

## scripts/check-book.py

The book checker. `make check-book` calls it; call it directly to pass flags or to check only some files.

```text
python3 scripts/check-book.py [FLAGS] [FILE.md ...]
```

| Invocation | Effect |
|---|---|
| `scripts/check-book.py` | Check every `.md` file under `book/` |
| `scripts/check-book.py FILE.md ...` | Check only the named files |
| `scripts/check-book.py --no-mermaid` | Skip rendering Mermaid blocks; everything else still runs |
| `scripts/check-book.py --require-mermaid` | Fail when the Mermaid CLI (`mmdc`) is not on `PATH`, instead of skipping with a notice |
| `scripts/check-book.py --help` | Print the usage text |

### What it checks

| Check | Rule |
|---|---|
| Length | A file must have fewer than 400 lines |
| Code fences | The number of triple-backtick markers in a file must be even |
| Local links | Every relative link target must exist on disk. External URLs, `mailto:` links and `#anchor` fragments are not followed |
| Images | Every relative image path must exist on disk |
| Mermaid | Every `mermaid` block must render with `mmdc`, when the CLI is available and `--no-mermaid` is not given |

Links and images inside code blocks and inline code are ignored.

### Output

One line per file, any errors indented under it, then a summary:

```text
ok   book/01-what-is-ai-native-development.md
FAIL book/14-hooks.md
   ERROR: broken link: 99-missing.md
check-book: 35 files, 1 failed, 53 Mermaid blocks rendered
```

The summary ends with `rendered` or with `NOT rendered (mmdc missing or --no-mermaid)`. Only the first means the diagrams were checked.

### Exit status

| Status | Meaning |
|---|---|
| 0 | Every file passed |
| 1 | At least one file has an error |
| 2 | Usage or environment problem: an unknown flag, no Markdown files found, or `--require-mermaid` without `mmdc` |

### Environment

| Variable | Effect |
|---|---|
| `MMDC_PUPPETEER_CONFIG` | Path to a Puppeteer config file, passed to `mmdc` as `-p`. Use it where the CLI's browser needs extra launch options, for example in a container |

The Mermaid CLI comes from the npm package `@mermaid-js/mermaid-cli`:

```bash
npm install -g @mermaid-js/mermaid-cli
```

## scripts/pdf/build.mjs

The PDF build behind `make pdf`. It reads the reading order from the Contents tables in `book/README.md`, renders each file with markdown-it, renders every Mermaid block to inline SVG with the Mermaid CLI, paginates with Paged.js in headless Chromium, and writes the metadata with `scripts/pdf/metadata.py`. The appendices part of the Contents tables is left out of the print and listed in the contents as links to `book/<file>` on GitHub; links to an appendix become links to that file, keeping any `#anchor`. In each chapter, every external link gets a citation marker numbered in order of first appearance, and `## Sources` becomes a numbered reference list (`[n] title — domain`) using the same numbers; a URL listed only under Sources takes the next number. A Mermaid block that fails to render, a link to a missing anchor, or content wider than the page fails the build.

`make pdf` runs `npm ci` when `node_modules/` is missing; the first run downloads a headless Chrome for puppeteer. Install the Python dependency once:

```bash
python3 -m pip install -r requirements-pdf.txt
make pdf
```

The cover and metadata take the version from the latest released `## [x.y.z]` heading in `docs/CHANGELOG.md`, with `+<short-sha>` appended unless `HEAD` is exactly at tag `vX.Y.Z`. The commit and build time come from git and the clock. Override them for a reproducible build:

| Variable | Effect |
|---|---|
| `BOOK_COMMIT` | The full commit SHA printed on the cover and in the metadata |
| `BOOK_VERSION` | The version string, used as given |
| `BOOK_BUILD_TIME` | The build timestamp, ISO 8601 in UTC, for example `2026-11-26T12:00:00Z` |
| `SOURCE_DATE_EPOCH` | The build time as Unix seconds, when `BOOK_BUILD_TIME` is not set |
| `BOOK_PDF_KEEP_HTML` | Keep the intermediate `dist/pdf-build/book.html` for debugging |

Print the metadata of a built PDF, or re-run its checks:

```bash
python3 scripts/pdf/metadata.py --show "dist/AI-Native Development.pdf"
python3 scripts/pdf/metadata.py --check "dist/AI-Native Development.pdf"
```

The [Book PDF workflow](../../../.github/workflows/book-pdf.yml) runs `make pdf` on every push to `main` and publishes the result to GitHub Pages, at <https://tamircohen28.github.io/ai-native-dev-guide/>. On a pull request that touches the book or the PDF tooling it builds the PDF and uploads it as a workflow artifact, without deploying.

## scripts/check-doc-standards.sh

Holds `README.md` and `docs/` to the [documentation standard](../../agent-guidelines/documentation-standards.md). It does not read `book/`.

```text
bash scripts/check-doc-standards.sh [--fix] [--strict] [--config FILE] [--init FILE] [ROOT]
```

| Flag | Effect |
|---|---|
| `--fix` | Append or repair the shared footer and insert the Mermaid theme line. Diagram styling is reported, never rewritten |
| `--strict` | Also flag box-drawing characters outside a `text` fence |
| `--config FILE` | Use a config other than `config/docs/doc-standards.json` |
| `--init FILE` | Use a Mermaid init file other than the one the config names |
| `ROOT` | The repository root to check; defaults to the current directory |

Violations are printed as `path:line kind: detail`. Exit status is 0 when clean, 1 when violations remain, 2 for a usage or environment problem.

## Figure scripts

For contributors who change a figure. Both write into `book/assets/`.

| Script | Builds | Needs |
|---|---|---|
| `book/assets/_src/figures/build.py` | The cover and the six concept figures | Python 3 |
| `book/assets/_src/make_charts.py --data FILE` | The ten field-data charts | Python 3 and the field-data aggregate, which is not in this repository |

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
