# Changelog

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for the full history. This file mirrors it; change both in the same commit.

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/); what a bump means for a book is defined in [docs/engineering/build-and-release/versioning.md](docs/engineering/build-and-release/versioning.md).

## [Unreleased]

### Added

- Repository scaffold around the book: landing page and hero banner, the `docs/` tree, contribution guide, documentation standard (`config/docs/`, `scripts/check-doc-standards.sh`), agent instructions, Makefile and CI.

## [0.1.0] - 2026-11-26

First complete edition of the book.

### Added

- 29 chapters in six parts: Foundations, Claude Code core, Extending the harness, Workflows, Production concerns, Field guide.
- Appendices A to E: cheat sheet, glossary, templates, sources and further learning, learning path and exercises.
- 17 SVG figures (a cover, six explanatory figures and ten field-data charts) and 53 inline Mermaid diagrams.
- `scripts/check-book.py`, which checks chapter length, code fences, local links, images and Mermaid rendering.
- Documentation facts verified against the official docs as read on 2026-11-25; every chapter lists its sources and Appendix D collects them.
