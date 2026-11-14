"""assets/cosmic-hero.svg: a black hole whose accretion disk is the last year of GitHub activity.

The disk is not decoration, it is data. Seven rings are the days of the week (inner ring = Sunday), the
53 segments around each ring are the weeks of the last 365 days (oldest to newest, ending at the labelled
"last 7 days" mark), and a segment's brightness and weight come from that day's contribution count. A
radar-like beam sweeps the disk; a month scale runs around its edge. The page rebuilds daily, so the disk
always shows the real current year.

Composition (viewBox 1000 x 540): identity typography on the left, the black hole on the right. The back
half of the disk is drawn before the shadow, the front half after it, with the lensed image of the far
side hugging the shadow between them. Physics labels are real (photon sphere at 1.5 r_s).
"""
import datetime
import math

import kit
from kit import AMBER, EMBER, SILVER, VIOLET, VOID, WHITE, f

W, H = 1000, 540
CX, CY = 704, 268           # centre of the mass
RS = 62                     # shadow radius on screen
TILT = -11                  # disk inclination on the page, degrees
FLAT = .155                 # ry / rx of the disk (viewing angle ~81 degrees)
R_IN, R_OUT = RS * 1.65, RS * 4.0
T_NOW = 1.0                 # ellipse angle (radians, clockwise from +x) where the newest week sits

CSS = (kit.TWINKLE_CSS +
       ".ring{animation:ring 6s ease-in-out infinite}@keyframes ring{0%,100%{opacity:1}50%{opacity:.72}}"
       ".hot{animation:hot 5.5s ease-in-out infinite}@keyframes hot{0%,100%{opacity:1}50%{opacity:.55}}"
       ".sw{opacity:0;animation:sw 30s linear infinite}"
       "@keyframes sw{0%{transform:rotate(0);opacity:1}100%{transform:rotate(360deg);opacity:1}}"
       ".scan{animation:scan 18s cubic-bezier(.45,0,.55,1) infinite}"
       "@keyframes scan{0%{transform:translateX(-80px)}100%{transform:translateX(1080px)}}"
       ".lum{animation:lum 14s ease-in-out infinite}@keyframes lum{0%,100%{opacity:.55}50%{opacity:1}}"
       ".orb{animation:orb 60s linear infinite}@keyframes orb{to{stroke-dashoffset:0}}"
       ".now{transform-box:fill-box;transform-origin:center;animation:now 2.8s ease-out infinite}"
       "@keyframes now{0%{transform:scale(.7);opacity:.9}100%{transform:scale(3);opacity:0}}")

LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
# stroke width, colour, opacity for each activity level
STYLE = {0: (.7, AMBER, .24), 1: (1.3, AMBER, .62), 2: (1.8, AMBER, .8), 3: (2.3, AMBER, .95), 4: (2.8, EMBER, 1)}


def calendar(data):
    """Map every day to (column, row, level, count). Row 0 is Sunday."""
    days = data["days"]
    offset = datetime.date.fromisoformat(days[0][0]).isoweekday() % 7
    cells = []
    for i, (date, count, level) in enumerate(days):
        col, row = divmod(offset + i, 7)
        lvl = LEVEL.get(level, 0)
        if lvl == 0 and (count or 0) > 0:
            lvl = 1
        cells.append((col, row, lvl, count or 0, date))
    return cells, (offset + len(days) + 6) // 7


def ring_r(row):
    return R_IN + (R_OUT - R_IN) * row / 6


def ellipse_xy(r, t):
    return CX + r * math.cos(t), CY + r * FLAT * math.sin(t)


