"""The background shared by every slice: void, soft glows, stars and a living neural constellation.

Everything here is computed in page coordinates (the whole profile is one canvas), so a line or glow that
crosses from one image into the next continues exactly. Nodes are generated row by row from fixed seeds, so
any slice can work out its neighbourhood on its own and gets the same answer as the slices around it.

Motion that would have to stay in step across a seam is avoided: each image starts its animations when it
loads, independently. Signals therefore only run along edges that lie entirely inside one slice; hubs pulse
and stars twinkle in place.
"""
import functools
import math
import random

import kit
from kit import AMBER, EMBER, SILVER, VIOLET, VOID, WHITE, f

ROW = 150                     # height of one generation row, in page pixels
PER_ROW = 30                  # candidate nodes per row before density thinning
REACH = 200                   # longest edge
CSS = (".sig{animation:sig linear infinite}@keyframes sig{to{stroke-dashoffset:0}}"
       ".hb{animation:hb 4.6s ease-in-out infinite}@keyframes hb{0%,100%{opacity:.95}50%{opacity:.3}}"
       ".hr{transform-box:fill-box;transform-origin:center;animation:hr 4.6s ease-out infinite}"
       "@keyframes hr{0%{transform:scale(.5);opacity:.6}75%,100%{transform:scale(2.6);opacity:0}}"
       ".ct{animation:ct 6s ease-in-out infinite}@keyframes ct{0%,100%{opacity:.8}50%{opacity:.15}}")


def frozen():
    return kit.LAYOUT.frozen


def density_at(y):
    for y0, y1, d in frozen()["density"]:
        if y0 <= y < y1:
            return d
    return 0.0


def blocked(x, y, pad=0):
    return any(x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad for x0, y0, x1, y1 in frozen()["keep"])


@functools.lru_cache(maxsize=None)
def row_nodes(r):
    """Nodes whose y falls in generation row r. Always draws the same random numbers per row."""
    rng = random.Random(7001 + r * 104729)
    out = []
    for i in range(PER_ROW):
        x, y = rng.uniform(26, 974), rng.uniform(r * ROW, (r + 1) * ROW)
        keep_roll, hub_roll, size = rng.random(), rng.random(), rng.uniform(1.0, 1.9)
        if keep_roll > density_at(y) or blocked(x, y, 7):
            continue
        if any(math.dist((x, y), (o[1], o[2])) < 34 for o in out):      # even spacing, no clumps
            continue
        out.append((r * 100 + i, x, y, hub_roll < .13, size))
    return out


def crosses_text(a, b):
    for k in range(1, 16):
        t = k / 16
        if blocked(a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, 5):
            return True
    return False


@functools.lru_cache(maxsize=None)
def row_edges(r):
    """Edges owned by row r: each node links to its two nearest neighbours in rows r-1..r+1."""
    pool = row_nodes(r - 1) + row_nodes(r) + row_nodes(r + 1)
    edges = set()
    for n in row_nodes(r):
        near = sorted((m for m in pool if m[0] != n[0]), key=lambda m: math.dist(n[1:3], m[1:3]))[:2]
        for m in near:
            # edges may pass faintly behind words (panels mask them with their own fill)
            if math.dist(n[1:3], m[1:3]) < REACH:
                edges.add((min(n, m), max(n, m)))
    return edges


def curve(a, b):
    """A gentle bow, the same in every slice, so a line crossing a seam stays continuous."""
    mx, my = (a[1] + b[1]) / 2, (a[2] + b[2]) / 2
    dx, dy = b[1] - a[1], b[2] - a[2]
    ln = math.hypot(dx, dy) or 1
    bow = ((a[0] * 31 + b[0] * 17) % 9 - 4) * .028 * ln
    return f"M{f(a[1])} {f(a[2])}Q{f(mx - dy / ln * bow)} {f(my + dx / ln * bow)} {f(b[1])} {f(b[2])}", ln


