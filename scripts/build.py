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


# --------------------------------------------------------------------------- 3D pieces
def globe(cx, cy, R, color, n=260, period=28):
    """A sphere of dots turning about a tilted axis. Each dot slides sideways on an eased curve while
    its brightness follows the same curve a quarter turn later, which reads as depth."""
    half = period / 2
    css = (f".gx{{animation:gx {half}s cubic-bezier(.37,0,.63,1) infinite alternate}}"
           "@keyframes gx{from{transform:translateX(calc(var(--a) * -1))}to{transform:translateX(var(--a))}}"
           f".gz{{animation:gz {half}s cubic-bezier(.37,0,.63,1) infinite alternate}}"
           "@keyframes gz{from{opacity:.08}to{opacity:1}}")
    dots = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        yn = 1 - 2 * (i + .5) / n
        amp = R * math.sqrt(1 - yn * yn)
        theta = (i * golden) % (2 * math.pi)
        d1 = ((theta + math.pi / 2) % (2 * math.pi)) * half / math.pi
        d2 = ((theta + math.pi) % (2 * math.pi)) * half / math.pi
        dots.append(f'<g class="gx" style="--a:{f(amp)}px;animation-delay:-{d1:.2f}s"><circle class="gz" '
                    f'style="animation-delay:-{d2:.2f}s" cx="{cx}" cy="{f(cy + R * yn)}" r="{1.8 if i % 3 else 2.4}"/></g>')
    rx, ry = R * 1.45, R * .34
    back = f'M{cx - rx},{cy}A{rx},{f(ry)} 0 0 1 {cx + rx},{cy}'
    front = f'M{cx + rx},{cy}A{rx},{f(ry)} 0 0 1 {cx - rx},{cy}'
    svg = (f'<defs><radialGradient id="core"><stop offset="0" stop-color="{color}" stop-opacity=".16"/>'
           f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient></defs>'
           f'<circle cx="{cx}" cy="{cy}" r="{R * 1.25:.0f}" fill="url(#core)"/>'
           f'<g transform="rotate(-16 {cx} {cy})">'
           f'<path d="{back}" fill="none" stroke="{color}" stroke-opacity=".22" stroke-dasharray="2 7"/>'
           f'<g fill="{color}" filter="url(#halo)">{"".join(dots)}</g>'
           f'<path d="{front}" fill="none" stroke="{color}" stroke-opacity=".6" stroke-dasharray="2 7"/>'
           f'<g><circle r="9" fill="{AMBER}" opacity=".18"/><circle r="3.2" fill="{AMBER}"/>'
           f'<animateMotion dur="{period * .6:.1f}s" repeatCount="indefinite" path="{front}{back[back.index("A"):]}"/></g></g>')
    return css, svg


