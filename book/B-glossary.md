# Appendix B — Glossary

The terms this book uses, each defined the way the chapters use it, with a link to the chapter that explains it. Entries marked (MCP) belong to the Model Context Protocol. Version-sensitive details are as of Nov 2026.

## A

- **`acceptEdits`.** The permission mode in which reads, file edits and common filesystem commands (`mkdir`, `touch`, `mv`, `cp`) in the working directory run without a prompt. → [Chapter 08](08-settings-and-permissions.md)
- **Adapter.** A tool-specific instruction file that points at the canonical source instead of restating it, such as a `CLAUDE.md` whose first line is `@AGENTS.md`. → [Chapter 23](23-cross-tool-agents-md-cursor-codex-gemini.md)
- **Agent.** A language model that reads your code, edits files and runs commands in a loop until it decides the task is finished. Anthropic's short definition is "LLMs autonomously using tools in a loop." → [Chapter 01](01-what-is-ai-native-development.md)
- **Agent SDK.** The Claude Code agent as a TypeScript or Python library, for running the same loop inside your own application with approval callbacks. → [Chapter 22](22-headless-ci-and-the-agent-sdk.md)
- **Agent teams.** An experimental Claude Code feature: one lead plus teammates, which are separate Claude Code instances that share a task list and a mailbox. → [Chapter 21](21-multi-agent-orchestration.md)
- **Agentic loop.** The cycle in which the model asks for a tool, the harness runs it and returns the result, and the model decides what to do next. It repeats until the model answers in plain text. → [Chapter 03](03-the-agentic-loop-and-tool-use.md)
- **`AGENTS.md`.** An open, tool-neutral Markdown file of instructions for coding agents. Claude Code reads it natively (v2.1.277 or later), by default only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` is on the path; the **Project instructions** setting in `/config` can load both. → [Chapter 23](23-cross-tool-agents-md-cursor-codex-gemini.md)
- **Auto-compaction.** Compaction that Claude Code triggers by itself as the context approaches the limit, at about 967K tokens on a 1M window by default. → [Chapter 09](09-plan-mode-checkpoints-and-context-management.md)
- **Auto memory.** Notes Claude writes for itself between sessions, kept as Markdown files under `~/.claude/projects/<project>/memory/` with a `MEMORY.md` index. It is machine-local and not shared with your team. → [Chapter 07](07-claude-md-and-memory.md)
- **Auto mode (`auto`).** The permission mode in which a separate classifier model reviews actions before they run and blocks the ones it judges risky. New interactive sessions start in it (v2.1.283 or later). → [Chapter 08](08-settings-and-permissions.md)

## B

- **Background task.** A shell command, subagent or session that runs while you keep working. It returns a task ID at once, and its result arrives later as a notification; `/tasks` lists them. → [Chapter 20](20-parallel-work-worktrees-and-background-tasks.md)
- **`--bare`.** A flag for `claude -p` that skips auto-discovery of hooks, skills, subagents, plugins, MCP servers, auto memory and `CLAUDE.md`. Settings files and their permission rules are still read. → [Chapter 22](22-headless-ci-and-the-agent-sdk.md)
- **`bypassPermissions`.** The permission mode that disables permission prompts and safety checks so tool calls run immediately. `deny` rules and hooks still apply, and it is meant for isolated containers and VMs only. → [Chapter 08](08-settings-and-permissions.md)

## C

- **Cache breakpoint.** The `cache_control` marker in an API request that says where the cacheable prefix ends. → [Chapter 04](04-prompt-caching-compaction-and-cost.md)
- **Cache-hit ratio.** Cache read tokens divided by all prompt tokens (input plus cache read plus cache creation). → [Chapter 04](04-prompt-caching-compaction-and-cost.md)
- **Cache read.** Prompt tokens found in the prompt cache, billed at a small fraction of the input price: 0.025x to 0.1x, depending on the model. → [Chapter 04](04-prompt-caching-compaction-and-cost.md)
- **Cache write.** Tokens a request stores in the prompt cache, billed above the input price: 1.25x for the 5-minute cache and 2x for the 1-hour cache. → [Chapter 04](04-prompt-caching-compaction-and-cost.md)
- **Canonical source.** The one file that holds a policy; every other copy is a pointer to it or is generated from it. In a multi-tool repository the canonical instruction file is `AGENTS.md`. → [Chapter 23](23-cross-tool-agents-md-cursor-codex-gemini.md)
- **Capability registry.** A JSON file that records, for each tool and capability, a status such as `native`, `emulated` or `unknown`, the date it was last verified, and the fallback to use. → [Chapter 23](23-cross-tool-agents-md-cursor-codex-gemini.md)
- **Checkpoint.** A snapshot Claude Code saves each time you send a prompt that starts a turn, so that `/rewind` can return to that point. → [Chapter 09](09-plan-mode-checkpoints-and-context-management.md)
- **Classifier.** In auto mode, the separate model that reviews each action before it runs. Anthropic's own figures show it misses some risky actions, so treat it as a filter and not a guarantee. → [Chapter 08](08-settings-and-permissions.md)
- **`CLAUDE.md`.** A Markdown instruction file that Claude Code loads into the context at the start of a session. It is context the model reads, not configuration the harness enforces. → [Chapter 07](07-claude-md-and-memory.md)
- **Client (MCP).** The component inside the host that holds the connection to one server. The host creates one client per server. → [Chapter 10](10-mcp-how-it-works.md)
- **Compaction.** Replacing the older part of a conversation with a summary to free the context window. It is lossy: detailed instructions from early in the conversation may be lost. → [Chapter 04](04-prompt-caching-compaction-and-cost.md)
- **Context editing.** An API feature that clears the oldest tool results from the conversation and leaves a placeholder. → [Chapter 04](04-prompt-caching-compaction-and-cost.md)
- **Context engineering.** Curating what goes into the context window: finding "the smallest possible set of high-signal tokens" for the task. → [Chapter 02](02-llms-tokens-and-the-context-window.md)
- **Context rot.** The drop in accuracy and recall as the number of tokens in the context grows, well before the window is full. → [Chapter 02](02-llms-tokens-and-the-context-window.md)
- **Context window.** All the text the model can reference when it generates a response, including the response itself: system prompt, tool definitions, messages, tool results and output. → [Chapter 02](02-llms-tokens-and-the-context-window.md)

## D

- **`default` mode.** The permission mode shown as Manual: only file reads in your working directories run without asking. `claude -p` and the Agent SDK start in it. → [Chapter 08](08-settings-and-permissions.md)
- **Definition of done.** A checkable statement of what "finished" means. In this book it is one gate command whose exit code decides it, for example "A change is done when `make agent-check` exits 0 on the committed tree." → [Chapter 26](26-repo-standards-and-team-adoption.md)
- **Delegation brief.** The task prompt Claude writes when it hands work to a subagent. A good one states the goal, the known facts, the scope and what to return. → [Chapter 12](12-subagents.md)
- **Deny rule.** A permission rule that blocks a tool use. Deny rules are evaluated first and hold in every permission mode, including `bypassPermissions`. → [Chapter 08](08-settings-and-permissions.md)
- **`dontAsk`.** The permission mode in which reads and pre-approved tools run and anything that would prompt is denied. It fits CI and scripts. → [Chapter 08](08-settings-and-permissions.md)
- **Drift check.** A check, usually in CI, that fails when two files that should agree no longer do: an adapter and `AGENTS.md`, a generated file and its source, a mirrored skill folder and its original. → [Chapter 26](26-repo-standards-and-team-adoption.md)

## E

- **Effort.** The setting that controls how many tokens the model spends on a response, thinking included: `low`, `medium`, `high`, `xhigh` or `max`. It is a behavioural signal, not a strict token budget. → [Chapter 02](02-llms-tokens-and-the-context-window.md)
- **Elicitation (MCP).** The feature through which a server asks the user for more input. → [Chapter 10](10-mcp-how-it-works.md)
- **Eval.** A test for non-deterministic behaviour such as a prompt or a skill: a task, several trials, and a grader that scores each trial. → [Chapter 18](18-testing-and-verification-loops.md)

## F

- **Fail closed.** Said of a guard that blocks when it is itself broken; a guard that fails open lets the action through. For a hook, `onFailure: "block"` makes it fail closed. → [Chapter 14](14-hooks.md)
- **False completion.** A report that work is done when it is not. The chapters call it a false "done" claim and list its causes: the check never ran, its result was hidden, the tests were weakened, the behaviour was mocked away, or a proxy was checked. → [Chapter 18](18-testing-and-verification-loops.md)
- **Fan-out.** Running several independent subtasks in parallel agents. Each agent has its own loop, context and cache, so the cost multiplies. → [Chapter 21](21-multi-agent-orchestration.md)
- **Fork.** A subagent that starts with a copy of your whole conversation instead of a fresh context. You start one with `/subtask`, and Claude may start one itself while fork mode is on. `/fork` is a different command: it copies the conversation into a new background session. → [Chapter 12](12-subagents.md)

## G

- **Gate.** A check that decides whether a change may proceed. The gate command is one command whose exit code is the definition of done, the same for a human, an agent and CI. → [Chapter 26](26-repo-standards-and-team-adoption.md)
- **Goal.** A condition set with `/goal`. Claude keeps working across turns until a separate evaluator model judges the condition met. → [Chapter 18](18-testing-and-verification-loops.md)

## H

- **Handoff.** The record that lets someone else continue a piece of work. In orchestration it is the file a worker writes when its task ends, listing commits, files changed and the validation commands that actually ran. → [Chapter 21](21-multi-agent-orchestration.md)
- **Handoff note.** A short file that states the goal, the current state and the next step, so that a fresh session, another person or another tool can continue. → [Chapter 09](09-plan-mode-checkpoints-and-context-management.md)
- **Harness.** The program around the model that turns "predict the next piece of text" into "get a task done": the loop, the tools, the permission checks and the context management. Claude Code is a harness. → [Chapter 01](01-what-is-ai-native-development.md)
- **Headless.** Running the agent with nobody at the keyboard, through `claude -p`, the GitHub Action or the Agent SDK. Every approval is decided before the run starts. → [Chapter 22](22-headless-ci-and-the-agent-sdk.md)
- **Hook.** Code that the harness runs when a named lifecycle event fires. The model cannot skip it; exit code 2 blocks the action and exit code 1 does not. → [Chapter 14](14-hooks.md)
- **Host (MCP).** The AI application that coordinates one or more clients, such as Claude Code or an IDE. → [Chapter 10](10-mcp-how-it-works.md)

## I

- **Inert gate.** A gate that exists, is green, and cannot detect the thing it is named after. → [Chapter 18](18-testing-and-verification-loops.md)
- **Integration branch.** The branch into which an integrator merges every worker branch of an objective. The full suite runs there once, the combined diff is reviewed, and one pull request is opened from it. → [Chapter 21](21-multi-agent-orchestration.md)
- **`isError` (MCP).** A field on a tool result that marks a tool execution error. It arrives as a normal result, so the model can read the message and correct its next call. → [Chapter 10](10-mcp-how-it-works.md)

## J

- **JSON-RPC.** The message format of MCP. Every message is a JSON-RPC 2.0 request, response or notification. → [Chapter 10](10-mcp-how-it-works.md)

## K

- **Keybindings.** The map from keys to actions in the terminal UI, stored in `~/.claude/keybindings.json`. → [Chapter 16](16-output-styles-statusline-keybindings.md)

## L

- **Lethal trifecta.** The three things that turn prompt injection into data theft when they meet in one session: access to private data, exposure to untrusted content, and the ability to communicate externally. → [Chapter 24](24-security-and-guardrails.md)
- **LLM (large language model).** A model that, given a sequence of tokens, predicts the next token. It remembers nothing between requests. → [Chapter 02](02-llms-tokens-and-the-context-window.md)

## M

- **Managed settings.** Settings an organisation deploys to its machines. They have the highest precedence of all settings scopes. → [Chapter 08](08-settings-and-permissions.md)
- **Marketplace.** A repository or directory with a `.claude-plugin/marketplace.json` file that lists plugins and says where to fetch each one. "It's a catalog, not a hosted store." → [Chapter 15](15-plugins-and-marketplaces.md)
- **Matcher.** The string in a hook configuration that filters when the hook applies. For tool events it names tools, such as `Bash` or `Edit|Write`. → [Chapter 14](14-hooks.md)
- **MCP (Model Context Protocol).** An open protocol for connecting AI applications to external systems. You wrap a system once as a server, and every application that speaks MCP can use it. → [Chapter 10](10-mcp-how-it-works.md)
- **MRTR (Multi Round-Trip Requests) (MCP).** How a server gets input in the middle of a call: it answers with an `input_required` result, and the client retries the call with the answer. → [Chapter 10](10-mcp-how-it-works.md)
- **Mutation check.** Changing the code in a small way and expecting at least one test to fail. If every test still passes, nothing covers that behaviour. → [Chapter 18](18-testing-and-verification-loops.md)

## O

- **Orchestrator.** The agent that owns a multi-task objective: it dispatches tasks to workers, tracks their handoffs and delivers one pull request. It writes state files, not code. → [Chapter 21](21-multi-agent-orchestration.md)
- **Output style.** A named set of instructions about how Claude responds (tone, format, how much it explains) that applies for the whole session. → [Chapter 16](16-output-styles-statusline-keybindings.md)
- **Over-eager action.** A destructive or out-of-scope action the agent takes by itself to get past an obstacle, with no attacker involved. → [Chapter 24](24-security-and-guardrails.md)

## P

- **Path-scoped rule.** A rule file with a `paths:` list in its frontmatter. It stays out of the context until Claude works on a matching file. → [Chapter 07](07-claude-md-and-memory.md)
- **Permission mode.** The setting that decides what happens to a tool call that no permission rule mentions: `default`, `acceptEdits`, `plan`, `auto`, `dontAsk` or `bypassPermissions`. → [Chapter 08](08-settings-and-permissions.md)
- **Permission rule.** An `allow`, `ask` or `deny` entry written as `Tool` or `Tool(specifier)`. Rules are evaluated deny first, then ask, then allow. → [Chapter 08](08-settings-and-permissions.md)
- **Plan mode (`plan`).** The permission mode in which Claude reads files, explores and writes a plan but does not edit your source until you approve. → [Chapter 09](09-plan-mode-checkpoints-and-context-management.md)
- **Plugin.** A directory of components (skills, agents, hooks, MCP server configuration and more), usually with a manifest, that packages them for sharing. → [Chapter 15](15-plugins-and-marketplaces.md)
- **`PostToolUse`.** The hook event that fires after a tool call. It cannot undo the call; exit code 2 only shows the hook's stderr to Claude. → [Chapter 14](14-hooks.md)
- **`PreToolUse`.** The hook event that fires before a tool call and can block it. → [Chapter 14](14-hooks.md)
- **Print mode.** `claude -p`: run one query without the interactive UI, print the result and exit. → [Chapter 06](06-cli-slash-commands-and-shortcuts.md)
- **Progressive disclosure.** Loading a skill in stages, so that you pay for a stage only when it is reached: name and description always, the body when the skill is used, supporting files on demand. → [Chapter 13](13-skills.md)
- **Prompt (MCP).** A template a server offers that the user picks explicitly. In Claude Code it appears as a slash command. → [Chapter 10](10-mcp-how-it-works.md)
- **Prompt cache.** The API's store of the processed prefix of a request. If the next request starts with exactly the same content, those tokens are billed at the cache read price. → [Chapter 04](04-prompt-caching-compaction-and-cost.md)
- **Prompt injection.** An attack in which text the agent reads (a file, a web page, a tool result) tells it to do something you did not ask for. → [Chapter 24](24-security-and-guardrails.md)

## R

- **Required check.** A CI status check that branch protection demands before a merge, whatever the agent or its summary says. → [Chapter 19](19-git-prs-and-code-review.md)
- **Resource (MCP).** Data with a URI that a server offers and the application attaches as context. In Claude Code you attach one with `@`. → [Chapter 10](10-mcp-how-it-works.md)
- **Rewind.** Going back to a checkpoint with `/rewind`, or `Esc` twice: restore the code, the conversation or both. It does not restore changes made only by Bash commands, most subagent edits, or anything on a remote system. → [Chapter 09](09-plan-mode-checkpoints-and-context-management.md)
- **Rug pull.** An attack in which an MCP server changes a tool description after you approved the server. → [Chapter 24](24-security-and-guardrails.md)
- **Rules.** Instruction files under `.claude/rules/`, one topic each. Without frontmatter a rule loads at launch; with a `paths:` list it becomes a path-scoped rule. → [Chapter 07](07-claude-md-and-memory.md)

## S

- **Sabotage pair.** A demonstrated failure followed by a demonstrated pass: break the thing a gate guards and watch it go red, then restore it and watch it go green. → [Chapter 18](18-testing-and-verification-loops.md)
- **Sandbox.** A boundary the operating system enforces around the shell commands Claude runs, limiting where they can write and what they can reach on the network. It is off by default and is not a permission mode. → [Chapter 08](08-settings-and-permissions.md)
- **Seam test.** A test at the place where two pieces of code meet, such as a writer and a reader. It feeds one side the other side's real output instead of a hand-written fixture. → [Chapter 18](18-testing-and-verification-loops.md)
- **Server (MCP).** A program that provides tools, resources and prompts to clients. It runs on your machine or remotely. → [Chapter 10](10-mcp-how-it-works.md)
- **`SessionStart`.** The hook event that fires when a session starts, including on a resume and after a compaction. It is the usual place to inject context. → [Chapter 14](14-hooks.md)
- **Settings scope.** A level at which a settings file applies. In order of precedence: managed, command line, project local, shared project, user. → [Chapter 08](08-settings-and-permissions.md)
- **Skill.** A folder with a `SKILL.md` file: frontmatter that tells Claude when to use it, and a body of instructions Claude follows when it runs. Claude loads it when your request matches the description, or you type `/skill-name`. → [Chapter 13](13-skills.md)
- **Slash command.** A command typed at the start of a message, such as `/clear`. Custom slash commands were merged into skills. → [Chapter 06](06-cli-slash-commands-and-shortcuts.md)
- **Slopsquatting.** Registering the package names that models tend to invent, so that an agent with shell access installs the attacker's package. → [Chapter 24](24-security-and-guardrails.md)
- **Spec-driven development.** Writing what to build and why as a specification file, turning it into a plan and then tasks, and implementing the tasks one by one. → [Chapter 17](17-explore-plan-implement-verify.md)
- **Status line.** The text under the prompt. Claude Code produces it by running a command of yours that receives session state as JSON on stdin. → [Chapter 16](16-output-styles-statusline-keybindings.md)
- **stdio (MCP).** The transport for local servers: the client launches the server as a subprocess, and they exchange one JSON-RPC message per line on stdin and stdout. → [Chapter 10](10-mcp-how-it-works.md)
- **`Stop`.** The hook event that fires every time Claude finishes responding. Exit code 2 blocks the stop and sends Claude back to work. → [Chapter 14](14-hooks.md)
- **Stop reason.** The `stop_reason` field on every API response, which says why the model stopped: `end_turn`, `tool_use` and others. The harness branches on it. → [Chapter 03](03-the-agentic-loop-and-tool-use.md)
- **Streamable HTTP (MCP).** The transport for remote servers: each client message is its own HTTP POST to a single endpoint. It replaces the deprecated HTTP+SSE transport. → [Chapter 10](10-mcp-how-it-works.md)
- **Subagent.** A second agentic loop that Claude starts with the `Agent` tool. It works in its own context window and returns a final report. Unless it is a fork it starts with a fresh context, but it still loads `CLAUDE.md`, a git status snapshot and preloaded skills (the built-in Explore and Plan agents skip the first two). → [Chapter 12](12-subagents.md)

## T

- **Task graph.** The set of tasks an objective is split into, each with the tasks it depends on and the files it may touch. → [Chapter 21](21-multi-agent-orchestration.md)
- **Thinking.** The model working through a problem in its own words before it answers. It is billed as output tokens, even when the text is collapsed. → [Chapter 02](02-llms-tokens-and-the-context-window.md)
- **Token.** The unit the model reads and writes: a word, part of a word, a character or a byte. Prices, rate limits and the context window are all measured in tokens. → [Chapter 02](02-llms-tokens-and-the-context-window.md)
- **Tool (MCP).** A function a server exposes for the model to call. In Claude Code it is named `mcp__<server>__<tool>`. → [Chapter 10](10-mcp-how-it-works.md)
- **Tool poisoning.** Hiding instructions in an MCP tool description, which the model reads and you usually do not. → [Chapter 24](24-security-and-guardrails.md)
- **Tool search.** The default behaviour in which only MCP tool names and server instructions load at session start, and a tool's full definition loads when Claude needs it. → [Chapter 11](11-mcp-in-practice.md)
- **Tool use.** The convention by which a model acts: it writes a structured request for a function you described, and the harness runs the function and returns the output. → [Chapter 03](03-the-agentic-loop-and-tool-use.md)
- **`tool_use` / `tool_result`.** The two content blocks of a tool call. `tool_use` comes from the model with an `id`, a tool name and the input; `tool_result` goes back in the next user message with the matching `tool_use_id`. → [Chapter 03](03-the-agentic-loop-and-tool-use.md)
- **Trust dialog.** The prompt an interactive session shows before it treats a folder's project configuration as trusted. A `claude -p` run shows none. → [Chapter 24](24-security-and-guardrails.md)

## U

- **`ultrathink`.** A keyword in a prompt that asks for deeper reasoning on that turn only, without changing the session's effort level. → [Chapter 09](09-plan-mode-checkpoints-and-context-management.md)
- **`UserPromptSubmit`.** The hook event that fires when you submit a prompt. It can reject the prompt. → [Chapter 14](14-hooks.md)

## W

- **Worker.** An agent that carries out exactly one scoped task of an objective in its own worktree. It ends at a commit plus a handoff, never at a pull request. → [Chapter 21](21-multi-agent-orchestration.md)
- **Workflow.** As a design term, a system in which LLMs and tools are orchestrated through predefined code paths, in contrast to an agent that directs its own process. → [Chapter 01](01-what-is-ai-native-development.md)
- **Workflow script.** A JavaScript script that orchestrates many subagents, also called a dynamic workflow. Claude writes it and a runtime executes it in the background. → [Chapter 21](21-multi-agent-orchestration.md)
- **Worktree.** An extra working directory attached to the same git repository, with its own files, index and `HEAD`. One worktree per writer keeps parallel agents from overwriting each other. → [Chapter 20](20-parallel-work-worktrees-and-background-tasks.md)

---

[← Previous: Cheat sheet](A-cheat-sheet.md) · [Contents](README.md) · [Next: Templates →](C-templates.md)
