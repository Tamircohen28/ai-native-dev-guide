# Engineering documentation

For people and agents changing this repository: the chapters, the figures, the checker, the CI. Readers of the book want the [user docs](../user/README.md) instead.

| Page | What it covers |
|------|----------------|
| [Architecture overview](architecture/overview.md) | What is in the repository, how the parts relate, and the authoring pipeline |
| [Decisions](decisions/README.md) | Architecture decision records, starting with [ADR-001](decisions/ADR-001-initial-architecture.md) |
| [Getting started](guides/getting-started.md) | A chapter change, end to end |
| [Build and release](build-and-release/README.md) | Development workflow, CI, versioning |

## Ground rules

- The book lives in `book/`. Everything else in the repository exists to check it, describe it or publish it.
- There is no build. A change is done when `make agent:check` and `make check-book` pass and a reviewer has read it.
- Authoring rules are in [CONTRIBUTING.md](../CONTRIBUTING.md#authoring-rules). They apply to every change under `book/`.
- Documentation outside the book follows the [documentation standard](../agent-guidelines/documentation-standards.md).

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
