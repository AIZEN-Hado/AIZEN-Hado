"""The profile as two tall, live SVGs (above and below the coder GIF).

GitHub can't layer a background behind several images, so each canvas draws everything itself: one starfield and one stream of rising particles run behind every section, and each
section adds a 3D object (the only colour on the page).

How the 3D works without JavaScript:
  * Turning bodies (globe, helix, wave field): a point on a circle seen side-on moves
    sinusoidally. Each point slides with an eased back-and-forth CSS animation, and its
    brightness follows the same curve a quarter turn later, which reads as depth.
  * Rigid wireframes: the rotation is computed here and written into SMIL value lists for every
    edge, so the browser only interpolates.
  * Nothing animated sits under an SVG filter; glows are static gradients (filters force a full
    repaint every frame).
"""
import datetime
import math
import random

import sf
from sf import AMBER, W, f

EASE = "cubic-bezier(.37,0,.63,1)"   # close to a sine half-wave


def phase_delays(theta, half):
    """Animation delays that put a back-and-forth (period 2*half) at angle theta, plus the delay
    for its depth curve a quarter turn later."""
    d_pos = ((theta + math.pi / 2) % (2 * math.pi)) * half / math.pi
    d_depth = ((theta + math.pi) % (2 * math.pi)) * half / math.pi
    return d_pos, d_depth


# =============================================================================== layout
def layout(part):
    sections = {"top": [("hero", 480), ("about", 560), ("focus", 520), ("journey", 470)],
                "bottom": [("stack", 700), ("telemetry", 900), ("contact", 440)]}[part]
    out, y = {}, 0
    for name, h in sections:
        out[name] = (y, h)
        y += h
    return out, y


# =============================================================================== background
CSS_BG = (
    ".bt{animation:bt ease-in-out infinite}@keyframes bt{50%{opacity:.06}}"
    ".rz{animation:rz linear infinite}@keyframes rz{to{transform:translateY(var(--l))}}"
    ".sw{animation:sw ease-in-out infinite alternate}@keyframes sw{to{transform:translateX(var(--s))}}"
    ".ss{animation:ss linear infinite}"
    "@keyframes ss{0%{transform:translate(0,0);opacity:0}1.2%{opacity:1}5.5%{transform:translate(var(--sx),var(--sy));opacity:0}"
    "100%{transform:translate(var(--sx),var(--sy));opacity:0}}"
)


def background(top, total):
    rng = random.Random("canvas-background")
    h = total - top
    s = [f'<rect width="{W}" height="{total}" fill="{sf.PAGE}"/>', '<g fill="#fff">']
    for i in range(round(W * h / 6800)):                          # still stars
        x, y = rng.uniform(0, W), rng.uniform(top, total)
        r = rng.choice([.5, .5, .6, .7, .8, 1.1])
        tw = (f' class="bt" style="animation-duration:{f(rng.uniform(4, 9))}s;animation-delay:-{f(rng.uniform(0, 9))}s"'
              if i % 6 == 0 else "")
        s.append(f'<circle{tw} cx="{f(x)}" cy="{f(y)}" r="{r}" opacity="{rng.uniform(.1, .55):.2f}"/>')
    # three depths of particles rising through the whole page, swaying as they go
    travel = -(h + 40)
    for count, radius, dur, op, halo in ((80, .6, 150, .35, False), (44, 1.0, 95, .55, False), (16, 1.6, 62, .8, True)):
        for _ in range(count):
            x = rng.uniform(10, W - 10)
            d = rng.uniform(0, dur)
            dot = f'<circle cx="{f(x)}" cy="{total + 20}" r="{radius}" opacity="{op}"/>'
            if halo:
                dot = f'<circle cx="{f(x)}" cy="{total + 20}" r="{radius * 3.4:.1f}" opacity=".06"/>' + dot
            s.append(f'<g class="rz" style="--l:{travel}px;animation-duration:{dur}s;animation-delay:-{f(d)}s">'
                     f'<g class="sw" style="--s:{f(rng.uniform(-28, 28))}px;animation-duration:{f(rng.uniform(6, 14))}s;'
                     f'animation-delay:-{f(rng.uniform(0, 14))}s">{dot}</g></g>')
    s.append("</g>")
    s.append('<defs><linearGradient id="c-sst" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient></defs><g fill="#fff">')
    for k in range(6):                                            # shooting stars
        x, y = rng.uniform(60, 620), top + (k + rng.uniform(.1, .7)) * h / 6
        dist, ang = rng.uniform(240, 380), math.radians(rng.uniform(12, 26))
        dur = rng.uniform(13, 22)
        s.append(f'<g class="ss" style="--sx:{f(dist * math.cos(ang))}px;--sy:{f(dist * math.sin(ang))}px;'
                 f'animation-duration:{f(dur)}s;animation-delay:-{f(rng.uniform(0, dur))}s">'
                 f'<g transform="translate({f(x)} {f(y)}) rotate({f(math.degrees(ang))})">'
                 f'<rect x="-80" y="-.6" width="80" height="1.2" fill="url(#c-sst)"/><circle r="1.3"/></g></g>')
    s.append("</g>")
    return "".join(s)


