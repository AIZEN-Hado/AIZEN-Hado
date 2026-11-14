"""assets/cosmic-hero.svg: an engraved accretion disk whose neural lattice bends around the mass.

Composition (viewBox 1000 x 560):
  left   identity typography
  right  a Schwarzschild black hole drawn in fine line-work: back half of the disk, the lensed image of
         the far side hugging the shadow, the shadow, the photon ring, then the front half of the disk.
         A lattice of nodes surrounds it; each edge is a geodesic bowed away from the mass.
Physics labels are real (photon sphere at 1.5 r_s, innermost stable circular orbit at 3 r_s).
"""
import math
import random

import kit
from kit import AMBER, EMBER, SILVER, VIOLET, VOID, WHITE, f

W, H = 1000, 540
CX, CY = 704, 268           # centre of the mass
RS = 62                     # shadow radius on screen
TILT = -11                  # disk inclination on the page, degrees
KEEP_CLEAR = [(740, 975, 105, 165), (760, 975, 345, 405), (760, 975, 500, 540)]   # callout + caption boxes
FLAT = .155                 # ry / rx of the disk (viewing angle ~81 degrees)

CSS = (kit.TWINKLE_CSS +
       ".flow{animation:flow linear infinite}@keyframes flow{to{stroke-dashoffset:0}}"
       ".ring{animation:ring 6s ease-in-out infinite}@keyframes ring{0%,100%{opacity:1}50%{opacity:.72}}"
       ".hub{animation:hub 5s ease-in-out infinite}@keyframes hub{0%,100%{opacity:.9}50%{opacity:.35}}"
       ".halo{transform-box:fill-box;transform-origin:center;animation:halo 5s ease-out infinite}"
       "@keyframes halo{0%{transform:scale(.6);opacity:.55}70%,100%{transform:scale(2.4);opacity:0}}"
       ".pulse{animation:pulse linear infinite}@keyframes pulse{to{stroke-dashoffset:0}}"
       ".scan{animation:scan 18s cubic-bezier(.45,0,.55,1) infinite}"
       "@keyframes scan{0%{transform:translateX(-80px)}100%{transform:translateX(1080px)}}"
       ".lum{animation:lum 14s ease-in-out infinite}@keyframes lum{0%,100%{opacity:.55}50%{opacity:1}}"
       ".orb{animation:orb 60s linear infinite}@keyframes orb{to{stroke-dashoffset:0}}")


def disk(doc):
    """Return (back, lensed, front) fragments, already in the tilted frame."""
    grad = doc.uid("dg")
    doc.define(
        f'<linearGradient id="{grad}" gradientUnits="userSpaceOnUse" x1="{CX - 300}" y1="0" x2="{CX + 300}" y2="0">'
        f'<stop offset="0" stop-color="{EMBER}"/><stop offset=".28" stop-color="{AMBER}"/>'
        f'<stop offset=".62" stop-color="{AMBER}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{VIOLET}" stop-opacity=".35"/></linearGradient>')
    rng = random.Random(7)
    back, front = [], []
    rings = []
    r = RS * 1.62
    while r < RS * 4.9:
        rings.append(r)
        r += 3.2 + (r - RS) * .028 + rng.uniform(-.8, .9)
    for i, rx in enumerate(rings):
        ry = rx * FLAT
        u = (rx - rings[0]) / (rings[-1] - rings[0])          # 0 inner .. 1 outer
        op = (1 - u) ** 1.6 * .85 + .05
        if rng.random() < .18:
            op *= .35                                          # gaps in the disk
        sw = .55 + (1 - u) * .65
        for upper, bucket in ((True, back), (False, front)):
            bucket.append(f'<path d="{kit.arc_half(CX, CY, rx, ry, upper)}" stroke="url(#{grad})" '
                          f'stroke-opacity="{f(op * (.62 if upper else 1))}" stroke-width="{f(sw)}"/>')
    # matter in orbit: dashed arcs, inner orbits faster (period ~ r^1.5)
    for rx, dash in ((RS * 1.75, "1.6 9"), (RS * 2.05, "2.4 13"), (RS * 2.5, "1.2 7"), (RS * 3.0, "3 19"),
                     (RS * 3.6, "1.4 11"), (RS * 4.3, "2 23")):
        ry = rx * FLAT
        half = kit.ellipse_len(rx, ry) / 2
        period = 9 * (rx / (RS * 1.75)) ** 1.5
        a, b = (float(v) for v in dash.split())
        cyc = a + b
        span = cyc * max(1, round(half / cyc))
        op = .9 - (rx - RS * 1.75) / (RS * 4.3) * .9 + .2
        for upper, bucket in ((True, back), (False, front)):
            bucket.append(
                f'<path class="flow" style="animation-duration:{period:.1f}s" d="{kit.arc_half(CX, CY, rx, ry, upper)}" '
                f'stroke="{EMBER}" stroke-opacity="{f(op * (.5 if upper else .95))}" stroke-width="1.3" '
                f'stroke-linecap="round" stroke-dasharray="{dash}" stroke-dashoffset="{f(span)}"/>')

    # the far side of the disk, lensed over and under the shadow
    lg = doc.uid("lg")
    doc.define(
        f'<linearGradient id="{lg}" gradientUnits="userSpaceOnUse" x1="{CX - RS * 1.7}" y1="0" x2="{CX + RS * 1.7}" y2="0">'
        f'<stop offset="0" stop-color="{EMBER}"/><stop offset=".45" stop-color="{AMBER}"/>'
        f'<stop offset="1" stop-color="{AMBER}" stop-opacity=".35"/></linearGradient>')
    lensed = []
    for i in range(14):
        rr = RS * (1.04 + i * .052)
        op = .95 * (1 - i / 14) ** 1.3 + .04
        # the image of the far side is squashed less than the disk itself, and lifted slightly
        ecy, erx, ery = CY - 2 - i * .5, rr * 1.02, rr * .93
        sw = .5 + (1 - i / 14) * .75
        lensed.append(f'<path d="{kit.arc_half(CX, ecy, erx, ery, True)}" stroke="url(#{lg})" '
                      f'stroke-opacity="{f(op)}" stroke-width="{f(sw)}"/>')
        if i < 7:
            lensed.append(f'<path d="{kit.arc_half(CX, ecy, erx * .985, ery * .9, False)}" stroke="url(#{lg})" '
                          f'stroke-opacity="{f(op * .42)}" stroke-width="{f(sw * .6)}"/>')
    return "".join(back), "".join(lensed), "".join(front)


