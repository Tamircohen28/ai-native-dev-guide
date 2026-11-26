# Appendix C — Templates

Copy-ready starting points for the files and messages this book uses most, each cut down to the smallest version that is correct. Replace every `<PLACEHOLDER>`, delete the lines you do not need, and follow the chapter link for the full version and the reasoning. Templates 1 to 9 are files you commit; 10 to 14 are messages and records you write. Keys, fields and flags are as of Nov 2026; check your version with `/help` and `claude --help`.

## 1. Project instruction file

**When to use:** a repository that an agent will work in has no instruction file yet. Save it as `AGENTS.md` so that every tool reads it. Explained in [chapter 8](08-claude-md-and-memory.md), [chapter 28](28-cross-tool-agents-md-cursor-codex-gemini.md) and [chapter 31](31-repo-standards-and-team-adoption.md).

```markdown
# <PROJECT_NAME>

<WHAT_THIS_REPO_IS, in one or two lines: purpose, language, main framework>

## Commands
- Install: `<INSTALL_COMMAND>`
- One test file: `<SINGLE_TEST_COMMAND>`
- Gate: `<GATE_COMMAND>` (lint, typecheck, tests). Run it before every commit; it must exit 0.

## Definition of done
A change is done when `<GATE_COMMAND>` exits 0 on the committed tree. Run it and quote its last
lines in your summary. After two failed attempts at the same failure, stop and find the root cause.

## Things the code will not tell you
- <MISLEADING_NAME_OR_LEGACY_AREA>: <WHAT_TO_DO_ABOUT_IT>
- <DECISION_THAT_IS_NOT_IN_THE_REPO>

## Conventions
- <CONVENTION>, because <REASON>.
- Work on a branch named `<BRANCH_PATTERN>`. Never commit to `<DEFAULT_BRANCH>`: <REASON>.
- Open a pull request when the gate passes. Do not merge it; a person does.

## Hard rules
- Never <FORBIDDEN_ACTION>. Why: <REASON, with the date of the incident>.
  Safe alternative: <SAFE_ALTERNATIVE>. Enforced by `.claude/hooks/<GUARD_NAME>.py`.
```

Keep the file under 200 lines and leave out anything an agent can learn by reading the code. Claude Code reads `AGENTS.md` natively (v2.1.277 or later), by default only when no `CLAUDE.md` or `CLAUDE.local.md` is on the path, so if the repository also has a `CLAUDE.md`, make it a thin adapter:

```markdown
@AGENTS.md

## Claude Code addenda
- <CLAUDE_ONLY_LINE, for example the skill that starts the app>
```

## 2. Team baseline `.claude/settings.json`

**When to use:** a team shares a repository and wants the same guard rails for everyone. Commit it as `.claude/settings.json`; personal additions go in `.claude/settings.local.json`. Explained in [chapter 9](09-settings-and-permissions.md).

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "default",
    "allow": ["Bash(<LINT_COMMAND>)", "Bash(<TYPECHECK_COMMAND>)", "Bash(<TEST_COMMAND> *)",
              "Bash(gh pr view *)", "Bash(gh pr checks *)"],
    "ask": ["Bash(git push *)", "Bash(gh pr merge *)", "Bash(<INSTALL_COMMAND> *)"],
    "deny": ["Read(.env)", "Read(.env.*)", "Read(./secrets/**)", "Read(~/.ssh/**)", "Read(~/.aws/**)"],
    "disableBypassPermissionsMode": "disable"
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "network": { "allowedDomains": ["<PACKAGE_REGISTRY_DOMAIN>"] }
  }
}
```

`"defaultMode": "default"` starts everyone's terminal sessions in Manual mode; delete the line to leave each developer's own starting mode alone, as the chapter's baseline does. `auto` and `bypassPermissions` have no effect in a project file. Rules are evaluated deny, then ask, then allow, so keep deny rules narrow. Do not allow runners such as `npx *` or `bash *`. The sandbox's domain list starts empty: add your Git host to `allowedDomains` if the allowed `gh` commands and `git push` should work.

## 3. `PreToolUse` guard hook with a named override

**When to use:** a hard rule must hold even when the model forgets it. Save the script as `.claude/hooks/<GUARD_NAME>.py`. For a rule with no exceptions, remove `OVERRIDE` and every line that uses it. Explained in [chapter 16](16-hooks.md); guard patterns are in [chapter 29](29-security-and-guardrails.md).

```python
#!/usr/bin/env python3
"""PreToolUse guard for Bash: block <WHAT_IT_BLOCKS> unless a human approved this one run."""
import json, os, re, sys

