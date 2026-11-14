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
SLICES = [("hero", 480), ("about", 560), ("focus", 520), ("journey", 390), ("projects", 150),
          ("p0", 124), ("p1", 124), ("p2", 124), ("telemetry", 490), ("contact", 150),
          ("l0", 84), ("l1", 84), ("l2", 84), ("l3", 84), ("footer", 140)]
OFFSET, _y = {}, 0
for _name, _h in SLICES:
    OFFSET[_name] = (_y, _h)
    _y += _h
TOTAL = _y

PAGE = "#030405"                                   # matches the bottom of the hero
INK, BODY, DIM = "#f4f6fa", "#9aa0aa", "#5d636d"   # text: strong, body, labels
# colour is reserved for the 3D objects
ICE, EMBER, MOSS, ROSE = "#8fb3ff", "#ff9e64", "#9ece6a", "#f7768e"


def _at(name, frac=0.0):
    y0, h = OFFSET[name]
    return y0 + h * frac


def _rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def bg_color(y):
    return PAGE


def backdrop(name):
    """Background for one slice: the same black as the hero."""
    _, h = OFFSET[name]
    if name == "footer":
        clip = f'<path d="M0,0H{W}V{h - 6}a6,6 0 0 1 -6,6H6a6,6 0 0 1 -6,-6Z"/>'
    else:
        clip = f'<rect width="{W}" height="{h}"/>'
    return f'<defs><clipPath id="page">{clip}</clipPath></defs><rect width="{W}" height="{h}" fill="{PAGE}"/>'


PARTICLE_CSS = (
    ".tw{animation:tw ease-in-out infinite}@keyframes tw{50%{opacity:.08}}"
    ".dr{animation:dr ease-in-out infinite alternate}@keyframes dr{to{transform:translate(var(--dx),var(--dy))}}"
    ".ss{animation:ss linear infinite}"
    "@keyframes ss{0%{transform:translate(0,0);opacity:0}1.5%{opacity:1}7%{transform:translate(var(--sx),var(--sy));opacity:0}"
    "100%{transform:translate(var(--sx),var(--sy));opacity:0}}"
)


def particles(name, density=None):
    """The live background: one starfield that runs behind the whole page. Every slice draws its own
    stretch of it with the same density as the hero, so the field reads as continuous."""
    _, h = OFFSET[name]
    rng = random.Random(f"stars-{name}")
    out = ['<g clip-path="url(#page)" fill="#fff">']
    for i in range(round(W * h / 7000)):                     # still stars, some twinkling
        x, y = rng.uniform(0, W), rng.uniform(0, h)
        r = rng.choice([.5, .5, .6, .7, .8, 1.1])
        tw = (f' class="tw" style="animation-duration:{f(rng.uniform(4, 8))}s;animation-delay:-{f(rng.uniform(0, 8))}s"'
              if i % 5 == 0 else "")
        out.append(f'<circle{tw} cx="{f(x)}" cy="{f(y)}" r="{r}" opacity="{rng.uniform(.12, .6):.2f}"/>')
    for _ in range(max(2, round(h / 90))):                   # slow drifting dust
        x, y = rng.uniform(40, W - 40), rng.uniform(20, h - 20)
        r = rng.choice([1, 1.3, 1.6])
        out.append(f'<g class="dr" style="--dx:{f(rng.uniform(-50, 50))}px;--dy:{f(rng.uniform(-6, 6))}px;'
                   f'animation-duration:{f(rng.uniform(16, 32))}s;animation-delay:-{f(rng.uniform(0, 32))}s">'
                   f'<circle cx="{f(x)}" cy="{f(y)}" r="{r * 3.2:.1f}" opacity=".05"/>'
                   f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" opacity=".7"/></g>')
    if h >= 300 or rng.random() < .3:                        # a shooting star now and then
        x, y = rng.uniform(80, 640), rng.uniform(20, max(30, h - 120))
        dist, ang = rng.uniform(220, 360), math.radians(rng.uniform(14, 28))
        dx, dy = dist * math.cos(ang), dist * math.sin(ang)
        tail = 70
        out.append('<defs><linearGradient id="sst" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                   '<stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient></defs>')
        out.append(f'<g class="ss" style="--sx:{f(dx)}px;--sy:{f(dy)}px;animation-duration:{f(rng.uniform(11, 19))}s;'
                   f'animation-delay:-{f(rng.uniform(0, 19))}s"><g transform="translate({f(x)} {f(y)}) rotate({f(math.degrees(ang))})">'
                   f'<rect x="-{tail}" y="-.6" width="{tail}" height="1.2" fill="url(#sst)"/><circle r="1.3"/></g></g>')
    out.append("</g>")
    return "".join(out)


GLOW = ('<filter id="neon" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="7" result="a"/>'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="a"/><feMergeNode in="a"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
GLOW += ('<filter id="halo" x="-300%" y="-300%" width="700%" height="700%"><feGaussianBlur stdDeviation="5" result="a"/>'
         '<feMerge><feMergeNode in="a"/><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
NEON_CSS = ""
LINE = 'fill="none" stroke-linecap="square" stroke-linejoin="miter" stroke-miterlimit="3.3"'


def neon_heading(index, title, color=None, y=132):
    """Section title in the hero's line-drawn letters, with an index and a rule that runs to the edge."""
    u = 5.2
    top = y - 6 * u
    paths, width, _ = glyphs(title, 104, top, u)
    return (label(f"{index:02d}", 60, y - 9, DIM, 1, size=13, spacing=2)
            + f'<g {LINE} stroke="#fff" stroke-opacity=".1" stroke-width="7">{paths}</g>'
            + f'<g {LINE} stroke="{INK}" stroke-width="2.1">{paths}</g>'
            + f'<rect x="{f(104 + width + 30)}" y="{f(y - 3 * u)}" width="{f(940 - 104 - width - 30)}" height="1" fill="#fff" fill-opacity=".1"/>')


def arrow(x, y, color, size=14):
    """Up-right arrow whose top-right corner sits at (x, y)."""
    return (f'<path d="M{f(x - size)},{f(y + size)}L{f(x)},{f(y)}M{f(x - size * .72)},{f(y)}H{f(x)}V{f(y + size * .72)}" '
            f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="square"/>')


def hairline(y, color=None, name=None):
    """Thin divider with a light that travels along it."""
    return ('<defs><linearGradient id="hl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity=".16"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity=".02"/></linearGradient>'
            '<linearGradient id="bm" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="hc"><rect x="60" y="{y - 2}" width="880" height="4"/></clipPath></defs>'
            f'<rect x="60" y="{y - .5}" width="880" height="1" fill="url(#hl)"/>'
            f'<g clip-path="url(#hc)"><rect class="beam" x="60" y="{y - .7}" width="170" height="1.4" fill="url(#bm)"/></g>')


BEAM_CSS = ".beam{animation:beam 9s linear infinite backwards}@keyframes beam{from{transform:translateX(-180px)}to{transform:translateX(900px)}}"
