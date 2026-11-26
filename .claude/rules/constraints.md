# Hard constraints

These rules have no exceptions. If a task seems to need one, stop and ask.

## Repository

- **No secrets.** Never commit tokens, keys, credentials or `.env` files, and never paste one
  into a file, a commit message or a PR.
- **No direct pushes to the default branch.** Work on a branch and open a PR.
- **No force-push to the default branch.** Resolve its name, never assume it:
  `git symbolic-ref --short refs/remotes/origin/HEAD`.
- **No `.github/workflows/` edits without review.** Propose the change in a PR and wait for a
  human to approve it.

## Book (`book/`)

- **Nothing private in book text.** No secrets, hostnames, personal names or project names,
  whether in prose, code samples, figures or alt text. Field data is anonymised: write
  "one developer", "a plugin repository", `example.com`. A person's name may appear only
  inside the URL of a cited source.
- **Every chapter stays under 400 lines.** `scripts/check-book.py` fails any file at 400 lines
  or more. Cut or split content; do not join lines to get under the limit.
- **Every chapter keeps the skeleton**, in this order: the `# NN — Title` heading; an opening
  paragraph that starts "After this chapter you"; `## Mental model`; the chapter's own
  sections; `## From the field`; `## Common problems`; `## Checklist`; `## Try it`;
  `## Sources`; the previous / contents / next footer. Two deliberate exceptions: chapter 27
  has no "Common problems" and chapter 28 has no "From the field".
- **Facts come from primary docs and carry a date, never from memory.** Fetch the official
  page, cite it under `## Sources`, and mark version-sensitive facts with the date they were
  read ("as of Nov 2026"). A claim with no reachable primary source stays out of the book.
- **`make check-book` must pass before a PR.** Quote its summary line in the PR body.
- **Do not edit generated files by hand.** `book/assets/chart-*.svg` come from
  `book/assets/_src/make_charts.py`, and `book/assets/fig-*.svg` and `book/assets/cover.svg`
  from `book/assets/_src/figures/build.py`. Change the input or the script, then regenerate.
- **Keep the sources appendix in step.** `book/D-sources.md` is maintained by hand; when a
  chapter's `## Sources` list changes, update it in the same change.
