# Platform target versions

Machine-readable source: [`platform-targets.json`](platform-targets.json).

This file records which version of each coding agent the repo was validated against. It does not say what each agent can do: that is stated once, in [`core/capabilities/platforms.json`](../../../core/capabilities/platforms.json).

| Target | Min supported | Validated against | Latest known |
|--------|---------------|-------------------|--------------|
| Claude Code | unknown | unknown | unknown |
| Codex | unknown | unknown | unknown |
| Cursor | unknown | unknown | unknown |
| Gemini CLI | unknown | unknown | unknown |
| OpenCode | unknown | unknown | unknown |

`unknown` means the target is declared but no version has been validated yet. A target gets a version here, and a version badge in the README, only after someone runs the repo's agent setup on that version and records it in `platform-targets.json`.

When a version is recorded:

1. Set `validated_against` (and `supported_min`, `latest_known`) for the target in `platform-targets.json`.
2. Update the row above to match.
3. Add the README badge for that target with the same version.
4. Run `bash scripts/check-platform-targets.sh .`.

The `capabilities` and `capability_gaps` fields in the JSON file are derived from the registry. Never type them by hand: run `bash scripts/check-platform-targets.sh . --sync-capabilities`.

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
