#!/usr/bin/env python3
"""Build the static profile SVGs: hero, intro, project rows, systems, contact rows, footer.

Each one is a slice of the same page-long canvas (see sf.py). Edit scripts/profile.json, then run:
    python3 scripts/build.py
"""
import json
import math
import pathlib
import random

import sf
from sf import AMBER, MONO, W, f, glyphs, svg_open, typed, units

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
    s.append(f'<clipPath id="panel"><path d="M0,6a6,6 0 0 1 6,-6H{W - 6}a6,6 0 0 1 6,6V{H}H0Z"/></clipPath>')
    s.append(f'<linearGradient id="sink" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sf.bg_color(H)}" stop-opacity="0"/>'
             f'<stop offset="1" stop-color="{sf.bg_color(H)}"/></linearGradient>')
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

    # sink into the page colour so the slice below continues seamlessly
    s.append(f'<rect y="{H - 130}" width="{W}" height="130" fill="url(#sink)"/>')
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


# --------------------------------------------------------------------------- shared slice shell
def shell(name, label, extra_css="", defs=""):
    _, h = sf.OFFSET[name]
    css = sf.PARTICLE_CSS + sf.NEON_CSS + sf.BEAM_CSS + extra_css
    return [svg_open(W, h, label, css), sf.backdrop(name), f"<defs>{sf.GLOW}{defs}</defs>", sf.particles(name)], h


# --------------------------------------------------------------------------- intro + first heading
def intro():
    s, h = shell("intro", " ".join("".join(t for t, _ in line) for line in CFG["about"]))
    y = 78
    for line in CFG["about"]:
        x = 60
        for chunk, strong in line:
            face, attrs = ("inter-600", 'fill="#ffffff"') if strong else ("inter-400", 'fill="#b4bcd0"')
            svg, w = sf.text(chunk, x, y, 23, face, attrs=attrs)
            s.append(svg)
            x += w
        y += 36
    s.append(sf.neon_heading(1, "PROJECTS", sf.VIOLET, 262))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- project row
ROW_COLORS = ["#a78bfa", "#8b7bff", "#7090ff", "#5ea2ff"]


def project(i, p):
    name = f"p{i}"
    color = ROW_COLORS[i % len(ROW_COLORS)]
    s, h = shell(name, p["repo"] + (": " + p["description"] if p.get("description") else ""),
                 f".beam{{animation-delay:{i * 1.4:.1f}s}}")
    desc = p.get("description", "")
    base = 60 if desc else 70
    s.append(sf.label(f"{i + 1:02d}", 61, base - 2, color, .85, size=13))
    s.append(sf.text(p["repo"], 112, base, 36, "inter-600")[0])
    if desc:
        s.append(sf.text(desc, 112, base + 30, 17, "inter-400", attrs='fill="#9aa3b8"')[0])
    if p.get("tags"):
        s.append(sf.label(p["tags"].upper(), 900, base - 4, color, .7, size=12, spacing=2, anchor="end"))
    s.append(f'<g filter="url(#halo)">{sf.arrow(940, base - 22, color)}</g>')
    s.append(sf.hairline(h - 1, color, name))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- systems
def systems():
    cols = CFG["stack"]
    s, h = shell("systems", "Systems. " + ". ".join(f"{k}: {', '.join(v)}" for k, v in cols.items()))
    s.append(sf.neon_heading(3, "SYSTEMS", sf.PINK, 132))
    xs = [60, 290, 520, 740]
    tints = [sf.PINK, sf.MAGENTA, "#fb7185", "#c084fc"]
    for c, (title, items) in enumerate(cols.items()):
        x, tint = xs[c], tints[c % len(tints)]
        s.append(f'<circle class="tw" style="animation-duration:4s;animation-delay:-{c}s" cx="{x + 3}" cy="199" r="3" fill="{tint}"/>')
        s.append(sf.label(title, x + 16, 204, tint, .95, size=12))
        s.append(f'<rect x="{x}" y="219" width="190" height="1" fill="{tint}" fill-opacity=".3"/>')
        for r, item in enumerate(items):
            s.append(sf.text(item, x, 256 + r * 31, 19, "inter-400", attrs='fill="#e9ecf5"')[0])
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- contact
def contact():
    s, h = shell("contact", "Contact")
    s.append(sf.neon_heading(4, "CONTACT", AMBER, 132))
    s.append("</svg>")
    return "".join(s)


LINK_COLORS = ["#ffb454", "#ffa24a", "#ff9442", "#ff8a3d"]


def link(i, l):
    name = f"l{i}"
    color = LINK_COLORS[i % len(LINK_COLORS)]
    s, h = shell(name, f'{l["label"]}: {l["detail"]}', f".beam{{animation-delay:{i * 1.4:.1f}s}}")
    s.append(sf.text(l["label"], 60, 52, 28, "inter-600")[0])
    s.append(sf.label(l["detail"], 900, 49, "#ffd9a8", .75, size=13, spacing=1, anchor="end"))
    s.append(f'<g filter="url(#halo)">{sf.arrow(940, 30, color)}</g>')
    s.append(sf.hairline(h - 1, color, name))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- footer
def footer():
    s, h = shell("footer", "End of transmission", ".cur{animation:cur 1.1s steps(1) infinite}@keyframes cur{50%{opacity:0}}")
    msg = "END OF TRANSMISSION"
    w = sf.text_width(msg, 12, "mono-500", 5)
    s.append(sf.label(msg, 500, 74, "#ffd9a8", .55, size=12, spacing=5, anchor="middle"))
    s.append(f'<rect class="cur" x="{f(500 + w / 2 + 10)}" y="63" width="7" height="13" fill="{AMBER}"/>')
    s.append("</svg>")
    return "".join(s)


def main():
    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):
        if old.name != "telemetry.svg":
            old.unlink()
    out = {"hero.svg": hero(), "intro.svg": intro(), "systems.svg": systems(), "contact.svg": contact(),
           "footer.svg": footer()}
    for i, p in enumerate(CFG["projects"]):
        out[f"project-{i + 1}.svg"] = project(i, p)
    for i, l in enumerate(CFG["links"]):
        out[f"link-{i + 1}.svg"] = link(i, l)
    for name, svg in out.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"assets/{name}  {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
