#!/usr/bin/env python3
"""Build the static profile SVGs (hero, section headings, project rows, stack, link buttons).

Edit scripts/profile.json, then run:  python3 scripts/build.py
"""
import json
import math
import pathlib
import random

from sf import AMBER, LINE, MONO, W, f, glyphs, mono, panel, svg_open, typed, units

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CFG = json.loads((ROOT / "scripts" / "profile.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- hero
def hero():
    H = 480
    CX, CY, RS = 500, 196, 64            # hole centre, shadow radius
    TILT, FLAT = -7, 0.125               # disk rotation (deg) and inclination squash
    rng = random.Random(23)

    def dash_pattern(kind):
        if kind == "dust":
            return [v for _ in range(rng.randint(2, 4)) for v in (rng.uniform(.8, 2.2), rng.uniform(3, 15))]
        if kind == "streak":
            return [v for _ in range(rng.randint(1, 3)) for v in (rng.uniform(10, 70), rng.uniform(12, 90))]
        return [rng.uniform(18, 60), rng.uniform(6, 22), rng.uniform(1, 2.5), rng.uniform(6, 30),
                rng.uniform(1, 2.5), rng.uniform(10, 40)]

    def flowing(circ, period, kind):
        """(pathLength, dasharray, style) for a dash flow that loops without a seam."""
        pat = dash_pattern(kind)
        p = sum(pat)
        k = max(1, round(circ / p))
        return f(k * p), " ".join(f(v) for v in pat), f"--p:-{f(p)}px;animation-duration:{period / k:.2f}s"

    style = f"""
.fl{{animation:flow linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:var(--p)}}}}
#disk{{transform-origin:{CX}px {CY}px;animation:open 2.5s cubic-bezier(.65,0,.15,1) .3s backwards}}
@keyframes open{{0%{{transform:scale(0,.012)}}34%{{transform:scale(1,.012)}}100%{{transform:none}}}}
#hole{{transform-origin:{CX}px {CY}px;animation:hole 1.5s cubic-bezier(.3,0,.2,1) 1.25s backwards}}
@keyframes hole{{from{{transform:scale(.05);opacity:0}}}}
#haze{{animation:fade 2.2s ease-out 1.3s backwards}}
#sky{{animation:fade 2.5s ease-out .2s backwards}}
@keyframes fade{{from{{opacity:0}}}}
.tw{{animation:tw 6s ease-in-out infinite}}
@keyframes tw{{50%{{opacity:.1}}}}
#photon{{animation:pulse 6s ease-in-out 3s infinite}}
@keyframes pulse{{50%{{opacity:.6}}}}
.nm{{stroke-dasharray:1 1.05;animation:draw .5s cubic-bezier(.4,0,.2,1) backwards}}
@keyframes draw{{from{{stroke-dashoffset:1.02}}}}
.ch{{animation:on .01s linear backwards}}
@keyframes on{{from{{opacity:0}}}}
#handle{{animation:fade 1.2s ease-out 5s backwards}}
"""
    s = [svg_open(W, H, f'{CFG["name"]} — AI Engineer, LLM Systems, Full Stack', style)]
    s.append("<defs>")
    s.append('<linearGradient id="dop" gradientUnits="userSpaceOnUse" x1="70" y1="0" x2="930" y2="0">'
             '<stop offset="0" stop-color="#fff" stop-opacity=".0"/><stop offset=".1" stop-color="#fff" stop-opacity=".8"/>'
             '<stop offset=".36" stop-color="#fff" stop-opacity="1"/><stop offset=".62" stop-color="#fff" stop-opacity=".62"/>'
             '<stop offset=".9" stop-color="#fff" stop-opacity=".3"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    s.append(f'<linearGradient id="lens" gradientUnits="userSpaceOnUse" x1="0" y1="{CY - 130}" x2="0" y2="{CY + 130}">'
             '<stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset=".5" stop-color="#fff" stop-opacity=".8"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity=".3"/></linearGradient>')
    s.append(f'<linearGradient id="crown" gradientUnits="userSpaceOnUse" x1="0" y1="{CY - RS - 10}" x2="0" y2="{CY + 10}">'
             '<stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset=".55" stop-color="#fff" stop-opacity=".35"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    s.append('<radialGradient id="g1"><stop offset="0" stop-color="#fff" stop-opacity=".5"/>'
             '<stop offset=".4" stop-color="#e6edf7" stop-opacity=".14"/><stop offset="1" stop-color="#e6edf7" stop-opacity="0"/></radialGradient>')
    s.append('<radialGradient id="g2"><stop offset=".5" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset=".58" stop-color="#fff" stop-opacity=".34"/><stop offset=".75" stop-color="#fff" stop-opacity=".08"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    s.append('<radialGradient id="bgr" cx=".5" cy=".4" r=".75"><stop offset="0" stop-color="#0a0c10"/>'
             '<stop offset=".6" stop-color="#050608"/><stop offset="1" stop-color="#020203"/></radialGradient>')
    # clip: everything except the half of the shadow that lies behind the disk plane
    s.append(f'<clipPath id="front"><path clip-rule="evenodd" d="M-200,-800H1200V1200H-200Z'
             f'M{CX - RS},{CY}A{RS},{RS} 0 0 1 {CX + RS},{CY}Z"/></clipPath>')
    # clip: everything except the whole shadow
    s.append(f'<clipPath id="outside"><path clip-rule="evenodd" d="M-200,-800H1200V1200H-200Z'
             f'M{CX - RS},{CY}A{RS},{RS} 0 0 1 {CX + RS},{CY}A{RS},{RS} 0 0 1 {CX - RS},{CY}Z"/></clipPath>')
    s.append(f'<clipPath id="panel"><rect width="{W}" height="{H}" rx="6"/></clipPath>')
    s.append("</defs>")

    s.append('<g clip-path="url(#panel)">')
    s.append(f'<rect width="{W}" height="{H}" fill="url(#bgr)"/>')

    s.append('<g id="sky" fill="#fff">')
    for i in range(70):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if abs(y - CY) < 70 + 40 * rng.random() or (340 < y < 450 and 200 < x < 800):
            continue
        cls = f' class="tw" style="animation-delay:-{f(rng.uniform(0, 6))}s"' if i % 5 == 0 else ""
        s.append(f'<circle{cls} cx="{f(x)}" cy="{f(y)}" r="{rng.choice([.5, .6, .8, 1.1])}" opacity="{rng.uniform(.15, .7):.2f}"/>')
    s.append("</g>")

    # soft light
    s.append(f'<g id="haze" transform="rotate({TILT} {CX} {CY})">'
             f'<ellipse cx="{CX}" cy="{CY}" rx="470" ry="62" fill="url(#g1)" opacity=".42"/>'
             f'<ellipse cx="{CX - 110}" cy="{CY}" rx="230" ry="26" fill="url(#g1)" opacity=".9"/>'
             f'<circle cx="{CX}" cy="{CY}" r="{RS * 1.75}" fill="url(#g2)"/></g>')

    # lensed light wrapping the shadow, then the shadow itself
    s.append('<g id="hole"><g fill="none" stroke="url(#lens)">')
    n = 15
    for i in range(n):
        u = i / (n - 1)
        r = RS + 3 + 52 * u ** 1.5
        pl, da, st = flowing(2 * math.pi * r, 7 + 16 * u, rng.choice(["dust", "mix", "streak"]))
        s.append(f'<circle class="fl" style="{st}" cx="{CX}" cy="{CY}" r="{f(r)}" pathLength="{pl}" stroke-dasharray="{da}" '
                 f'stroke-width="{f(1.5 - .9 * u)}" opacity="{(.95 * (1 - u) ** 1.7 + .05):.2f}" '
                 f'transform="rotate({rng.randint(0, 359)} {CX} {CY})"/>')
    s.append("</g>")
    s.append(f'<circle cx="{CX}" cy="{CY}" r="{RS + 5}" fill="none" stroke="url(#crown)" stroke-width="5"/>')
    s.append(f'<circle cx="{CX}" cy="{CY}" r="{RS}" fill="#000"/>')
    s.append(f'<g id="photon" fill="none" stroke="url(#lens)"><circle cx="{CX}" cy="{CY}" r="{RS + .8}" stroke-width="1.7"/>'
             f'<circle cx="{CX}" cy="{CY}" r="{RS + 3.4}" stroke-width=".6" opacity=".6"/></g>')
    s.append("</g>")

    # the disk: inner rings cross in front of the hole, outer rings pass around it
    s.append(f'<g transform="rotate({TILT} {CX} {CY})"><g id="disk">')
    rings = {"front": [], "outside": []}
    n = 66
    for i in range(n):
        u = i / (n - 1)
        rx = RS + 14 + (432 - RS - 14) * u ** 1.12
        ry = rx * FLAT
        h = ((rx - ry) / (rx + ry)) ** 2
        circ = math.pi * (rx + ry) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
        period = 10 * (rx / (RS + 14)) ** 1.35           # inner rings orbit faster
        kind = rng.choices(["dust", "streak", "mix"], weights=[3, 4, 4])[0]
        pl, da, st = flowing(circ, period, kind)
        op = (1 - u) ** 1.1 * .92 + .14 + rng.uniform(-.06, .06)
        sw = rng.uniform(.8, 2.0) * (1 - .45 * u)
        rings["front" if rx < RS * 2.3 else "outside"].append(
            f'<ellipse class="fl" style="{st}" cx="{CX}" cy="{CY}" rx="{f(rx)}" ry="{f(ry)}" pathLength="{pl}" '
            f'stroke-dasharray="{da}" stroke-width="{f(sw)}" opacity="{min(max(op, .08), 1):.2f}"/>')
    s.append('<g clip-path="url(#outside)" fill="none" stroke="url(#dop)">' + "".join(rings["outside"]) + "</g>")
    s.append('<g clip-path="url(#front)" fill="none" stroke="url(#dop)">' + "".join(rings["front"]))
    # one lone ember caught in orbit: the only colour on the page
    ex, ey = 232, 232 * FLAT
    s.append(f'<g><circle r="8" fill="{AMBER}" opacity=".16"/><circle r="2.5" fill="{AMBER}"/>'
             f'<animateMotion dur="15s" repeatCount="indefinite" '
             f'path="M{CX + ex},{CY}A{ex},{f(ey)} 0 1 0 {CX - ex},{CY}A{ex},{f(ey)} 0 1 0 {CX + ex},{CY}"/></g>')
    s.append("</g></g></g>")

    # name, plotted stroke by stroke, and one quiet line
    name = CFG["name"].upper()
    paths, _, t_end = glyphs(name, 500, 364, 540 / units(name), anchor="middle", cls="nm", t0=2.6)
    s.append(f'<g fill="none" stroke="#fff" stroke-opacity=".06" stroke-width="8" stroke-linejoin="miter" stroke-miterlimit="3.3">{paths}</g>')
    s.append(f'<g fill="none" stroke="#f4f7fb" stroke-width="2.3" stroke-linejoin="miter" stroke-miterlimit="3.3">{paths}</g>')
    tag, _ = typed(CFG["tagline"], 500, 437, t_end + .3, 0.03, text_anchor="middle",
                   font_family=MONO, font_size=15, letter_spacing=5, fill="#fff", fill_opacity=".62")
    s.append(tag)
    s.append(f'<text id="handle" x="40" y="44" font-family="{MONO}" font-size="11" letter-spacing="4" fill="#fff" '
             f'fill-opacity=".38">{CFG["handle"].upper()}</text>')
    s.append("</g></svg>")
    return "\n".join(s)


# --------------------------------------------------------------------------- section heading
def heading(index, title):
    H = 60
    style = ("#run{animation:run 6s linear infinite}"
             "@keyframes run{from{stroke-dashoffset:60}to{stroke-dashoffset:-1000}}")
    s = [svg_open(W, H, title, style), panel(W, H)]
    s.append(mono(f"{index:02d}", 40, 35, size=13, opacity=.38, spacing=2))
    paths, width, _ = glyphs(title, 84, 22.5, 2.5)
    s.append(f'<g {LINE} stroke="#fff" stroke-opacity=".9" stroke-width="1.5">{paths}</g>')
    x0 = 84 + width + 28
    s.append(f'<path d="M{f(x0)},30.5H960" stroke="#fff" stroke-opacity=".14" fill="none"/>')
    s.append(f'<path id="run" d="M{f(x0)},30.5H960" stroke="#fff" stroke-opacity=".8" stroke-dasharray="60 2000" fill="none"/>')
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- project row
def project(i, p):
    desc, tags = p.get("description", ""), p.get("tags", "")
    H = 136 if desc else 96
    style = (f"#beam{{animation:beam 7s linear {i * 1.3:.1f}s infinite backwards}}"
             "@keyframes beam{from{transform:translateX(-180px)}to{transform:translateX(1000px)}}")
    s = [svg_open(W, H, p["repo"], style)]
    s.append('<defs><linearGradient id="b" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
             f'</linearGradient><clipPath id="c"><rect width="{W}" height="{H}" rx="6"/></clipPath></defs>')
    s.append(panel(W, H))
    s.append(mono(f"{i + 1:02d}", 40, 56, size=14, opacity=.36, spacing=2))
    paths, _, _ = glyphs(p["repo"], 92, 36, 4)
    s.append(f'<g {LINE} stroke="#f4f7fb" stroke-width="2">{paths}</g>')
    if tags:
        s.append(mono(tags.upper(), 920, 55, size=13, opacity=.45, spacing=2, anchor="end"))
    if desc:
        s.append(mono(desc, 92, 104, size=17, opacity=.6, spacing=.5))
    s.append('<path d="M944,56L960,40M949,40H960V51" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="1.6" stroke-linecap="square"/>')
    s.append(f'<g clip-path="url(#c)"><rect id="beam" x="0" y="{H - 1.4}" width="180" height="1.4" fill="url(#b)"/></g>')
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- stack
def stack():
    cols = CFG["stack"]
    rows = max(len(v) for v in cols.values())
    H = 96 + rows * 29
    style = ".dot{animation:dot 4s ease-in-out infinite}@keyframes dot{50%{opacity:.2}}"
    s = [svg_open(W, H, "Stack: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in cols.items()), style), panel(W, H)]
    xs = [40, 280, 520, 750]
    for c, (title, items) in enumerate(cols.items()):
        x = xs[c]
        s.append(f'<circle class="dot" style="animation-delay:-{c}s" cx="{x + 3}" cy="41" r="2.4" fill="#fff"/>')
        s.append(mono(title, x + 16, 46, size=12, opacity=.45, spacing=3))
        s.append(f'<path d="M{x},62H{x + 190}" stroke="#fff" stroke-opacity=".12"/>')
        for r, item in enumerate(items):
            s.append(mono(item, x, 96 + r * 29, size=17, opacity=.84, spacing=.5))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- link button
def link(label):
    w, h = 240, 64
    s = [svg_open(w, h, label), panel(w, h)]
    paths, _, _ = glyphs(label, 24, 25, 2.3)
    s.append(f'<g {LINE} stroke="#f4f7fb" stroke-width="1.5">{paths}</g>')
    s.append('<path d="M204,38L216,26M208,26H216V34" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="1.4" stroke-linecap="square"/>')
    s.append("</svg>")
    return "".join(s)


def main():
    ASSETS.mkdir(exist_ok=True)
    out = {"hero.svg": hero(), "stack.svg": stack()}
    for i, title in enumerate(["PROJECTS", "TELEMETRY", "SYSTEMS", "CONTACT"]):
        out[f"h-{title.lower()}.svg"] = heading(i + 1, title)
    for i, p in enumerate(CFG["projects"]):
        out[f"p-{p['repo'].lower()}.svg"] = project(i, p)
    for l in CFG["links"]:
        out[f"l-{l['file']}.svg"] = link(l["label"])
    for name, svg in out.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"assets/{name}  {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