# =============================================================================== shared bits
def heading(index, title, y):
    return sf.neon_heading(index, title, y=y)


def body_line(parts, x, y, size):
    out = []
    for chunk, strong in parts:
        face, attrs = ("inter-600", f'fill="{sf.INK}"') if strong else ("inter-400", f'fill="{sf.BODY}"')
        svg, w = sf.text(chunk, x, y, size, face, attrs=attrs)
        out.append(svg)
        x += w
    return "".join(out)


def glow(uid, cx, cy, r, color, op=.14):
    return (f'<defs><radialGradient id="c-gl-{uid}"><stop offset="0" stop-color="{color}" stop-opacity="{op}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="url(#c-gl-{uid})"/>')


CSS_TURN = (f".gx{{animation:gx {EASE} infinite alternate}}"
            "@keyframes gx{from{transform:translateX(calc(var(--a) * -1))}to{transform:translateX(var(--a))}}"
            f".gy{{animation:gy {EASE} infinite alternate}}"
            "@keyframes gy{from{transform:translateY(calc(var(--a) * -1))}to{transform:translateY(var(--a))}}"
            f".gz{{animation:gz {EASE} infinite alternate}}@keyframes gz{{from{{opacity:var(--lo)}}to{{opacity:var(--hi)}}}}")


# =============================================================================== 3D: globe
def globe(cx, cy, R, color, n=300, period=30):
    half = period / 2
    golden = math.pi * (3 - math.sqrt(5))
    dots = []
    for i in range(n):
        yn = 1 - 2 * (i + .5) / n
        amp = R * math.sqrt(1 - yn * yn)
        d1, d2 = phase_delays((i * golden) % (2 * math.pi), half)
        dots.append(f'<g class="gx" style="--a:{f(amp)}px;animation-duration:{half}s;animation-delay:-{d1:.2f}s">'
                    f'<circle class="gz" style="--lo:.07;--hi:1;animation-duration:{half}s;animation-delay:-{d2:.2f}s" '
                    f'cx="{cx}" cy="{f(cy + R * yn)}" r="{1.7 if i % 3 else 2.3}"/></g>')
    # three latitude rings drawn as dashed ellipses for structure
    rx, ry = R * 1.48, R * .34
    back = f'M{cx - rx},{cy}A{rx},{f(ry)} 0 0 1 {cx + rx},{cy}'
    front = f'M{cx + rx},{cy}A{rx},{f(ry)} 0 0 1 {cx - rx},{cy}'
    return (glow("globe", cx, cy, R * 1.35, color, .17)
            + f'<g transform="rotate(-16 {cx} {cy})">'
            f'<path d="{back}" fill="none" stroke="{color}" stroke-opacity=".2" stroke-dasharray="2 7"/>'
            f'<g fill="{color}">{"".join(dots)}</g>'
            f'<path d="{front}" fill="none" stroke="{color}" stroke-opacity=".6" stroke-dasharray="2 7"/>'
            f'<g><circle r="9" fill="{AMBER}" opacity=".18"/><circle r="3.2" fill="{AMBER}"/>'
            f'<animateMotion dur="{period * .6:.1f}s" repeatCount="indefinite" path="{front}{back[back.index("A"):]}"/></g></g>')


# =============================================================================== 3D: wireframes
def polyhedron(shape):
    phi = (1 + math.sqrt(5)) / 2
    verts = {
        "cube": [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)],
        "octahedron": [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
        "tetrahedron": [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)],
        "icosahedron": [p for a in (-1, 1) for b in (-phi, phi) for p in ((0, a, b), (a, b, 0), (b, 0, a))],
    }[shape]
    norm = math.sqrt(sum(v * v for v in verts[0]))
    verts = [tuple(v / norm for v in p) for p in verts]
    dmin = min(math.dist(a, b) for i, a in enumerate(verts) for b in verts[i + 1:])
    edges = [(i, j) for i in range(len(verts)) for j in range(i + 1, len(verts))
             if math.dist(verts[i], verts[j]) < dmin * 1.01]
    return verts, edges


def solid(shape, cx, cy, R, color, period=18, samples=36, width=1.5, tilt=(.5, .3), uid=None):
    verts, edges = polyhedron(shape)
    tx, tz = tilt

    def project(p, ang):
        x, y, z = p
        x, z = x * math.cos(ang) + z * math.sin(ang), -x * math.sin(ang) + z * math.cos(ang)
        y, z = y * math.cos(tx) - z * math.sin(tx), y * math.sin(tx) + z * math.cos(tx)
        x, y = x * math.cos(tz) - y * math.sin(tz), x * math.sin(tz) + y * math.cos(tz)
        k = 1 / (1 - z * .22)
        return cx + x * R * k, cy + y * R * k, z

    frames = [[project(v, 2 * math.pi * i / samples) for v in verts] for i in range(samples + 1)]

    def anim(attr, vals):
        return f'<animate attributeName="{attr}" dur="{period}s" repeatCount="indefinite" values="{";".join(vals)}"/>'

    out = [glow(uid or shape, cx, cy, R * 1.4, color, .15),
           f'<g stroke="{color}" stroke-width="{width}" stroke-linecap="round">']
    for a, b in edges:
        out.append("<line>" + anim("x1", [f(fr[a][0]) for fr in frames]) + anim("y1", [f(fr[a][1]) for fr in frames])
                   + anim("x2", [f(fr[b][0]) for fr in frames]) + anim("y2", [f(fr[b][1]) for fr in frames])
                   + anim("stroke-opacity", [f"{.16 + .84 * (fr[a][2] + fr[b][2] + 2) / 4:.2f}" for fr in frames]) + "</line>")
    out.append("</g>")
    for i in range(len(verts)):
        out.append(f'<circle r="{width + .5:.1f}" fill="{color}">'
                   + anim("cx", [f(fr[i][0]) for fr in frames]) + anim("cy", [f(fr[i][1]) for fr in frames])
                   + anim("opacity", [f"{.2 + .8 * (fr[i][2] + 1) / 2:.2f}" for fr in frames]) + "</circle>")
    return "".join(out)


