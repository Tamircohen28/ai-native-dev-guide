@AGENTS.md

## Claude Code addenda

Claude-only notes. Policy lives in `AGENTS.md`; nothing here repeats it.

### Project skill

The project skill lives under `.claude/skills/`. Use it for chapter work instead of
re-deriving the workflow from scratch. If the skill and `AGENTS.md` disagree, `AGENTS.md`
wins: fix the skill in the same PR.

### Rules file

`.claude/rules/constraints.md` holds the hard constraints as a project rule. It is a short
reminder of limits already stated in `AGENTS.md`, not a second policy. Never add a rule
there that `AGENTS.md` does not have.

### Subagents for chapter reviews

Use subagents for bounded, read-only chapter reviews:

- One chapter or one appendix per subagent. Never hand one subagent the whole book.
- Name the file, the checks to run against it, and the return format: findings with line
  numbers, most serious first, in a short list.
- Launch independent chapter reviews together in one message so they run in parallel.
- The subagent reports; the main session decides, edits, and runs `make check-book`.
- A review brief states the question, not the expected answer.