def stars(y0, h):
    out, tw = [], []
    for r in range(int(y0 // ROW) - 1, int((y0 + h) // ROW) + 2):
        rng = random.Random(90001 + r * 7919)
        for i in range(16):
            x, y = rng.uniform(4, 996), rng.uniform(r * ROW, (r + 1) * ROW)
            mag, roll, twk = rng.random() ** 3, rng.random(), rng.random()
            if not (y0 - 3 <= y <= y0 + h + 3) or blocked(x, y, 4):
                continue
            col = EMBER if roll < .07 else ("#C4B5FD" if roll < .11 else WHITE)
            c = f'cx="{f(x)}" cy="{f(y - y0)}" r="{f(.35 + mag * 1.0)}" fill="{col}"'
            if twk < .07 and mag > .2:
                tw.append(f'<circle class="ct" style="animation-delay:-{(i * 1.37) % 6:.1f}s" {c}/>')
            else:
                out.append(f'<circle {c} opacity="{f(.16 + mag * .6)}"/>')
    return "".join(out) + "".join(tw)


def glows(doc):
    y0, h = doc.y0, doc.h
    out = []
    for cx, cy, r, col, op in frozen()["glows"]:
        if cy + r < y0 or cy - r > y0 + h:
            continue
        gid = doc.uid("gl")
        doc.define(f'<radialGradient id="{gid}" cx="{f(cx)}" cy="{f(cy - y0)}" r="{f(r)}" gradientUnits="userSpaceOnUse">'
                   f'<stop offset="0" stop-color="{col}" stop-opacity="{op}"/>'
                   f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
        out.append(f'<rect width="{doc.w}" height="{h}" fill="url(#{gid})"/>')
    return "".join(out)


def constellation(doc):
    y0, h = doc.y0, doc.h
    lo, hi = int((y0 - REACH) // ROW) - 1, int((y0 + h + REACH) // ROW) + 1
    edges = set()
    for r in range(lo, hi + 1):
        edges |= row_edges(r)
    lines, sigs, seen = [], [], set()
    for a, b in sorted(edges):
        if max(a[2], b[2]) < y0 - 2 or min(a[2], b[2]) > y0 + h + 2:
            continue
        d, ln = curve(a, b)
        lines.append(f'<path d="{d}"/>')
        seen.update((a, b))
        inside = min(a[2], b[2]) > y0 + 4 and max(a[2], b[2]) < y0 + h - 4
        if inside and (a[0] * 7 + b[0]) % 2 == 0 and not crosses_text(a, b):   # pulses never run behind words
            up, down = (a, b) if a[2] <= b[2] else (b, a)          # signals travel down the page
            d2, _ = curve(up, down)
            dash = ln * 2.4
            sigs.append(f'<path class="sig" style="animation-duration:{2.8 + (a[0] + b[0]) % 5 * .55:.2f}s;'
                        f'animation-delay:-{(a[0] * 13 + b[0]) % 40 / 10:.1f}s" d="{d2}" stroke="{AMBER}" '
                        f'stroke-width="1.3" stroke-linecap="round" stroke-dasharray="6 {f(dash)}" '
                        f'stroke-dashoffset="{f(dash + 6)}"/>')
    dots, hubs = [], []
    for n in sorted(seen | {n for r in range(lo, hi + 1) for n in row_nodes(r)}):
        _, x, y, hub, size = n
        if not (y0 - 8 <= y <= y0 + h + 8):
            continue
        if hub:
            delay = f"animation-delay:-{n[0] % 46 / 10:.1f}s"
            hubs.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="5" stroke="{AMBER}" stroke-opacity=".45" stroke-width=".8"/>'
                        f'<circle class="hr" style="{delay}" cx="{f(x)}" cy="{f(y)}" r="5" stroke="{AMBER}" stroke-width=".8"/>'
                        f'<circle class="hb" style="{delay}" cx="{f(x)}" cy="{f(y)}" r="2.2" fill="{EMBER}"/>')
        else:
            dots.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(size)}"/>')
    return (f'<g transform="translate(0 {f(-y0)})">'
            f'<g stroke="{SILVER}" stroke-opacity=".19" stroke-width=".7">{"".join(lines)}</g>{"".join(sigs)}'
            f'<g fill="{WHITE}" fill-opacity=".5">{"".join(dots)}</g>{"".join(hubs)}</g>')


def layer(doc):
    """Everything behind a slice's own content."""
    if "@keyframes sig" not in doc.css:
        doc.css += CSS
    return (f'<rect width="{doc.w}" height="{doc.h}" fill="{VOID}"/>' + glows(doc) + stars(doc.y0, doc.h)
            + constellation(doc))
