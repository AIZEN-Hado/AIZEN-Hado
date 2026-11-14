"""Shared pieces for the profile SVGs: the page-long backdrop, particles, and two ways of drawing text.

Every image in the README is a slice of one tall canvas. Each slice paints its part of the same
vertical gradient and the same glow fields, so stacked together they read as a single background.
"""
import json
import math
import pathlib
import random

AMBER = "#ffb454"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
W = 1000

GAP, SPACE = 1.7, 4.2

# Angular letterforms on a 4 x 6 grid: char -> (advance width, [strokes as "x,y x,y ..."])
GLYPHS = {
    "A": (4, ["0,6 2,0 4,6"]),
    "B": (4, ["0,0 0,6 4,6 4,3 0,3", "0,0 3,0 3,3"]),
    "C": (4, ["4,0 0,0 0,6 4,6"]),
    "D": (4, ["0,0 3,0 4,1 4,5 3,6 0,6 0,0"]),
    "E": (4, ["4,0 0,0 0,6 4,6", "0,3 3,3"]),
    "F": (4, ["4,0 0,0 0,6", "0,3 3,3"]),
    "G": (4, ["4,0 0,0 0,6 4,6 4,3 2,3"]),
    "H": (4, ["0,0 0,6", "0,3 4,3", "4,0 4,6"]),
    "I": (0, ["0,0 0,6"]),
    "J": (4, ["4,0 4,6 0,6 0,4"]),
    "K": (4, ["0,0 0,6", "4,0 0,3 4,6"]),
    "L": (4, ["0,0 0,6 4,6"]),
    "M": (4, ["0,6 0,0 2,3 4,0 4,6"]),
    "N": (4, ["0,6 0,0 4,6 4,0"]),
    "O": (4, ["0,0 4,0 4,6 0,6 0,0"]),
    "P": (4, ["0,6 0,0 4,0 4,3 0,3"]),
    "Q": (4, ["0,0 4,0 4,6 0,6 0,0", "2.6,4.4 4,6"]),
    "R": (4, ["0,6 0,0 4,0 4,3 0,3", "1.6,3 4,6"]),
    "S": (4, ["4,0 0,0 0,3 4,3 4,6 0,6"]),
    "T": (4, ["0,0 4,0", "2,0 2,6"]),
    "U": (4, ["0,0 0,6 4,6 4,0"]),
    "V": (4, ["0,0 2,6 4,0"]),
    "W": (4, ["0,0 0,6 2,3 4,6 4,0"]),
    "X": (4, ["0,0 4,6", "4,0 0,6"]),
    "Y": (4, ["0,0 2,2.7 4,0", "2,2.7 2,6"]),
    "Z": (4, ["0,0 4,0 0,6 4,6"]),
    "0": (4, ["0,0 4,0 4,6 0,6 0,0", "1.2,4.4 2.8,1.6"]),
    "1": (2, ["0,1.4 2,0 2,6"]),
    "2": (4, ["0,0 4,0 4,3 0,3 0,6 4,6"]),
    "3": (4, ["0,0 4,0 4,6 0,6", "1,3 4,3"]),
    "4": (4, ["0,0 0,3 4,3", "4,0 4,6"]),
    "5": (4, ["4,0 0,0 0,3 4,3 4,6 0,6"]),
    "6": (4, ["4,0 0,0 0,6 4,6 4,3 0,3"]),
    "7": (4, ["0,0 4,0 2,6"]),
    "8": (4, ["0,0 4,0 4,6 0,6 0,0", "0,3 4,3"]),
    "9": (4, ["4,3 0,3 0,0 4,0 4,6 0,6"]),
    "-": (4, ["0.6,3 3.4,3"]),
    "/": (4, ["0,6 4,0"]),
    ".": (0, ["0,5.4 0,6"]),
    "_": (4, ["0,6 4,6"]),
}


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def units(text):
    """Width of `text` in grid units."""
    total = 0.0
    for i, ch in enumerate(text):
        if ch == " ":
            total += SPACE
        else:
            total += GLYPHS[ch][0]
            if i < len(text) - 1 and text[i + 1] != " ":
                total += GAP
    return total


