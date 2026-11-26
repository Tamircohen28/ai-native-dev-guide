# Appendix A — Cheat sheet

A quick reference to the commands, keys, files and rules used across this book. Each section ends with a link to the chapter that explains it.

> **Note:** Names, defaults and version numbers are as of Nov 2026. Check your own build with `/help` and `claude --help`.

## 1. Start, leave and resume a session

| You want to | Do this |
|---|---|
| Start a session; start with a first prompt | `claude`; `claude "query"` |
| Ask one question and exit (print mode) | `claude -p "query"` |
| Reopen the most recent session in this directory | `claude --continue` (short form `-c`) |
| Pick a session from a list, or go to one by name or ID | `claude --resume`; `claude --resume oauth-migration` (short form `-r`); `/resume` inside a session |
| Open the session linked to a pull request | `claude --from-pr 1234` |
| Continue a copy and leave the original untouched | Add `--fork-session` to `--continue` or `--resume` |
| Name a session so you can find it later | `claude -n oauth-migration`, or `/rename oauth-migration` inside it |
| Start an unrelated task | `/clear`; the old conversation stays in the `/resume` picker |
| Undo the last turn | `/rewind`, or `Esc` twice on an empty prompt |
| Leave | `/exit`, or `Ctrl+D` twice |
| Check the install; update now | `claude doctor`; `claude update` |

- Resume restores the conversation, the model, the permission mode and the checkpoints. It does not restore background tasks or launch flags such as `--add-dir`, `--allowedTools`, `--mcp-config` and `--settings`: pass them again.
- Transcripts are JSONL files under `~/.claude/projects/<project>/`, kept 30 days by default (`cleanupPeriodDays`).
- `claude -c` skips sessions created with `claude -p`; use `claude -p --continue` for those.

→ [Chapter 05: Install and first session](05-install-and-first-session.md) and [Chapter 09: Plan mode, checkpoints and context management](09-plan-mode-checkpoints-and-context-management.md)

## 2. The most useful CLI flags

| Flag | Purpose |
|---|---|
| `-p`, `--print` | Print the response and exit, with no interactive mode |
| `-c`, `--continue` and `-r`, `--resume` | Load the most recent conversation in this directory; resume by ID or name, or show a picker |
| `--fork-session` | With `--resume` or `--continue`, create a new session ID |
| `-n`, `--name` | Display name, shown in `/resume` and the terminal title |
| `--model` | An alias (`sonnet`, `opus`, `haiku`, `fable`) or a full model name |
| `--effort` | `low`, `medium`, `high`, `xhigh`, `max` or `ultracode`, for this session |
| `--permission-mode` | Start in `default`, `acceptEdits`, `plan`, `auto`, `dontAsk` or `bypassPermissions`. `manual` is an alias for `default`, and it is the name `claude --help` prints |
| `--allowedTools` | Calls that run without prompting, in permission rule syntax. It does not limit which tools exist |
| `--disallowedTools`, `--tools` | Deny rules (a bare tool name removes the tool); restrict which built-in tools exist, as in `--tools "Bash,Edit,Read"` |
| `--add-dir` | Extra working directories Claude can read and edit |
| `--append-system-prompt` | Add text to the default system prompt (`--system-prompt` replaces all of it, safety instructions included) |
| `--output-format`, `--json-schema` | Print mode: `text`, `json` or `stream-json`; validated JSON returned in `structured_output` |
| `--max-turns`, `--max-budget-usd` | Print mode: cap agentic turns; stop at an estimated spend. `claude --help` does not list every flag: `--max-turns` is documented but missing from the help text of v2.1.332 |
| `--bare` | Skip auto-discovery of hooks, skills, subagents, plugins, MCP servers, auto memory and `CLAUDE.md` |
| `--setting-sources` | Choose which settings scopes load; `--setting-sources user` skips the project's settings files and its `.mcp.json` |
| `--mcp-config`, `--strict-mcp-config` | Load MCP servers from JSON; skip servers configured elsewhere |
| `--settings`, `--plugin-dir` | A settings file or inline JSON, or a plugin directory, for this session only |
| `-w`, `--worktree` | Start in an isolated git worktree at `.claude/worktrees/<name>` |
| `--bg`, `--background` | Start as a background session and return at once (cannot be combined with `-p`) |
| `--safe-mode`, `--debug`, `--verbose` | Start with all customizations disabled; debug log with a category filter such as `--debug=mcp`; full turn-by-turn output |
| `--dangerously-skip-permissions` | Same as `--permission-mode bypassPermissions`. Disposable sandboxes only |