def lattice(doc):
    """Nodes on loose shells around the mass; edges bow outward like light passing a lens."""
    rng = random.Random(11)
    nodes = []
    for shell, count in ((205, 9), (262, 12), (330, 15), (410, 13)):
        for k in range(count):
            a = 2 * math.pi * k / count + rng.uniform(-.18, .18) + shell * .01
            rad = shell * rng.uniform(.93, 1.07)
            x, y = CX + rad * math.cos(a), CY + rad * math.sin(a) * .78
            in_label = any(a <= x <= b and c <= y <= d for a, b, c, d in KEEP_CLEAR)
            if 24 < x < W - 24 and 24 < y < H - 24 and x > 455 and not in_label:
                nodes.append((x, y))
    edges = set()
    for i, (x1, y1) in enumerate(nodes):
        near = sorted(range(len(nodes)), key=lambda j: math.hypot(nodes[j][0] - x1, nodes[j][1] - y1))[1:4]
        for j in near[:2 + (i % 2)]:
            if math.hypot(nodes[j][0] - x1, nodes[j][1] - y1) < 150:
                edges.add(tuple(sorted((i, j))))
    lines, pulses = [], []
    for n, (i, j) in enumerate(sorted(edges)):
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        d = math.hypot(mx - CX, my - CY)
        bend = 5200 / max(d, 120)                                    # stronger near the mass
        ux, uy = (mx - CX) / d, (my - CY) / d
        qx, qy = mx + ux * bend, my + uy * bend
        path = f"M{f(x1)} {f(y1)}Q{f(qx)} {f(qy)} {f(x2)} {f(y2)}"
        lines.append(f'<path d="{path}"/>')
        if n % 7 == 3:
            ln = math.hypot(x2 - x1, y2 - y1) + bend
            pulses.append(
                f'<path class="pulse" style="animation-duration:{3.5 + (n % 5) * .7:.1f}s;animation-delay:-{n * .37 % 4:.2f}s" '
                f'd="{path}" stroke="{AMBER}" stroke-width="1.4" stroke-linecap="round" '
                f'stroke-dasharray="7 {f(ln * 2.2)}" stroke-dashoffset="{f(ln * 2.2 + 7)}"/>')
    dots, hubs = [], []
    for i, (x, y) in enumerate(nodes):
        hub = i % 9 == 4
        r = 2.4 if hub else 1.25 + (i % 3) * .3
        if hub:
            hubs.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="5.5" stroke="{AMBER}" stroke-opacity=".5"/>'
                        f'<circle class="halo" style="animation-delay:-{i * .6 % 5:.1f}s" cx="{f(x)}" cy="{f(y)}" '
                        f'r="5.5" stroke="{AMBER}" stroke-width=".8"/>'
                        f'<circle class="hub" style="animation-delay:-{i * .4 % 5:.1f}s" cx="{f(x)}" cy="{f(y)}" '
                        f'r="{r}" fill="{EMBER}"/>')
        else:
            dots.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>')
    return (f'<g stroke="{SILVER}" stroke-opacity=".22" stroke-width=".7">{"".join(lines)}</g>'
            f'{"".join(pulses)}<g fill="{WHITE}" fill-opacity=".55">{"".join(dots)}</g>{"".join(hubs)}')


