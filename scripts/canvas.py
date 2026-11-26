"""The background shared by every slice: void, a slow colour grade with depth, soft glows and sparse stars.

Everything is computed in page coordinates (the whole profile is one canvas), so a glow or the colour grade
continues exactly across seams. The background is deliberately quiet: it never competes with the content.

The grade is the "descent": the page is hottest and warmest next to the black hole at the top and cools
through violet to a deep blue-black as you read down, away from it.
"""
import random

import kit
from kit import AMBER, EMBER, VIOLET, VOID, WHITE, f

ROW = 150                     # height of one star-generation row, in page pixels
CSS = (".ct{animation:ct 6s ease-in-out infinite}@keyframes ct{0%,100%{opacity:.8}50%{opacity:.15}}")

# (fraction of page height, colour, opacity): the colour of the light at that depth
GRADE = [(0.00, AMBER, .0), (0.07, AMBER, .03), (0.16, AMBER, .045), (0.34, VIOLET, .06), (0.62, "#4F46E5", .055),
         (0.86, "#1E3A8A", .06), (1.00, VOID, 0)]


def frozen():
    return kit.LAYOUT.frozen


def blocked(x, y, pad=0):
    return any(x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad for x0, y0, x1, y1 in frozen()["keep"])


def density_at(y):
    for y0, y1, d in frozen()["density"]:
        if y0 <= y < y1:
            return d
    return .5


def stars(y0, h):
    """Sparse, deterministic stars. Never behind words; a few twinkle."""
    out, tw = [], []
    for r in range(int(y0 // ROW) - 1, int((y0 + h) // ROW) + 2):
        rng = random.Random(90001 + r * 7919)
        for i in range(14):
            x, y = rng.uniform(4, 996), rng.uniform(r * ROW, (r + 1) * ROW)
            mag, roll, twk, keep = rng.random() ** 3, rng.random(), rng.random(), rng.random()
            if not (y0 - 3 <= y <= y0 + h + 3) or keep > .55 + density_at(y) * .45 or blocked(x, y, 6):
                continue
            col = EMBER if roll < .07 else ("#C4B5FD" if roll < .11 else WHITE)
            c = f'cx="{f(x)}" cy="{f(y - y0)}" r="{f(.35 + mag * 1.0)}" fill="{col}"'
            if twk < .08 and mag > .2:
                tw.append(f'<circle class="ct" style="animation-delay:-{(i * 1.37) % 6:.1f}s" {c}/>')
            else:
                out.append(f'<circle {c} opacity="{f(.16 + mag * .6)}"/>')
    return "".join(out) + "".join(tw)


def extent(cx, cy, r, w, h):
    """The part of a w x h canvas a radial gradient of radius r can touch (it is transparent beyond r), as rect
    attributes. Filling only that box instead of the whole slice is exact and cuts the paint work."""
    x0, y0, x1, y1 = max(0, cx - r), max(0, cy - r), min(w, cx + r), min(h, cy + r)
    return f'x="{f(x0)}" y="{f(y0)}" width="{f(x1 - x0)}" height="{f(y1 - y0)}"'


def glows(doc):
    """Radial glows registered by slices (global, so they continue across seams)."""
    y0, h = doc.y0, doc.h
    out = []
    for cx, cy, r, col, op in frozen()["glows"]:
        if cy + r < y0 or cy - r > y0 + h:
            continue
        gid = doc.uid("gl")
        doc.define(f'<radialGradient id="{gid}" cx="{f(cx)}" cy="{f(cy - y0)}" r="{f(r)}" gradientUnits="userSpaceOnUse">'
                   f'<stop offset="0" stop-color="{col}" stop-opacity="{op}"/>'
                   f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
        out.append(f'<rect {extent(cx, cy - y0, r, doc.w, h)} fill="url(#{gid})"/>')
    return "".join(out)


def mix(base_hex, top_hex, a):
    """`top_hex` at opacity `a` over `base_hex`, as an opaque hex colour."""
    ch = lambda h, i: int(h[1 + 2 * i:3 + 2 * i], 16)
    return "#" + "".join(f"{round(ch(base_hex, i) * (1 - a) + ch(top_hex, i) * a):02X}" for i in range(3))


def base(doc):
    """The void and the colour grade in a single opaque gradient: the grade's stops are blended over the void in
    advance, so the browser paints one full-slice layer instead of two (this layer is under every slice, and every
    animated slice repaints it on every frame)."""
    total = frozen()["total"] or 1
    gid = doc.uid("gr")
    stops = "".join(f'<stop offset="{f(p)}" stop-color="{mix(VOID, col, op)}"/>' for p, col, op in GRADE)
    doc.define(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{f(-doc.y0)}" '
               f'x2="0" y2="{f(total - doc.y0)}">{stops}</linearGradient>')
    return f'<rect width="{doc.w}" height="{doc.h}" fill="url(#{gid})"/>'


def grade(doc):
    """One vertical gradient over the whole page, in page coordinates."""
    total = frozen()["total"] or 1
    gid = doc.uid("gr")
    stops = "".join(f'<stop offset="{f(p)}" stop-color="{col}" stop-opacity="{op}"/>' for p, col, op in GRADE)
    doc.define(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{f(-doc.y0)}" '
               f'x2="0" y2="{f(total - doc.y0)}">{stops}</linearGradient>')
    return f'<rect width="{doc.w}" height="{doc.h}" fill="url(#{gid})"/>'


def layer(doc):
    """Everything behind a slice's own content."""
    if "@keyframes ct" not in doc.css:
        doc.css += CSS
    return base(doc) + glows(doc) + stars(doc.y0, doc.h)


def grade_alpha(page_y):
    """The grade's opacity at a page y (colour is constant over the hero's range, so only opacity matters here)."""
    t = page_y / (frozen()["total"] or 1)
    for (p0, _, a0), (p1, _, a1) in zip(GRADE, GRADE[1:]):
        if p0 <= t <= p1:
            return a0 + (a1 - a0) * (t - p0) / (p1 - p0)
    return GRADE[-1][2]


def grade_strip(doc, y_from):
    """The grade over the bottom of a slice only, ramping from nothing at y_from to its true value at the slice's
    foot, so the slice meets the next one exactly. Painting the full slice again was a second full-size layer."""
    gid = doc.uid("gr")
    end = grade_alpha(doc.y0 + doc.h)
    col = GRADE[1][1]
    doc.define(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{y_from}" x2="0" y2="{doc.h}">'
               f'<stop offset="0" stop-color="{col}" stop-opacity="0"/><stop offset="1" stop-color="{col}" stop-opacity="{f(end)}"/>'
               f'</linearGradient>')
    return f'<rect y="{y_from}" width="{doc.w}" height="{doc.h - y_from}" fill="url(#{gid})"/>'