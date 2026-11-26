# Concepts

How the book is organised, so you can decide what to read and how far to trust each kind of statement in it.

## Six levels

The book's spine is a ladder of six levels of working with coding agents. Each level keeps everything below it; what changes is where your attention goes.

| Level | Name | What it means |
|---|---|---|
| 0 | Autocomplete and chat | You write the code. The model suggests and explains. |
| 1 | Single interactive agent session | The agent reads, edits and runs commands. You steer and approve. |
| 2 | Project memory and permissions | The repository carries your conventions and limits. You stop repeating yourself. |
| 3 | Extended harness | The agent gains tools and guardrails you built: MCP, skills, hooks, subagents. Rules become code. |
| 4 | Parallel and multi-agent work | Several agents work at once. You write briefs and review results. |
| 5 | Agents in the pipeline | Agents run unattended. You design the gates and watch the signals. |

The ladder is drawn in the book's [maturity ladder figure](../../book/assets/fig-maturity-ladder.svg), and [Appendix E](../../book/E-learning-path-and-exercises.md) has one section per level with projects and self-checks.

```mermaid
%%{init: {"theme":"base","themeVariables":{"darkMode":true,"background":"#0b0e14","primaryColor":"#1f2937","primaryTextColor":"#ffffff","primaryBorderColor":"#94a3b8","secondaryColor":"#334155","secondaryTextColor":"#ffffff","tertiaryColor":"#111827","tertiaryTextColor":"#ffffff","lineColor":"#64748b","textColor":"#ffffff","edgeLabelBackground":"#1f2937","clusterBkg":"#111827","clusterBorder":"#64748b","actorBkg":"#1f2937","actorBorder":"#94a3b8","actorTextColor":"#ffffff","actorLineColor":"#64748b","signalColor":"#64748b","signalTextColor":"#64748b","labelBoxBkgColor":"#1f2937","labelBoxBorderColor":"#94a3b8","labelTextColor":"#ffffff","loopTextColor":"#ffffff","noteBkgColor":"#334155","noteTextColor":"#ffffff","noteBorderColor":"#94a3b8","activationBkgColor":"#334155","activationBorderColor":"#94a3b8"}}}%%
flowchart LR
    L0["0: Autocomplete and chat"] --> L1["1: Single agent session"]
    L1 --> L2["2: Project memory and permissions"]
    L2 --> L3["3: Extended harness"]
    L3 --> L4["4: Parallel and multi-agent work"]
    L4 --> L5["5: Agents in the pipeline"]
```

## Six parts

The chapters are grouped into six parts. Parts follow the ladder roughly, but they are organised by topic, so a part can serve more than one level.

| Part | Chapters | Topic |
|---|---|---|
| I — Foundations | 1 to 4 | What AI-native development is; tokens and the context window; the agentic loop; caching and cost |
| II — Claude Code core | 5 to 9 | Installing, the CLI, instruction files and memory, settings and permissions, steering a long session |
| III — Extending the harness | 10 to 16 | MCP, subagents, skills, hooks, plugins, interface customisation |
| IV — Workflows | 17 to 23 | The explore-plan-implement-verify loop, testing, git and review, parallel work, orchestration, headless runs, cross-tool setups |
| V — Production concerns | 24 to 26 | Security, cost and observability, repo standards and team adoption |
| VI — Field guide | 27 to 29 | Troubleshooting catalogue, case studies, prompt cookbook |

Five appendices sit beside the parts: a cheat sheet (A), a glossary (B), templates (C), sources (D), and the learning path (E).

The 30-day plan in Appendix E shows how the two views line up: week 1 covers levels 0 and 1 with chapters 1 to 6 and 9; week 2 covers level 2 and the start of level 3 with chapters 7, 8 and 10 to 13; week 3 finishes level 3 and starts level 4 with chapters 14 to 19; week 4 finishes level 4 and covers level 5 with chapters 20 to 26. Chapters 27 to 29 are for review.

## The chapter skeleton

Every numbered chapter has the same parts in the same order. Once you know the shape, you can go straight to the part you need.

| Part of a chapter | What you find there | Use it to |
|---|---|---|
| Opening paragraph | What you can do after reading | Decide whether to read the chapter now |
| Mental model | The idea in plain words, with a diagram | Get the concept before the detail |
| Core sections | The mechanics, with copyable examples | Do the thing |
| From the field | What happened in real use | Calibrate the advice against practice |
| Common problems | A symptom, cause and fix table | Look up a failure |
| Checklist | Short, checkable items | Confirm your own setup |
| Try it | Exercises for your own repository | Practise |
| Sources | The pages the chapter relies on | Check a fact or read further |

Three callouts appear throughout, and they mean what they say: `Note` adds a detail, `Warning` marks something that can hurt, and `Field note` is an observation from the field data.

## Two kinds of evidence

The book keeps two kinds of evidence apart on every page. Knowing which one you are reading tells you how to use it.

| | Documentation | Field data |
|---|---|---|
| What it is | The official Claude Code, Claude API and Model Context Protocol docs, plus engineering posts, studies and security reports | One developer's repositories, configuration and about four weeks of session transcripts |
| When | Read on 2026-11-25 | A rolling window of about four weeks |
| Where it appears | The core sections of each chapter | "From the field" sections, `Field note` callouts and the charts |
| How it is marked | Version-sensitive facts carry "as of Nov 2026" | Labelled as field data, anonymised |
| How to use it | As a statement of how the tool behaved on that date; check your own version | As an example of what one person's month looked like, never as a benchmark |

A claim that could not be confirmed on a primary page was left out or marked "check in your version". [Appendix D](../../book/D-sources.md) lists every source, records which addresses have moved, and explains what the field data can and cannot tell you.

## Diagrams and figures

- **Diagrams** inside chapters are written in Mermaid and render inline in viewers that support it.
- **Figures and charts** are static SVG files in `book/assets/`. The ten charts are generated from the field data; the cover page of the book lists every figure and the chapters that use it.

## Accuracy and limits

Coding agents change quickly. Where your installed version disagrees with a chapter, trust the tool's own help output and the official docs, and treat the chapter as dated. The date to compare against is 2026-11-25.

---

<p align="center"><a href="https://github.com/TamirCohen28">Have a Question?</a>&nbsp;·&nbsp;<a href="https://github.com/TamirCohen28/ai-native-dev-guide/issues/new/choose">Open an Issue</a></p>
