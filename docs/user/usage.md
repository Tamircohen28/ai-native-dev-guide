# Usage

Reading the book offline, choosing a viewer, and validating a copy.

## Reading on GitHub

Open [`book/README.md`](../../book/README.md) in the repository. GitHub renders the Markdown, the Mermaid diagrams and the SVG figures with no setup. Every chapter ends with previous, contents and next links.

## Reading offline

The book is self-contained. Every link between chapters is relative and every figure is a local file, so the `book/` folder works anywhere as long as it stays together.

```bash
git clone https://github.com/TamirCohen28/ai-native-dev-guide.git
```

To carry it without git, copy or zip the whole `book/` folder, including `book/assets/`. Do not move individual chapters out of the folder: their links and images point at siblings.

External links (the Sources sections and Appendix D) need a network connection; everything else does not.

## Viewers that render Mermaid

The diagrams inside chapters are Mermaid code blocks. A viewer without Mermaid support shows them as code, which is readable but not what was intended.

| Viewer | Mermaid | Setup |
|---|---|---|
| GitHub (web) | Yes | None |
| VS Code Markdown preview | With an extension | Install a Mermaid preview extension, then open the preview |
| Obsidian | Yes | Open the `book/` folder as a vault |
| A static site generator | Depends on the generator | Enable its Mermaid plugin |
| A plain text editor or `less` | No | Diagrams appear as code; figures do not appear at all |

The SVG figures and charts are ordinary images and need no Mermaid support. The charts are drawn on a light card so they read on both light and dark pages.

## Finding things

| You want | Go to |
|---|---|
| The chapter list | [`book/README.md`](../../book/README.md) |
| A term you do not know | [Appendix B, the glossary](../../book/B-glossary.md) |
| A command, flag or setting, fast | [Appendix A, the cheat sheet](../../book/A-cheat-sheet.md) |
| A starting file to copy | [Appendix C, templates](../../book/C-templates.md) |
| Where a fact came from | The chapter's Sources section, then [Appendix D](../../book/D-sources.md) |
| A fix for a symptom | [Chapter 27](../../book/27-troubleshooting-common-problems.md) |
| A study plan | [Appendix E](../../book/E-learning-path-and-exercises.md) |

## Validating a copy

You only need this if you have changed something, or want to confirm a copy is intact.

```bash
make install       # once
make check-book    # full check, renders every Mermaid block
```

The checker reads every Markdown file under `book/` and reports one line per file, then a summary:

```text
ok   book/01-what-is-ai-native-development.md
...
check-book: 35 files, 0 failed, 53 Mermaid blocks rendered
```

What it checks:

| Check | Fails when |
|---|---|
| Length | A file has 400 lines or more |
| Code fences | A file has an odd number of fence markers, which means one is unclosed |
| Local links | A relative link points at a file that does not exist |
| Images | A relative image path points at a file that does not exist |
| Mermaid | A diagram block does not render with the Mermaid CLI |

Rendering needs the Mermaid CLI (`mmdc`). Without it the checker skips rendering and says so in the summary line: `NOT rendered (mmdc missing or --no-mermaid)`. Install it with:

```bash
npm install -g @mermaid-js/mermaid-cli
```

To check without rendering, or to check only some files, call the script directly:

```bash
python3 scripts/check-book.py --no-mermaid
python3 scripts/check-book.py book/14-hooks.md book/D-sources.md
```

`make agent:check` is the repository gate that CI runs. It includes the book check without Mermaid rendering, plus the repository's own consistency checks. All commands and flags are in the [command reference](reference/commands.md).

## Using the material

The book is MIT-licensed. The templates in [Appendix C](../../book/C-templates.md) are meant to be copied into your own repository and edited. Treat any version-sensitive value in them as dated, and check it against your installed tool.

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