def orbits(doc):
    """Two instrument rings with graduations, and one slow violet stream."""
    out = []
    rot = math.radians(TILT)
    for rx, ry, op in ((372, 112, .13), (468, 158, .08)):
        out.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{rx}" ry="{ry}" transform="rotate({TILT} {CX} {CY})" '
                   f'stroke="{SILVER}" stroke-opacity="{op}" stroke-width=".8"/>')
    ticks = []
    rx, ry = 372, 112
    for k in range(120):
        t = 2 * math.pi * k / 120
        x1, y1 = kit.ellipse_point(CX, CY, rx, ry, t, rot)
        long = k % 10 == 0
        x2, y2 = kit.ellipse_point(CX, CY, rx + (9 if long else 4.5), ry + (9 if long else 4.5) * ry / rx, t, rot)
        if x1 < 445 or not (10 < y1 < H - 10):
            continue
        ticks.append(f"M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}")
    out.append(f'<path d="{"".join(ticks)}" stroke="{SILVER}" stroke-opacity=".3" stroke-width=".7"/>')
    vl = kit.ellipse_len(430, 128)
    out.append(f'<ellipse class="orb" cx="{CX}" cy="{CY}" rx="430" ry="128" transform="rotate({TILT + 4} {CX} {CY})" '
               f'stroke="{VIOLET}" stroke-opacity=".45" stroke-width="1" stroke-dasharray="1 9 44 9" '
               f'stroke-dashoffset="{f(vl)}" pathLength="{f(vl)}"/>')
    return "".join(out)


def callout(doc, x0, y0, y1, title, sub, right=960):
    """Leader from a feature at (x0, y0) to a right-aligned two-line label on baseline row y1."""
    tw = max(kit.measure(title, 9.5, "mono-500", 1.8), kit.measure(sub, 9.5, "mono-400", 1))
    x2 = right - tw - 10
    x1 = min(x0 + abs(y1 - y0), x2 - 14)
    return (f'<circle cx="{f(x0)}" cy="{f(y0)}" r="2.2" fill="{AMBER}"/>'
            f'<circle cx="{f(x0)}" cy="{f(y0)}" r="5" stroke="{AMBER}" stroke-opacity=".5" stroke-width=".7"/>'
            f'<path d="M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}H{f(x2 + 2)}" stroke="{SILVER}" stroke-opacity=".5" stroke-width=".7"/>'
            + doc.text(title, right, y1 - 5, 9.5, "mono-500", AMBER, .95, "end", track=1.8)
            + doc.text(sub, right, y1 + 11, 9.5, "mono-400", SILVER, .8, "end", track=1))


