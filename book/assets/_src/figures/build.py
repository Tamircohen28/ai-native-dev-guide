#!/usr/bin/env python3
"""Builds the seven concept figures. Facts come from the session research files."""
import math
import os
import sys

from lib import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '')


# ------------------------------------------------------------------ 1. cover
def cover():
    f = Fig('cover.svg', 1200, 480, 'AI-Native Development: Zero to Hero',
            'Cover banner. Title, subtitle, and a loop of four steps: prompt, plan, tools, verify.')
    # title block
    f.rect(80, 108, 64, 6, fill=TEAL, rx=3)
    f.text(78, 196, 'AI-Native Development', size=60, weight=700, fill=INK, maxw=740)
    f.add(f'<text x="80" y="246" font-family="{SANS}" font-size="20" fill="{INK2}">'
          f'<tspan font-weight="700" fill="{TEAL}">Zero to Hero</tspan>'
          f'<tspan> — a field guide to building software with coding agents</tspan></text>')
    # zero-to-hero steps
    x0, y0, gap = 96, 346, 58
    f.line(x0, y0, x0 + 5 * gap, y0, stroke=RULE, sw=2)
    for i in range(6):
        cx = x0 + i * gap
        f.circle(cx, y0, 15, fill=RAMP[i], stroke=PAPER, sw=3)
        f.text(cx, y0 + 5, str(i), size=14, weight=700, anchor='middle',
               fill=WHITE if i >= 4 else INK)
    f.text(x0 - 15, y0 + 42, 'zero', size=14, fill=INK3)
    f.text(x0 + 5 * gap + 15, y0 + 42, 'hero', size=14, fill=INK3, anchor='end')
    # loop motif
    cx, cy, R = 1000, 240, 112
    f.circle(cx, cy, R, fill='none', stroke=FAINT, sw=10)

    def pt(deg):
        a = math.radians(deg)
        return cx + R * math.sin(a), cy - R * math.cos(a)

    for a0, a1 in ((30, 77), (103, 150), (210, 257), (283, 330)):
        (x1, y1), (x2, y2) = pt(a0), pt(a1)
        f.path(f'M{x1:.1f},{y1:.1f} A{R},{R} 0 0 1 {x2:.1f},{y2:.1f}', stroke=INK2, sw=2.25,
               arrow=True)
    nodes = [('prompt', 0, PLUM, PLUM_T), ('plan', 90, BLUE, BLUE_T),
             ('tools', 180, AMBER, AMBER_T), ('verify', 270, TEAL, TEAL_T)]
    for label, deg, c, t in nodes:
        x, y = pt(deg)
        f.rect(x - 52, y - 20, 104, 40, fill=t, stroke=c, sw=1.75, rx=20)
        f.text(x, y + 5.5, label, size=16, weight=600, fill=INK, anchor='middle')
    f.text(cx, cy + 5, 'repeat', size=15, fill=INK3, anchor='middle')
    return f


