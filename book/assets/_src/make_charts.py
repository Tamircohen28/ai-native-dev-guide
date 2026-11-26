#!/usr/bin/env python3
"""Build the ten field-data charts for the book as static, standalone SVG files.

Usage:
    python3 assets/_src/make_charts.py --data /path/to/05-sessions-quant.json [--out assets]

Standard library only. Every plotted number is read from the JSON aggregate
(05-sessions-quant.json). The single exception is chart-friction.svg: its numbers
come from the FRICTION table below, copied from 06-sessions-friction.md section 1
with the source line of each row. Display names (labels) are mapped by JSON key.

Design system (one light card that reads on light and dark pages):
  surface #ffffff, primary ink #191919, secondary ink #666666, hairlines #e7e7e7 / #c2c2c2
  categorical hues in fixed order: blue, orange, aqua, yellow; "other" in grey
  one-hue ordinal ramp (blue 600 / 400 / 250) for ranked tiers
  bars 16px thick, 4px rounded data-end, square at the baseline, 2px surface gap between fills
  every value is directly labelled (a static image has no hover and no table view)
"""
import argparse
import html
import json
import math
import os
import sys

# --------------------------------------------------------------------------- #
# Chart 10 source table. Copied from 06-sessions-friction.md, section 1.
# Columns: category (section heading), sessions affected (of the 37 substantive
# sessions), what was counted, source line of the "Frequency" bullet.
# Categories 13, 14, 16, 17 and 18 give no per-session count and are left out.
# --------------------------------------------------------------------------- #
FRICTION_SUBSTANTIVE_SESSIONS = 37  # line 7: "96 exist; 37 are substantive"
FRICTION = [
    # (category, sessions, what was counted, source line)
    ("Silent waits and the “status?” poke", 22, "218 status pokes", 19),
    ("Sessions that take hours", 10, "slow / too-long complaints (about 10 sessions)", 26),
    ("“Done” without evidence", 20, "60 agent self-corrections", 33),
    ("Approval friction", 17, "blanket approval re-typed 33 times", 40),
    ("Guards that block or nag legitimate work", 26, "199 hook blocks, plus 452 in subagents", 47),
    ("Shell traps: zsh, macOS, quoting", 19, "36 errors, plus 112 in subagents", 54),
    ("Scripted edits that silently corrupt", 9, "18 inline-script edits denied by the safety check", 61),
    ("Subagents that stall, die or return nothing", 16, "52 runs ended blocked or partial", 68),
    ("Parallel agents and sessions colliding", 5, "duplicate PRs or watchers mentioned", 75),
    ("Context bloat, compaction, lost instructions", 22, "86 compactions", 82),
    ("Usage and rate limits", 5, "limit messages (about 5 sessions)", 89),
    ("CI capacity: is it the code or the host?", 16, "flaky-test or runner discussion", 96),
    ("Bouncing manual work back to the owner", 14, "“do it yourself” prompts (about 14 sessions)", 116),
]
FRICTION_NOT_PLOTTED = 5  # categories 13, 14, 16, 17, 18 (lines 103, 109, 123, 130, 136)

# --------------------------------------------------------------------------- #
# Design tokens
# --------------------------------------------------------------------------- #
W = 860
PAD = 28
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
SURFACE = "#ffffff"
INK = "#191919"
INK2 = "#666666"
GRID = "#e7e7e7"
AXIS = "#c2c2c2"
BLUE = "#257de0"      # categorical slot 1
ORANGE = "#f47230"    # categorical slot 2
AQUA = "#00b894"      # categorical slot 3
YELLOW = "#f2a600"    # categorical slot 4
OTHER = "#c2c2c2"     # de-emphasis / "other"
RAMP = ["#1757ac", "#338ced", "#84b9f3"]  # ordinal: blue 600 / 400 / 250
ON_FILL = {BLUE: "#ffffff", ORANGE: "#ffffff", AQUA: "#ffffff", YELLOW: "#0b0b0b",
           RAMP[0]: "#ffffff", RAMP[1]: "#ffffff", RAMP[2]: "#0b0b0b"}
FOOTER = "Field data: one developer, ~4 weeks of Claude Code transcripts, Nov 2026"

# --------------------------------------------------------------------------- #
# Text metrics (approximate advance widths, per 1000 units of font size)
# --------------------------------------------------------------------------- #
_ADV = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191, "(": 333,
    ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278, ":": 278, ";": 278,
    "<": 584, "=": 584, ">": 584, "?": 556, "@": 1015, "[": 278, "\\": 278, "]": 278, "_": 556,
    "{": 334, "|": 260, "}": 334, "~": 584,
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722, "I": 278,
    "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778, "P": 667, "Q": 778, "R": 722,
    "S": 667, "T": 611, "U": 722, "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 300, "g": 556, "h": 556, "i": 240,
    "j": 240, "k": 500, "l": 240, "m": 833, "n": 556, "o": 556, "p": 556, "q": 556, "r": 350,
    "s": 500, "t": 300, "u": 556, "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "–": 556, "—": 1000, "·": 278, "×": 584, "÷": 584, "≈": 584, "±": 584, "≥": 584, "≤": 584,
    "…": 1000, "“": 360, "”": 360, "‘": 240, "’": 240, "→": 1000,
}