def solid(shape, cx, cy, R, color, period=18, samples=36):
    """A wireframe solid tumbling in 3D. The rotation is worked out here and written into the SVG as
    a looping list of positions for every edge, with brightness following depth."""
    phi = (1 + math.sqrt(5)) / 2
    if shape == "cube":
        verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    elif shape == "octahedron":
        verts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    else:
        verts = [p for a in (-1, 1) for b in (-phi, phi) for p in ((0, a, b), (a, b, 0), (b, 0, a))]
    norm = math.sqrt(sum(v * v for v in verts[0]))
    verts = [tuple(v / norm for v in p) for p in verts]
    dmin = min(math.dist(a, b) for i, a in enumerate(verts) for b in verts[i + 1:])
    edges = [(i, j) for i in range(len(verts)) for j in range(i + 1, len(verts))
             if math.dist(verts[i], verts[j]) < dmin * 1.01]
    tilt_x, tilt_z = .5, .3

    def project(p, ang):
        x, y, z = p
        x, z = x * math.cos(ang) + z * math.sin(ang), -x * math.sin(ang) + z * math.cos(ang)
        y, z = y * math.cos(tilt_x) - z * math.sin(tilt_x), y * math.sin(tilt_x) + z * math.cos(tilt_x)
        x, y = x * math.cos(tilt_z) - y * math.sin(tilt_z), x * math.sin(tilt_z) + y * math.cos(tilt_z)
        k = 1 / (1 - z * .22)
        return cx + x * R * k, cy + y * R * k, z

    frames = [[project(v, 2 * math.pi * i / samples) for v in verts] for i in range(samples + 1)]

    def anim(attr, vals):
        return f'<animate attributeName="{attr}" dur="{period}s" repeatCount="indefinite" values="{";".join(vals)}"/>'

    out = [f'<circle cx="{cx}" cy="{cy}" r="{R * 1.3:.0f}" fill="url(#glow-{shape})"/>',
           f'<g stroke="{color}" stroke-width="1.5" stroke-linecap="round" filter="url(#halo)">']
    for a, b in edges:
        seq = lambda idx, comp: [f(fr[idx][comp]) for fr in frames]
        depth = [f"{.18 + .82 * (fr[a][2] + fr[b][2] + 2) / 4:.2f}" for fr in frames]
        out.append('<line>' + anim("x1", seq(a, 0)) + anim("y1", seq(a, 1)) + anim("x2", seq(b, 0))
                   + anim("y2", seq(b, 1)) + anim("stroke-opacity", depth) + "</line>")
    for i in range(len(verts)):                          # small vertex points
        out.append(f'<circle r="1.9" fill="{color}" stroke="none">'
                   + anim("cx", [f(fr[i][0]) for fr in frames]) + anim("cy", [f(fr[i][1]) for fr in frames])
                   + anim("opacity", [f"{.25 + .75 * (fr[i][2] + 1) / 2:.2f}" for fr in frames]) + "</circle>")
    out.append("</g>")
    defs = (f'<radialGradient id="glow-{shape}"><stop offset="0" stop-color="{color}" stop-opacity=".13"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
    return defs, "".join(out)


# --------------------------------------------------------------------------- shared slice shell
def shell(name, label, extra_css="", defs=""):
    _, h = sf.OFFSET[name]
    css = sf.PARTICLE_CSS + sf.BEAM_CSS + extra_css
    return [svg_open(W, h, label, css), sf.backdrop(name), f"<defs>{sf.GLOW}{defs}</defs>", sf.particles(name)], h


def heading_slice(name, index, title):
    s, h = shell(name, title)
    s.append(sf.neon_heading(index, title, y=118))
    s.append("</svg>")
    return "".join(s)


def body_line(parts, x, y, size):
    out = []
    for chunk, strong in parts:
        face, attrs = ("inter-600", f'fill="{sf.INK}"') if strong else ("inter-400", f'fill="{sf.BODY}"')
        svg, w = sf.text(chunk, x, y, size, face, attrs=attrs)
        out.append(svg)
        x += w
    return "".join(out)


# --------------------------------------------------------------------------- about
def about():
    css, ball = globe(780, 300, 148, sf.ICE)
    plain = " ".join("".join(t for t, _ in line) for line in CFG["about"])
    s, h = shell("about", "About. " + plain + " " + ". ".join(f"{k}: {v}" for k, v in CFG["facts"]), css)
    s.append(sf.neon_heading(1, "ABOUT"))
    y = 206
    for line in CFG["about"]:
        s.append(body_line(line, 60, y, 23))
        y += 37
    y = 392
    for key, value in CFG["facts"]:
        s.append(f'<rect x="60" y="{y - 22}" width="1.5" height="30" fill="#fff" fill-opacity=".35"/>')
        s.append(sf.label(key, 76, y - 9, sf.DIM, 1, size=11))
        s.append(sf.text(value, 76, y + 13, 17, "inter-400", attrs=f'fill="{sf.INK}"')[0])
        y += 52
    s.append(ball)
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- what I do
FOCUS_COLORS = [sf.EMBER, sf.ROSE, sf.MOSS]


def focus():
    pieces = [solid(p["shape"], 190 + i * 310, 262, 72, FOCUS_COLORS[i], period=16 + i * 5)
              for i, p in enumerate(CFG["focus"])]
    s, h = shell("focus", "What I do. " + ". ".join(f'{p["title"]}: {" ".join(p["lines"])}' for p in CFG["focus"]),
                 defs="".join(d for d, _ in pieces))
    s.append(sf.neon_heading(2, "WHAT I DO"))
    for i, (p, (_, svg)) in enumerate(zip(CFG["focus"], pieces)):
        cx = 190 + i * 310
        s.append(svg)
        s.append(sf.text(p["title"], cx, 386, 22, "inter-600", anchor="middle", attrs=f'fill="{sf.INK}"')[0])
        for j, line in enumerate(p["lines"]):
            s.append(sf.text(line, cx, 416 + j * 23, 16, "inter-400", anchor="middle", attrs=f'fill="{sf.BODY}"')[0])
        s.append(sf.label(p["tags"], cx, 478, sf.DIM, 1, size=11, spacing=1.5, anchor="middle"))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- journey
def journey():
    css = (".pulse{animation:pulse 7s cubic-bezier(.4,0,.2,1) infinite}"
           "@keyframes pulse{0%{transform:translateX(0);opacity:0}8%{opacity:1}92%{opacity:1}100%{transform:translateX(760px);opacity:0}}"
           ".ring{transform-box:fill-box;transform-origin:center;animation:ring 3.5s ease-out infinite}"
           "@keyframes ring{from{transform:scale(.4);opacity:.6}to{transform:scale(2.4);opacity:0}}")
    nodes = CFG["journey"]
    s, h = shell("journey", "Journey. " + ". ".join(f'{n["when"]}: {n["title"]}, {n["sub"]}' for n in nodes), css)
    s.append(sf.neon_heading(3, "JOURNEY"))
    line_y, xs = 236, [120, 500, 880]
    s.append(f'<rect x="120" y="{line_y - .5}" width="760" height="1" fill="#fff" fill-opacity=".18"/>')
    s.append(f'<g class="pulse"><circle cx="120" cy="{line_y}" r="10" fill="#fff" opacity=".1"/>'
             f'<circle cx="120" cy="{line_y}" r="2.6" fill="#fff"/></g>')
    for i, (n, x) in enumerate(zip(nodes, xs)):
        anchor = ("start", "middle", "end")[i]
        s.append(f'<circle class="ring" style="animation-delay:-{i * 1.1:.1f}s" cx="{x}" cy="{line_y}" r="8" fill="none" stroke="#fff"/>')
        s.append(f'<circle cx="{x}" cy="{line_y}" r="4" fill="{sf.INK}"/>')
        s.append(sf.text(n["when"], x, line_y - 26, 26, "inter-800", anchor=anchor, attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.text(n["title"], x, line_y + 40, 19, "inter-600", anchor=anchor, attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.text(n["sub"], x, line_y + 65, 15, "inter-400", anchor=anchor, attrs=f'fill="{sf.BODY}"')[0])
    s.append(sf.label("CERTIFIED", 120, 352, sf.DIM, 1, size=11))
    s.append(sf.text("   ·   ".join(CFG["certifications"]), 220, 353, 15, "inter-400", attrs=f'fill="{sf.BODY}"')[0])
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- project row
def project(i, p):
    name = f"p{i}"
    s, h = shell(name, f'{p["name"]}: {p["description"]}', f".beam{{animation-delay:{i * 1.6:.1f}s}}")
    s.append(sf.label(f"{i + 1:02d}", 61, 56, sf.DIM, 1, size=13))
    s.append(sf.text(p["name"], 112, 58, 34, "inter-600", attrs=f'fill="{sf.INK}"')[0])
    s.append(sf.text(p["description"], 112, 90, 17, "inter-400", attrs=f'fill="{sf.BODY}"')[0])
    s.append(sf.label(p["tags"].upper(), 900, 53, sf.DIM, 1, size=11, spacing=1.5, anchor="end"))
    s.append(sf.arrow(940, 38, sf.INK))
    s.append(sf.hairline(h - 1))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- contact rows + footer
def link(i, l):
    name = f"l{i}"
    s, h = shell(name, f'{l["label"]}: {l["detail"]}', f".beam{{animation-delay:{i * 1.6:.1f}s}}")
    s.append(sf.text(l["label"], 60, 52, 28, "inter-600", attrs=f'fill="{sf.INK}"')[0])
    s.append(sf.label(l["detail"], 900, 49, sf.BODY, 1, size=13, spacing=1, anchor="end"))
    s.append(sf.arrow(940, 30, sf.INK))
    s.append(sf.hairline(h - 1))
    s.append("</svg>")
    return "".join(s)


def footer():
    s, h = shell("footer", "End of transmission", ".cur{animation:cur 1.1s steps(1) infinite}@keyframes cur{50%{opacity:0}}")
    msg = "END OF TRANSMISSION"
    w = sf.text_width(msg, 12, "mono-500", 5)
    s.append(sf.label(msg, 500, 74, sf.DIM, 1, size=12, spacing=5, anchor="middle"))
    s.append(f'<rect class="cur" x="{f(500 + w / 2 + 10)}" y="63" width="7" height="13" fill="{sf.INK}"/>')
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- README
def readme():
    img = '<img align="top" width="100%" src="assets/{}" alt="{}" />'
    rows = [f'<a href="{CFG["links"][0]["url"]}">' + img.format("hero.svg", f'{CFG["name"]} — AI Engineer, LLM Systems, Full Stack') + "</a>",
            img.format("about.svg", "About: " + " ".join("".join(t for t, _ in line) for line in CFG["about"])
                       + " " + ". ".join(f"{k}: {v}" for k, v in CFG["facts"]) + "."),
            img.format("focus.svg", "What I do: " + ". ".join(f'{p["title"]}: {" ".join(p["lines"])}' for p in CFG["focus"]) + "."),
            img.format("journey.svg", "Journey: " + ". ".join(f'{n["when"]}: {n["title"]}, {n["sub"]}' for n in CFG["journey"])
                       + ". Certifications: " + ", ".join(CFG["certifications"]) + "."),
            img.format("projects.svg", "Projects")]
    for i, p in enumerate(CFG["projects"]):
        rows.append(f'<a href="{p["url"]}">' + img.format(f"project-{i + 1}.svg", f'{p["name"]}: {p["description"]}') + "</a>")
    rows.append(img.format("telemetry.svg", "Telemetry: contributions over the last 12 months, updated daily"))
    rows.append(img.format("contact.svg", "Contact"))
    for i, l in enumerate(CFG["links"]):
        rows.append(f'<a href="{l["url"]}">' + img.format(f"link-{i + 1}.svg", l["label"]) + "</a>")
    rows.append(img.format("footer.svg", ""))
    # one paragraph, no whitespace between tags: the slices stack into a single canvas
    return "<p>" + "".join(rows) + "</p>\n"


def main():
    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):
        if old.name != "telemetry.svg":
            old.unlink()
    out = {"hero.svg": hero(), "about.svg": about(), "focus.svg": focus(), "journey.svg": journey(),
           "projects.svg": heading_slice("projects", 4, "PROJECTS"),
           "contact.svg": heading_slice("contact", 6, "CONTACT"), "footer.svg": footer()}
    for i, p in enumerate(CFG["projects"]):
        out[f"project-{i + 1}.svg"] = project(i, p)
    for i, l in enumerate(CFG["links"]):
        out[f"link-{i + 1}.svg"] = link(i, l)
    for name, svg in out.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"assets/{name}  {len(svg) // 1024} KB")
    (ROOT / "README.md").write_text(readme(), encoding="utf-8")


if __name__ == "__main__":
    main()