# ------------------------------------------------------- 2. context window
def context_window():
    f = Fig('fig-context-window.svg', 960, 700, 'Anatomy of a context window',
            'Stacked bar of what fills a Claude Code context window: system prompt, tool '
            'definitions, CLAUDE.md and memory, skill descriptions, conversation messages, tool '
            'results, free space and the output reserve. Illustrative, not to scale.')
    f.header('Anatomy of a context window',
             'Everything a Claude Code session sends to the model on each request. '
             'Illustrative, not to scale.')
    segs = [
        ('System prompt', ["Claude Code's own instructions, plus the output style."], 52, '#2B5BC7', 'A'),
        ('Tool definitions', ['Built-in tools plus MCP. With tool search on (the default),',
                              'only MCP tool names and server instructions load at start.'], 68, '#5179D5', 'A'),
        ('`CLAUDE.md`, rules, auto memory', ['Delivered as a user message after the system prompt.',
                                             '`MEMORY.md`: the first 200 lines or 25KB.'], 68, '#7E9CE2', 'A'),
        ('Skill descriptions', ["Descriptions only. A skill's body loads when it is invoked."], 52, '#B0C3EF', 'A'),
        ('Conversation messages', ["Your prompts and the model's replies, earlier thinking included."], 86, '#D08A2A', 'B'),
        ('Tool results', ['File reads, command output, MCP responses, subagent summaries.'], 86, '#E8B66C', 'B'),
        ('Free space', ['What is left for the turns still to come.'], 68, None, 'C'),
        ('Output reserve', ['The reply being generated counts toward the window too.'], 52, PLUM_T, 'C'),
    ]
    bx, bw, top, gap = 54, 148, 104, 3
    y = top
    spans_ = {}
    for name, notes, h, col, grp in segs:
        if col is None:
            f.rect(bx + 0.75, y + 0.75, bw - 1.5, h - 1.5, fill=CARD, stroke=INK3, sw=1.5, rx=4, dash='5 4')
        elif grp == 'C':
            f.rect(bx + 0.75, y + 0.75, bw - 1.5, h - 1.5, fill=col, stroke=PLUM, sw=1.5, rx=4)
        else:
            f.rect(bx, y, bw, h, fill=col, rx=4)
        mid = y + h / 2
        f.line(bx + bw + 6, mid, bx + bw + 20, mid, stroke=RULE, sw=1.5)
        block = 15 + 18 * len(notes)
        ty = mid - block / 2 + 13
        f.text(bx + bw + 30, ty, name, size=T_NODE, weight=600, maxw=430)
        for i, n in enumerate(notes):
            f.text(bx + bw + 30, ty + 19 + i * 17, n, size=T_SMALL, fill=INK2, maxw=440, mfill=INK)
        a, b = spans_.get(grp, (y, y + h))
        spans_[grp] = (min(a, y), y + h)
        y += h + gap
    bottom = y - gap
    # extent of the window
    f.line(36, top, 36, bottom, stroke=INK3, sw=1.5)
    f.line(31, top, 41, top, stroke=INK3, sw=1.5)
    f.line(31, bottom, 41, bottom, stroke=INK3, sw=1.5)
    f.text(27, (top + bottom) / 2, 'one context window', size=T_SMALL, fill=INK3, anchor='middle',
           rotate=-90)
    # group brackets
    groups = {
        'A': (BLUE, 'Loaded at session start', ['Counts on every request,', 'cached or not.']),
        'B': (AMBER, 'Grows with every turn', ['Each request resends the history;', '`/compact` summarizes it.']),
        'C': (INK3, 'Headroom', ['As it runs out, Claude Code', 'compacts automatically.']),
    }
    gx = 700
    for g, (c, head, notes) in groups.items():
        a, b = spans_[g]
        f.path(f'M{gx - 8},{a + 4} H{gx} V{b - 4} H{gx - 8}', stroke=c, sw=2)
        mid = (a + b) / 2
        f.text(gx + 16, mid - 14, head, size=T_NODE, weight=600, fill=c, maxw=228)
        for i, n in enumerate(notes):
            f.text(gx + 16, mid + 6 + i * 17, n, size=T_SMALL, fill=INK2, maxw=228, mfill=INK)
    f.text(32, bottom + 38, '`/context` shows current usage as a colored grid; `/context all` '
           'expands the per-item breakdown.', size=T_SMALL, fill=INK3, mfill=INK2, maxw=896)
    f.H = int(bottom + 62)
    return f


