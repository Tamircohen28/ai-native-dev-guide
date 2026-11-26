"""Shared palette, type scale and SVG helpers for the book's concept figures."""
import html

# ---- palette (one set for all seven figures) ---------------------------------
PAPER = '#F5F2EA'   # figure ground
EDGE = '#D9D2C2'    # figure outline
BAND = '#ECE7DA'    # zone behind a group of nodes
CARD = '#FFFEFB'    # node surface
FAINT = '#E7E1D3'   # quiet fills, grid lines
RULE = '#C9C1AF'    # borders, leaders
INK = '#1B2430'     # primary text
INK2 = '#465062'    # secondary text, connectors
INK3 = '#58616F'    # muted text
BLUE = '#2B5BC7';  BLUE_T = '#E1E9FA'    # model, context
TEAL = '#09736A';  TEAL_T = '#D9F0EC'    # enforced, permissions
AMBER = '#9A5205'; AMBER_T = '#FBEBCF'   # hooks, advisory
PLUM = '#7A45B0';  PLUM_T = '#EEE3F7'    # you
RED = '#B93A32';   RED_T = '#F9E1DE'     # blocked
WHITE = '#FFFFFF'
RAMP = ['#E1E9FA', '#C3D2F4', '#9DB6EC', '#7092E0', '#3F6BCB', '#234FB4']  # level 0..5

# ---- type scale --------------------------------------------------------------
T_TITLE = 22
T_SUB = 14.5
T_NODE = 15
T_BODY = 13.5
T_SMALL = 13

SANS = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

_H = dict(zip('abcdefghijklmnopqrstuvwxyz',
              [556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556,
               333, 500, 278, 556, 500, 722, 500, 500, 500]))
_H.update(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
              [667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778,
               722, 667, 611, 722, 667, 944, 667, 667, 611]))
_H.update({c: 556 for c in '0123456789'})
_H.update({' ': 278, '.': 278, ',': 278, ':': 278, ';': 278, '-': 333, '_': 556, '/': 278,
           '(': 333, ')': 333, "'": 191, '"': 355, '<': 584, '>': 584, '=': 584, '+': 584,
           '*': 389, '@': 1015, '&': 667, '!': 278, '?': 556, '%': 889, '#': 556, '{': 334,
           '}': 334, '[': 278, ']': 278, '|': 260, '→': 1000, '·': 278, '—': 1000,
           '…': 1000, '’': 222})


def tw(s, size, bold=False, mono=False):
    """Estimated advance width of a string, in px."""
    if mono:
        return len(s) * 0.602 * size
    w = sum(_H.get(ch, 600) for ch in s) / 1000 * size
    return w * (1.06 if bold else 1.0)


def spans(s):
    """Split 'text `code` text' into [(text, is_mono), ...]."""
    out = []
    for i, part in enumerate(s.split('`')):
        if part:
            out.append((part, i % 2 == 1))
    return out


def esc(s):
    return html.escape(s, quote=False)


