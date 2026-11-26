# Contributing

This repository is a book. A contribution is a correction, a clarification, a new example, a figure, or a change to the tooling that checks the text. This page covers the conventions for all of them and the authoring rules every chapter follows.

For a worked example from branch to pull request, see the [getting-started guide](engineering/guides/getting-started.md).

## Before you start

- Small fixes (a typo, a broken link, a wrong flag) can go straight to a pull request.
- Anything larger (a new section, a restructured chapter, a new figure) is easier to land if you open an issue first and agree on the scope.
- Run `make install` once after cloning, and install the Mermaid CLI if you intend to touch a diagram. See [Prerequisites](../README.md#prerequisites).

## Branches

Work on a branch, never on `main`. Name it by the kind of change:

| Prefix | Use for | Example |
|--------|---------|---------|
| `feat/` | New content or new tooling | `feat/ch14-hook-timeouts` |
| `fix/` | Corrections to text, links, figures or scripts | `fix/ch08-permission-order` |

## Commits

One logical change per commit, with a conventional message:

```text
<type>(<scope>): <description>
```

- **type**: `feat`, `fix`, `docs`, `chore`, `ci`, `refactor` or `test`.
- **scope**: the part of the repository touched. Use the chapter for book text (`ch07`, `appendix-d`), otherwise the area (`figures`, `scripts`, `docs`, `ci`).
- **description**: imperative, lower case, no trailing full stop.

```text
fix(ch08): correct the deny-ask-allow evaluation order
feat(ch14): add a tested Stop hook example
docs(contributing): explain how to regenerate the sources appendix
```

## Pull requests

1. Rebase on the current `main` and make sure the branch contains only your change.
2. Run both checks and keep their last lines:

   ```bash
   make agent:check
   make check-book
   ```

   If you touched `README.md` or anything under `docs/`, also run `make lint`, which checks the documentation standard and workflow action pinning.

3. Open the pull request and fill in the template. The test plan asks for the output of both commands; paste it, do not summarise it.
4. For a factual change, name the source in the pull request: the page, and the date you read it.
5. If you changed a figure, open it at full size and say so in the test plan.
6. CI must be green and every review thread resolved before a merge. The repository owner merges; opening a pull request is not merging it.

Add a line under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md) and in the root `CHANGELOG.md` for any change a reader would notice.

## Authoring rules

These rules are what keeps 29 chapters reading like one book. `make check-book` enforces the mechanical ones; review enforces the rest.

### One chapter, one file, under 400 lines

Each chapter and appendix is a single Markdown file in `book/`, named `NN-topic.md` or `X-topic.md`. A file must stay under 400 lines; the checker fails at 400. When a chapter outgrows the limit, tighten it or split the topic into two chapters. Do not move text into a side file.

### The fixed chapter skeleton

Every numbered chapter has the same parts in the same order, so a reader can skim to the one they need:

| # | Part | What goes in it |
|---|------|-----------------|
| 1 | Title and opening paragraph | What the reader can do after the chapter |
| 2 | Mental model | The idea in plain words, with one Mermaid diagram |
| 3 | Core sections | The mechanics, with examples that can be copied and run |
| 4 | From the field | What happened when this was used for real, from the field data |
| 5 | Common problems | A table of symptom, cause and fix |
| 6 | Checklist | Short, checkable items |
| 7 | Try it | Exercises the reader can do in their own repository |
| 8 | Sources | Every page the chapter relies on, with its URL |
| 9 | Footer navigation | Previous chapter, contents, next chapter |

Callouts have fixed meanings: `Note` adds a detail, `Warning` marks something that can hurt, `Field note` is an observation from the field data.

### Facts come from primary sources, with a date

- A statement about how a tool behaves must be confirmed on a primary page (official documentation, a specification, the vendor's own post) at the time of writing. Do not write tool behaviour from memory.
- Facts that change with releases (models, prices, limits, defaults, version numbers) carry an "as of" month and year.
- If a claim cannot be confirmed on a primary page, leave it out or mark it as unconfirmed and say where the reader can check.
- Field data is labelled as field data. It is one developer's numbers, so present it as an example, never as a benchmark.

### Nothing private in the text

Book text contains no secrets, tokens, hostnames, personal names or project names. Incidents are told generically: "a deployment script", not the repository it lived in. This applies to code samples, transcripts and figure labels as well as prose.

### Diagrams and figures

- Diagrams inside chapters are Mermaid blocks, written inline so they render on GitHub. Keep node labels in double quotes.
- Figures and charts are static SVG files in `book/assets/`, generated by the scripts in `book/assets/_src/`. Do not hand-edit a generated file: change the script and regenerate.
  - The cover and the six concept figures come from `book/assets/_src/figures/build.py`, which needs only Python 3.
  - The ten field-data charts come from `book/assets/_src/make_charts.py`, which reads an aggregate of the session data that is private and not in this repository. If you cannot regenerate a chart because that input is missing, stop and say so in the pull request or open an issue. Do not patch the output.
- Every image needs alt text that says what the figure shows.

### Keep the sources appendix in step

`book/D-sources.md` is the union of every chapter's Sources section, with the chapters that cite each page. It is maintained by hand: no generator for it lives in this repository. When a chapter's Sources list changes, update `book/D-sources.md` to match in the same pull request, so the two never disagree. If a URL moved, print the new address and record the move under "Moved addresses".

### Check before you open the pull request

```bash
make check-book
```

It must end with `0 failed` and report the Mermaid blocks as `rendered`. A run that says `NOT rendered` did not check the diagrams.

## Documentation outside the book

`README.md` and everything under `docs/` follow the [documentation standard](agent-guidelines/documentation-standards.md): diagrams are themed Mermaid blocks and every page ends with the shared footer. Do not type either by hand:

```bash
bash scripts/check-doc-standards.sh --fix .
```

## Licence

By contributing you agree that your contribution is released under the [MIT License](../LICENSE).

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