def dust(doc):
    """Fine continuous rings between and around the data tracks: the photographic look of a disk."""
    grad = doc.uid("dg")
    doc.define(
        f'<linearGradient id="{grad}" gradientUnits="userSpaceOnUse" x1="{CX - 300}" y1="0" x2="{CX + 300}" y2="0">'
        f'<stop offset="0" stop-color="{EMBER}"/><stop offset=".3" stop-color="{AMBER}"/>'
        f'<stop offset=".7" stop-color="{AMBER}" stop-opacity=".6"/><stop offset="1" stop-color="{VIOLET}" stop-opacity=".4"/></linearGradient>')
    back, front = [], []
    r = R_IN - 26
    while r < R_OUT + 8:
        u = max(0, (r - R_IN) / (R_OUT - R_IN))
        op = (1 - u) ** 1.5 * .5 + .06
        ry = r * FLAT
        back.append(f'<path d="{kit.arc_half(CX, CY, r, ry, True)}" stroke="url(#{grad})" stroke-opacity="{f(op * .6)}" stroke-width=".5"/>')
        front.append(f'<path d="{kit.arc_half(CX, CY, r, ry, False)}" stroke="url(#{grad})" stroke-opacity="{f(op)}" stroke-width=".5"/>')
        r += 3.1 + u * 2.4
    return "".join(back), "".join(front)


def disk(doc, data):
    """Return (back, lensed, front, today_xy). Everything is in the unrotated disk frame."""
    cells, cols = calendar(data)
    slot = 2 * math.pi / cols
    angle = lambda col: T_NOW + slot * (col - (cols - 1))           # centre of a week
    layers = {True: [], False: []}                                    # True = back half (above the shadow)
    glows = {True: [], False: []}
    hot_n = 0
    for col, row, lvl, count, date in cells:
        t0, t1 = angle(col) - slot * .41, angle(col) + slot * .41
        tm = angle(col)
        back = math.sin(tm) < 0
        r = ring_r(row)
        x0, y0 = ellipse_xy(r, t0)
        x1, y1 = ellipse_xy(r, t1)
        w, color, op = STYLE[lvl]
        op *= .6 if back else 1
        d = f"M{f(x0)} {f(y0)}A{f(r)} {f(r * FLAT)} 0 0 1 {f(x1)} {f(y1)}"
        cls = ""
        if lvl >= 3:
            cls = f' class="hot" style="animation-delay:-{(hot_n * 1.37) % 5.5:.1f}s"'
            hot_n += 1
        layers[back].append(f'<path{cls} d="{d}" stroke="{color}" stroke-opacity="{f(op)}" stroke-width="{w}" stroke-linecap="round"/>')
        if lvl >= 2:
            glows[back].append(f'<path d="{d}" stroke="{AMBER}" stroke-opacity="{f(.8 * (.6 if back else 1))}" stroke-width="{w + 3}" stroke-linecap="round"/>')

    # the sweep: a beam turning in the disk plane (a circle squashed by FLAT), drawn once per half
    trail = []
    for k in range(16):
        a = -k * .028
        trail.append(f'<path d="M{f(R_IN - 10)} 0L{f(R_OUT + 14)} 0" transform="rotate({f(math.degrees(a))})" '
                     f'stroke="{AMBER}" stroke-opacity="{f(.5 * (1 - k / 16) ** 1.6)}" stroke-width="{f(1.5 - k * .05)}" vector-effect="non-scaling-stroke"/>')
    beam = (f'<g transform="translate({CX} {CY}) scale(1 {FLAT})"><g class="sw" style="transform-origin:0 0">{"".join(trail)}</g></g>')

    cb, cf = doc.uid("cb"), doc.uid("cf")
    doc.define(f'<clipPath id="{cb}"><rect x="-500" y="-500" width="2400" height="{500 + CY}"/></clipPath>'
               f'<clipPath id="{cf}"><rect x="-500" y="{CY}" width="2400" height="{600}"/></clipPath>')
    dust_b, dust_f = dust(doc)
    blur = f'<g filter="url(#blur3)">{"".join(glows[True])}</g>'
    back_g = f'<g clip-path="url(#{cb})">{dust_b}{blur}{"".join(layers[True])}{beam}</g>'
    blur = f'<g filter="url(#blur3)">{"".join(glows[False])}</g>'
    front_g = f'<g clip-path="url(#{cf})">{dust_f}{blur}{"".join(layers[False])}{beam}</g>'

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
        ecy, erx, ery = CY - 2 - i * .5, rr * 1.02, rr * .93
        sw = .5 + (1 - i / 14) * .75
        lensed.append(f'<path d="{kit.arc_half(CX, ecy, erx, ery, True)}" stroke="url(#{lg})" '
                      f'stroke-opacity="{f(op)}" stroke-width="{f(sw)}"/>')
        if i < 7:
            lensed.append(f'<path d="{kit.arc_half(CX, ecy, erx * .985, ery * .9, False)}" stroke="url(#{lg})" '
                          f'stroke-opacity="{f(op * .42)}" stroke-width="{f(sw * .6)}"/>')
    # where "now" is: the newest day, on its weekday ring
    last = cells[-1]
    return back_g, "".join(lensed), front_g, ellipse_xy(ring_r(last[1]), angle(last[0])), cells, angle, slot