BLOCK = re.compile(r"<COMMAND_REGEX>")    # for example r"\bterraform\b[^\n;|&]*\bdestroy\b"
OVERRIDE = "<ALLOW_VARIABLE>"             # for example ALLOW_TF_DESTROY; one variable per guard

try:
    payload = json.load(sys.stdin)        # the event arrives as JSON on stdin
    command = (payload.get("tool_input") or {}).get("command") or ""
    hit = payload.get("tool_name") == "Bash" and BLOCK.search(command)
except Exception:                         # bad JSON, or JSON of an unexpected shape
    sys.stderr.write("guard: unreadable payload, blocking\n")
    sys.exit(2)                           # fail closed with exit 2; a traceback would exit 1
if not hit:
    sys.exit(0)                           # exit 0 with no output: no opinion
# An inline `VAR=1 cmd` prefix never reaches this process's environment, so read the text too.
if os.environ.get(OVERRIDE) == "1" or re.search(rf"\b{OVERRIDE}=1\b", command):
    sys.exit(0)
sys.stderr.write(
    "BLOCKED: <WHY_IT_CANNOT_BE_UNDONE>. Safe alternative: <SAFE_ALTERNATIVE>.\n"
    "Stop and ask the user. Only after an explicit yes for this one action, re-run with the\n"
    f"prefix {OVERRIDE}=1. Never add it yourself.\n")
sys.exit(2)                               # exit 2 blocks; stderr goes back to the model
```

Register it in `.claude/settings.json`, next to the keys from template 2. `onFailure` (v2.1.295 or later) makes a crash or a timeout block instead of letting the command through. This template blocks with `exit 2` and a reason on stderr, and it also blocks a payload it cannot read; chapter 16's guard uses the other documented form, exit 0 with a JSON `deny`, and lets an unreadable payload through. Use one form per hook. Test the guard before you trust it: pipe in one payload that must block and one that must pass, as chapter 16 shows, then confirm that `/hooks` lists it.

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "timeout": 10, "onFailure": "block",
                     "command": "python3 \"${CLAUDE_PROJECT_DIR}\"/.claude/hooks/<GUARD_NAME>.py" } ] }
    ]
  }
}
```

## 4. `Stop` hook that requires the check to pass

**When to use:** a turn must not end while the gate fails. The hook runs the check itself, so "done" cannot rest on a check that never ran. With the loop guard it buys one more attempt and then lets the turn end, so keep CI as the gate that counts. One documented exception: when a `Stop` hook exits 2 with nothing on stdout and its stderr says a file is missing (such as `No such file or directory`), the run counts as a non-blocking error and the turn ends; if your check can print that message, exit 0 and print `{"decision": "block", "reason": "..."}` on stdout instead. Save the script as `.claude/hooks/require-check.sh`, make it executable (`chmod +x`), install `jq`, and register it with the JSON below. Explained in [chapter 16](16-hooks.md) and [chapter 23](23-testing-and-verification-loops.md).

```bash
#!/usr/bin/env bash
# Stop hook: do not let a turn end while the check fails, but push back only once.
set -uo pipefail
CHECK='<GATE_COMMAND>'                      # for example: make check
input=$(cat)
# Loop guard: stop_hook_active is true when a Stop hook has already sent Claude back.
# Without this test, a check that stays red blocks every stop.
if [ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" = "true" ]; then
  exit 0
fi
# Stop fires after every response, so skip the check when the working tree is clean.
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$(git -C "$root" status --porcelain)" ] || exit 0
if ! output=$(cd "$root" && bash -c "$CHECK" 2>&1); then
  echo "The check failed: $CHECK. Fix it before finishing, or state plainly what is still broken:" >&2
  printf '%s\n' "$output" | tail -n 20 >&2
  exit 2                                    # exit 2 blocks the stop; exit 1 would not
fi
exit 0
```