class Fig:
    def __init__(self, name, W, H, title, desc):
        self.name, self.W, self.H, self.title, self.desc = name, W, H, title, desc
        self.el = []
        self.markers = {}
        self.warn = []

    # -- primitives --
    def add(self, s):
        self.el.append(s)

    def rect(self, x, y, w, h, fill=CARD, stroke=None, sw=1.5, rx=10, dash=None):
        a = f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw:g}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.add(a + '/>')

    def circle(self, cx, cy, r, fill=CARD, stroke=None, sw=1.5):
        a = f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw:g}"'
        self.add(a + '/>')

    def _marker(self, color):
        mid = 'ah' + color.lstrip('#').lower()
        self.markers[mid] = color
        return mid

    def path(self, d, stroke=INK2, sw=1.75, fill='none', dash=None, arrow=False, cap='round'):
        a = (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}" '
             f'stroke-linecap="{cap}" stroke-linejoin="round"')
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if arrow:
            a += f' marker-end="url(#{self._marker(stroke)})"'
        self.add(a + '/>')

    def line(self, x1, y1, x2, y2, **kw):
        self.path(f'M{x1:g},{y1:g} L{x2:g},{y2:g}', **kw)

    def text(self, x, y, s, size=T_SMALL, fill=INK, weight=400, anchor='start', mono=False,
             maxw=None, mfill=None, ls=None, rotate=None):
        """One line of text. Backticks mark monospace spans. Returns estimated width."""
        parts = [(s, True)] if mono else spans(s)
        bold = weight >= 600
        msize = size if size <= 14 else size - 1
        est = sum(tw(p, msize if m else size, bold and not m, m) for p, m in parts)
        if ls:
            est += ls * len(s)
        if maxw is not None and est * 1.05 > maxw:
            self.warn.append(f'{self.name}: "{s}" est {est:.0f}px > max {maxw:.0f}px')
        a = (f'<text x="{x:g}" y="{y:g}" font-family="{SANS}" font-size="{size:g}" '
             f'font-weight="{weight}" fill="{fill}"')
        if anchor != 'start':
            a += f' text-anchor="{anchor}"'
        if ls:
            a += f' letter-spacing="{ls:g}"'
        if rotate is not None:
            a += f' transform="rotate({rotate:g} {x:g} {y:g})"'
        a += '>'
        if len(parts) == 1 and not parts[0][1]:
            a += esc(parts[0][0])
        else:
            for p, m in parts:
                if m:
                    a += (f'<tspan font-family="{MONO}" font-size="{msize:g}" '
                          f'fill="{mfill or fill}">{esc(p)}</tspan>')
                else:
                    a += f'<tspan>{esc(p)}</tspan>'
        self.add(a + '</text>')
        return est

    def lines(self, x, y, rows, lh=18, **kw):
        for i, r in enumerate(rows):
            self.text(x, y + i * lh, r, **kw)

    def chip(self, x, y, label, fill, tfill, stroke=None, size=T_SMALL, h=24, padx=10,
             anchor='start', weight=600, mono=False):
        """Pill with a label. x is the left edge, centre, or right edge per anchor."""
        parts = [(label, True)] if mono else spans(label)
        w = sum(tw(p, size, weight >= 600 and not m, m) for p, m in parts) * 1.04 + 2 * padx
        x0 = x if anchor == 'start' else (x - w / 2 if anchor == 'middle' else x - w)
        self.rect(x0, y, w, h, fill=fill, stroke=stroke, sw=1.25, rx=h / 2)
        self.text(x0 + w / 2, y + h / 2 + size * 0.35, label, size=size, fill=tfill,
                  weight=weight, anchor='middle', mono=mono)
        return w

    def node(self, x, y, w, h, title, subs=(), fill=CARD, stroke=INK2, tfill=INK, sfill=INK2,
             sw=1.5, rx=10, dash=None, tsize=T_NODE, ssize=T_SMALL, lh=17, tmono=False):
        """Box with a centred title and optional centred sub-lines."""
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx, dash=dash)
        block = tsize + len(subs) * lh + (4 if subs else 0)
        ty = y + (h - block) / 2 + tsize * 0.82
        self.text(x + w / 2, ty, title, size=tsize, fill=tfill, weight=600, anchor='middle',
                  maxw=w - 20, mono=tmono)
        for i, s in enumerate(subs):
            self.text(x + w / 2, ty + 5 + (i + 1) * lh, s, size=ssize, fill=sfill,
                      anchor='middle', maxw=w - 16, mfill=INK)

    def header(self, title, subtitle=None, x=32):
        self.text(x, 48, title, size=T_TITLE, weight=700, fill=INK, maxw=self.W - 2 * x)
        if subtitle:
            self.text(x, 73, subtitle, size=T_SUB, fill=INK2, maxw=self.W - 2 * x)

    # -- output --
    def svg(self):
        defs = ''.join(
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="11" '
            f'markerHeight="11" markerUnits="userSpaceOnUse" orient="auto">'
            f'<path d="M1,1.4 L9.2,5 L1,8.6 Z" fill="{c}"/></marker>'
            for mid, c in sorted(self.markers.items()))
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" '
                f'viewBox="0 0 {self.W} {self.H}" role="img" aria-labelledby="t d">\n'
                f'<title id="t">{esc(self.title)}</title>\n<desc id="d">{esc(self.desc)}</desc>\n')
        if defs:
            head += f'<defs>{defs}</defs>\n'
        head += (f'<rect x="0.75" y="0.75" width="{self.W - 1.5:g}" height="{self.H - 1.5:g}" '
                 f'rx="14" fill="{PAPER}" stroke="{EDGE}" stroke-width="1.5"/>\n')
        return head + '\n'.join(self.el) + '\n</svg>\n'

    def save(self, outdir):
        with open(outdir + self.name, 'w', encoding='utf-8') as fh:
            fh.write(self.svg())
        return self.warn


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