def build(profile):
    alt = (f'{profile["name"]}: {profile["tagline"]} '
           'Line-engraved black hole with a lensed neural lattice, labelled photon sphere and innermost stable orbit.')
    doc = kit.Doc(W, H, alt, CSS)
    clip = kit.plate(doc)

    g = []
    # atmosphere
    neb, lift, core = doc.uid("ng"), doc.uid("lift"), doc.uid("core")
    doc.define(
        f'<radialGradient id="{lift}" cx="{CX}" cy="{CY}" r="560" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#141826"/><stop offset=".55" stop-color="#0A0C14"/><stop offset="1" stop-color="{VOID}"/></radialGradient>'
        f'<radialGradient id="{neb}" cx="905" cy="92" r="330" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{VIOLET}" stop-opacity=".22"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="{core}" cx="{CX}" cy="{CY}" r="300" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{AMBER}" stop-opacity=".2"/><stop offset=".45" stop-color="{AMBER}" stop-opacity=".05"/>'
        f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>'
        f'<filter id="blur8" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>'
        f'<filter id="blur3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.6"/></filter>'
        f'<linearGradient id="scanG" x1="0" x2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{AMBER}" stop-opacity=".07"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>')
    g.append(f'<rect width="{W}" height="{H}" fill="url(#{lift})"/>')
    g.append(f'<rect width="{W}" height="{H}" fill="url(#{neb})"/>')
    g.append(kit.stars(3, W, H, 230, avoid=(CX, CY, 150)))
    g.append(f'<rect class="lum" width="{W}" height="{H}" fill="url(#{core})"/>')
    doc.define(f'<linearGradient id="fadeL" gradientUnits="userSpaceOnUse" x1="400" x2="560" y1="0" y2="0">'
               f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>'
               f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
               f'<rect width="{W}" height="{H}" fill="url(#fadeL)"/></mask>')
    g.append(f'<g mask="url(#fade)">{orbits(doc)}{lattice(doc)}</g>')

    back, lensed, front = disk(doc)
    # soft glow, drawn once and left static (filters are expensive to animate)
    glow = (f'<g filter="url(#blur8)" opacity=".75"><ellipse cx="{CX}" cy="{CY}" rx="{RS * 2.2}" ry="{RS * 2.2 * FLAT * 1.4}" '
            f'stroke="{AMBER}" stroke-width="10" stroke-opacity=".7"/>'
            f'<circle cx="{CX}" cy="{CY - 3}" r="{RS * 1.18}" stroke="{AMBER}" stroke-width="9" stroke-opacity=".55"/></g>')
    shadow = f'<circle cx="{CX}" cy="{CY}" r="{RS}" fill="#010102"/>'
    photon = (f'<g class="ring"><circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width="1.6" filter="url(#blur3)"/>'
              f'<circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width=".9"/></g>')
    g.append(f'<g transform="rotate({TILT} {CX} {CY})">{glow}{back}{lensed}{shadow}{photon}{front}</g>')

    # measurement marks around the mass
    rot = math.radians(TILT)
    ticks = []
    for ang in (0, 90, 180, 270):
        a = math.radians(ang) + rot
        r1, r2 = (310, 324) if ang in (0, 180) else (122, 134)
        ticks.append(f"M{f(CX + r1 * math.cos(a))} {f(CY + r1 * math.sin(a))}L{f(CX + r2 * math.cos(a))} {f(CY + r2 * math.sin(a))}")
    g.append(f'<path d="{"".join(ticks)}" stroke="{WHITE}" stroke-opacity=".5" stroke-width=".8"/>')
    top = kit.ellipse_point(CX, CY - 1, 0, RS + 1.6, -math.pi / 2, rot)
    g.append(callout(doc, top[0] + 2, top[1], 136, "PHOTON SPHERE", "r = 1.5 rs  ·  light orbits"))
    isco = kit.ellipse_point(CX, CY, RS * 1.62, RS * 1.62 * FLAT, 1.25, rot)    # front inner edge of the disk
    g.append(callout(doc, isco[0], isco[1], 376, "ISCO", "r = 3 rs  ·  inner edge"))

    # viewing geometry, bottom right (inclination follows from the disk's axis ratio: acos(0.155) ~ 81 deg)
    g.append(doc.text("SCHWARZSCHILD  ·  i ≈ 81°", W - 40, H - 19, 9.5, "mono-400", SILVER, .55, "end", track=1.6))

    # the scan: a faint band of light crossing the plate
    g.append(f'<g class="scan" transform="translate(-200 0)"><rect x="-60" width="120" height="{H}" fill="url(#scanG)"/>'
             f'<rect x="-.4" width=".8" height="{H}" fill="{AMBER}" fill-opacity=".18"/></g>')

    # identity
    x = 58
    g.append(f'<path d="M{x} 116h22" stroke="{AMBER}" stroke-width="1.4"/>')
    g.append(doc.text(profile["kicker"], x + 34, 120, 10.5, "mono-500", AMBER, 1, track=3.2))
    g.append(doc.text(profile["first"], x - 3, 212, 80, "serif", WHITE))
    g.append(doc.text(profile["last"], x - 1, 290, 80, "serif-i", WHITE))
    ty = 350
    for i, line in enumerate(profile["tagline_lines"]):
        g.append(doc.text(line, x, ty + i * 30, 21, "sans-300", WHITE if i else SILVER, 1 if i else .95))
    fy = 446
    cx = x
    for i, item in enumerate(profile["focus"]):
        g.append(f'<rect x="{f(cx)}" y="{fy - 7}" width="5" height="5" fill="{AMBER}" transform="rotate(45 {f(cx + 2.5)} {fy - 4.5})"/>')
        g.append(doc.text(item, cx + 14, fy, 10, "mono-400", WHITE, .78, track=2))
        cx += 14 + kit.measure(item, 10, "mono-400", 2) + 26

    g.append(kit.registration(doc))
    g.append(kit.corner_labels(doc, tl="PLATE 00  /  EVENT HORIZON STUDY", tr=profile["handle"].upper() + "  /  2026",
                               bl=profile["coords"], br=""))
    doc.add(f'<g clip-path="url(#{clip})">{"".join(g)}</g>', kit.plate_border(doc))
    return doc