# ----------------------------------------------------------- 3. agent loop
def agent_loop():
    f = Fig('fig-agentic-loop.svg', 960, 652, 'The agent loop',
            'A user prompt goes to the model. While the model stops with stop_reason tool_use, '
            'each tool_use block passes PreToolUse hooks and permission rules, the harness runs '
            'the tool, and a tool_result goes back to the model. The loop ends with end_turn.')
    f.header('The agent loop',
             'The model asks for tools until it can answer. The harness runs them, never the model.')
    # harness zone
    f.rect(16, 418, 928, 218, fill=BAND, rx=14)
    f.text(36, 594, 'Inside the harness', size=T_BODY, weight=600, fill=INK2)
    f.text(36, 613, 'Claude Code runs every step in this band.', size=T_SMALL, fill=INK3, maxw=310)

    # top row
    f.node(32, 108, 200, 74, 'Your prompt', ['joins the conversation'], fill=PLUM_T, stroke=PLUM)
    f.node(380, 108, 200, 74, 'Model', ['reads the whole context'], fill=BLUE_T, stroke=BLUE)
    f.node(728, 108, 200, 74, 'Final answer', ['`Stop` hooks fire here'], fill=CARD, stroke=INK, sw=2)
    f.line(232, 145, 376, 145, arrow=True)
    f.text(304, 136, 'request', size=T_SMALL, fill=INK3, anchor='middle')
    f.line(580, 145, 724, 145, arrow=True)
    f.text(652, 136, 'stop_reason:', size=T_SMALL, fill=INK, anchor='middle', mono=True, maxw=140)
    f.text(652, 164, '"end_turn"', size=T_SMALL, fill=INK, anchor='middle', mono=True, maxw=140)

    # middle row: the two message blocks
    f.node(32, 262, 240, 84, 'tool_result', ['`tool_use_id` · `content`', 'optional `is_error: true`'],
           fill=CARD, stroke=INK3, tmono=True)
    f.node(688, 262, 240, 84, 'tool_use', ['`id` · `name` · `input`', 'one or more per reply'],
           fill=CARD, stroke=INK3, tmono=True)
    f.path('M530,182 V294 Q530,304 540,304 H684', arrow=True)
    f.text(542, 226, 'stop_reason:', size=T_SMALL, fill=INK, mono=True)
    f.text(542, 244, '"tool_use"', size=T_SMALL, fill=INK, mono=True)
    f.path('M272,304 H420 Q430,304 430,294 V186', arrow=True)
    f.text(418, 226, 'appended to messages,', size=T_SMALL, fill=INK2, anchor='end')
    f.text(418, 244, 'then a new request', size=T_SMALL, fill=INK2, anchor='end')

    # bottom row: gates and execution
    f.node(688, 436, 240, 84, '`PreToolUse` hooks', ['your code runs first;', 'exit code 2 blocks the call'],
           fill=AMBER_T, stroke=AMBER)
    f.node(360, 436, 240, 84, 'Rules, mode, rules',
           ['`deny`, then `ask`, then the', 'mode, then `allow`'], fill=TEAL_T, stroke=TEAL)
    f.node(32, 436, 240, 84, 'Tool runs', ['the harness executes it,', 'never the model'],
           fill=CARD, stroke=INK2)
    f.line(808, 346, 808, 432, arrow=True)
    f.line(688, 478, 604, 478, arrow=True)
    f.text(646, 469, 'no block', size=T_SMALL, fill=INK3, anchor='middle')
    f.line(360, 478, 276, 478, arrow=True)
    f.text(318, 469, 'allowed', size=T_SMALL, fill=INK3, anchor='middle')
    f.line(152, 436, 152, 350, arrow=True)
    f.chip(166, 380, '`PostToolUse` hooks', AMBER_T, INK, stroke=AMBER, weight=400)
    f.text(516, 397, 'Repeats while `stop_reason` is `"tool_use"`', size=T_BODY, fill=INK2, mfill=INK,
           anchor='middle', weight=600)

    # blocked branch
    f.rect(360, 574, 568, 42, fill=RED_T, stroke=RED, rx=10)
    f.text(644, 600, 'Blocked: the tool does not run', size=T_NODE, weight=600, fill=RED, anchor='middle')
    f.line(480, 520, 480, 570, stroke=RED, dash='5 4', arrow=True)
    f.text(492, 551, '`deny` rule, or you decline', size=T_SMALL, fill=RED, mfill=RED)
    f.line(808, 520, 808, 570, stroke=RED, dash='5 4', arrow=True)
    f.text(820, 551, 'exit code 2', size=T_SMALL, fill=RED)
    return f


