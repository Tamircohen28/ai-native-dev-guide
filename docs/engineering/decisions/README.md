# Architecture decision records

Decisions that shape the repository, each with the context it was made in and what it costs. An ADR is written when a choice would be expensive to reverse or would surprise a new contributor.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-initial-architecture.md) | Initial architecture: a book as plain Markdown, gated by a checker | Accepted | 2026-11-26 |

## Writing a new ADR

1. Copy the section layout of [ADR-001](ADR-001-initial-architecture.md): Status, Context, Decision, Consequences, Alternatives considered.
2. Name the file `ADR-NNN-short-slug.md`, using the next free number.
3. Add a row to the index above in the same pull request.
4. Keep it to one decision. If you are recording two, write two files.

## Changing a decision

An accepted ADR is not edited to say something different. Write a new ADR that supersedes it, set the old one's status to `Superseded by ADR-NNN`, and link both ways. The history of why the repository looks the way it does is the point of keeping these.

| Status | Meaning |
|--------|---------|
| Proposed | Under discussion in a pull request |
| Accepted | In force |
| Superseded by ADR-NNN | Replaced; kept for history |

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