def month_scale(doc, cells, angle, slot):
    """Month ticks and labels on a ring just outside the data, in the disk plane."""
    rot = math.radians(TILT)
    r_t, r_l = R_OUT + 16, R_OUT + 34
    out, seen = [], set()
    for col, row, lvl, count, date in cells:
        d = datetime.date.fromisoformat(date)
        if d.day > 7 or (d.year, d.month) in seen:
            continue
        seen.add((d.year, d.month))
        t = angle(col) - slot * .5
        x1, y1 = kit.ellipse_point(CX, CY, r_t, r_t * FLAT, t, rot)
        x2, y2 = kit.ellipse_point(CX, CY, r_t + 9, (r_t + 9) * FLAT, t, rot)
        xl, yl = kit.ellipse_point(CX, CY, r_l + 8, (r_l + 8) * FLAT, t, rot)
        out.append(f'<path d="M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}" stroke="{WHITE}" stroke-opacity=".45" stroke-width=".8"/>')
        if 452 < xl < 975 and abs(math.cos(t)) > .45:                    # not on top of the black hole
            out.append(doc.text(d.strftime("%b").upper(), xl, yl + 3, 8.5, "mono-400", SILVER, .85, "middle", track=1.2))
    out.insert(0, f'<ellipse cx="{CX}" cy="{CY}" rx="{r_t}" ry="{f(r_t * FLAT)}" transform="rotate({TILT} {CX} {CY})" '
                  f'stroke="{SILVER}" stroke-opacity=".16" stroke-width=".8"/>')
    return "".join(out)


def stream(doc):
    """One slow violet stream, the only ambient motion in the plane besides the sweep."""
    vl = kit.ellipse_len(430, 128)
    return (f'<ellipse class="orb" cx="{CX}" cy="{CY}" rx="430" ry="128" transform="rotate({TILT + 4} {CX} {CY})" '
            f'stroke="{VIOLET}" stroke-opacity=".4" stroke-width="1" stroke-dasharray="1 9 44 9" '
            f'stroke-dashoffset="{f(vl)}" pathLength="{f(vl)}"/>')


def callout(doc, x0, y0, y1, title, sub, right=960):
    """Leader from a feature at (x0, y0) to a right-aligned two-line label on baseline row y1."""
    tw = max(kit.measure(title, 9.5, "mono-500", 1.8), kit.measure(sub, 9.5, "mono-400", 1))
    x2 = right - tw - 10
    x1 = min(x0 + abs(y1 - y0), x2 - 14)
    if x0 > x2 + 6:                                   # marker sits above the label: drop straight onto it
        leader = f'M{f(x0)} {f(y0)}V{f(y1 - 19)}'
    else:
        leader = f'M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}H{f(x2 + 2)}'
    return (f'<circle cx="{f(x0)}" cy="{f(y0)}" r="2.2" fill="{AMBER}"/>'
            f'<circle class="now" cx="{f(x0)}" cy="{f(y0)}" r="5" stroke="{AMBER}" stroke-width=".9"/>'
            f'<path d="{leader}" stroke="{SILVER}" stroke-opacity=".5" stroke-width=".7"/>'
            + doc.text(title, right, y1 - 5, 9.5, "mono-500", AMBER, .95, "end", track=1.8)
            + doc.text(sub, right, y1 + 11, 9.5, "mono-400", SILVER, .8, "end", track=1))