# -------------------------------------------------------- 4. extension map
def extension_map():
    f = Fig('fig-extension-map.svg', 960, 684, 'Six ways to extend Claude Code',
            'Matrix of CLAUDE.md and rules, skills, subagents, hooks, MCP servers and plugins: '
            'who triggers each, when it enters context, and what it is best for.')
    f.header('Six ways to extend Claude Code',
             'Who triggers each one, what it costs in context, and what it is best for.')
    X0, X1 = 24, 936
    cS, cT, cC, cB = 24, 228, 460, 712          # column lefts
    tcols = [(257, 'always', 'loaded', BLUE), (315, 'model', 'decides', TEAL),
             (373, 'you', 'invoke', PLUM), (431, 'harness', 'event', AMBER)]
    hy = 96
    f.text(cS + 16, hy + 40, 'EXTENSION', size=T_SMALL, weight=700, fill=INK3, ls=0.8)
    f.text((cT + cC) / 2, hy + 14, 'WHO TRIGGERS IT', size=T_SMALL, weight=700, fill=INK3, ls=0.8,
           anchor='middle')
    for cx, a, b, c in tcols:
        f.text(cx, hy + 34, a, size=T_SMALL, weight=600, fill=c, anchor='middle', maxw=56)
        f.text(cx, hy + 50, b, size=T_SMALL, weight=600, fill=c, anchor='middle', maxw=56)
    f.text(cC + 16, hy + 40, 'WHEN IT ENTERS CONTEXT', size=T_SMALL, weight=700, fill=INK3, ls=0.8)
    f.text(cB + 14, hy + 40, 'BEST FOR', size=T_SMALL, weight=700, fill=INK3, ls=0.8)

    rows = [
        ('`CLAUDE.md` and rules', '`.claude/rules/*.md`', [0],
         ['In full at launch, every session.', 'Nested files and `paths:` rules', 'load on demand.'],
         ['Conventions every task needs.', 'Advisory, not enforced.']),
        ('Skills', '`<name>/SKILL.md`', [1, 2],
         ['Descriptions on every turn;', 'the body only when invoked.'],
         ['Procedures and reference', 'material used only sometimes.']),
        ('Subagents', '`.claude/agents/*.md`', [1, 2],
         ['Works in its own context window;', 'a summary returns to yours.', 'A fork starts with a copy of yours.'],
         ['Noisy or parallel work that', 'should stay out of your context.']),
        ('Hooks', '`hooks` in `settings.json`', [3],
         ['Runs outside the conversation.', 'Only what it returns is added', 'to context.'],
         ['Rules with zero exceptions:', 'hard blocks, must-run steps.']),
        ('MCP servers', '`.mcp.json`', [1, 2],
         ['Tool names and server instructions', 'at session start; full definitions', 'on demand (tool search).'],
         ['Connecting the tools Claude', 'needs when a CLI will not do.']),
        ('Plugins', '`.claude-plugin/`', None,
         ['What it ships: skill and agent', 'descriptions on every turn, its', 'MCP servers in every session.'],
         ['Packaging the other five to', 'share across projects and teams.']),
    ]
    y, rh, pitch = hy + 62, 72, 80
    for name, path, dots, ctx, best in rows:
        f.rect(X0, y, X1 - X0, rh, fill=CARD, stroke=FAINT, sw=1.5, rx=10)
        for xx in (cT, cC, cB):
            f.line(xx, y + 10, xx, y + rh - 10, stroke=FAINT, sw=1.5)
        mid = y + rh / 2
        f.text(cS + 16, mid - 5, name, size=T_NODE, weight=600, maxw=cT - cS - 26)
        f.text(cS + 16, mid + 16, path, size=T_SMALL, fill=INK2, maxw=cT - cS - 26)
        if dots is None:
            f.rect(cT + 12, mid - 23, cC - cT - 24, 46, fill=PAPER, stroke=RULE, sw=1.25, rx=8, dash='4 3')
            f.text((cT + cC) / 2, mid - 3, 'a bundle: each component', size=T_SMALL, fill=INK2,
                   anchor='middle', maxw=cC - cT - 36)
            f.text((cT + cC) / 2, mid + 14, 'keeps its own trigger', size=T_SMALL, fill=INK2,
                   anchor='middle', maxw=cC - cT - 36)
        else:
            for i, (cx, _, _, c) in enumerate(tcols):
                if i in dots:
                    f.circle(cx, mid, 9, fill=c)
                else:
                    f.circle(cx, mid, 3, fill=FAINT)
        for col, rows_, maxw in ((cC + 16, ctx, cB - cC - 26), (cB + 14, best, X1 - cB - 24)):
            ty = mid - (len(rows_) - 1) * 8.5 + 4.5
            for i, t in enumerate(rows_):
                f.text(col, ty + i * 17, t, size=T_SMALL, fill=INK if col > cB else INK2, mfill=INK,
                       maxw=maxw)
        y += pitch
    f.text(32, y + 18, 'Custom slash commands have been merged into skills. A skill runs when the '
           'model matches its description or when you type `/skill-name`.', size=T_SMALL, fill=INK3,
           mfill=INK2, maxw=896)
    f.H = int(y + 40)
    return f