# =============================================================================== 3D: helix
def helix(x0, x1, cy, A, color, n=70, turns=3.2, period=12):
    """Two strands twisting around the timeline axis."""
    half = period / 2
    out = []
    for strand in (0, 1):
        out.append(f'<g fill="{color[strand]}">')
        for i in range(n):
            u = i / (n - 1)
            x = x0 + (x1 - x0) * u
            theta = 2 * math.pi * turns * u + strand * math.pi
            d1, d2 = phase_delays(theta, half)
            edge = min(u, 1 - u) * 12
            fade = min(1, edge)
            out.append(f'<g class="gy" style="--a:{A}px;animation-duration:{half}s;animation-delay:-{d1:.2f}s">'
                       f'<circle class="gz" style="--lo:{.06 * fade:.2f};--hi:{.95 * fade:.2f};animation-duration:{half}s;'
                       f'animation-delay:-{d2:.2f}s" cx="{f(x)}" cy="{cy}" r="{2.2 if i % 2 else 1.6}"/></g>')
        out.append("</g>")
    return "".join(out)


# =============================================================================== 3D: wave field
def wave_field(top, bottom, color_near, color_far, cols=92, rows=19, period=7, zmin=1.6, zmax=7.0):
    """A perspective grid of particles (an ocean) with a travelling wave running toward the viewer.
    World points sit on a flat plane; a pinhole camera projects them, so spacing, size and wave
    height all shrink with distance."""
    half = period / 2
    out = []
    span = (bottom + 40 - top) / (1 / zmin - 1 / zmax)
    for r in range(rows):                                         # far rows first
        z = zmax - (zmax - zmin) * r / (rows - 1)
        t = (z - zmin) / (zmax - zmin)                            # 0 near, 1 far
        y = top + span * (1 / z - 1 / zmax)
        col = "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in zip(sf._rgb(color_near), sf._rgb(color_far)))
        amp = 40 / z
        op = .92 * (1 - t) ** 1.25 + .12
        rad = .45 + 3.4 / z
        for c in range(cols):
            X = -7 + 14 * c / (cols - 1)
            x = 500 + X * 520 / z
            if x < -8 or x > W + 8:
                continue
            d1, _ = phase_delays(X * 1.25 + z * 2.3, half)
            out.append(f'<g class="gy" style="--a:{f(amp)}px;animation-duration:{half}s;animation-delay:-{d1:.2f}s">'
                       f'<circle cx="{f(x)}" cy="{f(y)}" r="{rad:.1f}" fill="{col}" opacity="{op:.2f}"/></g>')
    return "".join(out)


# =============================================================================== sections
def about(cfg, y0):
    s = [f'<g transform="translate(0 {y0})">', heading(1, "ABOUT", 132)]
    y = 206
    for line in cfg["about"]:
        s.append(body_line(line, 60, y, 23))
        y += 37
    y = 392
    for key, value in cfg["facts"]:
        s.append(f'<rect x="60" y="{y - 22}" width="1.5" height="30" fill="#fff" fill-opacity=".35"/>')
        s.append(sf.label(key, 76, y - 9, sf.DIM, 1, size=11))
        s.append(sf.text(value, 76, y + 13, 17, "inter-400", attrs=f'fill="{sf.INK}"')[0])
        y += 52
    s.append(globe(780, 300, 150, sf.SKY))
    s.append("</g>")
    return "".join(s)


FOCUS_COLORS = [sf.YELLOW, sf.PINK, sf.AQUA]


def focus(cfg, y0):
    s = [f'<g transform="translate(0 {y0})">', heading(2, "WHAT I DO", 132)]
    for i, p in enumerate(cfg["focus"]):
        cx = 190 + i * 310
        s.append(solid(p["shape"], cx, 262, 72, FOCUS_COLORS[i], period=16 + i * 5, uid=f"focus{i}"))
        s.append(sf.text(p["title"], cx, 386, 22, "inter-600", anchor="middle", attrs=f'fill="{sf.INK}"')[0])
        for j, line in enumerate(p["lines"]):
            s.append(sf.text(line, cx, 416 + j * 23, 16, "inter-400", anchor="middle", attrs=f'fill="{sf.BODY}"')[0])
        s.append(sf.label(p["tags"], cx, 478, sf.DIM, 1, size=11, spacing=1.5, anchor="middle"))
    s.append("</g>")
    return "".join(s)