```json
{ "hooks": { "Stop": [ { "hooks": [
  { "type": "command", "command": "\"${CLAUDE_PROJECT_DIR}\"/.claude/hooks/require-check.sh", "timeout": 300 }
] } ] } }
```

## 5. `SKILL.md`

**When to use:** you have explained the same multi-step procedure twice. Save it as `.claude/skills/<skill-name>/SKILL.md`; the skill is then also the command `/<skill-name>`. Add `disable-model-invocation: true` to the frontmatter when the skill has side effects. Explained in [chapter 15](15-skills.md).

```markdown
---
name: <skill-name>
description: "Use when the user asks for <SITUATION> or says '<TRIGGER_PHRASE>'. <WHAT_IT_DOES>. Not for <NEAR_MISS>."
allowed-tools:
  - Read
  - Bash(<EXACT_COMMAND> *)
---

# <Skill title>

<ONE_LINE_PURPOSE>. Arguments: `$ARGUMENTS`.

## Hard rules
- <WHAT_IT_MUST_NEVER_DO, for example: do not push or tag; print the result and stop>

## Workflow
1. Run `<EXACT_COMMAND> $ARGUMENTS`. If it fails, show the error and stop.
2. <NEXT_STEP>
3. Output <FORMAT>. If there is nothing to report, say so in one line.
```

## 6. Subagent definition: a read-only reviewer

**When to use:** you want a review from a context that did not write the code. Save it as `.claude/agents/reviewer.md`. With only `Read, Grep, Glob` it cannot run `git diff`, so name the files and the goal when you ask for it. Explained in [chapter 14](14-subagents.md).

```markdown
---
name: reviewer
description: Reviews named files against a stated goal and reports defects with file and line evidence. Use after a change is written and before it is committed. Read-only.
tools: Read, Grep, Glob
model: inherit
---

You review code that someone else wrote. You have not seen the conversation that produced it.
You are given the goal of the change and the files to review, as paths. If either is missing,
say so and stop.

## Procedure
1. Read every named file in full. Use Grep and Glob to find callers and tests of what changed.
2. Check the change against the goal: does it do what was asked, all of it, and nothing extra?
3. Look for wrong behaviour, missing error handling, security problems, then missing or weak tests.
4. For each finding, quote the line and explain how it fails. If you cannot, drop the finding.

## Rules
- You cannot edit files or run commands. Describe the fix; do not ask for more tools.
- An empty finding list with `approve` is a valid outcome. Do not invent findings.

## Return
Verdict: `approve` or `request-changes`, with one sentence of reasoning. Then one block per
finding: severity, confidence, path:line, evidence, recommended fix. End with the files you read.
```

## 7. Plugin manifest and marketplace entry

**When to use:** a skill, agent or hook should travel to other repositories or teammates. The manifest is `plugins/<plugin-name>/.claude-plugin/plugin.json`; only `name` is required, and no skills, agents or hooks go inside that `.claude-plugin/` folder. The catalogue is `.claude-plugin/marketplace.json` at the root of the same repository. Check both with `claude plugin validate`. Explained in [chapter 17](17-plugins-and-marketplaces.md).

```json
{
  "name": "<plugin-name>",
  "version": "0.1.0",
  "description": "<WHAT_THE_PLUGIN_PROVIDES>",
  "author": { "name": "<AUTHOR_NAME>" }
}
```

```json
{
  "name": "<marketplace-name>",
  "owner": { "name": "<OWNER_NAME>" },
  "plugins": [
    { "name": "<plugin-name>", "source": "./plugins/<plugin-name>", "description": "<WHAT_THE_PLUGIN_PROVIDES>" }
  ]
}
```

## 8. Project `.mcp.json` with environment expansion