# ----------------------------------------------------- 5. MCP architecture
def mcp_architecture():
    f = Fig('fig-mcp-architecture.svg', 960, 690, 'How MCP connects an application to its tools',
            'An application connects through an MCP client to a local MCP server over stdio and '
            'to a remote MCP server over Streamable HTTP. Servers expose tools, resources and '
            'prompts. The client sends tools/list, then tools/call.')
    f.header('How MCP connects an application to its tools',
             'One protocol, two standard transports. Servers expose tools, resources and prompts.')
    # zones
    f.add(f'<path d="M26,92 H934 Q948,92 948,106 V270 Q948,284 934,284 H402 Q388,284 388,298 '
          f'V414 Q388,428 374,428 H26 Q12,428 12,414 V106 Q12,92 26,92 Z" fill="{BAND}"/>')
    f.text(30, 114, 'YOUR MACHINE', size=T_SMALL, weight=700, fill=INK3, ls=1)
    f.text(936, 420, 'REMOTE', size=T_SMALL, weight=700, fill=INK3, ls=1, anchor='end')

    # application
    f.rect(28, 126, 344, 290, fill=CARD, stroke=BLUE, sw=1.5, rx=12)
    f.text(46, 152, 'Application', size=T_NODE, weight=600)
    f.text(46, 171, 'for example, Claude Code', size=T_SMALL, fill=INK2)
    f.text(46, 198, 'Tools reach the model as', size=T_SMALL, fill=INK2, maxw=176)
    f.text(46, 216, 'mcp__<server>__<tool>', size=T_SMALL, fill=INK, mono=True, maxw=178)
    f.node(46, 250, 140, 74, 'Model', ['chooses a tool'], fill=BLUE_T, stroke=BLUE)
    f.path('M186,275 C214,275 204,226 232,226', arrow=True)
    f.path('M186,299 C214,299 204,348 232,348', arrow=True)
    f.text(46, 356, 'A human should always be', size=T_SMALL, fill=PLUM, maxw=176)
    f.text(46, 374, 'able to deny a tool call.', size=T_SMALL, fill=PLUM, maxw=176)
    for y in (226, 348):
        f.node(236, y - 27, 120, 54, 'MCP client', fill=TEAL_T, stroke=TEAL)

    # servers
    def server(y, tag):
        f.rect(668, y, 268, 92, fill=CARD, stroke=INK2, sw=1.5, rx=10)
        f.text(684, y + 28, 'MCP server', size=T_NODE, weight=600)
        f.text(920, y + 28, tag, size=T_SMALL, fill=INK3, anchor='end')
        x = 684
        for lab in ('tools', 'resources', 'prompts'):
            x += f.chip(x, y + 48, lab, FAINT, INK, weight=400, h=26) + 8

    server(180, 'local process')
    server(302, 'remote service')

    # transports
    for y in (226, 348):
        f.line(356, y, 668, y, stroke=INK2, sw=2.5)
        f.circle(356, y, 5.5, fill=TEAL, stroke=CARD, sw=1.5)
        f.circle(668, y, 5.5, fill=INK2, stroke=CARD, sw=1.5)
    f.add(f'<text x="512" y="212" font-family="{SANS}" font-size="13" fill="{INK2}" text-anchor="middle">'
          f'<tspan font-family="{MONO}" font-weight="700" fill="{INK}">stdio</tspan>'
          f'<tspan dx="6">for local servers</tspan></text>')
    f.text(512, 247, 'the client launches the server as a', size=T_SMALL, fill=INK2, anchor='middle', maxw=296)
    f.text(512, 264, 'subprocess; newline-delimited messages', size=T_SMALL, fill=INK2, anchor='middle', maxw=296)
    f.add(f'<text x="528" y="334" font-family="{SANS}" font-size="13" fill="{INK2}" text-anchor="middle">'
          f'<tspan font-weight="700" fill="{INK}">Streamable HTTP</tspan>'
          f'<tspan dx="6">for remote servers</tspan></text>')
    f.text(528, 369, 'each client message is an HTTP POST', size=T_SMALL, fill=INK2, anchor='middle', maxw=262)
    f.text(528, 386, 'to a single MCP endpoint', size=T_SMALL, fill=INK2, anchor='middle', maxw=262)

    # exchange
    py = 448
    f.rect(24, py, 912, 196, fill=CARD, stroke=RULE, sw=1.5, rx=12)
    f.text(44, py + 28, 'The same exchange on either transport', size=T_NODE, weight=600)
    f.text(916, py + 28, 'JSON-RPC, UTF-8', size=T_SMALL, fill=INK3, anchor='end')
    cx, sx = 200, 760
    for x, lab, fill, st in ((cx, 'MCP client', TEAL_T, TEAL), (sx, 'MCP server', PAPER, INK2)):
        f.line(x, py + 70, x, py + 184, stroke=RULE, sw=1.5, dash='4 4')
        f.chip(x, py + 44, lab, fill, INK, stroke=st, anchor='middle', h=26)
    steps = [
        (py + 92, True, '`tools/list` \u00b7 discover, paginated with `cursor` and `nextCursor`'),
        (py + 120, False, "the server's tools"),
        (py + 148, True, '`tools/call` { `name`, `arguments` } \u00b7 the tool the model chose'),
        (py + 176, False, 'result, with `isError: true` if the tool itself failed'),
    ]
    for y, fwd, lab in steps:
        if fwd:
            f.line(cx + 4, y, sx - 5, y, stroke=INK, sw=1.75, arrow=True)
        else:
            f.line(sx - 4, y, cx + 5, y, stroke=INK2, sw=1.75, dash='6 4', arrow=True)
        f.text((cx + sx) / 2, y - 7, lab, size=T_SMALL, fill=INK2, mfill=INK, anchor='middle', maxw=540)
    f.text(32, py + 222, 'Spec revision 2026-07-28 is stateless: no `initialize` handshake; every request '
           'carries its protocol version in `_meta`.', size=T_SMALL, fill=INK3, mfill=INK2, maxw=896)
    return f


