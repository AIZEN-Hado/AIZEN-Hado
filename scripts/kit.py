"""Shared toolkit for every profile SVG: palette, outlined typography, plate chrome, starfields.

Standard library only, so the daily telemetry workflow needs no installs.

Text is drawn from glyph outlines (scripts/glyphs.json, built by fonts.py) because SVGs displayed through
GitHub's image proxy cannot load fonts. Each glyph is defined once per file and placed with <use>.
"""
import json
import math
import pathlib
import random

# ---------------------------------------------------------------------------------------------- palette
VOID = "#050508"
DEEP = "#0B0D16"
AMBER = "#FF6B35"
VIOLET = "#8B5CF6"
WHITE = "#F5F5F7"
SILVER = "#8892A6"
EMBER = "#FFD2B8"          # the white-hot end of amber, used only at the brightest points

THEMES = {                 # for transparent section bands that sit directly on GitHub's page colour
    "dark": {"ink": WHITE, "muted": SILVER, "accent": AMBER, "rule": "#2A2F3E", "faint": "#1A1E2A"},
    "light": {"ink": DEEP, "muted": "#5A6377", "accent": "#D9480F", "rule": "#D3D7E0", "faint": "#E8EBF1"},
}

ROOT = pathlib.Path(__file__).resolve().parent.parent
_FONTS = json.loads((ROOT / "scripts" / "glyphs.json").read_text(encoding="utf-8"))
FALLBACK = "sans-400"

# Shared motion rules. Base styles are always the finished composition; animation only modulates it,
# so prefers-reduced-motion (or a renderer without CSS animation) still shows a complete image.
# Browsers do not reliably apply this inside an SVG shown as <img>, so the README also swaps in the frozen
# twin from assets/static/ with <picture><source media="(prefers-reduced-motion: reduce)">.
MOTION_OFF = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
STATIC = "*{animation:none!important}"


def f(x):
    """Compact number formatting for coordinates."""
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


class Layout:
    """The profile is one tall canvas cut into horizontal slices, one image each, stacked with no gaps.

    Each Doc takes the current cursor as its top edge (page coordinates) and advances it when saved, so
    images must be built in README order. The build runs twice: the "collect" pass records where text and
    illustrations sit, how dense the background should be and where the glows are; the "draw" pass renders
    the shared background with that knowledge, so nothing in it ever runs behind a word.
    """

    def __init__(self):
        self.phase = "draw"
        self.reset()
        self.frozen = {"keep": [], "density": [], "glows": [], "slices": {}, "total": 0}

    def reset(self):
        self.cursor = 0
        self.items = []                  # (name, height, alt, link) in page order
        self.keep, self.density, self.glows, self.slices = [], [], [], {}

    def freeze(self):
        self.frozen = {"keep": list(self.keep), "density": list(self.density), "glows": list(self.glows),
                       "slices": dict(self.slices), "total": self.cursor}

    def load(self, path):
        self.frozen = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

    def dump(self, path):
        pathlib.Path(path).write_text(json.dumps(self.frozen, separators=(",", ":")) + "\n", encoding="utf-8")


LAYOUT = Layout()