def build(profile, data):
    cells, cols = calendar(data)
    active = sum(1 for c in cells if c[3] > 0)
    last7 = sum(c[3] for c in cells[-7:])
    alt = (f'{profile["name"]}: {profile["tagline"]} A black hole whose accretion disk is the last 365 days of '
           f'GitHub activity: {data["total"]} contributions on {active} active days, {last7} in the last 7 days.')
    doc = kit.Doc(W, H, alt, CSS)
    clip = kit.plate(doc, density=0)

    g = []
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
        f'<filter id="blur3" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.4"/></filter>'
        f'<linearGradient id="scanG" x1="0" x2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{AMBER}" stop-opacity=".07"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>')
    g.append(f'<rect width="{W}" height="{H}" fill="url(#{lift})"/>')
    g.append(f'<rect width="{W}" height="{H}" fill="url(#{neb})"/>')
    g.append(kit.stars(3, W, H, 150, avoid=(CX, CY, 150)))
    g.append(f'<rect class="lum" width="{W}" height="{H}" fill="url(#{core})"/>')
    doc.define(f'<linearGradient id="fadeL" gradientUnits="userSpaceOnUse" x1="400" x2="520" y1="0" y2="0">'
               f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>'
               f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
               f'<rect width="{W}" height="{H}" fill="url(#fadeL)"/></mask>')
    g.append(f'<g mask="url(#fade)">{stream(doc)}</g>')

    back, lensed, front, now_xy, cells, angle, slot = disk(doc, data)
    glow = (f'<g filter="url(#blur8)" opacity=".75"><ellipse cx="{CX}" cy="{CY}" rx="{RS * 2.1}" ry="{RS * 2.1 * FLAT * 1.4}" '
            f'stroke="{AMBER}" stroke-width="10" stroke-opacity=".6"/>'
            f'<circle cx="{CX}" cy="{CY - 3}" r="{RS * 1.18}" stroke="{AMBER}" stroke-width="9" stroke-opacity=".55"/></g>')
    shadow = f'<circle cx="{CX}" cy="{CY}" r="{RS}" fill="#010102"/>'
    photon = (f'<g class="ring"><circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width="1.6" filter="url(#blur3)"/>'
              f'<circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width=".9"/></g>')
    g.append(f'<g transform="rotate({TILT} {CX} {CY})">{glow}{back}{lensed}{shadow}{photon}{front}</g>')
    g.append(month_scale(doc, cells, angle, slot))

    # the scan: a faint band of light crossing the plate
    g.append(f'<g class="scan" transform="translate(-200 0)"><rect x="-60" width="120" height="{H}" fill="url(#scanG)"/>'
             f'<rect x="-.4" width=".8" height="{H}" fill="{AMBER}" fill-opacity=".18"/></g>')

    # melt into the shared canvas below, then let the shared glows reach up into the hero
    doc.define(f'<linearGradient id="melt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VOID}" stop-opacity="0"/>'
               f'<stop offset="1" stop-color="{VOID}"/></linearGradient>')
    g.append(f'<rect y="{H - 130}" width="{W}" height="130" fill="url(#melt)"/>')
    import canvas
    g.append(canvas.grade(doc))          # the page's colour grade, continuous with the slice below
    g.append(canvas.glows(doc))

    # callouts: one physical, one real
    rot = math.radians(TILT)
    top = kit.ellipse_point(CX, CY - 1, 0, RS + 1.6, -math.pi / 2, rot)
    g.append(callout(doc, top[0] + 2, top[1], 136, "PHOTON SPHERE", "r = 1.5 rs  ·  light orbits"))
    nx, ny = CX + (now_xy[0] - CX) * math.cos(rot) - (now_xy[1] - CY) * math.sin(rot), \
        CY + (now_xy[0] - CX) * math.sin(rot) + (now_xy[1] - CY) * math.cos(rot)
    last7 = sum(c[3] for c in cells[-7:])
    g.append(callout(doc, nx, ny, 396, "LAST 7 DAYS", f"{last7} contributions  ·  newest edge"))

    # legend and totals
    active = sum(1 for c in cells if c[3] > 0)
    g.append(doc.text("RING = WEEKDAY  ·  ARC = WEEK  ·  GLOW = CONTRIBUTIONS", W - 40, H - 19, 9.5, "mono-400", SILVER, .6, "end", track=1.4))
    g.append(doc.text(f'{data["total"]} CONTRIBUTIONS  ·  {active} ACTIVE DAYS  ·  LAST 365 DAYS', W - 40, H - 36, 9.5, "mono-500", AMBER, .9, "end", track=1.4))

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