CSS_JOURNEY = (".ring{transform-box:fill-box;transform-origin:center;animation:ring 3.5s ease-out infinite}"
               "@keyframes ring{from{transform:scale(.4);opacity:.6}to{transform:scale(2.6);opacity:0}}")


def journey(cfg, y0):
    s = [f'<g transform="translate(0 {y0})">', heading(3, "JOURNEY", 132)]
    line_y, xs = 268, [120, 500, 880]
    s.append(glow("journey", 500, line_y, 420, sf.VIOLET, .07))
    s.append(f'<rect x="120" y="{line_y - .5}" width="760" height="1" fill="#fff" fill-opacity=".14"/>')
    s.append(helix(100, 900, line_y, 30, (sf.VIOLET, sf.PINK)))
    for i, (n, x) in enumerate(zip(cfg["journey"], xs)):
        anchor = ("start", "middle", "end")[i]
        s.append(f'<circle class="ring" style="animation-delay:-{i * 1.1:.1f}s" cx="{x}" cy="{line_y}" r="8" fill="none" stroke="#fff"/>')
        s.append(f'<circle cx="{x}" cy="{line_y}" r="5" fill="{sf.PAGE}" stroke="{sf.INK}" stroke-width="2"/>')
        s.append(sf.text(n["when"], x, line_y - 54, 26, "inter-800", anchor=anchor, attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.text(n["title"], x, line_y + 72, 19, "inter-600", anchor=anchor, attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.text(n["sub"], x, line_y + 97, 15, "inter-400", anchor=anchor, attrs=f'fill="{sf.BODY}"')[0])
    s.append(sf.label("CERTIFIED", 120, 418, sf.DIM, 1, size=11))
    s.append(sf.text("   ·   ".join(cfg["certifications"]), 220, 419, 15, "inter-400", attrs=f'fill="{sf.BODY}"')[0])
    s.append("</g>")
    return "".join(s)


# =============================================================================== stack: a turning sphere of names
GROUP_GLYPHS = ["diamond", "hexagon", "triangle", "square", "ring", "cross", "spark"]


def glyph(kind, x, y, r, color, width=1.4):
    """Small category symbol centred on (x, y)."""
    st = f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'
    if kind == "diamond":
        return f'<path d="M{f(x)},{f(y - r)}L{f(x + r)},{f(y)}L{f(x)},{f(y + r)}L{f(x - r)},{f(y)}Z" {st}/>'
    if kind == "hexagon":
        pts = " ".join(f"{f(x + r * math.cos(math.radians(60 * k + 30)))},{f(y + r * math.sin(math.radians(60 * k + 30)))}" for k in range(6))
        return f'<polygon points="{pts}" {st}/>'
    if kind == "triangle":
        return f'<path d="M{f(x)},{f(y - r)}L{f(x + r * .95)},{f(y + r * .7)}L{f(x - r * .95)},{f(y + r * .7)}Z" {st}/>'
    if kind == "square":
        return f'<rect x="{f(x - r * .8)}" y="{f(y - r * .8)}" width="{f(r * 1.6)}" height="{f(r * 1.6)}" {st}/>'
    if kind == "ring":
        return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r * .85)}" {st}/><circle cx="{f(x)}" cy="{f(y)}" r="{f(r * .25)}" fill="{color}"/>'
    if kind == "cross":
        return f'<path d="M{f(x - r)},{f(y)}H{f(x + r)}M{f(x)},{f(y - r)}V{f(y + r)}" {st}/>'
    return (f'<path d="M{f(x)},{f(y - r)}Q{f(x + r * .2)},{f(y - r * .2)} {f(x + r)},{f(y)}Q{f(x + r * .2)},{f(y + r * .2)} {f(x)},{f(y + r)}'
            f'Q{f(x - r * .2)},{f(y + r * .2)} {f(x - r)},{f(y)}Q{f(x - r * .2)},{f(y - r * .2)} {f(x)},{f(y - r)}Z" fill="{color}"/>')


CSS_STACK = (".sd{transform-box:fill-box;transform-origin:center;animation:sd " + EASE + " infinite alternate}"
             "@keyframes sd{from{opacity:.12;transform:scale(.62)}to{opacity:1;transform:scale(1.12)}}"
             ".spin{transform-box:fill-box;transform-origin:center;animation:spin linear infinite}@keyframes spin{to{transform:rotate(360deg)}}")