class Doc:
    """One SVG slice. Collects glyph definitions so each glyph is stored once."""

    def __init__(self, w, h, label, css=""):
        self.w, self.h, self.label, self.css = w, h, label, css
        self.body, self.defs, self._glyphs = [], [], {}
        self._uid = 0
        self.y0 = LAYOUT.cursor

    def keep(self, x0, y0, x1, y1):
        """Reserve a local rectangle: the background constellation stays out of it."""
        LAYOUT.keep.append([round(x0), round(self.y0 + y0), round(x1), round(self.y0 + y1)])

    # -- assembly ----------------------------------------------------------------------------------
    def add(self, *parts):
        self.body.extend(p for p in parts if p)
        return self

    def define(self, *parts):
        self.defs.extend(parts)

    def uid(self, prefix="u"):
        self._uid += 1
        return f"{prefix}{self._uid}"

    def render(self, static=False):
        glyph_defs = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in self._glyphs.values())
        css = (self.css + (STATIC if static else MOTION_OFF)).strip()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" role="img" aria-label="{esc(self.label)}" fill="none">'
                f'<title>{esc(self.label)}</title>'
                f'<style>{css}</style>'
                f'<defs>{glyph_defs}{"".join(self.defs)}</defs>'
                f'{"".join(self.body)}</svg>\n')

    def save(self, name, link=None):
        """Write assets/<name>; animated images also get a frozen twin in assets/static/<name>."""
        LAYOUT.items.append((name, self.h, self.label, link))
        LAYOUT.slices[name] = [self.y0, self.h]
        LAYOUT.cursor += self.h
        path = ROOT / "assets" / name
        if LAYOUT.phase == "collect":
            return path
        path.write_text(self.render(), encoding="utf-8")
        if "animation" in self.css:
            (ROOT / "assets" / "static").mkdir(exist_ok=True)
            (ROOT / "assets" / "static" / name).write_text(self.render(static=True), encoding="utf-8")
        return path

    # -- typography --------------------------------------------------------------------------------
    def _glyph(self, face, ch):
        font = _FONTS[face]
        if ch not in font["g"]:
            face, font = FALLBACK, _FONTS[FALLBACK]
            if ch not in font["g"]:
                ch = "?"
        adv, d = font["g"][ch]
        if not d:
            return face, adv, None
        key = (face, ch)
        if key not in self._glyphs:
            self._glyphs[key] = (f"g{len(self._glyphs):x}", d)
        return face, adv, self._glyphs[key][0]

    def text(self, s, x, y, size, face="sans-400", fill=WHITE, opacity=1, anchor="start", track=0,
             cls=None, extra=""):
        """Draw `s` with its baseline at y. `track` is letter-spacing in px. Returns the svg fragment."""
        width = measure(s, size, face, track)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        upm = _FONTS[face]["upm"]
        k = size / upm
        kern = _FONTS[face].get("k", {})
        pen, uses = 0.0, []
        for i, ch in enumerate(s):
            used_face, adv, gid = self._glyph(face, ch)
            # glyphs from the fallback face are scaled into this face's units
            scale = _FONTS[face]["upm"] / _FONTS[used_face]["upm"]
            if gid:
                if scale != 1:
                    uses.append(f'<use href="#{gid}" transform="translate({f(pen)} 0) scale({scale:.4f})"/>')
                else:
                    uses.append(f'<use href="#{gid}" x="{f(pen)}"/>')
            pen += adv * scale + track / k
            if i + 1 < len(s):
                pen += kern.get(s[i:i + 2], 0)
        size_box = (x - 7, y - size * .82 - 6, x + width + 7, y + size * .28 + 6)
        self.keep(*size_box)
        op = f' fill-opacity="{opacity}"' if opacity != 1 else ""
        c = f' class="{cls}"' if cls else ""
        return (f'<g{c} fill="{fill}"{op} transform="translate({f(x)} {f(y)}) scale({k:.5f} {-k:.5f})"{extra}>'
                f'{"".join(uses)}</g>')

    def runs(self, parts, x, y, size, face="sans-400", anchor="start", track=0):
        """Draw consecutive styled runs on one baseline: parts = [(text, fill, opacity, face|None), ...]."""
        total = sum(measure(t, size, fc or face, track) for t, _, _, fc in parts)
        if anchor == "middle":
            x -= total / 2
        elif anchor == "end":
            x -= total
        out = []
        for t, fill, op, fc in parts:
            out.append(self.text(t, x, y, size, fc or face, fill, op, track=track))
            x += measure(t, size, fc or face, track)
        return "".join(out)


def measure(s, size, face="sans-400", track=0):
    font = _FONTS[face]
    k = size / font["upm"]
    kern = font.get("k", {})
    total = 0.0
    for i, ch in enumerate(s):
        if ch in font["g"]:
            total += font["g"][ch][0] * k
        else:
            fb = _FONTS[FALLBACK]
            total += fb["g"].get(ch, fb["g"]["?"])[0] * size / fb["upm"]
        if i + 1 < len(s):
            total += kern.get(s[i:i + 2], 0) * k + track
    return total