def glyphs(text, x, top, u, anchor="start", cls=None, t0=0.0, step=0.055):
    """Return (svg paths, width, end time). With `cls`, each stroke gets a staggered animation-delay."""
    text = text.upper()
    width = units(text) * u
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    out, k = [], 0
    for ch in text:
        if ch == " ":
            x += SPACE * u
            continue
        adv, strokes = GLYPHS[ch]
        for stroke in strokes:
            pts = []
            for p in stroke.split():
                px, py = p.split(",")
                pts.append(f"{f(x + float(px) * u)},{f(top + float(py) * u)}")
            anim = f' class="{cls}" pathLength="1" style="animation-delay:{t0 + k * step:.2f}s"' if cls else ""
            out.append(f'<path{anim} d="M{"L".join(pts)}"/>')
            k += 1
        x += (adv + GAP) * u
    return "".join(out), width, t0 + k * step


def typed(text, x, y, t0, step=0.03, **attrs):
    """Mono text that appears one character at a time."""
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    spans = "".join(
        f'<tspan class="ch" style="animation-delay:{t0 + i * step:.2f}s">{esc(c)}</tspan>' if c != " " else " "
        for i, c in enumerate(text))
    return f'<text x="{x}" y="{y}" xml:space="preserve" {a}>{spans}</text>', t0 + len(text) * step