→ [Chapter 06: CLI, slash commands and shortcuts](06-cli-slash-commands-and-shortcuts.md)

## 3. Slash commands by purpose

A command is recognised only at the start of your message. Not every command appears for every user; `/help` shows what your build has.

| Purpose | Command | What it does |
|---|---|---|
| Session | `/clear [name]` | New conversation with empty context. Aliases `/reset`, `/new` |
| | `/resume [session]`, `/rename [name]`, `/branch [name]` | Reopen a session by ID or name, or open the picker; name the current session; copy the conversation into a new session and switch to it |
| | `/rewind` | Rewind the conversation, the code or both. Aliases `/checkpoint`, `/undo` |
| Steer | `/plan [description]` | Enter plan mode, optionally starting on a task |
| | `/goal [condition]` | Keep working across turns until the condition is met; `/goal clear` removes it |
| | `/btw [question]` | A side question that is not added to the conversation |
| Context | `/context [all]` | Show what fills the context window; `all` lists it item by item |
| | `/compact [instructions]`, `/autocompact` | Summarise the conversation, with an optional focus; set when automatic compaction fires |
| | `/memory`, `/init` | List and edit instruction files and auto memory; generate a starting `CLAUDE.md` |
| | `/usage` | Session cost, plan limits and the prompt cache line. Aliases `/cost`, `/stats` |
| Config | `/model [model]`, `/effort` | Switch model and save it as your default; set the effort level |
| | `/permissions`, `/sandbox` | Manage allow, ask and deny rules; toggle the sandbox |
| | `/config`, `/output-style`, `/statusline`, `/keybindings` | Settings interface; switch output style; configure the status line; open the keybindings file |
| Extensions | `/mcp`, `/plugin` | Manage MCP connections and sign-in; manage plugins |
| | `/skills`, `/hooks`, `/agents` | List skills (`t` sorts by tokens); view registered hooks; a reminder on managing subagents |
| | `/reload-plugins`, `/reload-skills` | Apply plugin changes without a restart; re-scan skill directories |
| Review | `/diff`, `/code-review` | Read the changes in your working tree; review a diff, PR, branch or path for correctness bugs |
| | `/security-review`, `/simplify`, `/verify` | Check the branch for vulnerabilities; clean up changed code; build, run and observe a change |
| Parallel | `/tasks`, `/background` | View and manage background work; detach this session as a background agent |
| | `/subtask <task>`, `/fork` | Start a fork with a copy of the conversation; copy the conversation into a new background session |
| | `/batch <instruction>` | Split a change into 5 to 30 units, one background subagent per unit in its own worktree |
| | `/loop`, `/schedule` | Repeat a prompt in an open session; manage cloud scheduled tasks |
| Diagnostics | `/doctor`, `/status`, `/help`, `/debug` | Setup checkup with fixes; version, model and account; command list; debug logging |

→ [Chapter 06: CLI, slash commands and shortcuts](06-cli-slash-commands-and-shortcuts.md)

## 4. Keyboard shortcuts and input prefixes

| Key or prefix | What it does |
|---|---|
| `Esc` | Stop the current response or tool call; the work so far is kept. At a permission prompt it declines |
| `Esc` twice on an empty prompt | Open the rewind menu |
| `Shift+Tab` | Cycle permission modes. At a plan approval prompt it approves the plan, so use `Esc` to back out |
| `Ctrl+C` | Interrupt a running operation. With nothing running: clear the prompt, then exit on the second press |
| `Ctrl+B` | Send running Bash commands and agents to the background (press twice inside tmux) |
| `Ctrl+O` | Transcript viewer: tool details, and thinking as gray italic text |
| `Ctrl+R`, `Ctrl+S`, `Ctrl+T` | Search prompt history; stash or restore the prompt text; toggle Claude's task checklist |
| `Ctrl+G`, `Ctrl+V` | Open the prompt in your text editor; paste an image (`Cmd+V` in iTerm2, `Alt+V` on Windows and WSL) |
| `Ctrl+J`, or `\` then `Enter` | New line, in any terminal |
| `Enter` while Claude works | Queue the message; `Ctrl+Enter` sends queued messages now |
| `Option+P` or `Alt+P` | Switch model without clearing the prompt |
| `?` on an empty prompt | Show the shortcut panel for your terminal |
| `/` at the start | A command or a skill |
| `!` at the start | Shell mode: you run a command and its output joins the session |
| `@` | Mention a file or directory with path autocomplete; also attaches an MCP resource |
| `#` | Not documented today. Say "add this to CLAUDE.md" or use `/memory` |
| `ultrathink` in a prompt | Deeper reasoning for that turn only. "think hard" is ordinary text |