def tw(s, size, bold=False):
    """Estimated rendered width of a string, slightly generous on purpose."""
    units = 0
    for ch in s:
        units += 610 if ch.isdigit() else _ADV.get(ch, 600)
    return units / 1000.0 * size * (1.09 if bold else 1.04)


def wrap(s, size, max_w, bold=False):
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if cur and tw(trial, size, bold) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------- #
# Number formatting
# --------------------------------------------------------------------------- #
def n0(v):
    return f"{int(round(v)):,}"


def compact(v):
    v = float(v)
    if v >= 1e9:
        return f"{v / 1e9:.2f}B"
    if v >= 1e6:
        return f"{v / 1e6:.1f}M"
    if v >= 1e3:
        return f"{v / 1e3:.0f}K"
    return f"{v:.0f}"


def pct(v, digits=1):
    """Percentage with enough decimals to stay non-zero for tiny shares."""
    if 0 < v < 0.005:
        return f"{v:.3f}%"
    if 0 < v < 0.1:
        return f"{v:.2f}%"
    return f"{v:.{digits}f}%"


def f1(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# --------------------------------------------------------------------------- #
# SVG canvas
# --------------------------------------------------------------------------- #
class Canvas:
    def __init__(self):
        self.el = []

    def add(self, s):
        self.el.append(s)

    def text(self, x, y, s, size=13, fill=INK, weight=None, anchor=None, tab=False):
        a = [f'x="{f1(x)}"', f'y="{f1(y)}"', f'font-size="{size}"', f'fill="{fill}"']
        if weight:
            a.append(f'font-weight="{weight}"')
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if tab:
            a.append('style="font-variant-numeric: tabular-nums"')
        self.add(f"<text {' '.join(a)}>{html.escape(str(s))}</text>")

    def spans(self, x, y, parts, size=13, anchor=None, halo=False):
        """parts: list of (text, fill, weight, dx). halo: surface-coloured knock-out behind the glyphs."""
        a = [f'x="{f1(x)}"', f'y="{f1(y)}"', f'font-size="{size}"']
        if halo:
            a.append(f'stroke="{SURFACE}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"')
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        inner = ""
        for s, fill, weight, dx in parts:
            t = [f'fill="{fill}"']
            if weight:
                t.append(f'font-weight="{weight}"')
            if dx:
                t.append(f'dx="{dx}"')
            inner += f"<tspan {' '.join(t)}>{html.escape(str(s))}</tspan>"
        self.add(f"<text {' '.join(a)}>{inner}</text>")

    def rect(self, x, y, w, h, fill, rx=0, opacity=None):
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        r = f' rx="{f1(rx)}"' if rx else ""
        self.add(f'<rect x="{f1(x)}" y="{f1(y)}" width="{f1(w)}" height="{f1(h)}"{r} fill="{fill}"{o}/>')

    def line(self, x1, y1, x2, y2, stroke=GRID, width=1):
        self.add(f'<line x1="{f1(x1)}" y1="{f1(y1)}" x2="{f1(x2)}" y2="{f1(y2)}" '
                 f'stroke="{stroke}" stroke-width="{width}"/>')

    def bar(self, x, y, w, h, fill, r=4):
        """Horizontal bar: square at the baseline, rounded at the data end."""
        if w < 2 * r:
            self.rect(x, y, w, h, fill)
            return
        self.add(f'<path d="M{f1(x)},{f1(y)}h{f1(w - r)}a{r},{r} 0 0 1 {r},{r}v{f1(h - 2 * r)}'
                 f'a{r},{r} 0 0 1 -{r},{r}h-{f1(w - r)}z" fill="{fill}"/>')


def begin(title, subtitle):
    """Title and subtitle; returns (canvas, y of the first content pixel)."""
    cv = Canvas()
    y = 44
    for ln in wrap(title, 20, W - 2 * PAD, bold=True):
        cv.text(PAD, y, ln, size=20, weight=600)
        y += 26
    y -= 3
    for ln in wrap(subtitle, 13, W - 2 * PAD):
        cv.text(PAD, y, ln, size=13, fill=INK2)
        y += 18
    return cv, y + 8


def legend(cv, y, items, x=PAD):
    """One row of swatch + name pairs. Returns the y below the row."""
    for color, label in items:
        cv.rect(x, y - 10, 11, 11, color, rx=2.5)
        cv.text(x + 17, y, label, size=12.5, fill=INK)
        x += 17 + tw(label, 12.5) + 24
    return y + 22


def finish(cv, name, bottom, title, desc, out_dir):
    height = int(math.ceil(bottom + 56))
    cv.line(PAD, height - 36, W - PAD, height - 36, stroke=GRID)
    cv.text(PAD, height - 15, FOOTER, size=11.5, fill=INK2)
    doc = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" aria-labelledby="t d" font-family="{FONT}">',
        f'<title id="t">{html.escape(title)}</title>',
        f'<desc id="d">{html.escape(desc)}</desc>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="10" fill="{SURFACE}" '
        f'stroke="#0b0b0b" stroke-opacity="0.12"/>',
    ]
    doc += cv.el
    doc.append("</svg>")
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(doc) + "\n")
    return path, height