def stack(cfg, y0):
    """Every tool in the stack orbits on a turning sphere, coloured and marked by group; a readable
    index of the same list sits beside it."""
    groups = cfg["stack"]
    s = [f'<g transform="translate(0 {y0})">', heading(4, "STACK", 132)]
    # index
    y = 200
    for k, g in enumerate(groups):
        color = getattr(sf, g["color"])
        s.append(glyph(GROUP_GLYPHS[k], 68, y - 4, 6, color))
        s.append(sf.label(g["group"], 86, y, color, 1, size=11, spacing=2))
        s.append(sf.label(f'{len(g["items"]):02d}', 330, y, sf.DIM, 1, size=11, spacing=1, anchor="end"))
        s.append(sf.text("  ·  ".join(n for _, n in g["items"]), 86, y + 22, 13.5, "inter-400", attrs=f'fill="{sf.BODY}"')[0])
        y += 64
    # sphere
    cx, cy, R, period = 650, 400, 220, 34
    half = period / 2
    s.append(glow("stack", cx, cy, R * 1.25, sf.VIOLET, .12))
    s.append(f'<g fill="none" stroke="#fff">'
             f'<circle cx="{cx}" cy="{cy}" r="{R + 30}" stroke-opacity=".07"/>'
             f'<circle class="spin" style="animation-duration:90s" cx="{cx}" cy="{cy}" r="{R + 42}" stroke-opacity=".22" stroke-dasharray="1 9"/>'
             f'<circle class="spin" style="animation-duration:140s;animation-direction:reverse" cx="{cx}" cy="{cy}" r="{R + 52}" stroke-opacity=".12" stroke-dasharray="30 60 4 60"/>')
    for k in range(-2, 3):                                        # latitude lines
        yy = cy + R * .78 * k / 3
        rx = R * math.sqrt(1 - (k / 3) ** 2)
        s.append(f'<ellipse cx="{cx}" cy="{f(yy)}" rx="{f(rx)}" ry="{f(rx * .16)}" stroke-opacity=".08" stroke-dasharray="2 6"/>')
    ticks = "".join(f"M{f(cx + (R + 30) * math.cos(math.radians(a)))},{f(cy + (R + 30) * math.sin(math.radians(a)))}"
                    f"L{f(cx + (R + 38) * math.cos(math.radians(a)))},{f(cy + (R + 38) * math.sin(math.radians(a)))}" for a in range(0, 360, 15))
    s.append(f'<path d="{ticks}" stroke-opacity=".25"/></g>')
    items = [(n, getattr(sf, g["color"]), GROUP_GLYPHS[k]) for k, g in enumerate(groups) for _, n in g["items"]]
    golden = math.pi * (3 - math.sqrt(5))
    n = len(items)
    for i, (name, color, kind) in enumerate(items):
        yn = 1 - 2 * (i + .5) / n
        amp = R * math.sqrt(1 - yn * yn)
        d1, d2 = phase_delays((i * golden * 1.0) % (2 * math.pi), half)
        label, w = sf.text(name, 0, 0, 17, "inter-600", attrs=f'fill="{color}"')
        x0 = cx - (w + 16) / 2
        yy = cy + R * .82 * yn
        s.append(f'<g class="gx" style="--a:{f(amp)}px;animation-duration:{half}s;animation-delay:-{d1:.2f}s">'
                 f'<g class="sd" style="animation-duration:{half}s;animation-delay:-{d2:.2f}s">'
                 + glyph(kind, x0 + 5, yy - 6, 5, color, 1.3)
                 + f'<g transform="translate({f(x0 + 16)} {f(yy)})">{label}</g></g></g>')
    s.append("</g>")
    return "".join(s)


# =============================================================================== telemetry: a HUD
CSS_TELE = (".wk{animation:wk 9s ease-in-out infinite}@keyframes wk{0%,14%,100%{opacity:.55}7%{opacity:1}}"
            ".now{animation:now 2s ease-in-out infinite}@keyframes now{50%{opacity:.3}}"
            ".lit{animation:lit 1.6s steps(1) infinite}@keyframes lit{50%{opacity:.2}}"
            ".draw{stroke-dasharray:1;animation:draw 9s ease-in-out infinite}"
            "@keyframes draw{0%{stroke-dashoffset:1}45%,90%{stroke-dashoffset:0}100%{stroke-dashoffset:-1}}")


def brackets(x, y, w, h, color, k=10, op=.8):
    d = (f"M{x},{y + k}V{y}H{x + k}M{x + w - k},{y}H{x + w}V{y + k}M{x + w},{y + h - k}V{y + h}H{x + w - k}"
         f"M{x + k},{y + h}H{x}V{y + h - k}")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="1.4"/>'