→ [Chapter 06: CLI, slash commands and shortcuts](06-cli-slash-commands-and-shortcuts.md) and [Chapter 16: Output styles, status line and keybindings](16-output-styles-statusline-keybindings.md)

## 5. Permission modes at a glance

| Mode | Runs without asking | Fits |
|---|---|---|
| `default` (shown as Manual) | File reads in your working directories | Sensitive work; your first weeks |
| `acceptEdits` | Reads, file edits and common filesystem commands (`mkdir`, `touch`, `mv`, `cp`) in the working directory | Iterating while you review the diff |
| `plan` | Reads and exploration; no edits to your source until you approve the plan | Looking before changing |
| `auto` | Everything, after a classifier model reviews each action | Everyday interactive work |
| `dontAsk` | Reads and pre-approved tools; anything that would prompt is denied | CI and scripts |
| `bypassPermissions` | Everything, apart from a short list no mode auto-approves | Isolated containers and VMs only |

- **Starting mode:** the `--permission-mode` flag, then `permissions.defaultMode`, then the built-in default. That default is `auto` for interactive sessions (v2.1.283 or later) and `default` for `claude -p` and the Agent SDK.
- **`Shift+Tab` cycle:** `auto`, `default`, `acceptEdits`, `plan`, then `bypassPermissions` only if it was enabled at launch. `dontAsk` is never in the cycle.
- **In every mode:** `deny` rules block, `ask` rules prompt (in `dontAsk` they deny), and hooks run.
- **Not a mode:** the sandbox is a separate operating-system boundary around shell commands, off by default (`/sandbox`).

→ [Chapter 08: Settings and permissions](08-settings-and-permissions.md)

## 6. Settings scopes and precedence

| Precedence | Scope | Location | Affects |
|---|---|---|---|
| 1 (highest) | Managed | `managed-settings.json` in the system directory, or pushed by an administrator | Everyone it is deployed to |
| 2 | Command line | `--settings <file-or-json>` | This run only |
| 3 | Project local | `.claude/settings.local.json` | You, in this project |
| 4 | Shared project | `.claude/settings.json` | Everyone who works in the repo |
| 5 | User | `~/.claude/settings.json` | You, in every project |

- A key set at a higher level overrides the same key lower down; list keys such as `permissions.allow` are combined. A tool denied at any level cannot be allowed by another level.
- `.claude/settings.json` is read from the session's primary working directory, with no parent-directory fallback.
- Settings files are strict JSON: a comment or a trailing comma is a syntax error. `~/.claude.json` is not a settings scope.

→ [Chapter 08: Settings and permissions](08-settings-and-permissions.md)

## 7. Permission rule syntax

| Rule | Matches |
|---|---|
| `Bash` | Every Bash command. In `deny`, a bare tool name removes the tool from Claude's context |
| `Bash(npm run build)`, `Bash(npm test *)` | That exact command; `npm test` alone or with anything after it. The space matters: `Bash(ls *)` does not match `lsof` |
| `Read(./.env)`, `Read(~/Documents/*.pdf)` | Paths in gitignore syntax. A bare filename matches at any depth |
| `Edit(/src/**/*.ts)` | Every built-in file-editing tool. `/path` is anchored at the settings file's own root |
| `Read(//Users/alice/secrets/**)` | `//path` is anchored at the filesystem root |
| `WebFetch(domain:example.com)` | That hostname only; `domain:*.example.com` matches subdomains but not `example.com` |
| `mcp__puppeteer`, `mcp__puppeteer__puppeteer_navigate` | Every tool from one MCP server; one tool |
| `Agent(Explore)`, `Skill(name)`, `Agent(fork)` | In `deny`: switch off one subagent type, one skill, or forks |

