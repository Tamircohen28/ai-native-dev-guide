# Security Policy

This repository is a book: Markdown chapters, appendices and SVG figures, plus a few
scripts and workflows that check them. There is no shipped software, so "security" here
means the safety of what the text tells a reader to do and of the repository itself.

## Supported Versions

Only the latest tagged edition is supported. Fixes land on `main` and ship in the next
tagged edition; older editions are not patched.

| Version | Supported |
|---------|-----------|
| Latest tagged edition | Yes |
| Any earlier edition | No |

## Reporting a Vulnerability

Report privately by email: **tamircohen2468@gmail.com**

Please do **not** open a public issue, pull request or discussion for a security report.
The same private channel is used for Code of Conduct reports (see
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)). Where the repository has GitHub private
vulnerability reporting enabled, **Security → Report a vulnerability** opens a private
security advisory and is an equally good route.

Include, as far as you can:

- the file and line (or the commit) where the problem is
- what the problem is and what a reader or the repository is exposed to
- for a leaked secret: where it appears, never the secret value itself

You can expect an acknowledgement within 3 working days and a fix or a decision within
14 days. Reporters are credited in the changelog unless they ask not to be.

## What Counts as a Security Issue

- **A leaked secret or private identifier** in the text, a figure, an example or the git
  history: a token, key, password, internal hostname, account identifier or personal data.
- **A harmful command in an example**: a command or configuration a reader is told to run
  that destroys data, weakens their machine or account, exfiltrates information, or
  disables a safety control without saying so.
- **A compromised workflow**: a GitHub Actions workflow, script or dependency in this
  repository that could run untrusted code, leak repository secrets, or be altered by a
  third party (for example an action pinned to a movable ref).

## What Does Not

Typos, broken links, outdated tool versions and disagreements with the advice are
ordinary issues. Open them through the normal issue tracker.