# --------------------------------------------------------------------------- #
# Ranked horizontal bars (shared by seven charts)
# --------------------------------------------------------------------------- #
def hbars(cv, y, rows, vmax=None, pitch=30, bar_h=16, cap_w=520, min_x0=0, refs=None):
    """rows: dicts with label, value, color, v1 (bold), v2 (secondary, optional),
    sub (second label line, optional). Bars share one baseline; every row is labelled.
    refs: optional list of (value, text) reference lines. Returns (bottom y, x0, scale)."""
    vmax = vmax or max(r["value"] for r in rows)
    label_w = 0
    for r in rows:
        label_w = max(label_w, tw(r["label"], 13), tw(r.get("sub", ""), 11.5))
    x0 = max(PAD + label_w + 12, min_x0)
    avail = W - PAD - x0

    def vlabel_w(r):
        w = tw(r["v1"], 13, bold=True)
        if r.get("v2"):
            w += 7 + tw(r["v2"], 12.5)
        return w * 1.12 + 10

    max_w = cap_w
    for r in rows:
        if r["value"] > 0:
            max_w = min(max_w, (avail - vlabel_w(r)) / (r["value"] / vmax))
    scale = max_w / vmax
    top = y
    if refs:
        y += 18
    bottom = y + len(rows) * pitch
    if refs:
        for value, text in refs:
            gx = x0 + value * scale
            cv.line(gx, y - 4, gx, bottom, stroke=GRID)
            cv.text(gx, top + 8, text, size=11.5, fill=INK2, anchor="middle")
    for i, r in enumerate(rows):
        cy = y + i * pitch + pitch / 2.0
        w = r["value"] * scale
        if r["value"] > 0:
            w = max(w, 2)
        cv.bar(x0, cy - bar_h / 2.0, w, bar_h, r["color"])
        if r.get("sub"):
            cv.text(x0 - 12, cy - 2, r["label"], size=13, anchor="end")
            cv.text(x0 - 12, cy + 13, r["sub"], size=11.5, fill=INK2, anchor="end")
        else:
            cv.text(x0 - 12, cy + 4.5, r["label"], size=13, anchor="end")
        parts = [(r["v1"], INK, 600, 0)]
        if r.get("v2"):
            parts.append((r["v2"], INK2, None, 7))
        cv.spans(x0 + w + 8, cy + 4.5, parts, size=13, halo=bool(refs))
    cv.line(x0, y - 4, x0, bottom + 4, stroke=AXIS)
    return bottom + 4, x0, scale


def describe(rows):
    return "; ".join(f"{r['label']}: {r['v1']}" + (f" ({r['v2']})" if r.get("v2") else "") for r in rows)


