# ai-native-dev-guide — AGENTS.md

> **Keep this file lean.** Every agent loads it on every task, so each line costs context.
> Add a rule only when an agent got something wrong without it. Link to a longer page
> instead of pasting it. Delete a rule once a check enforces it.

## What this repo is

"AI-Native Development: Zero to Hero" is a book: a field guide to building software with
coding agents. It has 29 Markdown chapters, appendices A–E and SVG figures.

The repo is documentation only. There is no runtime. The product is the Markdown under
`book/`; the only code is the scripts that check it, draw its figures and build the optional
PDF edition (`make pdf`, `scripts/pdf/`).

## Layout

| Path | What it holds |
|------|---------------|
| `book/README.md` | The book's contents page |
| `book/NN-<slug>.md` | Chapters `01` to `29`, one per file |
| `book/A-…md` to `book/E-…md` | Appendices |
| `book/assets/` | Figures: `chart-*.svg`, `fig-*.svg`, `cover.svg` |
| `book/assets/_src/` | The scripts that generate those figures |
| `scripts/` | Checks: `check-book.py` and the `check-*.sh` scripts |
| `scripts/pdf/` | The PDF build: `build.mjs`, `book.css`, `metadata.py` |
| `docs/` | Docs about the repo itself, not book content |
| `docs/agent-guidelines/` | Detail this file links to |
| `core/capabilities/platforms.json` | Which coding agents this repo targets and what each can do |

`core/capabilities/platforms.json` is the one statement of what each target can do. Do not
restate a target's support here, in the README or in another file. See
[platform-equivalence.md](docs/agent-guidelines/platform-equivalence.md) for which file
carries which instruction.

Skills live in one tree, `.claude/skills/`. If a `.agents/skills/` bridge is ever added, it
must hold the same directory names.

## Commands

| Command | Purpose |
|---------|---------|
| `make agent:check` | **The definition of done.** Runs every check an agent must pass before a PR. |
| `make check-book` | Checks the book: file length, code fences, local links, images, Mermaid syntax |
| `make check-doc-standards` | Checks the footer and themed Mermaid in `README.md` and `docs/` |
| `python3 scripts/check-book.py book/NN-<slug>.md` | Checks the named files only |
| `make pdf` | Builds `dist/AI-Native Development.pdf`; needs Node.js and `pypdf` |

Work is done when `make agent:check` exits 0 and you have quoted its output. A check that
did not run is not a pass: if a tool is missing, say so.

## Book authoring rules

### One chapter, one file

- One chapter per file, under 400 lines. `check-book.py` fails a longer file.
- If a chapter outgrows the limit, cut or split the content. Do not shorten it by removing
  sources or examples.
- When you add, rename or reorder a file, update `book/README.md` and the footer
  navigation of the neighbouring chapters in the same change.

### The chapter skeleton

Every chapter has these parts, in this order:

1. **Opener.** The `# NN — Title` heading, then one paragraph saying what the reader can do
   after the chapter.
2. **`## Mental model`**, with one Mermaid diagram.
3. **Core sections**, with runnable examples.
4. **`## From the field`**: what real use showed.
5. **`## Common problems`**: a table of symptom, cause and fix.
6. **`## Checklist`**
7. **`## Try it`**: exercises.
8. **`## Sources`**
9. **Footer navigation**: a `---` rule, then one line with three links,
   `Previous · Contents · Next`. Contents links to `README.md`.

Copy the exact heading text and footer form from a neighbouring chapter.

### Facts and sources

- Facts come from primary documentation, read on a stated date. Never write a fact about a
  tool from memory.
- Anything you could not confirm is left out, or marked "check in your version".
- Version-sensitive facts carry a date, and the version when the source gives one.
- Every source a chapter relies on is listed in its `## Sources` section.
- When a chapter's Sources list changes, update the sources appendix,
  `book/D-sources.md`, in the same change. It is maintained by hand: no generator for it
  lives in this repo.

### Privacy

- No secrets, hostnames, IP addresses, emails, personal names, handles or real project
  names in book text.
- Incidents are told generically: what happened and what it taught, not who or where.
- Field numbers are aggregates. State the sample and its limits next to the number.

### Diagrams and examples

- Mermaid labels go in double quotes: `A["Reads files"]`, `-->|"resume"|`.
- An example that can be run must be run before it is printed. Print the command and the
  output you saw.
- An example you could not run is labelled as not run, or left out.

### Generated files

Never edit these by hand. Change the input and regenerate.

| File | Regenerate from |
|------|-----------------|
| `book/assets/chart-*.svg` | `book/assets/_src/make_charts.py --data <usage JSON>` |
| `book/assets/fig-*.svg`, `book/assets/cover.svg` | `book/assets/_src/figures/build.py` |

The charts' input data (a usage-statistics JSON file) is private and is not in this repo.
If you cannot regenerate a file because its input is missing, stop and say so in the PR.
Do not patch the output.

## Docs outside the book

`README.md` and everything under `docs/` follow
[documentation-standards.md](docs/agent-guidelines/documentation-standards.md). That
standard does not apply to `book/`, which follows the rules above.

## Branches and commits

- Branch from the default branch: `feat/<short-slug>` for new content or tooling,
  `fix/<short-slug>` for corrections.
- Commit messages: `<type>(<scope>): <description>`. For example
  `fix(ch07): correct the settings precedence order` or
  `feat(scripts): check footer navigation links`.
- One logical change per commit. A regenerated file goes in the same commit as the input
  that changed it.

## Versioning and changelog

- Editions follow the policy in
  [versioning.md](docs/engineering/build-and-release/versioning.md).
- Every user-visible change adds a line under `[Unreleased]` in `docs/CHANGELOG.md`, and
  the root `CHANGELOG.md` mirror is updated in the same commit.

## Pull requests

- Never push to the default branch. Every change lands through a PR.
- Run `make agent:check` before opening the PR.
- The PR body states what was verified and how: the commands run and their output, and for
  changed facts, the source and the date it was read.
- Opening a PR is not merging it. The repo owner merges.
- Do not merge with a failing or skipped check.

## Hard constraints

- Never commit secrets, tokens or `.env` files.
- Never hand-edit a generated file.
- Never state an unverified fact as verified, in the book or in a PR body.
- Never weaken or delete a check to make it pass. Fix the content, or raise the problem.
- Never add a build step, a runtime or a dependency unless the owner asks for it.
- Never rewrite published history: no force-push to a shared branch.

## Dependency management

- Configure `.github/dependabot.yml` with only the ecosystems present in this repo.
- Weekly cadence for npm/pip, monthly for GitHub Actions. Never daily.
- Group minor and patch updates into one PR per ecosystem.
- Block automatic major-version PRs.
- Set `open-pull-requests-limit` to 3 or lower. Never one PR per dependency.
- Do not blindly merge Dependabot PRs — require CI to pass first.