# ---------------------------------------------------- 6. guardrail layers
def guardrail_layers():
    f = Fig('fig-guardrail-layers.svg', 960, 540, 'Guardrails in depth',
            'Five nested layers, outermost to innermost: human review and CI gates, hooks, sandbox, '
            'permission rules and modes, and instructions. The first four are enforced; '
            'instructions are advisory only.')
    f.header('Guardrails in depth',
             'Five layers between what the model intends and your main branch. Only the innermost is advisory.')
    layers = [
        ('Human review and CI gates',
         'Branch protection, a person who approves the merge, CI as the real gate.',
         'enforced outside the session', '#EAE4D6'),
        ('Hooks',
         'Your code on lifecycle events. A `PreToolUse` deny overrides every permission mode; only exit code 2 or a JSON deny blocks.',
         'enforced by your code', '#EFEADD'),
        ('Sandbox',
         'OS-level filesystem and network limits, for shell commands only. Off by default.',
         'enforced by the OS', '#F4F0E6'),
        ('Permission rules and modes',
         '`allow`, `ask` and `deny` rules; `deny` holds in every mode. Rules match text, not intent.',
         'enforced by the harness', '#F9F6EF'),
    ]
    x, y, w, strip, inset, pad = 24, 96, 912, 60, 24, 14
    inner_h = 78
    total_h = len(layers) * strip + inner_h + len(layers) * pad
    h = total_h
    for name, note, tag, fill in layers:
        f.rect(x, y, w, h, fill=fill, stroke=INK2, sw=1.5, rx=12)
        f.text(x + 18, y + 25, name, size=T_NODE, weight=600)
        f.chip(x + w - 14, y + 9, tag, TEAL, WHITE, anchor='end', h=24)
        f.text(x + 18, y + 46, note, size=T_SMALL, fill=INK2, mfill=INK, maxw=w - 36)
        x += inset; w -= 2 * inset; y += strip; h -= strip + pad
    f.rect(x, y, w, inner_h, fill=CARD, stroke=AMBER, sw=2, rx=12, dash='7 5')
    f.text(x + 18, y + 28, 'Instructions', size=T_NODE, weight=600)
    f.chip(x + w - 14, y + 11, 'advisory only', AMBER, WHITE, anchor='end', h=24)
    f.text(x + 18, y + 49, '`CLAUDE.md` and rules are context, not configuration. No guarantee of strict compliance.',
           size=T_SMALL, fill=INK2, mfill=INK, maxw=w - 36)
    f.text(x + 18, y + 66, 'To block an action regardless of what the model decides, move it one layer out.',
           size=T_SMALL, fill=INK2, maxw=w - 36)
    by = 96 + total_h
    # legend
    f.line(32, by + 30, 62, by + 30, stroke=INK2, sw=1.75)
    f.text(70, by + 34.5, 'enforced: holds whatever the model decides', size=T_SMALL, fill=INK2)
    f.line(384, by + 30, 414, by + 30, stroke=AMBER, sw=2, dash='7 5')
    f.text(422, by + 34.5, 'advisory: guidance the model may not follow', size=T_SMALL, fill=INK2)
    f.H = int(by + 56)
    return f