def streaks(days):
    counts = [c for _, c, _ in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur = 0
    seq = counts[:-1] if counts and counts[-1] == 0 else counts
    for c in reversed(seq):
        if not c:
            break
        cur += 1
    return cur, longest


def smooth(points, floor=None):
    """Catmull-Rom through the points, as cubic Bezier segments (control points kept above `floor`)."""
    d = f"M{f(points[0][0])},{f(points[0][1])}"
    for i in range(len(points) - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        if floor is not None:
            c1 = (c1[0], min(c1[1], floor))
            c2 = (c2[0], min(c2[1], floor))
            if p1[1] >= floor - .5 or p2[1] >= floor - .5:      # flat runs stay on the floor
                c1 = (c1[0], max(c1[1], min(p1[1], p2[1])))
                c2 = (c2[0], max(c2[1], min(p1[1], p2[1])))
        d += f"C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d


def telemetry(data, y0):
    live = data["total"] is not None
    days = data["days"]
    cur, longest = streaks(days) if live else (None, None)
    s = [f'<g transform="translate(0 {y0})">', heading(5, "TELEMETRY", 132)]
    s.append(sf.label("LIVE · UPDATED DAILY" if live else "AWAITING FIRST SYNC", 940, 104, sf.DIM, 1, size=10, spacing=2, anchor="end"))
    s.append(f'<circle class="lit" cx="{f(940 - sf.text_width("LIVE · UPDATED DAILY" if live else "AWAITING FIRST SYNC", 10, "mono-500", 2) - 12)}" cy="100" r="3" fill="{sf.AQUA}"/>')

    # ---- readouts
    cells = [("CONTRIBUTIONS", data["total"], "LAST 12 MONTHS", sf.AQUA), ("COMMITS", data.get("commits"), "THIS YEAR", sf.SKY),
             ("PULL REQUESTS", data.get("prs"), "THIS YEAR", sf.VIOLET), ("STARS", data.get("stars"), "ON PUBLIC REPOS", sf.PINK),
             ("CURRENT STREAK", cur, "DAYS", sf.YELLOW), ("LONGEST STREAK", longest, "DAYS", sf.ORANGE)]
    cw, gap, top = 140, 8, 176
    for i, (label, value, sub, color) in enumerate(cells):
        x = 60 + i * (cw + gap)
        s.append(f'<rect x="{x}" y="{top}" width="{cw}" height="104" fill="{color}" fill-opacity=".04"/>')
        s.append(brackets(x, top, cw, 104, color))
        s.append(sf.label(label, x + 14, top + 24, color, .95, size=9.5, spacing=1.5))
        s.append(sf.text(f"{value:,}" if value is not None else "--", x + 14, top + 70, 36, "inter-800", attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.label(sub, x + 14, top + 91, sf.DIM, 1, size=9, spacing=1.5))
        s.append(f'<rect class="lit" style="animation-delay:-{i * .27:.2f}s" x="{x + cw - 16}" y="{top + 16}" width="4" height="4" fill="{color}"/>')

    # ---- activity: last 60 days
    gx0, gx1, gy0, gy1 = 60, 940, 330, 520
    s.append(sf.label("ACTIVITY · LAST 60 DAYS", gx0, gy0 - 8, sf.BODY, 1, size=10, spacing=2))
    recent = days[-60:]
    vals = [c for _, c, _ in recent]
    peak = max(vals + [1])
    top_y = gy0 + 26
    pts = [(gx0 + (gx1 - gx0) * i / (len(vals) - 1), gy1 - (gy1 - top_y) * v / peak) for i, v in enumerate(vals)]
    grid = "".join(f"M{gx0},{f(gy1 - (gy1 - top_y) * k / 4)}H{gx1}" for k in range(5))
    s.append(f'<path d="{grid}" stroke="#fff" stroke-opacity=".07" stroke-dasharray="2 5" fill="none"/>')
    for i, (date, _, _) in enumerate(recent):
        dt = datetime.date.fromisoformat(date)
        if dt.day == 1 or i in (0, len(recent) - 1):
            x = pts[i][0]
            s.append(f'<rect x="{f(x - .5)}" y="{gy1}" width="1" height="6" fill="#fff" fill-opacity=".3"/>')
            s.append(sf.label(dt.strftime("%b %d").upper(), x, gy1 + 22, sf.DIM, 1, size=9.5, spacing=1,
                              anchor="start" if i == 0 else "end" if i == len(recent) - 1 else "middle"))
    line = smooth(pts, gy1)
    s.append('<defs><linearGradient id="c-area" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{sf.AQUA}" stop-opacity=".28"/><stop offset="1" stop-color="{sf.AQUA}" stop-opacity="0"/></linearGradient>'
             f'<linearGradient id="c-line" gradientUnits="userSpaceOnUse" x1="{gx0}" y1="0" x2="{gx1}" y2="0">'
             f'<stop offset="0" stop-color="{sf.VIOLET}"/><stop offset=".5" stop-color="{sf.AQUA}"/><stop offset="1" stop-color="{sf.PINK}"/></linearGradient></defs>')
    s.append(f'<path d="{line}L{gx1},{gy1}L{gx0},{gy1}Z" fill="url(#c-area)"/>')
    s.append(f'<path d="{line}" fill="none" stroke="url(#c-line)" stroke-opacity=".35" stroke-width="2"/>')
    s.append(f'<path class="draw" pathLength="1" d="{line}" fill="none" stroke="url(#c-line)" stroke-width="2.4" stroke-linecap="round"/>')
    if live:
        pi = max(range(len(vals)), key=lambda i: vals[i])
        px, py = pts[pi]
        s.append(f'<circle cx="{f(px)}" cy="{f(py)}" r="9" fill="{sf.PINK}" opacity=".18"/><circle cx="{f(px)}" cy="{f(py)}" r="3.4" fill="{sf.PINK}"/>')
        s.append(sf.label(f"PEAK {peak}", px, py - 14, sf.PINK, 1, size=10, spacing=1.5, anchor="middle"))
    s.append(f'<g><circle r="10" fill="#fff" opacity=".12"/><circle r="3" fill="#fff"/>'
             f'<animateMotion dur="9s" repeatCount="indefinite" path="{line}"/></g>')

    # ---- contribution terrain (left) + languages ring (right)
    s.append(sf.label("CONTRIBUTION FIELD · 12 MONTHS", 60, 586, sf.BODY, 1, size=10, spacing=2))
    first = datetime.date.fromisoformat(days[0][0])
    offset = first.isoweekday() % 7
    weeks = (offset + len(days) + 6) // 7
    maxc = max([c for _, c, _ in days] + [1])
    tcx, half_w, horizon, front_y, z0, dz = 332, 270, 640, 846, 6.0, 1.7

    def cam(wk, d, height=0.0):
        z = z0 + d * dz
        x = tcx + (wk - (weeks - 1) / 2) * (half_w / ((weeks - 1) / 2)) * z0 / z
        y = horizon + (front_y - horizon) * z0 / z - height * z0 / z
        return x, y, z0 / z

    s.append(glow("terrain", tcx, 790, 320, sf.AQUA, .08))
    grid = []
    for d in range(7):
        xa, ya, _ = cam(-.6, d)
        xb, yb, _ = cam(weeks - .4, d)
        grid.append(f'M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}')
    for wk in range(0, weeks + 1, 4):
        xa, ya, _ = cam(wk - .5, -.4)
        xb, yb, _ = cam(wk - .5, 6.4)
        grid.append(f'M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}')
    s.append(f'<path d="{"".join(grid)}" stroke="{sf.AQUA}" stroke-opacity=".12" fill="none"/>')
    cols = [[] for _ in range(weeks)]
    for i, (_, count, _) in enumerate(days):
        wk, d = divmod(offset + i, 7)
        cols[wk].append((d, count, i == len(days) - 1))
    for wk, entries in enumerate(cols):
        parts = []
        for d, count, today in sorted(entries, key=lambda e: -e[0]):
            v = math.sqrt(count / maxc)
            x, y, p = cam(wk, d)
            if today and live:
                _, ty, _ = cam(wk, d, 8 + 70 * v)
                parts.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(ty)}" stroke="{sf.YELLOW}" stroke-width="{2.2 * p:.1f}"/>'
                             f'<circle class="now" cx="{f(x)}" cy="{f(ty)}" r="{3.6 * p:.1f}" fill="{sf.YELLOW}"/>')
                continue
            if count == 0:
                parts.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{.9 * p + .2:.1f}" fill="{sf.AQUA}" opacity="{.12 + .2 * p:.2f}"/>')
                continue
            _, ty, _ = cam(wk, d, 8 + 70 * v)
            parts.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(ty)}" stroke="{sf.AQUA}" '
                         f'stroke-width="{2 * p:.1f}" stroke-opacity="{(.2 + .55 * v) * (.45 + .55 * p):.2f}"/>'
                         f'<circle cx="{f(x)}" cy="{f(ty)}" r="{(1.1 + 1.4 * v) * p:.1f}" fill="#eafffb" opacity="{(.45 + .55 * v) * (.5 + .5 * p):.2f}"/>')
        s.append(f'<g class="wk" style="animation-delay:{wk * .09:.2f}s">{"".join(parts)}</g>')

    s.append(sf.label("LANGUAGES", 640, 586, sf.BODY, 1, size=10, spacing=2))
    rcx, rcy, rr = 712, 720, 62
    s.append(f'<circle class="spin" style="animation-duration:60s" cx="{rcx}" cy="{rcy}" r="{rr + 16}" fill="none" stroke="#fff" stroke-opacity=".18" stroke-dasharray="1 7"/>')
    s.append(f'<circle cx="{rcx}" cy="{rcy}" r="{rr}" fill="none" stroke="#fff" stroke-opacity=".06" stroke-width="12"/>')
    shades = [sf.YELLOW, sf.SKY, sf.PINK, sf.AQUA, sf.VIOLET, "#5d636d"]
    if data["langs"]:
        total = sum(data["langs"].values())
        top_l = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:5]
        rest = total - sum(v for _, v in top_l)
        if rest > 0:
            top_l.append(("Other", rest))
        circ = 2 * math.pi * rr
        acc = 0.0
        for (lang, size), color in zip(top_l, shades):
            frac = size / total
            s.append(f'<circle cx="{rcx}" cy="{rcy}" r="{rr}" fill="none" stroke="{color}" stroke-width="12" '
                     f'stroke-dasharray="{f(max(frac * circ - 3, .5))} {f(circ)}" stroke-dashoffset="{f(-acc * circ)}" '
                     f'transform="rotate(-90 {rcx} {rcy})"/>')
            acc += frac
        lead = top_l[0]
        s.append(sf.text(f"{round(100 * lead[1] / total)}%", rcx, rcy + 6, 22, "inter-800", anchor="middle", attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.label({"Jupyter Notebook": "JUPYTER"}.get(lead[0], lead[0]).upper()[:10], rcx, rcy + 24, shades[0], 1, size=9, spacing=1.5, anchor="middle"))
        for i, ((lang, size), color) in enumerate(zip(top_l, shades)):
            ly = 672 + i * 22
            short = {"Jupyter Notebook": "Jupyter"}.get(lang, lang)
            s.append(f'<rect x="808" y="{ly - 8}" width="8" height="8" rx="1.5" fill="{color}"/>')
            s.append(sf.text(short, 824, ly, 13, "inter-400", attrs=f'fill="{sf.INK}"')[0])
            s.append(sf.label(f"{round(100 * size / total)}%", 940, ly, sf.DIM, 1, size=10, spacing=1, anchor="end"))
    s.append("</g>")
    return "".join(s)


def contact(cfg, y0, h):
    s = [f'<g transform="translate(0 {y0})">', heading(6, "CONTACT", 132),
         sf.text(cfg.get("contact_line", "Reach me through any of the links below."), 60, 196, 23, "inter-400",
                 attrs=f'fill="{sf.BODY}"')[0]]
    s.append(wave_field(236, h, sf.PINK, sf.VIOLET))
    s.append(f'<defs><linearGradient id="c-fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sf.PAGE}" stop-opacity="0"/>'
             f'<stop offset="1" stop-color="{sf.PAGE}"/></linearGradient></defs>'
             f'<rect y="{h - 70}" width="{W}" height="70" fill="url(#c-fade)"/>')
    s.append("</g>")
    return "".join(s)


# =============================================================================== the canvas
def _svg(total, label, css, body, round_top):
    clip = (f'<path d="M0,6a6,6 0 0 1 6,-6H{W - 6}a6,6 0 0 1 6,6V{total}H0Z"/>' if round_top
            else f'<rect width="{W}" height="{total}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {total}" width="{W}" height="{total}" role="img" '
            f'aria-label="{sf.esc(label)}"><style>{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>'
            f'<defs><clipPath id="c-all">{clip}</clipPath></defs><g clip-path="url(#c-all)">{body}</g></svg>')


def build(cfg, hero_svg, data):
    """Return (top canvas, bottom canvas). The coder GIF sits between them."""
    lay, total = layout("top")
    hero_inner = hero_svg[hero_svg.index(">") + 1: hero_svg.rindex("</svg>")]
    label = (f'{cfg["name"]}: AI engineer, LLM systems, full stack. '
             + " ".join("".join(t for t, _ in line) for line in cfg["about"]) + " "
             + ". ".join(f'{p["title"]}: {" ".join(p["lines"])}' for p in cfg["focus"]) + ". Journey: "
             + ". ".join(f'{n["when"]}: {n["title"]}, {n["sub"]}' for n in cfg["journey"]) + ".")
    top = _svg(total, label, CSS_BG + CSS_TURN + CSS_JOURNEY,
               background(lay["hero"][1], total) + f"<g>{hero_inner}</g>" + about(cfg, lay["about"][0])
               + focus(cfg, lay["focus"][0]) + journey(cfg, lay["journey"][0]), True)

    lay, total = layout("bottom")
    label = ("Stack: " + "; ".join(f'{g["group"].title()}: {", ".join(n for _, n in g["items"])}' for g in cfg["stack"])
             + ". Telemetry: contributions, commits, pull requests, stars, streaks, a 60 day activity graph, a 3D contribution field and languages. Contact.")
    bottom = _svg(total, label, CSS_BG + CSS_TURN + CSS_STACK + CSS_TELE,
                  background(0, total) + stack(cfg, lay["stack"][0]) + telemetry(data, lay["telemetry"][0])
                  + contact(cfg, lay["contact"][0], lay["contact"][1]), False)
    return top, bottom


# =============================================================================== link chips + footer
def chip(label, sub, w, h=96, first=False):
    rng = random.Random(f"chip-{label}")
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
         f'aria-label="{sf.esc(label)}"><rect width="{w}" height="{h}" fill="{sf.PAGE}"/><g fill="#fff">']
    for _ in range(round(w * h / 6800)):
        s.append(f'<circle cx="{f(rng.uniform(0, w))}" cy="{f(rng.uniform(0, h))}" r="{rng.choice([.5, .6, .8])}" '
                 f'opacity="{rng.uniform(.1, .45):.2f}"/>')
    s.append("</g>")
    if not first:
        s.append(f'<rect x="0" y="22" width="1" height="{h - 44}" fill="#fff" fill-opacity=".12"/>')
    s.append(f'<rect x="0" y="{h - 1}" width="{w}" height="1" fill="#fff" fill-opacity=".08"/>')
    pad = 40 if first else 28
    s.append(sf.text(label, pad, 50, 22, "inter-600", attrs=f'fill="{sf.INK}"')[0])
    s.append(sf.label(sub, pad, 74, sf.DIM, 1, size=10, spacing=1.5))
    s.append(sf.arrow(w - 28, 34, sf.INK, size=12))
    s.append("</svg>")
    return "".join(s)


def footer(h=110):
    css = ".cur{animation:cur 1.1s steps(1) infinite}@keyframes cur{50%{opacity:0}}"
    msg = "END OF TRANSMISSION"
    w = sf.text_width(msg, 12, "mono-500", 5)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" '
            f'aria-label="End of transmission"><style>{css}</style>'
            f'<path d="M0,0H{W}V{h - 6}a6,6 0 0 1 -6,6H6a6,6 0 0 1 -6,-6Z" fill="{sf.PAGE}"/>'
            + sf.label(msg, 500, 64, sf.DIM, 1, size=12, spacing=5, anchor="middle")
            + f'<rect class="cur" x="{f(500 + w / 2 + 10)}" y="53" width="7" height="13" fill="{sf.INK}"/></svg>')
