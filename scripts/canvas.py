"""The whole profile as one tall, live SVG.

GitHub can't layer a background behind several images, so everything is drawn into a single
canvas: one starfield and one stream of rising particles run behind every section, and each
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
def layout(cfg):
    sections = [("hero", 480), ("about", 560), ("focus", 520), ("journey", 460),
                ("projects", 150 + 124 * len(cfg["projects"])), ("telemetry", 610), ("contact", 440)]
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
    out = [f'<g fill="{color}">']
    for strand in (0, 1):
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
    s.append(globe(780, 300, 150, sf.ICE))
    s.append("</g>")
    return "".join(s)


FOCUS_COLORS = [sf.EMBER, sf.ROSE, sf.MOSS]


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
    s.append(glow("journey", 500, line_y, 420, sf.MOSS, .05))
    s.append(f'<rect x="120" y="{line_y - .5}" width="760" height="1" fill="#fff" fill-opacity=".14"/>')
    s.append(helix(100, 900, line_y, 30, sf.MOSS))
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


CSS_BEAM = ".beam{animation:beam 9s linear infinite backwards}@keyframes beam{from{transform:translateX(-180px)}to{transform:translateX(900px)}}"
PROJECT_SHAPES = [("tetrahedron", sf.EMBER), ("octahedron", sf.ICE), ("cube", sf.ROSE)]


def hairline(y, uid, delay):
    return (f'<defs><clipPath id="c-hc-{uid}"><rect x="60" y="{y - 2}" width="880" height="4"/></clipPath></defs>'
            f'<rect x="60" y="{y - .5}" width="880" height="1" fill="url(#c-hl)"/>'
            f'<g clip-path="url(#c-hc-{uid})"><rect class="beam" style="animation-delay:{delay}s" x="60" y="{y - .7}" '
            f'width="170" height="1.4" fill="url(#c-bm)"/></g>')


def projects(cfg, y0):
    s = [f'<g transform="translate(0 {y0})">', heading(4, "PROJECTS", 118),
         '<defs><linearGradient id="c-hl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity=".16"/>'
         '<stop offset="1" stop-color="#fff" stop-opacity=".02"/></linearGradient>'
         '<linearGradient id="c-bm" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
         '<stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>']
    for i, p in enumerate(cfg["projects"]):
        top = 150 + i * 124
        shape, color = PROJECT_SHAPES[i % len(PROJECT_SHAPES)]
        s.append(solid(shape, 82, top + 50, 17, color, period=11 + i * 3, samples=30, width=1.3, uid=f"proj{i}"))
        s.append(sf.text(p["name"], 126, top + 58, 34, "inter-600", attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.text(p["description"], 126, top + 90, 17, "inter-400", attrs=f'fill="{sf.BODY}"')[0])
        s.append(sf.label(p["tags"].upper(), 940, top + 53, sf.DIM, 1, size=11, spacing=1.5, anchor="end"))
        s.append(hairline(top + 123, f"p{i}", round(i * 1.6, 1)))
    s.append("</g>")
    return "".join(s)


CSS_TERRAIN = (".wk{animation:wk 9s ease-in-out infinite}@keyframes wk{0%,14%,100%{opacity:.55}7%{opacity:1}}"
               ".now{animation:now 2s ease-in-out infinite}@keyframes now{50%{opacity:.3}}")


def telemetry(data, y0):
    live = data["total"] is not None
    s = [f'<g transform="translate(0 {y0})">', heading(5, "TELEMETRY", 132)]
    active = sum(1 for _, c, _ in data["days"] if c)
    stats = [(data["total"], "CONTRIBUTIONS / 12 MONTHS"), (active if live else None, "ACTIVE DAYS"),
             (data["repos"], "PUBLIC REPOSITORIES")]
    for i, (value, caption) in enumerate(stats):
        x = 60 + i * 310
        s.append(sf.text(f"{value:,}" if value is not None else "--", x, 236, 58, "inter-800", attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.label(caption, x + 2, 266, sf.DIM, 1, size=12))

    # contribution terrain: one bar per day on a floor seen in perspective
    days = data["days"]
    first = datetime.date.fromisoformat(days[0][0])
    offset = first.isoweekday() % 7
    weeks = (offset + len(days) + 6) // 7
    maxc = max([c for _, c, _ in days] + [1])
    horizon, front_y, z0, dz = 318, 532, 6.0, 1.7          # camera: front row at depth z0

    def cam(wk, d, height=0.0):
        """Project floor cell (week, day) lifted by `height` (front-row pixels) to the screen."""
        z = z0 + d * dz
        x = 500 + (wk - (weeks - 1) / 2) * (430 / ((weeks - 1) / 2)) * z0 / z
        y = horizon + (front_y - horizon) * z0 / z - height * z0 / z
        return x, y, z0 / z

    s.append(glow("terrain", 500, 470, 440, sf.ICE, .08))
    grid = []
    for d in range(7):
        xa, ya, _ = cam(-.6, d)
        xb, yb, _ = cam(weeks - .4, d)
        grid.append(f'M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}')
    for wk in range(0, weeks + 1, 4):
        xa, ya, _ = cam(wk - .5, -.4)
        xb, yb, _ = cam(wk - .5, 6.4)
        grid.append(f'M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}')
    s.append(f'<path d="{"".join(grid)}" stroke="{sf.ICE}" stroke-opacity=".12" fill="none"/>')
    cols = [[] for _ in range(weeks)]
    for i, (_, count, _) in enumerate(days):
        wk, d = divmod(offset + i, 7)
        cols[wk].append((d, count, i == len(days) - 1))
    for wk, entries in enumerate(cols):
        parts = []
        for d, count, today in sorted(entries, key=lambda e: -e[0]):     # back rows first
            v = math.sqrt(count / maxc)
            x, y, p = cam(wk, d)
            if today and live:
                _, ty, _ = cam(wk, d, 8 + 74 * v)
                parts.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(ty)}" stroke="{AMBER}" stroke-width="{2.6 * p:.1f}"/>'
                             f'<circle class="now" cx="{f(x)}" cy="{f(ty)}" r="{4 * p:.1f}" fill="{AMBER}"/>')
                continue
            if count == 0:
                parts.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{1.1 * p + .2:.1f}" fill="{sf.ICE}" opacity="{.12 + .2 * p:.2f}"/>')
                continue
            _, ty, _ = cam(wk, d, 8 + 74 * v)
            parts.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(ty)}" stroke="{sf.ICE}" '
                         f'stroke-width="{2.6 * p:.1f}" stroke-opacity="{(.2 + .55 * v) * (.45 + .55 * p):.2f}"/>'
                         f'<circle cx="{f(x)}" cy="{f(ty)}" r="{(1.3 + 1.6 * v) * p:.1f}" fill="#eef3ff" opacity="{(.45 + .55 * v) * (.5 + .5 * p):.2f}"/>')
        s.append(f'<g class="wk" style="animation-delay:{wk * .09:.2f}s">{"".join(parts)}</g>')

    if not live:
        s.append(sf.label("AWAITING FIRST SYNC", 500, 572, sf.DIM, 1, size=12, spacing=4, anchor="middle"))
    elif data["langs"]:
        total = sum(data["langs"].values())
        top = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:5]
        rest = total - sum(v for _, v in top)
        if rest > 0:
            top.append(("Other", rest))
        shades = [1, .66, .46, .32, .22, .12]
        x = 60.0
        for (lang, size), shade in zip(top, shades):
            w = 880 * size / total
            s.append(f'<rect x="{f(x)}" y="556" width="{f(max(w - 3, 1))}" height="3" fill="#fff" fill-opacity="{shade}"/>')
            x += w
        slot = 880 / len(top)
        for i, ((lang, size), shade) in enumerate(zip(top, shades)):
            lx = 60 + i * slot
            short = {"Jupyter Notebook": "Jupyter"}.get(lang, lang).upper()[:12]
            s.append(f'<rect x="{f(lx)}" y="575" width="8" height="8" fill="#fff" fill-opacity="{shade}"/>')
            s.append(sf.label(f"{short} {round(100 * size / total)}%", lx + 16, 584, sf.BODY, 1, size=11, spacing=1))
    s.append("</g>")
    return "".join(s)


def contact(cfg, y0, h):
    s = [f'<g transform="translate(0 {y0})">', heading(6, "CONTACT", 132),
         sf.text(cfg.get("contact_line", "Reach me through any of the links below."), 60, 196, 23, "inter-400",
                 attrs=f'fill="{sf.BODY}"')[0]]
    s.append(wave_field(236, h, sf.EMBER, sf.ROSE))
    s.append(f'<defs><linearGradient id="c-fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sf.PAGE}" stop-opacity="0"/>'
             f'<stop offset="1" stop-color="{sf.PAGE}"/></linearGradient></defs>'
             f'<rect y="{h - 70}" width="{W}" height="70" fill="url(#c-fade)"/>')
    s.append("</g>")
    return "".join(s)


# =============================================================================== the canvas
def build(cfg, hero_svg, data):
    lay, total = layout(cfg)
    hero_inner = hero_svg[hero_svg.index(">") + 1: hero_svg.rindex("</svg>")]
    css = CSS_BG + CSS_TURN + CSS_JOURNEY + CSS_BEAM + CSS_TERRAIN
    label = (f'{cfg["name"]}: AI engineer, LLM systems, full stack. '
             + " ".join("".join(t for t, _ in line) for line in cfg["about"]) + " "
             + ". ".join(f'{p["title"]}: {" ".join(p["lines"])}' for p in cfg["focus"]) + ". Projects: "
             + "; ".join(f'{p["name"]}, {p["description"]}' for p in cfg["projects"]) + ".")
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {total}" width="{W}" height="{total}" role="img" '
         f'aria-label="{sf.esc(label)}"><style>{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>',
         f'<defs><clipPath id="c-all"><path d="M0,6a6,6 0 0 1 6,-6H{W - 6}a6,6 0 0 1 6,6V{total}H0Z"/></clipPath></defs>',
         '<g clip-path="url(#c-all)">',
         background(lay["hero"][1], total),
         f"<g>{hero_inner}</g>",
         about(cfg, lay["about"][0]), focus(cfg, lay["focus"][0]), journey(cfg, lay["journey"][0]),
         projects(cfg, lay["projects"][0]), telemetry(data, lay["telemetry"][0]),
         contact(cfg, lay["contact"][0], lay["contact"][1]),
         "</g></svg>"]
    return "".join(s)


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
