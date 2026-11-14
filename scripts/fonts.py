#!/usr/bin/env python3
"""Export glyph outlines + kerning to scripts/glyphs.json (dev-time only; the JSON is committed).

SVGs shown through GitHub's <img> proxy cannot load web fonts, so every visible letter is drawn as a
path. This script turns real font files into a compact table those renderers read.

  pip install fonttools brotli uharfbuzz
  python3 scripts/fonts.py --serif DIR_WITH_INSTRUMENT_SERIF_WOFF2

Sources (all SIL Open Font License 1.1):
  Instrument Serif  npm @fontsource/instrument-serif (files/instrument-serif-latin-400-*.woff2)
  Inter             https://rsms.me/inter  (Inter-Light/Regular/Medium.otf)
  JetBrains Mono    https://www.jetbrains.com/lp/mono  (JetBrainsMono-Regular/Medium.ttf)
"""
import argparse
import io
import json
import pathlib

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

CHARS = "".join(chr(c) for c in range(32, 127)) + "·—–’‘“”°′″→↗←×≈≤≥αδκ§•▲▼"
KERN_CHARS = "".join(chr(c) for c in range(33, 127)) + "’‘“”"


def export(path):
    raw = pathlib.Path(path).read_bytes()
    font = TTFont(io.BytesIO(raw))
    if font.flavor:                                     # woff/woff2 -> plain sfnt for harfbuzz
        font.flavor = None
        buf = io.BytesIO()
        font.save(buf)
        raw = buf.getvalue()
        font = TTFont(io.BytesIO(raw))
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    glyphs = {}
    for ch in CHARS:
        name = cmap.get(ord(ch))
        if not name:
            continue
        pen = SVGPathPen(gs, ntos=lambda v: str(round(v)))
        gs[name].draw(pen)
        glyphs[ch] = [round(gs[name].width), pen.getCommands()]

    hbfont = hb.Font(hb.Face(raw))

    def advance(s):
        buf = hb.Buffer()
        buf.add_str(s)
        buf.guess_segment_properties()
        hb.shape(hbfont, buf, {"liga": False, "calt": False})
        return sum(p.x_advance for p in buf.glyph_positions)

    kern = {}
    present = [c for c in KERN_CHARS if c in glyphs]
    for a in present:
        for b in present:
            delta = advance(a + b) - glyphs[a][0] - glyphs[b][0]
            if abs(delta) >= upm * 0.004:
                kern[a + b] = delta
    asc = font["hhea"].ascent
    cap = getattr(font["OS/2"], "sCapHeight", 0) or round(asc * .7)
    return {"upm": upm, "cap": cap, "g": glyphs, "k": kern}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serif", required=True, help="directory holding instrument-serif-latin-400-*.woff2")
    ap.add_argument("--inter", default="/usr/share/fonts/opentype/inter")
    ap.add_argument("--mono", default="/usr/share/fonts/truetype/jetbrains-mono")
    a = ap.parse_args()
    s, i, m = pathlib.Path(a.serif), pathlib.Path(a.inter), pathlib.Path(a.mono)
    faces = {
        "serif": s / "instrument-serif-latin-400-normal.woff2",
        "serif-i": s / "instrument-serif-latin-400-italic.woff2",
        "sans-300": i / "Inter-Light.otf",
        "sans-400": i / "Inter-Regular.otf",
        "sans-500": i / "Inter-Medium.otf",
        "mono-400": m / "JetBrainsMono-Regular.ttf",
        "mono-500": m / "JetBrainsMono-Medium.ttf",
    }
    out = {name: export(p) for name, p in faces.items()}
    dest = pathlib.Path(__file__).resolve().parent / "glyphs.json"
    dest.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    for name, d in out.items():
        print(f"{name:9s} glyphs={len(d['g']):3d} kern={len(d['k']):5d}")
    print(f"wrote {dest} ({dest.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