**When to use:** teammates should share MCP server definitions without sharing secrets. Save it as `.mcp.json` in the project root, not under `.claude/`. Explained in [chapter 13](13-mcp-in-practice.md).

```json
{
  "mcpServers": {
    "<remote-server>": {
      "type": "http",
      "url": "${<URL_VARIABLE>:-<DEFAULT_BASE_URL>}/mcp",
      "headers": { "Authorization": "Bearer ${<TOKEN_VARIABLE>}" }
    },
    "<local-server>": {
      "type": "stdio",
      "command": "<COMMAND>", "args": ["<ARGUMENT>"],
      "env": { "<NAME_THE_SERVER_READS>": "${<NAME_IN_YOUR_SHELL>}" }
    }
  }
}
```

`${VAR}` and `${VAR:-default}` expand in `command`, `args`, `env`, `url` and `headers`. Give each token its own variable name: `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and `NPM_TOKEN` read as empty in a remote `url` or `headers`. Keep `type`: an entry with a `url` and no `type` is skipped.

## 9. GitHub Actions workflow for pull-request review

**When to use:** you want Claude to review every pull request inside your own GitHub Actions. Save it as `.github/workflows/claude-code-review.yml` and store `ANTHROPIC_API_KEY` as a repository secret. This is the documented workflow. Keep it advisory, not a required check. Explained in [chapter 27](27-headless-ci-and-the-agent-sdk.md) and [chapter 24](24-git-prs-and-code-review.md).

```yaml
name: Code Review
on:
  pull_request:
    types: [opened, synchronize, ready_for_review, reopened]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
        with:
          fetch-depth: 1
      - uses: anthropics/claude-code-action@9c5ddab2e6d17b83ea679153b31f1d5f023cf636 # v1.0.217
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          plugin_marketplaces: "https://github.com/anthropics/claude-plugins-official.git"
          plugins: "code-review@claude-plugins-official"
          prompt: "/code-review:code-review --comment ${{ github.repository }}/pull/${{ github.event.pull_request.number }}"
          claude_args: '--allowedTools "mcp__github_inline_comment__create_inline_comment"'
```

`--comment` posts the review; without it the findings stay in the run log. The `claude_args` line is required for inline comments. To cap cost, add a job timeout and pass `--max-turns` in `claude_args`.

## 10. Task brief

**When to use:** any task that touches more than one file or runs longer than a few minutes. Paste it as the prompt or keep it in the issue. Goal, constraints, definition of done and proof command are required; delete the context and budget sections when they do not apply. Explained in [chapter 22](22-explore-plan-implement-verify.md); shorter prompt forms are in [chapter 34](34-prompt-cookbook-and-anti-patterns.md).

```markdown
## Goal
<WHAT_IS_OBSERVABLY_TRUE_WHEN_THIS_IS_FINISHED>

## Context the repo does not show
<DECISIONS_ALREADY_MADE>. <WHAT_IS_APPROVED>. <WHAT_WAS_RULED_OUT>.

## Constraints
- Change only <PATHS>.
- Out of scope: <THE_NEIGHBOURING_FIX_OR_OBVIOUS_SHORTCUT>. Mention it in your report.

## Definition of done
- <BEHAVIOUR_THAT_A_TEST_PROVES>
- Existing tests still pass.

## Proof command
`<COMMAND>` exits 0. Paste the command and its output in the final report.

## Budget
<TIME_LIMIT>. Tell me at the halfway point if you will miss it.
```

## 11. Subagent delegation brief

**When to use:** you ask Claude to hand work to a subagent. A subagent that is not a fork starts without your conversation, so the request must carry all four parts. Explained in [chapter 14](14-subagents.md).

```text
Use a subagent to <TASK>.
Goal:   <ONE_SENTENCE, including what "done" looks like>
Known:  <FACTS_ALREADY_ESTABLISHED, with file paths>. Ruled out: <WHAT, and how>.
Scope:  <read-only | may edit>. Look in <PATHS> only. Do not touch <PATHS>. You may run <COMMAND>.
Return: <FORMAT>, under <N> words, with file:line evidence. If you are blocked, say so and stop.
```

## 12. Handoff note for a fresh session

**When to use:** before a break, near a usage limit, or when the context has drifted. Ask Claude to write `HANDOFF.md` in this shape and to check every claim against git and the test output first. Start the next session with `claude "Read HANDOFF.md, check the State section against git, then continue from Next steps."` Explained in [chapter 10](10-plan-mode-checkpoints-and-context-management.md).

```markdown
# Handoff: <TASK_TITLE>

