# Changelog

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/); what a bump means for a book is defined in [engineering/build-and-release/versioning.md](engineering/build-and-release/versioning.md).

## [Unreleased]

### Added

- PDF edition: the five appendices are no longer printed (about 50 pages fewer); the contents lists them as links to their files on GitHub, and links to an appendix open it there. External links in each chapter carry numbered citation markers that match a numbered Sources reference list, and the table of contents and body links are styled as links.
- A PDF edition of the whole book: `make pdf` builds `dist/AI-Native Development.pdf` with a cover (version, commit, license, build time), a table of contents with page numbers, page numbers on every page and PDF metadata (`scripts/pdf/`). The Book PDF workflow rebuilds it on every push to `main` and publishes it on GitHub Pages; pull requests that touch the book build it as an artifact.
- Repository scaffold around the book: landing page and hero banner, the `docs/` tree, contribution guide, documentation standard (`config/docs/`, `scripts/check-doc-standards.sh`), agent instructions, Makefile and CI.
- Five chapters, renumbering the book from 29 to 34 chapters: 05 Inside the harness (components, the session and turn lifecycle, request assembly, settings and permissions inside the harness, where state lives, trust boundaries); 11 The extension model (CLAUDE.md, skills, subagents, hooks, MCP servers and plugins with their file structures, and how to choose between them); and a three-part workshop, 19 Guide: write a subagent, 20 Guide: write a skill, 21 Guide: build and ship a plugin.
- A settings scope-stack diagram in chapter 09.
- Cheat-sheet rows for the permission check order and 13 authoring commands; 17 glossary terms; the workshop as the level-3 project in the learning path.

### Changed

- License: the repository moves from MIT to CC BY-NC-SA 4.0 (credit required, non-commercial use only, adaptations allowed under the same license).
- Chapters 05 to 29 are now 06 to 34. Every link, heading, footer and cross-reference was remapped, and the contents, ladder, cheat sheet, glossary, learning path and sources follow the new numbering.

### Fixed

- The permission check order is now stated as the docs give it: hooks, deny rules, ask rules, the permission mode, then allow rules (chapters 03 and 09, and the agent-loop figure).
- The force-push guards printed in chapters 16, 21 and 32 now also block a `+`-prefixed refspec; the chapter 21 guard now blocks on malformed input instead of letting it through.

## [0.1.0] - 2026-11-26

First complete edition of the book.

### Added

- 29 chapters in six parts: Foundations, Claude Code core, Extending the harness, Workflows, Production concerns, Field guide.
- Appendices A to E: cheat sheet, glossary, templates, sources and further learning, learning path and exercises.
- 17 SVG figures (a cover, six explanatory figures and ten field-data charts) and 53 inline Mermaid diagrams.
- `scripts/check-book.py`, which checks chapter length, code fences, local links, images and Mermaid rendering.
- Documentation facts verified against the official docs as read on 2026-11-25; every chapter lists its sources and Appendix D collects them.