- **Order:** deny, then ask, then allow. The first match decides, and a narrow allow cannot rescue what a broad deny blocks.
- **Compound commands** are split on `&&`, `||`, `;`, `|` and newlines; every subcommand must be allowed.
- **Paths:** use `Read` and `Edit` only. `Write(path)`, `Grep(path)` and `Glob(path)` do not match, and a `.claudeignore` file has no effect.
- **Limits:** a Bash rule matches text, not intent. A deny on `Bash(rm *)` does not stop `/bin/rm` or `bash -c 'rm ...'`; use a hook or the sandbox for that.

→ [Chapter 08: Settings and permissions](08-settings-and-permissions.md)

## 8. Instruction-file load order

| File | When it loads |
|---|---|
| Managed `CLAUDE.md`, then `~/.claude/CLAUDE.md` | At launch, broadest first |
| `CLAUDE.md` or `.claude/CLAUDE.md` in the working directory and every directory above it | At launch, ordered from the filesystem root down |
| `CLAUDE.local.md` | At launch, after the `CLAUDE.md` in the same directory |
| Rule files under `.claude/rules/` without `paths:` | At launch; `~/.claude/rules/` loads before project rules |
| `MEMORY.md`, the auto memory index | The first 200 lines or 25KB at session start; topic files on demand |
| `@path` imports | Together with the file that imports them, up to four hops deep |
| A `CLAUDE.md` in a subdirectory | When Claude reads, writes or edits a file in that subdirectory |
| Rules with `paths:` | When Claude touches a matching file |
| `AGENTS.md` | Only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` is on the path (v2.1.277 or later) |

- Files are concatenated, never overridden; if two disagree there is no winner. They arrive as a user message: context the model reads, not configuration the harness enforces.
- After compaction the project-root `CLAUDE.md`, unscoped rules and auto memory are re-injected from disk. Path-scoped rules and subdirectory files return only when a matching file is touched again.
- `/memory` or `/context all` shows what loaded. Aim for under 200 lines per file.

→ [Chapter 07: CLAUDE.md and memory](07-claude-md-and-memory.md)

## 9. Context commands, and what `/rewind` does not restore

| Situation | Use |
|---|---|
| See what fills the window | `/context`, or `/context all` for each item |
| Same task, long history, direction settled | `/compact <what to keep>` |
| The next task is unrelated, or two corrections on one problem failed | `/clear`, then a fresh prompt |
| A quick side question | `/btw <question>` |
| Try an alternative and keep this thread | `/branch [name]` |
| Only the last stretch went wrong | `/rewind`: restore, or summarise from a chosen message |
| Compact earlier than the default (about 967K tokens on a 1M window) | `/autocompact 500k` |
| Stopping for the day, or handing over | Write a handoff note to a file, then exit |

| Change made by | Does `/rewind` restore it? |
|---|---|
| Claude's file editing tools | Yes |
| Bash, on a file Claude had already edited | Yes |
| Bash only: `sed -i`, a formatter, a code generator, `mv`, `rm` | No. Use git |
| A subagent | Usually no |
| You, outside Claude Code | Normally not captured |
| Symlinked or hard-linked files | No |
| Databases, APIs, deployments | No. Undo by hand |

A checkpoint is created by every prompt that starts a turn; the 100 most recent in a session are kept. After a full restore, `git status --short` lists what the rewind missed.

→ [Chapter 09: Plan mode, checkpoints and context management](09-plan-mode-checkpoints-and-context-management.md)

## 10. The extension surfaces compared

| Surface | Who triggers it | When it enters context | Use it for |
|---|---|---|---|
| `CLAUDE.md` and rules | Claude Code, at launch (path-scoped rules when a matching file is touched) | In full, on every turn | Facts and conventions needed in most tasks |
| Skill | Claude, when your request matches the description; or you, with `/name` | Name and description on every turn; the body on use; references and scripts on demand | A procedure needed only sometimes |
| Subagent | Claude, through the `Agent` tool; you, with `/subtask` for a fork | Its description is always in context; its work stays in its own window and a final report comes back | Parallel work, noisy output, an independent review |
| Hook | The harness, on a lifecycle event | Never, unless it prints `additionalContext` or a block reason | A rule that must hold every time |
| MCP server | Claude calls tools; you attach resources with `@` and run prompts as commands | Tool names and server instructions at start; a full definition when needed; results when called | Access to an external system |
| Plugin | You install and enable it | Its components load as in the rows above | Packaging and sharing the other surfaces |
| Output style | You, with `/output-style` | For the whole session; still applies after compaction | A different voice or format in every reply |

Of these, only a hook is executed by the harness every time. `CLAUDE.md`, a skill body, a subagent prompt and an output style are text the model reads, and it may decide a line does not apply.

→ [Chapter 07](07-claude-md-and-memory.md), [Chapter 11](11-mcp-in-practice.md), [Chapter 12](12-subagents.md), [Chapter 13](13-skills.md), [Chapter 14](14-hooks.md), [Chapter 15](15-plugins-and-marketplaces.md) and [Chapter 16](16-output-styles-statusline-keybindings.md)

## 11. Hooks: exit codes and the events used most

| Exit code | Meaning | What happens |
|---|---|---|
| `0` | Success | Valid JSON on stdout is applied. Claude never sees the stderr of a hook that exits 0 |
| `2` | Blocking error | On an event that can block, the action stops and stderr becomes the block message |
| Anything else, including `1` | Non-blocking error | The action goes ahead |

A timeout or a crash does not block either. Add `onFailure: "block"` (v2.1.295 or later) to a guard that must fail closed.

| Event | Fires | What exit 2 does |
|---|---|---|
| `PreToolUse` | Before a matching tool call | Blocks the call; the reason goes to Claude |
| `PostToolUse` | After a tool call | Cannot undo it; only shows stderr to Claude |
| `UserPromptSubmit` | When you submit a prompt | Rejects the prompt |
| `SessionStart` | At session start; `source` tells a resume or a compaction from a fresh start | Only renders a notice. Use the event to inject context |
| `Stop` | Every time Claude finishes responding | Blocks the stop and sends Claude back to work. Exit early when `stop_hook_active` is true. Exception: with nothing on stdout and a stderr that says a file is missing (`No such file or directory`), the exit 2 is a non-blocking error |
| `PreCompact` | Before a compaction | Can block it |

- **JSON instead of exit 2:** exit 0 and print `hookSpecificOutput.permissionDecision: "deny"` with a `permissionDecisionReason`. Choose one approach per hook.
- **Who reads what:** `hookSpecificOutput.additionalContext` reaches the model; `systemMessage` reaches you.
- **Matcher:** one string (`Bash`, `Edit|Write`, `*`), never an array; names are case-sensitive. The reference lists 34 events, and `/hooks` shows what is registered.

→ [Chapter 14: Hooks](14-hooks.md)

## 12. Skill and subagent frontmatter worth remembering

| File | Field | What to remember |
|---|---|---|
| Skill (`SKILL.md`) | `description`, `when_to_use` | What Claude matches your request against. The combined text is cut at 1,536 characters in the listing |
| | `disable-model-invocation`, `user-invocable` | `disable-model-invocation: true`: only you can run it, for anything with side effects. `user-invocable: false`: only Claude can |
| | `allowed-tools`, `disallowed-tools` | Pre-approve tools for the invoking turn (not a sandbox); remove tools while the skill is active |
| | `context: fork`, `agent` | Run the skill in a fresh subagent of that type, which does not see your conversation |
| | `argument-hint`, `arguments` | Autocomplete hint; names for positional arguments (`$ARGUMENTS`, `$0`, `$name` in the body) |
| | `paths`, `model`, `effort` | Globs for the files that activate the skill; model for the turn when you type `/name`; effort for the rest of that turn |
| Subagent (`.claude/agents/*.md`) | `name`, `description` | Required. The description tells Claude when to delegate |
| | `tools`, `disallowedTools` | Allowlist (every available tool if omitted); denylist |
| | `model`, `effort`, `maxTurns` | `sonnet`, `opus`, `haiku`, `fable`, a full model ID or `inherit`; effort; a cap on turns |
| | `permissionMode` | Ignored when the parent runs in `bypassPermissions`, `acceptEdits` or auto mode |
| | `skills`, `isolation` | Skills injected in full at startup; `isolation: worktree` runs it in a temporary git worktree, branched from the default branch |
| | `background`, `memory` | Stay in the background; a memory directory (`user`, `project` or `local`) that persists |
| | `omitClaudeMd`, `mcpServers`, `hooks` | Start without `CLAUDE.md` files; MCP servers and hooks scoped to the agent |

Skill field names are lowercase with hyphens (except `when_to_use`); subagent field names are camelCase. In both, an unknown field is ignored without an error. Plugin agents ignore `permissionMode`, `mcpServers` and `hooks`.

→ [Chapter 13: Skills](13-skills.md) and [Chapter 12: Subagents](12-subagents.md)

## 13. MCP commands and scopes

| Task | Command |
|---|---|
| Add a remote server (Streamable HTTP) | `claude mcp add --transport http <name> <url>` |
| Add a local server (stdio) | `claude mcp add [options] <name> -- <command> [args...]` |
| Pass a variable or a header | `--env KEY=value`; `--header "Authorization: Bearer your-token"` |
| Choose the scope | `--scope project` (short form `-s`); local is the default |
| List, inspect, remove, add from JSON | `claude mcp list`; `claude mcp get <name>`; `claude mcp remove <name>`; `claude mcp add-json <name> '<json>'` |
| Sign in or out with OAuth | `claude mcp login <name>`; `claude mcp logout <name>`; or `/mcp` in a session |
| Status, reconnect, switch one off | `/mcp`; `/mcp reconnect all`; `/mcp disable <name>` |

| Scope | Loads in | Shared | Stored in |
|---|---|---|---|
| Local (default) | The current project only | No | `~/.claude.json`, under that project's path |
| Project | The current project only | Yes, through version control | `.mcp.json` in the project root |
| User | All your projects | No | `~/.claude.json` |

- **Precedence** for one name defined twice: local, project, user, plugin-provided, then claude.ai connectors. The whole winning entry is used; fields are not merged.
- **Tool names:** `mcp__<server>__<tool>`; a plugin's server gives `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`. Permission rules use the same names.
- **Limits:** a warning at 10,000 tokens; 25,000 tokens kept in the conversation (`MAX_MCP_OUTPUT_TOKENS`); a larger result is saved to a file. Startup timeout `MCP_TIMEOUT`, 30000 ms.
- **Defaults:** tool search is on, so only tool names and server instructions load at session start. Use HTTP for remote servers and stdio for local ones; SSE is deprecated.

→ [Chapter 11: MCP in practice](11-mcp-in-practice.md) and [Chapter 10: MCP: how the protocol works](10-mcp-how-it-works.md)

## 14. Headless recipes

```bash
# One question, or piped input
claude -p "What does the auth module do?"
git log --oneline -20 | claude -p "summarize these recent commits"

# A result a script can parse, with the cost estimate
out=$(claude -p "Summarize this project" --output-format json)
echo "$out" | jq -r '.result'
echo "$out" | jq '.total_cost_usd'

# CI with an exact allowlist
claude -p "run the test suite" --permission-mode dontAsk --allowedTools "Bash(npm test)" "Read"

# Read-only review of a diff: clean start, capped
git diff origin/main...HEAD |
  claude -p "Review this diff for bugs. Give file, line and problem. Say 'no findings' if clean." \
    --bare --permission-mode dontAsk --allowedTools "Read" \
    --max-turns 10 --output-format json | jq -r '.result'

# Hardened call for a repository you did not write
claude -p "$PROMPT" --bare --setting-sources user \
  --strict-mcp-config --mcp-config ci/mcp.json \
  --permission-mode dontAsk --allowedTools "Read" "Bash(npm test)" \
  --max-turns 15 --max-budget-usd 2
```

- `claude -p` starts in `default` mode. A call that needs approval is denied and the run carries on without it.
- A `-p` run shows no trust dialog: it uses the repository's hooks, its settings `env` block and its `.mcp.json` servers without asking.
- `--bare` never reads OAuth or keychain credentials, so set `ANTHROPIC_API_KEY`. Hooks do not run in bare mode.
- Put the prompt directly after `-p`. For structured data add `--json-schema` and read `structured_output` with `jq -e`.
- Exit code `0` means success, but a failure inside the run (missing authentication, for example) is printed as the result on stdout. Check the output, not only the status.

→ [Chapter 22: Headless mode, CI and the Agent SDK](22-headless-ci-and-the-agent-sdk.md)

## 15. Which mechanism for which job

| You want | Use | Why |
|---|---|---|
| A fact or convention Claude needs in most tasks | `CLAUDE.md` | Loaded in full every session |
| Rules for one part of the tree | `.claude/rules/` with `paths:` | Loads only when a matching file is touched |
| A procedure needed only sometimes | A skill | The body loads only when it is used |
| A procedure with side effects that only you start | A skill with `disable-model-invocation: true` | Claude cannot decide to run it |
| Something that must happen, or must never happen, every time | A hook, a deny rule or a managed setting | The harness executes it; the model cannot skip it |
| A limit on what shell commands can touch | The sandbox | Enforced by the operating system |
| Access to an external system | An MCP server, or a CLI such as `gh` when one exists | MCP tool definitions and results cost context |
| Noisy exploration, parallel work, an independent review | A fresh-context subagent | Its tool calls stay out of your context |
| A side task that needs what this conversation knows | A fork (`/subtask`) | It starts with a copy of the conversation |
| The same extensions for a whole team | A plugin in a marketplace | One versioned unit to install |
| Two agents writing at the same time | One worktree per writer | Two writers in one checkout overwrite each other |
| The same mechanical change across many units | `/batch` or a workflow script | A worktree per unit, bounded concurrency |
| A run with nobody at the keyboard | `claude -p` or the Agent SDK | Approvals are decided before the run starts |
| One set of rules for several coding agents | `AGENTS.md` as the canonical source, with thin adapters | Copies drift; pointers do not |

→ [Chapter 13: Skills](13-skills.md), [Chapter 16: Output styles, status line and keybindings](16-output-styles-statusline-keybindings.md) and [Chapter 21: Multi-agent orchestration](21-multi-agent-orchestration.md)

## 16. The cost levers

| Lever | What to do | Why it works |
|---|---|---|
| Context length | `/clear` between unrelated tasks; `/compact <focus>` at a boundary you choose | The whole conversation is resent on every call |
| Prompt cache | Pick the model and effort at the start of a task; do not connect MCP servers mid-task; avoid long idle gaps | Each of these discards the cache, and the next call rewrites the context at more than the input price |
| Standing load | `CLAUDE.md` under 200 lines; procedures in skills; unused plugins and MCP servers disabled; a CLI such as `gh` where one exists | Always-on text and tool definitions are paid for on every call |
| Output | Lower `/effort`; ask for a diff or a summary, not a whole file | Output and thinking cost five times the input price |
| Noisy output | Pre-filter it with a hook; give verbose work to a subagent | Keeps the main context small (a subagent does not reduce total tokens) |
| Model tier | `model: haiku` for simple subagents; a stronger model for design and review | Match the model to the task |
| Fan-out | Fewer, well-scoped subagents | Each one runs its own loop with its own context and cache |
| Unattended runs | `--max-turns` and `--max-budget-usd`, with headroom | Turns have no limit by default, and spend can pass the cap |
| Idle spend | Stop `/loop` tasks and background agents you no longer need | They keep making calls |
| Measurement | `/usage` for cost and the `Prompt cache (main)` line; `/context` for what fills the window | Change one thing, then measure again |

→ [Chapter 25: Cost, usage and observability](25-cost-usage-and-observability.md) and [Chapter 04: Prompt caching, compaction and cost](04-prompt-caching-compaction-and-cost.md)

## 17. First aid when a session goes wrong

| When | Move |
|---|---|
| The agent drifts | Press `Esc` at once and redirect |
| You do not know what is wrong | Look before you guess: `/context`, `/usage`, `/hooks`, `/mcp`, `/doctor` |
| The last turn went wrong | `/rewind`, or `Esc` twice; then `git status` for what the rewind missed |
| Two corrections failed, or the same fix keeps coming back | `/clear`, find the root cause, then write a better prompt that carries what you learned |
| It says "done" without proof | Name a command that passes or fails, and ask for "the command you ran and its output" |
| A forbidden action happened | Undo it with git, then add a hook or a deny rule |
| Your own setup may be the cause | `claude --safe-mode`; then `claude --debug` and read the log under `~/.claude/debug/` |
| Claude Code will not start, or the terminal froze | `claude doctor` from the shell; close the terminal, then `claude --resume` |
| The same problem returns in a later session | Move the fix up a layer: from a prompt to `CLAUDE.md`, then to a hook or a deny rule |

→ [Chapter 27: Troubleshooting: common problems and fixes](27-troubleshooting-common-problems.md)

---

[← Previous: Prompt cookbook and anti-patterns](29-prompt-cookbook-and-anti-patterns.md) · [Contents](README.md) · [Next: Glossary →](B-glossary.md)
