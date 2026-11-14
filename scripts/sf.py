"""Shared pieces for the profile SVGs: palette, panel chrome and the line-drawn typeface."""

BG = "#050608"
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


def panel(w, h):
    return (f'<rect width="{w}" height="{h}" rx="6" fill="{BG}"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="5.5" fill="none" stroke="#fff" stroke-opacity=".08"/>')


def mono(text, x, y, size=13, opacity=.5, spacing=2, anchor="start", fill="#fff"):
    return (f'<text x="{f(x)}" y="{f(y)}" font-family="{MONO}" font-size="{size}" letter-spacing="{spacing}" '
            f'text-anchor="{anchor}" fill="{fill}" fill-opacity="{opacity}" xml:space="preserve">{esc(text)}</text>')


LINE = 'fill="none" stroke-linecap="square" stroke-linejoin="miter" stroke-miterlimit="3.3"'