## Goal and done-check
<GOAL>. Done when `<PROOF_COMMAND>` exits 0 and <OBSERVABLE_RESULT>.

## State
- Branch `<BRANCH>`, last commit `<SHA>`, <N> uncommitted files
- Failing: <TEST_OR_CHECK> (expected <X>, got <Y>)

## Done, with evidence
- <ITEM>: `<COMMAND>` → <RESULT>

## Tried and rejected
- <APPROACH>: <WHY_IT_WAS_DROPPED>

## Next steps
1. <EXACT_NEXT_COMMAND_OR_EDIT>
2. <FOLLOWING_STEP>

## Open questions
- <QUESTION_ONLY_A_HUMAN_CAN_ANSWER>
```

## 13. Pull-request body with a verification section

**When to use:** every pull request, and above all one an agent wrote. Save it as `pr-body.md` and pass it with `gh pr create --body-file pr-body.md`. A reviewer should be able to rerun your proof. Explained in [chapter 24](24-git-prs-and-code-review.md).

```markdown
## What and why
<ONE_OR_TWO_SENTENCES>. Closes #<ISSUE>.

## How it was verified
- `<GATE_COMMAND>` → exit 0 (<PASSED_AND_FAILED_COUNTS>) on commit <SHA>
- <MANUAL_OR_BROWSER_CHECK>: <WHAT_WAS_OBSERVED>

## Risk and where to look
<LOW | MEDIUM | HIGH>: <WHAT_IT_TOUCHES>. Written with an agent. Please check <FILE_OR_LOGIC>.

## Not verified
<WHAT_STILL_NEEDS_A_HUMAN_OR_PRODUCTION>
```

## 14. Incident-to-rule record

**When to use:** after an incident, or a correction you have made twice. Fill in the top part first and agree the fix layer before anything is written; "none" is a valid answer. A hard rule then exists three times: the rule, the hook that enforces it, and a memory note that names the hook. Explained in [chapter 16](16-hooks.md) and [chapter 31](31-repo-standards-and-team-adoption.md); worked cases are in [chapter 33](33-case-studies-from-real-work.md).

```markdown
## Incident: <DATE>, <ONE_LINE_TITLE>
- What happened: <THE_ACTIONS_IN_ORDER, without adjectives>
- How it was noticed: <WHO_OR_WHAT_CAUGHT_IT, and how long after>
- Root cause: <THE_MECHANISM, not the blame>
- One-off or pattern: <SEEN_BEFORE_OR_NOT>
- Fix layer: none | memory | rule | hook | test | workflow -> <THE_EXACT_CHANGE>

### Rule, for the instruction file
Never <FORBIDDEN_ACTION> (hard rule).
- Why: <REASON>. It happened on <DATE>.
- Safe alternative: `<SAFE_COMMAND>`. It needs my explicit yes each time.
- Enforced by `.claude/hooks/<GUARD_NAME>.py`. Do not work around it.

### Enforcing hook
- Event and matcher: `PreToolUse`, `<MATCHER>`. Blocks: <PATTERN>. Override: `<ALLOW_VARIABLE>=1`, or none.
- Proof: <PAYLOAD_THAT_MUST_BLOCK> → exit 2. <PAYLOAD_THAT_MUST_PASS> → exit 0. Listed in `/hooks`.

### Memory note
<THE_RULE_IN_ONE_SENTENCE>. Why: <THE_DATED_INCIDENT>. How to apply: `<GUARD_NAME>.py` blocks
this command. When it blocks, stop and ask; do not look for a way round.
```

---

[← Previous: Glossary](B-glossary.md) · [Contents](README.md) · [Next: Sources and further learning →](D-sources.md)