def paragraph(doc, segments, x, y, size, max_w, leading):
    """Wrap styled runs. segments = [(text, face, fill, opacity), ...]. Returns (svg, number of lines)."""
    words = []                                            # (word, style, joined_to_previous)
    for text, face, fill, op in segments:
        for i, word in enumerate(text.split(" ")):
            if word:
                words.append((word, (face, fill, op), i == 0 and not text.startswith(" ")))
    lines, cur, cur_w = [], [], 0.0
    for word, st, glued in words:
        ww = measure(word, size, st[0])
        gap = 0 if (glued and cur) else measure(" ", size, st[0])
        if cur and cur_w + gap + ww > max_w:
            lines.append(cur)
            cur, cur_w, gap = [], 0.0, 0
        cur.append((word, st, gap if cur else 0))
        cur_w += (gap if len(cur) > 1 else 0) + ww
    if cur:
        lines.append(cur)
    out = []
    for n, line in enumerate(lines):
        pen = x
        run, run_st, run_x = "", None, x
        for word, st, gap in line:
            if st != run_st and run:
                out.append(doc.text(run, run_x, y + n * leading, size, run_st[0], run_st[1], run_st[2]))
                run, run_x = "", pen + (gap if gap else 0)
                run_st = st
                run = word
                pen += gap + measure(word, size, st[0])
                continue
            if not run:
                run_st, run_x = st, pen + gap
                run = word
            else:
                run += " " * (1 if gap else 0) + word
            pen += gap + measure(word, size, st[0])
        if run:
            out.append(doc.text(run, run_x, y + n * leading, size, run_st[0], run_st[1], run_st[2]))
    return "".join(out), len(lines)


def balanced(s, size, face, max_w, track=0):
    """Wrap, then even out a two-line result so the last line is never a lone word."""
    lines = wrap(s, size, face, max_w, track)
    if len(lines) != 2:
        return lines
    words = s.split()
    best = min(range(1, len(words)), key=lambda i: max(measure(" ".join(words[:i]), size, face, track),
                                                      measure(" ".join(words[i:]), size, face, track)))
    return [" ".join(words[:best]), " ".join(words[best:])]


def wrap(s, size, face, max_w, track=0):
    """Greedy word wrap into lines no wider than max_w."""
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, size, face, track) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------------------------- chrome
def plate(doc, density=.5, last=False, glow=None, **_):
    """Paint this slice of the shared canvas and return a clip id for its content.

    density  how busy the background constellation is here (0 = none)
    glow     optional (cx, cy, r, colour, opacity) in local coordinates; glows are global, so they
             continue across the seams into neighbouring slices
    The first slice rounds the canvas's top corners and the slice saved with last=True its bottom ones.
    """
    import canvas
    w, h = doc.w, doc.h
    if LAYOUT.phase == "collect":
        LAYOUT.density.append([doc.y0, doc.y0 + h, density])
        if glow:
            cx, cy, r, col, op = glow
            LAYOUT.glows.append([cx, doc.y0 + cy, r, col, op])
    r = 18
    top, bottom = doc.y0 == 0, last
    clip = doc.uid("clip")
    d = (f"M0 {r if top else 0}" + (f"A{r} {r} 0 0 1 {r} 0" if top else "") +
         f"H{w - (r if top else 0)}" + (f"A{r} {r} 0 0 1 {w} {r}" if top else "") +
         f"V{h - (r if bottom else 0)}" + (f"A{r} {r} 0 0 1 {w - r} {h}" if bottom else "") +
         f"H{r if bottom else 0}" + (f"A{r} {r} 0 0 1 0 {h - r}" if bottom else "") + "Z")
    doc.define(f'<clipPath id="{clip}"><path d="{d}"/></clipPath>')
    doc.add(f'<g clip-path="url(#{clip})">{canvas.layer(doc)}</g>')
    return clip


