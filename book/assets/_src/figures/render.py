#!/usr/bin/env python3
"""xmllint each asset, then render with qlmanage.
qlmanage draws an SVG into a 768px square view and crops what does not fit, so the render uses a
scratch copy whose root width/height are scaled to fit (the viewBox is untouched, or set to a crop).
usage: render.py [name ...]            whole figures
       render.py name:x,y,w,h [...]    zoomed crop of one region
"""
import re, subprocess, sys, os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '')
S = os.path.join(os.environ.get('FIG_RENDER_DIR', '/tmp/figs-render'), '')
os.makedirs(S, exist_ok=True)
ALL = ['cover', 'fig-context-window', 'fig-agentic-loop', 'fig-extension-map', 'fig-mcp-architecture',
       'fig-guardrail-layers', 'fig-maturity-ladder']
for arg in (sys.argv[1:] or ALL):
    name, _, crop = arg.partition(':')
    src = A + name + '.svg'
    r = subprocess.run(['xmllint', '--noout', src], capture_output=True, text=True)
    status = 'xml ok' if r.returncode == 0 else 'XML FAIL ' + r.stderr.strip()
    t = open(src, encoding='utf-8').read()
    m = re.search(r'<svg [^>]*>', t)
    W, H = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', m.group(0)).groups())
    if crop:
        x, y, w, h = (float(v) for v in crop.split(','))
        tag = 'crop%d_%d' % (x, y)
    else:
        x, y, w, h, tag = 0, 0, W, H, 'full'
    k = 768 / max(w, h)
    root = re.sub(r'width="[\d.]+" height="[\d.]+" viewBox="[^"]+"',
                  'width="%.1f" height="%.1f" viewBox="%g %g %g %g"' % (w * k, h * k, x, y, w, h), m.group(0), 1)
    out = S + '%s.%s.svg' % (name, tag)
    open(out, 'w', encoding='utf-8').write(t.replace(m.group(0), root, 1))
    subprocess.run(['qlmanage', '-t', '-s', '1600', '-o', S, out], capture_output=True)
    png = out + '.png'
    print(status, name, '%gx%g' % (W, H), '->', png if os.path.exists(png) else 'NO PNG')