# ------------------------------------------------------ 7. maturity ladder
def maturity_ladder():
    f = Fig('fig-maturity-ladder.svg', 960, 610, 'From zero to hero: six levels',
            'A six-rung ladder: 0 autocomplete and chat, 1 single interactive agent session, '
            '2 project memory and permissions, 3 extended harness, 4 parallel and multi-agent '
            'work, 5 agents in the pipeline. Each rung notes what changes for the developer.')
    f.header('From zero to hero: six levels of AI-native development',
             'Each level keeps everything below it. What changes is where your attention goes.')
    levels = [
        ('Agents in the pipeline', 'headless, CI, gates, observability',
         'Agents run unattended. You design the gates and watch the signals.'),
        ('Parallel and multi-agent work', 'worktrees, orchestration, workflows',
         'Several agents work at once. You write briefs and review results.'),
        ('Extended harness', 'MCP, skills, hooks, subagents',
         'The agent gains tools and guardrails you built. Rules become code.'),
        ('Project memory and permissions', '`CLAUDE.md`, settings',
         'The repo carries your conventions and limits. You stop repeating yourself.'),
        ('Single interactive agent session', '',
         'The agent reads, edits and runs commands. You steer and approve.'),
        ('Autocomplete and chat', '',
         'You write the code. The model suggests and explains.'),
    ]
    top, ch, gap = 100, 70, 10
    rx1, rx2 = 52, 112
    bottom = top + 6 * ch + 5 * gap
    for xr in (rx1, rx2):
        f.line(xr, top - 2, xr, bottom + 2, stroke=INK2, sw=4)
    for i, (title, tags, change) in enumerate(levels):
        lvl = 5 - i
        y = top + i * (ch + gap)
        mid = y + ch / 2
        f.line(rx1, mid, rx2, mid, stroke=INK2, sw=4)
        f.line(rx2 + 4, mid, 150, mid, stroke=RULE, sw=1.5, dash='3 4')
        f.circle((rx1 + rx2) / 2, mid, 18, fill=RAMP[lvl], stroke=PAPER, sw=3)
        f.text((rx1 + rx2) / 2, mid + 5.5, str(lvl), size=16, weight=700, anchor='middle',
               fill=WHITE if lvl >= 4 else INK)
        f.rect(150, y, 786, ch, fill=CARD, stroke=FAINT, sw=1.5, rx=10)
        f.rect(150, y, 8, ch, fill=RAMP[lvl], rx=4)
        w = f.text(176, y + 29, title, size=15.5, weight=600)
        if tags:
            f.text(176 + w + 14, y + 29, tags, size=T_SMALL, fill=INK3, mfill=INK3, maxw=730 - w)
        f.text(176, y + 52, change, size=T_BODY, fill=INK2, maxw=740)
    f.H = int(bottom + 30)
    return f


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    warns = []
    for fn in (cover, context_window, agent_loop, extension_map, mcp_architecture, guardrail_layers,
               maturity_ladder):
        fig = fn()
        warns += fig.save(out)
        print(f'wrote {out}{fig.name}  {fig.W}x{fig.H}')
    print('\n'.join(['WARN ' + w for w in warns]) or 'no width warnings')