def svg_open(w, h, label, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{esc(label)}"><style>{style}'
            f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>')


# ----------------------------------------------------------------------------- text as outlines
# Inter and JetBrains Mono (both SIL Open Font License) exported as glyph outlines, so text looks
# the same on every device without loading a font.
_FONTS = json.loads((pathlib.Path(__file__).resolve().parent / "glyphs.json").read_text(encoding="utf-8"))


def text_width(s, size, face="inter-400", spacing=0):
    font = _FONTS[face]
    k = size / font["upm"]
    return sum(font["g"].get(c, font["g"]["?"])[0] * k + spacing for c in s) - (spacing if s else 0)


def text(s, x, y, size, face="inter-400", anchor="start", spacing=0, attrs='fill="#fff"'):
    """Return (svg, width) for `s` drawn as paths with its baseline at y."""
    font = _FONTS[face]
    k = size / font["upm"]
    width = text_width(s, size, face, spacing)
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    parts = []
    for c in s:
        adv, d = font["g"].get(c, font["g"]["?"])
        if d:
            parts.append(f'<path transform="translate({f(x)} {f(y)}) scale({k:.5f} -{k:.5f})" d="{d}"/>')
        x += adv * k + spacing
    return f'<g {attrs}>{"".join(parts)}</g>', width


def label(s, x, y, color="#fff", opacity=.6, size=12, spacing=3, anchor="start"):
    """Small mono caption."""
    return text(s, x, y, size, "mono-500", anchor, spacing, f'fill="{color}" fill-opacity="{opacity}"')[0]


# ----------------------------------------------------------------------------- the page canvas
SLICES = [("hero", 480), ("intro", 300), ("p0", 110), ("p1", 110), ("p2", 110), ("p3", 110),
          ("telemetry", 490), ("systems", 440), ("contact", 150), ("l0", 84), ("l1", 84), ("l2", 84),
          ("l3", 84), ("footer", 140)]
OFFSET, _y = {}, 0
for _name, _h in SLICES:
    OFFSET[_name] = (_y, _h)
    _y += _h
TOTAL = _y

VIOLET, BLUE, CYAN, MINT, PINK, MAGENTA = "#8b7bff", "#5ea2ff", "#22d3ee", "#34d399", "#f472b6", "#e879f9"
ORANGE = "#ff8a3d"


def _at(name, frac=0.0):
    y0, h = OFFSET[name]
    return y0 + h * frac


# background colour down the page
STOPS = [(0, "#030405"), (_at("intro"), "#030405"), (_at("p0"), "#0b0a24"), (_at("telemetry"), "#081428"),
         (_at("systems"), "#05191d"), (_at("contact"), "#1a0b20"), (_at("l2"), "#1b100a"), (TOTAL, "#040302")]
# soft static glows: (cx, cy, rx, ry, colour, opacity) in page coordinates
GLOWS = [(140, _at("p0") - 20, 440, 250, VIOLET, .26), (900, _at("p2"), 400, 300, BLUE, .20),
         (180, _at("telemetry", .45), 470, 300, CYAN, .15), (880, _at("telemetry", .95), 420, 260, MINT, .11),
         (160, _at("systems", .6), 430, 290, MAGENTA, .15), (870, _at("contact", .4), 420, 260, PINK, .14),
         (260, _at("l2"), 440, 230, AMBER, .13), (820, _at("footer", .1), 360, 170, ORANGE, .08)]
# what floats in the background changes as you move down the page
ZONES = [(_at("intro"), "motes", [VIOLET, BLUE, "#c4b5fd", "#ffffff"]),
         (_at("telemetry"), "streaks", [CYAN, "#67e8f9", MINT]),
         (_at("systems"), "sparks", [PINK, MAGENTA, "#fb7185"]),
         (_at("contact"), "embers", [AMBER, ORANGE, "#ffd08a"])]


def _rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def bg_color(y):
    for (y0, c0), (y1, c1) in zip(STOPS, STOPS[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0) if y1 > y0 else 0
            t = t * t * (3 - 2 * t)
            return "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in zip(_rgb(c0), _rgb(c1)))
    return STOPS[-1][1]


def backdrop(name):
    """Background for one slice: its stretch of the page gradient plus any glows that reach into it."""
    y0, h = OFFSET[name]
    n = max(2, round(h / 30))
    stops = "".join(f'<stop offset="{i / n:.3f}" stop-color="{bg_color(y0 + h * i / n)}"/>' for i in range(n + 1))
    s = [f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>']
    body = []
    for i, (cx, cy, rx, ry, col, op) in enumerate(GLOWS):
        if cy + ry < y0 or cy - ry > y0 + h:
            continue
        s.append(f'<radialGradient id="gl{i}"><stop offset="0" stop-color="{col}" stop-opacity="{op}"/>'
                 f'<stop offset=".55" stop-color="{col}" stop-opacity="{op * .35:.3f}"/>'
                 f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
        body.append(f'<ellipse cx="{cx}" cy="{f(cy - y0)}" rx="{rx}" ry="{ry}" fill="url(#gl{i})"/>')
    if name == "footer":
        s.append(f'<clipPath id="page"><path d="M0,0H{W}V{h - 6}a6,6 0 0 1 -6,6H6a6,6 0 0 1 -6,-6Z"/></clipPath>')
    else:
        s.append(f'<clipPath id="page"><rect width="{W}" height="{h}"/></clipPath>')
    s.append("</defs>")
    s.append(f'<g clip-path="url(#page)"><rect width="{W}" height="{h}" fill="url(#bg)"/>{"".join(body)}</g>')
    return "".join(s)


PARTICLE_CSS = (
    ".mo{animation:mo ease-in-out infinite alternate}@keyframes mo{from{transform:translate(0,0)}to{transform:translate(var(--dx),var(--dy))}}"
    ".tw{animation:tw ease-in-out infinite}@keyframes tw{50%{opacity:.15}}"
    ".st{animation:st linear infinite}@keyframes st{from{transform:translateX(-80px)}to{transform:translateX(1080px)}}"
    ".sp{transform-box:fill-box;transform-origin:center;animation:sp ease-in-out infinite}"
    "@keyframes sp{0%,100%{transform:scale(.5) rotate(0deg);opacity:.2}50%{transform:scale(1.15) rotate(90deg);opacity:1}}"
    ".em{animation:em ease-out infinite}@keyframes em{0%{transform:translateY(14px);opacity:0}25%{opacity:1}100%{transform:translateY(-22px);opacity:0}}"
)


def particles(name, density=13):
    """Animated background particles for one slice. Their kind and colour depend on the page position."""
    y0, h = OFFSET[name]
    rng = random.Random(f"particles-{name}")
    out = []
    for _ in range(max(3, round(h * density / 100))):
        x, y = rng.uniform(10, W - 10), rng.uniform(9, h - 9)
        # blend zones near their boundaries so the change is gradual
        yy = y0 + y + rng.uniform(-90, 90)
        kind, cols = ZONES[0][1], ZONES[0][2]
        for start, k, c in ZONES:
            if yy >= start:
                kind, cols = k, c
        col = rng.choice(cols)
        d = f"animation-duration:{f(rng.uniform(4, 9))}s;animation-delay:-{f(rng.uniform(0, 9))}s"
        if kind == "motes":
            r = rng.choice([.8, 1, 1.2, 1.6, 2.2])
            halo = f'<circle cx="{f(x)}" cy="{f(y)}" r="{r * 3}" fill="{col}" opacity=".14"/>' if r > 1.4 and col != "#ffffff" else ""
            out.append(f'<g class="mo" style="--dx:{f(rng.uniform(-60, 60))}px;--dy:{f(rng.uniform(-5, 5))}px;'
                       f'animation-duration:{f(rng.uniform(14, 30))}s;animation-delay:-{f(rng.uniform(0, 30))}s">{halo}'
                       f'<circle class="tw" style="{d}" cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{col}" opacity="{rng.uniform(.45, .95):.2f}"/></g>')
        elif kind == "streaks":
            w = rng.uniform(10, 46)
            dur = rng.uniform(7, 18)
            out.append(f'<rect class="st" style="animation-duration:{f(dur)}s;animation-delay:-{f(rng.uniform(0, dur))}s" '
                       f'x="{f(-w)}" y="{f(y)}" width="{f(w)}" height="{rng.choice([1, 1.2, 1.6])}" rx=".8" fill="{col}" '
                       f'opacity="{rng.uniform(.25, .75):.2f}"/>')
        elif kind == "sparks":
            a = rng.choice([3, 4, 5])
            shape = (f'<path d="M{f(x - a)},{f(y)}H{f(x + a)}M{f(x)},{f(y - a)}V{f(y + a)}" stroke="{col}" stroke-width="1.2" fill="none"/>'
                     if rng.random() < .6 else
                     f'<circle cx="{f(x)}" cy="{f(y)}" r="{a - 1}" stroke="{col}" stroke-width="1.1" fill="none"/>')
            out.append(f'<g class="sp" style="{d}">{shape}</g>')
        else:  # embers
            r = rng.choice([.9, 1.2, 1.6, 2])
            y = min(max(y, 26), h - 18)
            out.append(f'<circle class="em" style="{d}" cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{col}"/>')
    return "".join(out)


GLOW = ('<filter id="neon" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="7" result="a"/>'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="a"/><feMergeNode in="a"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
GLOW += ('<filter id="halo" x="-300%" y="-300%" width="700%" height="700%"><feGaussianBlur stdDeviation="5" result="a"/>'
         '<feMerge><feMergeNode in="a"/><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
NEON_CSS = (".neon{animation:neon 7s linear infinite}"
            "@keyframes neon{0%,91%,100%{opacity:1}92%{opacity:.5}93.5%{opacity:1}95%{opacity:.72}96%{opacity:1}}")


def neon_heading(index, title, color, y):
    """Outlined neon section title with its small index label. Needs GLOW in <defs> and NEON_CSS."""
    size = 62
    k = size / _FONTS["inter-800"]["upm"]
    outline, _ = text(title, 58, y, size, "inter-800", spacing=7,
                      attrs=f'fill="{color}" fill-opacity=".1" stroke="{color}" stroke-width="{1.7 / k:.1f}" stroke-linejoin="round"')
    return (label(f"{index:02d}", 61, y - 68, color, .8, size=13, spacing=3)
            + f'<g class="neon" filter="url(#neon)">{outline}</g>')


def arrow(x, y, color, size=14):
    """Up-right arrow whose top-right corner sits at (x, y)."""
    return (f'<path d="M{f(x - size)},{f(y + size)}L{f(x)},{f(y)}M{f(x - size * .72)},{f(y)}H{f(x)}V{f(y + size * .72)}" '
            f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="square"/>')


def hairline(y, color, name):
    """Thin divider with a light that travels along it."""
    return (f'<defs><linearGradient id="hl" x1="0" x2="1"><stop offset="0" stop-color="{color}" stop-opacity=".5"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="bm" x1="0" x2="1"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="hc"><rect x="60" y="{y - 2}" width="880" height="4"/></clipPath></defs>'
            f'<rect x="60" y="{y - .5}" width="880" height="1" fill="url(#hl)"/>'
            f'<g clip-path="url(#hc)"><rect class="beam" x="60" y="{y - .8}" width="170" height="1.6" fill="url(#bm)"/></g>')


BEAM_CSS = ".beam{animation:beam 7s linear infinite backwards}@keyframes beam{from{transform:translateX(-180px)}to{transform:translateX(900px)}}"