# --------------------------------------------------------------------------- #
# 1. Leverage: unit chart, one square = one event per human prompt
# --------------------------------------------------------------------------- #
def chart_leverage(d, out):
    s = d["scale"]
    prompts, resp, tools = s["human_prompts_total"], s["assistant_responses_total"], s["tool_calls_total"]
    rpp, tpp = s["responses_per_human_prompt"], s["tool_calls_per_human_prompt"]
    resp_sub = 100.0 * s["assistant_responses_subagents"] / resp
    tool_sub = 100.0 * s["tool_calls_sub"] / tools
    title = f"One human prompt sets off about {rpp:.0f} model responses and {tpp:.0f} tool calls"
    subtitle = (f"Averages per human prompt: {n0(resp)} assistant responses (one per API call) and "
                f"{n0(tools)} tool calls, main thread and subagents combined, divided by "
                f"{n0(prompts)} human prompts. One square = one event.")
    cv, y = begin(title, subtitle)
    y = legend(cv, y + 12, [(ORANGE, "Typed by the human"), (BLUE, "Produced by the agent")])
    blocks = [
        ("1", "human prompt", f"{n0(prompts)} in total", 1.0, ORANGE),
        (f"{rpp:.1f}", "assistant responses", f"{n0(resp)} in total, {resp_sub:.0f}% from subagents", rpp, BLUE),
        (f"{tpp:.1f}", "tool calls", f"{n0(tools)} in total, {tool_sub:.0f}% from subagents", tpp, BLUE),
    ]
    cell, gap, per_row, group_gap = 15, 3, 30, 9
    gx0 = 268
    y += 10
    for big, name, detail, units, color in blocks:
        full = int(units)
        frac = units - full
        cells = full + (1 if frac > 0.02 else 0)
        n_rows = int(math.ceil(cells / float(per_row)))
        grid_h = n_rows * (cell + gap) - gap
        block_h = max(66, grid_h)
        ty = y + (block_h - 66) / 2.0
        cv.text(PAD, ty + 27, big, size=30, weight=600)
        cv.text(PAD, ty + 47, name, size=13.5, weight=600)
        cv.text(PAD, ty + 64, detail, size=12, fill=INK2)
        gy0 = y + (block_h - grid_h) / 2.0
        for k in range(cells):
            row, col = divmod(k, per_row)
            x = gx0 + col * (cell + gap) + (col // 10) * group_gap
            w = cell if k < full else max(cell * frac, 2)
            cv.rect(x, gy0 + row * (cell + gap), w, cell, color, rx=min(2.5, w / 2.0))
        y += block_h + 26
    desc = (f"{n0(prompts)} human prompts, {n0(resp)} assistant responses ({rpp} per prompt), "
            f"{n0(tools)} tool calls ({tpp} per prompt).")
    return finish(cv, "chart-leverage.svg", y - 22, title, desc, out)


# --------------------------------------------------------------------------- #
# 2. Tool calls by tool group
# --------------------------------------------------------------------------- #
TOOL_GROUP_LABEL = {
    "Bash": "Bash (shell commands)",
    "Read": "Read",
    "Edit": "Edit",
    "Write": "Write",
    "Grep+Glob": "Grep + Glob",
    "Agent (subagent launch)": "Agent (subagent launch)",
    "Skill": "Skill",
    "WebSearch+WebFetch": "WebSearch + WebFetch",
    "MCP (all servers)": "MCP tools (all servers)",
    "Other built-ins": "Other built-in tools",
}


def tool_group_label(key):
    if key in TOOL_GROUP_LABEL:
        return TOOL_GROUP_LABEL[key]
    if key.startswith("Agent coordination"):
        return "Agent coordination (messages, monitors)"
    if key.startswith("Unavailable tool names"):
        return "Unavailable tool names, called anyway"
    return key


def chart_tool_share(d, out):
    groups = d["tool_groups"]
    total = d["tool_totals"]["calls"]
    items = sorted(groups.items(), key=lambda kv: -kv[1]["calls"])
    tail = [kv for kv in items if kv[0].startswith("Other")]
    items = [kv for kv in items if not kv[0].startswith("Other")] + tail
    rows = [{"label": tool_group_label(k), "value": v["calls"],
             "color": OTHER if k.startswith("Other") else BLUE,
             "v1": n0(v["calls"]), "v2": pct(100.0 * v["calls"] / total)} for k, v in items]
    bash = 100.0 * groups["Bash"]["calls"] / total
    title = f"{bash:.0f}% of all tool calls are shell commands"
    subtitle = (f"Tool calls by tool group, main thread and subagents combined (n = {n0(total)}; "
                f"one tool call = one tool_use block). Number, then share of all calls.")
    cv, y = begin(title, subtitle)
    bottom, _, _ = hbars(cv, y + 8, rows)
    return finish(cv, "chart-tool-share.svg", bottom, title, describe(rows), out)


# --------------------------------------------------------------------------- #
# 3. Token mix: the whole, then the non-cache-read remainder enlarged
# --------------------------------------------------------------------------- #
def segbar(cv, x, y, w, h, parts, total, inside=None):
    """Tall segmented bar. parts: (value, color). Returns [(x_start, x_end)] per part
    (None where the part is too thin to draw). 2px surface gap between blocks."""
    edges, acc = [], 0.0
    for value, _ in parts:
        a = x + w * acc / total
        acc += value
        edges.append((a, x + w * acc / total))
    drawn = [i for i, (a, b) in enumerate(edges) if b - a >= 0.5]
    out = [None] * len(parts)
    for j, i in enumerate(drawn):
        a, b = edges[i]
        if j > 0:
            a += 1
        if j < len(drawn) - 1:
            b -= 1
        else:
            b = x + w
        bw = max(b - a, 0.8)
        cv.rect(a, y, bw, h, parts[i][1], rx=min(4, bw / 2.0))
        out[i] = (a, a + bw)
        if inside and inside[i]:
            if tw(inside[i], 13, bold=True) + 20 <= bw:
                cv.text(a + 10, y + h / 2.0 + 4.6, inside[i], size=13, weight=600, fill=ON_FILL[parts[i][1]])
    return out


def chart_token_mix(d, out):
    t = d["tokens"]["total"]
    total = t["total"]
    classes = [
        ("Cache read", t["cache_read"], BLUE, "input tokens served from the prompt cache"),
        ("Cache write", t["cache_creation"], ORANGE, "input tokens newly written to the cache"),
        ("Output", t["output"], AQUA, "tokens the model generated"),
        ("Uncached input", t["input"], YELLOW, "input tokens that bypassed the cache"),
    ]
    assert sum(c[1] for c in classes) == total, "token classes do not add up to the total"
    read_share = 100.0 * t["cache_read"] / total
    fresh = total - t["cache_read"]
    fresh_share = 100.0 * fresh / total
    title = f"{read_share:.0f}% of all tokens are cache reads: context re-read, not new text"
    subtitle = (f"All {compact(total)} tokens logged for {n0(t['responses'])} model responses, by token class "
                f"(subagents included). Cache-hit ratio = cache read ÷ (cache read + cache write + "
                f"uncached input) = {t['cache_hit_ratio_pct']:.1f}%.")
    cv, y = begin(title, subtitle)
    bw = W - 2 * PAD
    y += 22
    cv.text(PAD, y, f"All tokens: {compact(total)}", size=12.5, weight=600)
    y += 10
    spans = segbar(cv, PAD, y, bw, 28, [(c[1], c[2]) for c in classes], total,
                   inside=[f"{read_share:.1f}% of all tokens", None, None, None])
    tail_x = spans[1][0]
    zoom_y = y + 28 + 58
    # zoom fan from the tail of the top bar to the full width of the lower bar
    cv.add(f'<path d="M{f1(tail_x)},{f1(y + 30)}L{W - PAD},{f1(y + 30)}L{W - PAD},{f1(zoom_y - 2)}'
           f'L{PAD},{f1(zoom_y - 2)}z" fill="#f4f4f4"/>')
    cv.line(tail_x, y + 30, PAD, zoom_y - 2, stroke=AXIS)
    cv.line(W - PAD, y + 30, W - PAD, zoom_y - 2, stroke=AXIS)
    cv.text(W - PAD - 10, zoom_y - 12,
            f"The other {fresh_share:.1f}%, enlarged: {compact(fresh)} tokens that were not cache reads",
            size=12.5, weight=600, anchor="end")
    fresh_parts = classes[1:]
    segbar(cv, PAD, zoom_y, bw, 28, [(c[1], c[2]) for c in fresh_parts], fresh,
           inside=[f"{100.0 * c[1] / fresh:.1f}% of the remainder" if i == 0 else f"{100.0 * c[1] / fresh:.1f}%"
                   for i, c in enumerate(fresh_parts)])
    y = zoom_y + 28 + 34
    # legend as a list: name, meaning, tokens, share of all tokens
    c_tok, c_share = 690, W - PAD
    cv.text(PAD, y, "Token class", size=11.5, fill=INK2)
    cv.text(c_tok, y, "Tokens", size=11.5, fill=INK2, anchor="end")
    cv.text(c_share, y, "Share of all tokens", size=11.5, fill=INK2, anchor="end")
    cv.line(PAD, y + 8, W - PAD, y + 8, stroke=GRID)
    y += 28
    smallest = min(classes, key=lambda c: c[1])
    for name, value, color, meaning in classes:
        note = meaning
        if name == smallest[0]:
            note += f" (1 token in {n0(total / float(value))}; too thin to draw)"
        cv.rect(PAD, y - 10.5, 12, 12, color, rx=2.5)
        cv.text(PAD + 20, y, name, size=13, weight=600)
        cv.text(PAD + 130, y, note, size=12.5, fill=INK2)
        cv.text(c_tok, y, compact(value), size=13, weight=600, anchor="end", tab=True)
        cv.text(c_share, y, pct(100.0 * value / total, 2), size=13, anchor="end", tab=True)
        y += 25
    desc = "; ".join(f"{c[0]}: {n0(c[1])} tokens ({pct(100.0 * c[1] / total, 2)})" for c in classes)
    return finish(cv, "chart-token-mix.svg", y - 14, title, desc, out)


# --------------------------------------------------------------------------- #
# 4. Session concentration: share of sessions vs share of tokens
# --------------------------------------------------------------------------- #
TOP_A, TOP_B = 5, 10  # the two cut-offs the JSON reports (top5_..., top10_...)


def chart_session_concentration(d, out):
    tk = d["tokens"]
    n = tk["per_session_total_tokens"]["n"]
    total = tk["total"]["total"]
    top_a = tk[f"top{TOP_A}_sessions_share_of_tokens_pct"]
    top_b = tk[f"top{TOP_B}_sessions_share_of_tokens_pct"]
    automated = d["scale"]["sessions_automated_tmp_or_sdk"]
    counts = [TOP_A, TOP_B - TOP_A, n - TOP_B]
    shares = [top_a, top_b - top_a, 100.0 - top_b]
    names = [f"{TOP_A} largest sessions", f"Next {TOP_B - TOP_A}", f"Remaining {n - TOP_B} sessions"]
    title = f"The {TOP_A} largest sessions used {top_a:.0f}% of all tokens; the {TOP_B} largest used {top_b:.0f}%"
    subtitle = (f"Share of {compact(total)} tokens (all classes; each session counted with its subagents) by "
                f"session size rank, among the {n} sessions with at least one model response. "
                f"{automated} of the {n} are short automated runs.")
    cv, y = begin(title, subtitle)
    y = legend(cv, y + 12, list(zip(RAMP, names)))
    x0, bw, bh, gap_y = 136, W - PAD - 136, 28, 62
    y1 = y + 8
    y2 = y1 + bh + gap_y

    def edges(values, whole):
        res, acc = [], 0.0
        for v in values:
            a = x0 + bw * acc / whole
            acc += v
            res.append((a, x0 + bw * acc / whole))
        return res

    e1, e2 = edges(counts, float(n)), edges(shares, 100.0)
    for i in range(3):
        cv.add(f'<path d="M{f1(e1[i][0] + (1 if i else 0))},{f1(y1 + bh + 2)}'
               f'L{f1(e1[i][1] - (1 if i < 2 else 0))},{f1(y1 + bh + 2)}'
               f'L{f1(e2[i][1] - (1 if i < 2 else 0))},{f1(y2 - 2)}'
               f'L{f1(e2[i][0] + (1 if i else 0))},{f1(y2 - 2)}z" fill="{RAMP[i]}" fill-opacity="0.13"/>')
    for row_y, es, labels in ((y1, e1, [str(counts[0]), str(counts[1]), f"{counts[2]} sessions"]),
                              (y2, e2, [f"{v:.1f}%" for v in shares])):
        for i, (a, b) in enumerate(es):
            a2 = a + (1 if i else 0)
            b2 = b - (1 if i < 2 else 0)
            cv.rect(a2, row_y, b2 - a2, bh, RAMP[i], rx=4)
            if tw(labels[i], 13, bold=True) + 16 <= b2 - a2:
                cv.text(a2 + 9 if b2 - a2 > 70 else (a2 + b2) / 2.0, row_y + bh / 2.0 + 4.6, labels[i],
                        size=13, weight=600, fill=ON_FILL[RAMP[i]],
                        anchor=None if b2 - a2 > 70 else "middle")
    cv.text(PAD, y1 + 13, "Sessions", size=13, weight=600)
    cv.text(PAD, y1 + 29, n0(n), size=12, fill=INK2)
    cv.text(PAD, y2 + 13, "Tokens", size=13, weight=600)
    cv.text(PAD, y2 + 29, compact(total), size=12, fill=INK2)
    # bracket under the first two token blocks: the top-10 share
    bx1, bx2, by = e2[0][0], e2[1][1] - 1, y2 + bh + 9
    cv.add(f'<path d="M{f1(bx1)},{f1(by)}v6H{f1(bx2)}v-6" fill="none" stroke="{INK2}" stroke-width="1"/>')
    cv.text((bx1 + bx2) / 2.0, by + 24,
            f"{TOP_B} largest sessions = {top_b:.1f}% of all tokens",
            size=12.5, weight=600, anchor="middle")
    desc = "; ".join(f"{names[i]}: {counts[i]} of {n} sessions, {shares[i]:.1f}% of tokens" for i in range(3))
    return finish(cv, "chart-session-concentration.svg", by + 30, title, desc, out)


# --------------------------------------------------------------------------- #
# 5. Who writes to the main thread
# --------------------------------------------------------------------------- #
INBOUND_LABEL = {
    "task_notification": "Background-task notifications",
    "peer_session_message": "Messages from other agent sessions",
    "human_prompt": "Human prompts",
    "harness_and_meta": "Harness and meta text",
    "slash_command": "Slash commands",
    "skill_body": "Skill instructions loaded",
    "compact_summary": "Compaction summaries",
    "bang_shell_input": "Shell lines typed with !",
    "sdk_prompt": "Headless (SDK) prompts",
    "interrupt_marker": "Interrupt markers",
    "scheduled_task_prompt": "Scheduled-task prompts",
}
INBOUND_HUMAN = {"human_prompt", "slash_command", "bang_shell_input"}
INBOUND_MERGE = {"meta_other": "harness_and_meta", "harness_meta": "harness_and_meta"}


def chart_inbound(d, out):
    raw = d["scale"]["inbound_main_thread_messages"]
    merged = {}
    for k, v in raw.items():
        k2 = INBOUND_MERGE.get(k, k)
        merged[k2] = merged.get(k2, 0) + v
    total = sum(raw.values())
    items = sorted(merged.items(), key=lambda kv: -kv[1])
    rows = [{"label": INBOUND_LABEL.get(k, k), "value": v,
             "color": ORANGE if k in INBOUND_HUMAN else BLUE,
             "v1": n0(v), "v2": pct(100.0 * v / total)} for k, v in items]
    human = 100.0 * raw["human_prompt"] / total
    typed = 100.0 * sum(raw[k] for k in INBOUND_HUMAN) / total
    title = f"Only {human:.0f}% of the messages reaching the main thread are human prompts"
    subtitle = (f"Text-bearing user-role events delivered to the main thread, by origin (n = {n0(total)}). "
                f"Counting slash commands and ! shell lines, the human typed {typed:.0f}%; agents, "
                f"background tasks and the harness wrote the rest.")
    cv, y = begin(title, subtitle)
    y = legend(cv, y + 12, [(ORANGE, "Typed by the human"), (BLUE, "Written by agents, background tasks or the harness")])
    bottom, _, _ = hbars(cv, y + 2, rows)
    return finish(cv, "chart-inbound-messages.svg", bottom, title, describe(rows), out)


# --------------------------------------------------------------------------- #
# 6. Subagent launches by type
# --------------------------------------------------------------------------- #
def chart_subagent_types(d, out, top_n=10):
    sa = d["subagents"]
    total = sa["agent_tool_calls"]
    merged = {}
    for name, count in sa["agent_tool_calls_by_type"]:
        role = name.split(":")[-1]          # drop the plugin namespace prefix
        if role == "(unspecified)":
            role = "(no type given)"
        merged[role] = merged.get(role, 0) + count
    assert sum(merged.values()) == total, "subagent types do not add up to the total"
    items = sorted(merged.items(), key=lambda kv: -kv[1])
    top, rest = items[:top_n], items[top_n:]
    rows = [{"label": k, "value": v, "color": BLUE, "v1": n0(v), "v2": pct(100.0 * v / total)} for k, v in top]
    other = sum(v for _, v in rest)
    rows.append({"label": f"Other ({len(rest)} types)", "value": other, "color": OTHER,
                 "v1": n0(other), "v2": pct(100.0 * other / total)})
    lead = 100.0 * (top[0][1] + top[1][1]) / total
    title = f"Two agent types take {lead:.0f}% of all subagent launches"
    subtitle = (f"Agent-tool calls by subagent type (n = {n0(total)}). Plugin namespace prefixes are dropped "
                f"and same-named roles merged, giving {len(items)} types; the {top_n} most used are shown.")
    cv, y = begin(title, subtitle)
    bottom, _, _ = hbars(cv, y + 8, rows)
    return finish(cv, "chart-subagent-types.svg", bottom, title, describe(rows), out)


# --------------------------------------------------------------------------- #
# 7. Hook executions by event, and how rarely a hook blocks
# --------------------------------------------------------------------------- #
HOOK_LABEL = {
    "PreToolUse": "PreToolUse (before a tool call)",
    "PostToolUse": "PostToolUse (after a tool call)",
    "Stop": "Stop (turn ends)",
    "SubagentStop": "SubagentStop (subagent ends)",
    "SessionStart": "SessionStart",
    "TeammateIdle": "TeammateIdle",
    "UserPromptSubmit": "UserPromptSubmit (prompt sent)",
}


def chart_hooks(d, out):
    fr = d["friction"]
    events = fr["hook_executions_by_event"]
    total = fr["hook_executions_logged"]
    blocks = fr["hook_blocked_tool_calls"]
    calls = d["tool_totals"]["calls"]
    one_in = int(round(calls / float(blocks)))
    rows = [{"label": HOOK_LABEL.get(k, k), "value": v, "color": BLUE,
             "v1": n0(v), "v2": pct(100.0 * v / total)}
            for k, v in sorted(events.items(), key=lambda kv: -kv[1])]
    title = f"Hooks ran {total / 1000.0:.0f}K times and blocked {n0(blocks)} tool calls"
    subtitle = (f"Successful hook executions logged, by hook event (n = {n0(total)}). PreToolUse hooks ran "
                f"{fr['hook_executions_per_tool_call']} times per tool call. Blocks = tool calls rejected by "
                f"a hook; that count is a lower bound.")
    cv, y = begin(title, subtitle)
    bottom, _, _ = hbars(cv, y + 8, rows)
    y = bottom + 22
    cv.line(PAD, y, W - PAD, y, stroke=GRID)
    y += 20
    # call-out: the blocked calls, with a unit grid for scale
    cv.text(PAD, y + 30, n0(blocks), size=30, weight=600)
    cv.text(PAD, y + 50, "tool calls blocked by a hook", size=13.5, weight=600)
    cv.text(PAD, y + 67, f"{fr['hook_blocked_rate_pct_of_tool_calls']}% of {n0(calls)} tool calls", size=12, fill=INK2)
    gx0, cols, pitch_d, r = 292, 46, 11.6, 3.6
    n_rows = int(math.ceil(one_in / float(cols)))
    cv.rect(gx0, y - 2, 11, 11, ORANGE, rx=5.5)
    cv.text(gx0 + 17, y + 8, "1 blocked by a hook", size=12.5)
    lx = gx0 + 17 + tw("1 blocked by a hook", 12.5) + 24
    cv.rect(lx, y - 2, 11, 11, OTHER, rx=5.5)
    cv.text(lx + 17, y + 8, f"{n0(one_in - 1)} not blocked, out of every {n0(one_in)} tool calls", size=12.5)
    gy0 = y + 26
    for k in range(one_in):
        row, col = divmod(k, cols)
        cv.add(f'<circle cx="{f1(gx0 + r + col * pitch_d)}" cy="{f1(gy0 + r + row * pitch_d)}" r="{r}" '
               f'fill="{ORANGE if k == 0 else OTHER}"/>')
    grid_bottom = gy0 + n_rows * pitch_d
    desc = describe(rows) + f"; tool calls blocked by a hook: {n0(blocks)} of {n0(calls)}"
    return finish(cv, "chart-hooks.svg", max(grid_bottom, y + 70), title, desc, out)


# --------------------------------------------------------------------------- #
# 8. Bash error classes
# --------------------------------------------------------------------------- #
BASH_ERR = {  # key: (display name, kind)
    "exit-other": ("Other non-zero exit", "fail"),
    "hook-block": ("Blocked by a PreToolUse hook", "guard"),
    "exit-unrecognised": ("Non-zero exit, no error line in the output", "fail"),
    "harness-block": ("Refused by the harness (sleep-poll, safety check)", "guard"),
    "exit-zsh-equals": ("zsh: unquoted word starting with =", "shell"),
    "exit-sed": ("sed syntax error (BSD sed)", "shell"),
    "exit-zsh-glob": ("zsh: no matches found (unquoted glob)", "shell"),
    "exit-no-such-file": ("No such file or directory", "fail"),
    "exit-test-or-check-failed": ("Tests or checks reported failures", "fail"),
    "exit-python": ("Python traceback", "fail"),
}
KIND_COLOR = {"fail": BLUE, "guard": ORANGE, "shell": AQUA}


def chart_bash_errors(d, out, top_n=10):
    b = d["bash"]
    total = b["errors"]
    classes = sorted(b["error_classes"], key=lambda kv: -kv[1])
    assert sum(v for _, v in classes) == total, "bash error classes do not add up to the total"
    top, rest = classes[:top_n], classes[top_n:]
    rows, kind_sum = [], {"fail": 0, "guard": 0, "shell": 0}
    for key, count in top:
        name, kind = BASH_ERR.get(key, (key, "fail"))
        kind_sum[kind] += count
        rows.append({"label": name, "value": count, "color": KIND_COLOR[kind],
                     "v1": n0(count), "v2": pct(100.0 * count / total)})
    other = sum(v for _, v in rest)
    rows.append({"label": f"{len(rest)} further classes", "value": other, "color": OTHER,
                 "v1": n0(other), "v2": pct(100.0 * other / total)})
    guard, shell = 100.0 * kind_sum["guard"] / total, 100.0 * kind_sum["shell"] / total
    title = f"Guardrail refusals are {guard:.0f}% of Bash errors; zsh and sed traps add another {shell:.0f}%"
    subtitle = (f"Bash calls the harness flagged as errors, by class of the first error-like output line "
                f"(n = {n0(total)}, which is {b['error_rate_pct']}% of {n0(b['calls'])} Bash calls). "
                f"The classifier is heuristic.")
    cv, y = begin(title, subtitle)
    y = legend(cv, y + 12, [(BLUE, "Command failed"), (ORANGE, "Refused by a guardrail"),
                            (AQUA, "Shell-dialect trap (zsh, BSD sed)"), (OTHER, "Other classes")])
    bottom, _, _ = hbars(cv, y + 2, rows)
    return finish(cv, "chart-bash-errors.svg", bottom, title, describe(rows), out)


# --------------------------------------------------------------------------- #
# 9. Human prompt length
# --------------------------------------------------------------------------- #
LENGTH_LABEL = {"<50": "Under 50 characters", "50-199": "50 to 199", "200-999": "200 to 999",
                "1k-4.9k": "1,000 to 4,999", ">=5k": "5,000 or more"}
LENGTH_ORDER = ["<50", "50-199", "200-999", "1k-4.9k", ">=5k"]


def chart_prompt_length(d, out):
    buckets = d["scale"]["prompt_length_chars"]
    assert set(buckets) == set(LENGTH_ORDER), "unexpected prompt-length buckets"
    total = sum(buckets.values())
    rows, cum = [], 0
    for key in LENGTH_ORDER:
        cum += buckets[key]
        rows.append({"label": LENGTH_LABEL[key], "value": buckets[key], "color": BLUE,
                     "v1": n0(buckets[key]), "v2": pct(100.0 * buckets[key] / total)})
    first = 100.0 * buckets[LENGTH_ORDER[0]] / total
    under200 = 100.0 * (buckets["<50"] + buckets["50-199"]) / total
    long_n = buckets["1k-4.9k"] + buckets[">=5k"]
    title = f"{first:.0f}% of human prompts are shorter than 50 characters"
    subtitle = (f"Human prompts on the main thread by length in characters (n = {n0(total)}; slash commands "
                f"and prompts queued mid-turn are not included). {under200:.0f}% are under 200 characters; "
                f"{n0(long_n)} run to 1,000 or more.")
    cv, y = begin(title, subtitle)
    bottom, _, _ = hbars(cv, y + 8, rows, pitch=34, bar_h=18)
    return finish(cv, "chart-prompt-length.svg", bottom, title, describe(rows), out)


# --------------------------------------------------------------------------- #
# 10. Friction categories (numbers from the FRICTION table at the top)
# --------------------------------------------------------------------------- #
def chart_friction(out):
    n = FRICTION_SUBSTANTIVE_SESSIONS
    items = sorted(FRICTION, key=lambda r: -r[1])
    rows = [{"label": cat, "sub": what, "value": sessions, "color": BLUE,
             "v1": str(sessions), "v2": f"of {n}"} for cat, sessions, what, _ in items]
    over_half = sum(1 for r in items if r[1] > n / 2.0)
    title = f"Over-eager guards were the most widespread friction: {items[0][1]} of {n} sessions"
    subtitle = (f"Sessions in which each friction category appeared, of {n} substantive sessions "
                f"(regex counts, ±30%). Grey line: what was counted. {over_half} categories reached more than "
                f"half of the sessions; {FRICTION_NOT_PLOTTED} categories with no per-session count are not plotted.")
    cv, y = begin(title, subtitle)
    bottom, _, _ = hbars(cv, y + 8, rows, vmax=n, pitch=40, bar_h=16, cap_w=450,
                         refs=[(n / 2.0, "half"), (n, f"all {n}")])
    desc = "; ".join(f"{r['label']}: {r['v1']} of {n} sessions ({r['sub']})" for r in rows)
    return finish(cv, "chart-friction.svg", bottom, title, desc, out)


# --------------------------------------------------------------------------- #
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", default=os.environ.get("QUANT_JSON", os.path.join(here, "05-sessions-quant.json")),
                    help="path to 05-sessions-quant.json (or set QUANT_JSON)")
    ap.add_argument("--out", default=os.path.dirname(here), help="output directory (default: assets/)")
    args = ap.parse_args()
    if not os.path.isfile(args.data):
        sys.exit(f"data file not found: {args.data}\npass --data /path/to/05-sessions-quant.json")
    with open(args.data, encoding="utf-8") as fh:
        d = json.load(fh)
    built = [
        chart_leverage(d, args.out),
        chart_tool_share(d, args.out),
        chart_token_mix(d, args.out),
        chart_session_concentration(d, args.out),
        chart_inbound(d, args.out),
        chart_subagent_types(d, args.out),
        chart_hooks(d, args.out),
        chart_bash_errors(d, args.out),
        chart_prompt_length(d, args.out),
        chart_friction(args.out),
    ]
    for path, height in built:
        print(f"{os.path.basename(path):34s} {W}x{height}")


if __name__ == "__main__":
    main()