def panel(doc, x0=12, y0=8, x1=None, y1=None, r=16):
    """A floating instrument panel: faint frame over a darkened patch of the canvas."""
    x1 = doc.w - 12 if x1 is None else x1
    y1 = doc.h - 8 if y1 is None else y1
    doc.keep(x0 - 6, y0 - 6, x1 + 6, y1 + 6)
    return (f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="{r}" fill="#08090E" fill-opacity=".86" '
            f'stroke="#FFFFFF" stroke-opacity=".075"/>')


def plate_border(doc, r=18):
    """Slices no longer have their own border; kept so older call sites still work."""
    return ""


def registration(doc, inset=22, arm=9, color=SILVER, opacity=.45):
    """Corner crop marks."""
    w, h = doc.w, doc.h
    out = []
    for cx, cy, sx, sy in ((inset, inset, 1, 1), (w - inset, inset, -1, 1),
                           (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)):
        out.append(f'M{f(cx)} {f(cy + sy * arm)}V{f(cy)}H{f(cx + sx * arm)}')
    return f'<path d="{"".join(out)}" stroke="{color}" stroke-opacity="{opacity}" stroke-width="1"/>'


def corner_labels(doc, tl="", tr="", bl="", br="", inset=40, size=9.5, color=SILVER, opacity=.55):
    w, h = doc.w, doc.h
    out = []
    if tl:
        out.append(doc.text(tl, inset, 27, size, "mono-400", color, opacity, track=1.6))
    if tr:
        out.append(doc.text(tr, w - inset, 27, size, "mono-400", color, opacity, "end", track=1.6))
    if bl:
        out.append(doc.text(bl, inset, h - 19, size, "mono-400", color, opacity, track=1.6))
    if br:
        out.append(doc.text(br, w - inset, h - 19, size, "mono-400", color, opacity, "end", track=1.6))
    return "".join(out)


def stars(seed, w, h, n, avoid=None, twinkle=0.08, keep=()):
    """Deterministic sparse starfield. `avoid` = (cx, cy, r) and `keep` = [(x0, y0, x1, y1)] stay clear,
    so a star never sits beside a word and reads as punctuation."""
    rng = random.Random(seed)
    out, tw = [], []
    for i in range(n):
        x, y = rng.uniform(8, w - 8), rng.uniform(8, h - 8)
        if avoid and math.hypot(x - avoid[0], y - avoid[1]) < avoid[2]:
            continue
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in keep):
            continue
        mag = rng.random() ** 3
        r = .35 + mag * 1.05
        op = .18 + mag * .62
        col = WHITE
        roll = rng.random()
        if roll < .07:
            col = EMBER
        elif roll < .11:
            col = "#C4B5FD"
        c = f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col}" opacity="{f(op)}"/>'
        if rng.random() < twinkle and mag > .25:
            tw.append(f'<circle class="tw" style="animation-delay:-{rng.uniform(0, 7):.1f}s" cx="{f(x)}" '
                      f'cy="{f(y)}" r="{f(r)}" fill="{col}"/>')
        else:
            out.append(c)
    return "".join(out) + "".join(tw)


TWINKLE_CSS = ".tw{opacity:.7;animation:tw 7s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.7}50%{opacity:.12}}"


def ellipse_point(cx, cy, rx, ry, t, rot=0.0):
    """Point on an ellipse at parameter t (radians), rotated by rot (radians) about its centre."""
    x, y = rx * math.cos(t), ry * math.sin(t)
    c, s = math.cos(rot), math.sin(rot)
    return cx + x * c - y * s, cy + x * s + y * c


def arc_half(cx, cy, rx, ry, upper, ccw=True):
    """Half of an axis-aligned ellipse as a path. Direction is counter-clockwise on screen when ccw."""
    if upper:   # right -> over the top -> left
        return f"M{f(cx + rx)} {f(cy)}A{f(rx)} {f(ry)} 0 0 0 {f(cx - rx)} {f(cy)}"
    return f"M{f(cx - rx)} {f(cy)}A{f(rx)} {f(ry)} 0 0 0 {f(cx + rx)} {f(cy)}"   # left -> under -> right


def ellipse_len(rx, ry):
    """Ramanujan's approximation of an ellipse perimeter."""
    h = ((rx - ry) / (rx + ry)) ** 2
    return math.pi * (rx + ry) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
