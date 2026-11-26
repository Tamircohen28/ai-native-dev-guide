# Platform equivalence

Capability parity, not file parity. The authoritative status for every target is
[`core/capabilities/platforms.json`](../../core/capabilities/platforms.json). This page
does not repeat it. It only maps each kind of agent instruction to the one file in this
repo that carries it, so a contributor knows where to edit.

This repo is documentation only. It ships no plugin manifest and is not installed as a
plugin on any target: every row below is a project-level file an agent reads from a
checkout.

| What | Canonical file | Thin adapters that point at it |
|------|----------------|--------------------------------|
| Policy for any agent | [`AGENTS.md`](../../AGENTS.md) | `CLAUDE.md` (line 1 imports it), `.cursor/rules/000-project.mdc` (points at it) |
| Project skill | `.claude/skills/` | none — see the skill bridge note below |
| Hard constraints for Claude Code | `.claude/rules/constraints.md` | none; `AGENTS.md` wins if the two disagree |
| Documentation rules | [`documentation-standards.md`](documentation-standards.md) | none |

## Skill bridge

The project skill lives in one tree, `.claude/skills/`. There is no `.agents/skills/` copy.
An agent that does not load `.claude/skills/` gets the same working rules from `AGENTS.md`,
which is written to stand on its own. If a `.agents/skills/` bridge is added later, it must
hold the same directory names as `.claude/skills/`; `scripts/check-feature-equivalence.sh`
fails when the two differ.

## Editing rules

- Change policy in `AGENTS.md` only. An adapter never restates a rule.
- Change what a target can do in `core/capabilities/platforms.json` only, then run
  `bash scripts/check-platform-targets.sh . --sync-capabilities` so
  `docs/engineering/build-and-release/platform-targets.json` follows.
- Claude Desktop is a runtime surface of the Claude Code files above, not a separate
  format. The registry says what is and is not verified there.
