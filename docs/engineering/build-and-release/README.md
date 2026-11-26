# Build and release

There is no build: the book is read as the Markdown in `book/`. This section covers what stands in for one, which is the checks, the CI that runs them, and how an edition is versioned and tagged.

| Page | What it covers |
|------|----------------|
| [Development workflow](development-workflow.md) | The day-to-day loop: branch, edit, check, pull request |
| [CI workflow](ci-workflow.md) | What runs on a push, a pull request and a version tag |
| [Versioning](versioning.md) | What a version number means for a book, and how to cut an edition |
| [Platform targets](platform-targets.md) | Which coding tools the repository declares support for, and their validation state |

## At a glance

| Question | Answer |
|---|---|
| What is the definition of done? | `make agent:check` exits 0, and `make check-book` ends with `0 failed` and `rendered` |
| What does CI run? | `make agent:check`, a secret scan, and the action-pinning check |
| Does CI render Mermaid? | No. The runner has no Mermaid CLI, so rendering is a local step |
| Where is the version declared? | The newest release heading in `docs/CHANGELOG.md`, mirrored in the root `CHANGELOG.md` and the README version badge, and the matching `vX.Y.Z` tag |
| What does a release produce? | A GitHub Release with generated notes, and an updated `stable` branch |
| Who merges? | The repository owner |

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
