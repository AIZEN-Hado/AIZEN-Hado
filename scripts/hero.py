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
import re

import canvas
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
       "@keyframes now{0%{transform:scale(.7);opacity:.9}100%{transform:scale(3);opacity:0}}"
       # Entrance. Every rule uses fill-mode `backwards`, so the resting style is the finished composition.
       ".ad{stroke-dasharray:1;animation:ad .55s cubic-bezier(.4,0,.2,1) backwards}"
       ".hot.ad{animation:ad .55s cubic-bezier(.4,0,.2,1) backwards,hot 5.5s ease-in-out infinite}"
       "@keyframes ad{from{stroke-dashoffset:1}}"
       ".rise{animation:rise 1.3s cubic-bezier(.16,1,.3,1) backwards}"
       "@keyframes rise{from{transform:translateY(var(--d,100px))}}"
       ".fin{animation:fin 1.2s ease-out backwards}@keyframes fin{from{opacity:0}}"
       ".dr{stroke-dasharray:24;animation:dr .9s cubic-bezier(.5,0,.2,1) .15s backwards}"
       "@keyframes dr{from{stroke-dashoffset:24}}"
       # Loops. Light rides the rings at Keplerian speed (period ~ r^1.5), a hot spot circles the photon ring,
       # and a warm wave runs through the letters of the name every ten seconds.
       ".orbit{transform-origin:0 0;animation:orbit linear infinite}@keyframes orbit{to{transform:rotate(360deg)}}"
       ".hs{animation:hs 6.5s linear infinite}@keyframes hs{to{stroke-dashoffset:-400}}"
       ".gw{opacity:0;animation:gw 10s ease-in-out infinite}"
       "@keyframes gw{0%{opacity:0}2.6%{opacity:.95}8%{opacity:0}100%{opacity:0}}")

LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
# stroke width, colour, opacity for each activity level
STYLE = {0: (.7, AMBER, .24), 1: (1.3, AMBER, .62), 2: (1.8, AMBER, .8), 3: (2.3, AMBER, .95), 4: (2.8, EMBER, 1)}


def halo(shape, width, peak, sigma, n=9):
    """What a Gaussian blur makes of a stroked outline, without a filter: n translucent strokes whose widths follow
    the blur profile, so the glow is brightest on the line and fades smoothly on both sides. `shape` holds the
    element's geometry; `peak` is the opacity at the centre of the glow. (A filter on a rotated group costs a
    full off-screen layer plus a resample on every frame; these are a handful of plain strokes.)"""
    out = []
    for i in range(1, n + 1):
        half = sigma * math.sqrt(-2 * math.log(i / n)) if i < n else 0
        out.append(shape.replace("/>", f' stroke-width="{f(width + 2 * half)}" stroke-opacity="{f(peak / n)}"/>'))
    return "".join(out)


def box(cx, cy, hx, hy):
    """x/y/width/height attributes for a box centred on (cx, cy) with half-extents hx, hy."""
    return f'x="{f(cx - hx)}" y="{f(cy - hy)}" width="{f(2 * hx)}" height="{f(2 * hy)}"'


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
    back, front = [], []
    r = R_IN - 26
    while r < R_OUT + 8:
        u = max(0, (r - R_IN) / (R_OUT - R_IN))
        op = (1 - u) ** 1.5 * .5 + .06
        ry = r * FLAT
        # a solid colour per ring, white-hot at the inner edge and amber outward. (Each ring used to carry a
        # horizontal colour gradient, which cost more to paint than any other part of the disk.)
        col = canvas.mix(AMBER, EMBER, .6 * (1 - u) ** 2)
        back.append(f'<path d="{kit.arc_half(CX, CY, r, ry, True)}" stroke="{col}" stroke-opacity="{f(op * .6)}" stroke-width=".5"/>')
        front.append(f'<path d="{kit.arc_half(CX, CY, r, ry, False)}" stroke="{col}" stroke-opacity="{f(op)}" stroke-width=".5"/>')
        r += 4.2 + u * 3.2
    return "".join(back), "".join(front)


def disk(doc, data):
    """Return (back, lensed, front, today_xy). Everything is in the unrotated disk frame."""
    cells, cols = calendar(data)
    slot = 2 * math.pi / cols
    angle = lambda col: T_NOW + slot * (col - (cols - 1))           # centre of a week
    layers = {(b, r): [] for b in (True, False) for r in range(7)}   # b True = back half (above the shadow)
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
        # the year draws itself: each arc strokes in, oldest week first, ring by ring (no masks: they force every
        # frame through off-screen layers, which doubled the cost of the image)
        draw = .5 + row * .16 + (col / max(1, cols - 1)) * 2.4
        if lvl >= 3:
            cls = f' class="hot ad" pathLength="1" style="animation-delay:{draw:.2f}s,-{(hot_n * 1.37) % 5.5:.1f}s"'
            hot_n += 1
        else:
            cls = f' class="ad" pathLength="1" style="animation-delay:{draw:.2f}s"'
        layers[(back, row)].append(f'<path{cls} d="{d}" stroke="{color}" stroke-opacity="{f(op)}" stroke-width="{w}" stroke-linecap="round"/>')
        if lvl >= 2:
            k = .6 if back else 1
            glows[back].append(f'<path d="{d}" stroke="{AMBER}" stroke-opacity="{f(.25 * k)}" stroke-width="{f(w + 7)}" stroke-linecap="round"/>'
                               f'<path d="{d}" stroke="{AMBER}" stroke-opacity="{f(.43 * k)}" stroke-width="{f(w + 3.4)}" stroke-linecap="round"/>')

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

    # Light riding the rings. Decorative, drawn over the data, and removed under reduced motion.
    def orbiters(back):
        out = []
        for row in range(7):
            r = ring_r(row)
            period = 15 * (r / R_IN) ** 1.5
            n_c = 1 if row < 3 else 2
            for k in range(n_c):
                segs = []
                for i in range(6):
                    a0, a1 = -i * .157, -(i + 1) * .157
                    op = .85 * (1 - i / 6) ** 1.5 * (.62 if back else 1)
                    col = "#FFE3BD" if i == 0 else AMBER
                    segs.append(f'<path d="M{f(r * math.cos(a0))} {f(r * math.sin(a0))}A{f(r)} {f(r)} 0 0 0 '
                                f'{f(r * math.cos(a1))} {f(r * math.sin(a1))}" stroke="{col}" stroke-opacity="{f(op)}" '
                                f'stroke-width="{f(2.1 - i * .2)}" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
                phase = (row * 1.9 + k * period / n_c) % period
                out.append(f'<g class="orbit" style="animation-duration:{period:.1f}s;animation-delay:-{phase:.1f}s">{"".join(segs)}</g>')
        return (f'<g class="fx fin" style="animation-delay:3.4s" transform="translate({CX} {CY}) scale(1 {FLAT})">'
                f'{"".join(out)}</g>')

    def glow_layer(back):
        return f'<g class="fin" style="animation-delay:2.1s">{"".join(glows[back])}</g>'

    back_g = f'<g clip-path="url(#{cb})">{dust_b}{glow_layer(True)}{"".join(a for r in range(7) for a in layers[(True, r)])}{orbiters(True)}{beam}</g>'
    front_g = f'<g clip-path="url(#{cf})">{dust_f}{glow_layer(False)}{"".join(a for r in range(7) for a in layers[(False, r)])}{orbiters(False)}{beam}</g>'

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
    """One slow violet stream, the only ambient motion in the plane besides the sweep. It fades in from the left
    through its own stroke gradient (a mask would cost a full-canvas off-screen layer on every frame)."""
    vl = kit.ellipse_len(430, 128)
    fid = doc.uid("fv")
    doc.define(f'<linearGradient id="{fid}" gradientUnits="userSpaceOnUse" x1="400" x2="520" y1="0" y2="0" '
               f'gradientTransform="rotate({-(TILT + 4)} {CX} {CY})">'      # undo the ellipse's own rotation
               f'<stop offset="0" stop-color="{VIOLET}" stop-opacity="0"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>')
    return (f'<ellipse class="orb" cx="{CX}" cy="{CY}" rx="430" ry="128" transform="rotate({TILT + 4} {CX} {CY})" '
            f'stroke="url(#{fid})" stroke-opacity=".4" stroke-width="1" stroke-dasharray="1 9 44 9" '
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


def infall(doc):
    """Matter spiralling into the hole: ~22 grains on spiral paths that speed up as they fall, each with a short
    tail, fading toward ember as they near the photon ring (gravitational redshift). Purely decorative (.fx)."""
    import random
    rng = random.Random(11)
    cx = doc.uid("pc")
    hole = (f"M{CX - RS * 1.04} {CY}A{f(RS * 1.04)} {f(RS * 1.04)} 0 1 0 {f(CX + RS * 1.04)} {CY}"
            f"A{f(RS * 1.04)} {f(RS * 1.04)} 0 1 0 {f(CX - RS * 1.04)} {CY}Z")
    # outside the shadow everywhere, and anything in the front half (it passes in front of the hole)
    doc.define(f'<clipPath id="{cx}"><path clip-rule="evenodd" d="M-500 -500H1700V1100H-500Z{hole}"/>'
               f'<rect x="-500" y="{CY}" width="2400" height="600"/></clipPath>')
    paths, grains = [], []
    for i in range(22):
        a0 = rng.uniform(0, 2 * math.pi)
        r0 = R_OUT * rng.uniform(.86, 1.06)
        sweep = rng.uniform(1.15, 1.75) * 2 * math.pi
        pts = []
        n = 56
        for k in range(n + 1):
            u = k / n
            r = RS * 1.06 + (r0 - RS * 1.06) * (1 - u) ** 1.35
            x, y = ellipse_xy(r, a0 + sweep * u)
            pts.append(f"{'M' if k == 0 else 'L'}{f(x)} {f(y)}")
        pid = doc.uid("fp")
        doc.define(f'<path id="{pid}" d="{"".join(pts)}"/>')
        dur = rng.uniform(7.5, 13)
        begin = -rng.uniform(0, dur)
        size = rng.uniform(.9, 1.6)
        hot = rng.random() < .3
        for tail, (lag, op, sc) in enumerate(((0, .95, 1), (.12, .45, .75))):
            fill = WHITE if (hot and tail == 0) else AMBER
            grains.append(
                f'<circle r="{f(size * sc)}" fill="{fill}" opacity="0">'
                f'<animateMotion dur="{dur:.2f}s" begin="{begin - lag:.2f}s" repeatCount="indefinite" calcMode="spline" '
                f'keyPoints="0;1" keyTimes="0;1" keySplines=".45 0 .9 .55"><mpath href="#{pid}"/></animateMotion>'
                f'<animate attributeName="opacity" dur="{dur:.2f}s" begin="{begin - lag:.2f}s" repeatCount="indefinite" '
                f'values="0;{op};{op};0" keyTimes="0;.1;.8;1"/>'
                + (f'<animate attributeName="fill" dur="{dur:.2f}s" begin="{begin - lag:.2f}s" repeatCount="indefinite" '
                   f'values="{fill};{fill};{EMBER}" keyTimes="0;.6;1"/>' if tail == 0 else "") + '</circle>')
    return f'<g class="fx fin" style="animation-delay:2.6s" clip-path="url(#{cx})">{"".join(grains)}</g>'


def hotspot():
    """A bright knot circling the photon ring: light that has orbited the hole once, brightest where it comes toward us."""
    r = RS + 1.6
    return (f'<g class="fx fin" style="animation-delay:3s">'
            f'<circle class="hs" cx="{CX}" cy="{CY - 1}" r="{f(r)}" stroke="{WHITE}" stroke-width="2.4" stroke-linecap="round" '
            f'stroke-dasharray="9 391" stroke-opacity=".95"/>'
            f'<circle class="hs" style="animation-delay:-3.25s" cx="{CX}" cy="{CY - 1}" r="{f(r)}" stroke="{AMBER}" stroke-width="2" '
            f'stroke-linecap="round" stroke-dasharray="5 395" stroke-opacity=".7"/></g>')


def glint_wave(text, lag):
    """Turn one run of glyphs into a travelling pulse: each letter lights a moment after the one to its left."""
    k = float(re.search(r"scale\(([\d.]+) ", text).group(1))
    def one(m):
        pen = float(m.group(2)) * k                       # the letter's distance from the start of the line, in px
        return f'<use class="gw" style="animation-delay:{4.2 + lag + pen / 330:.2f}s" href="#{m.group(1)}" x="{m.group(2)}"/>'
    return re.sub(r'<use href="#([^"]+)" x="([^"]+)"/>', one, text)


def rise(doc, content, y0, y1, delay, dist=100, x0=30, x1=620):
    """Reveal `content` by lifting it out of a clip box (a line rising from behind a mask)."""
    cid = doc.uid("rc")
    doc.define(f'<clipPath id="{cid}"><rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}"/></clipPath>')
    return f'<g clip-path="url(#{cid})"><g class="rise" style="--d:{dist}px;animation-delay:{delay:.2f}s">{content}</g></g>'


def build(profile, data):
    cells, cols = calendar(data)
    active = sum(1 for c in cells if c[3] > 0)
    last7 = sum(c[3] for c in cells[-7:])
    alt = (f'{profile["name"]}: {profile["tagline"]} A black hole whose accretion disk is the last 365 days of '
           f'GitHub activity: {data["total"]} contributions on {active} active days, {last7} in the last 7 days.')
    doc = kit.Doc(W, H, alt, CSS)
    clip = kit.plate(doc, density=0, bg=False)      # the opaque `lift` below covers a plate background completely

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
        f'<linearGradient id="scanG" x1="0" x2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{AMBER}" stop-opacity=".07"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>')
    g.append(f'<rect width="{W}" height="{H}" fill="url(#{lift})"/>')
    g.append(f'<rect {canvas.extent(905, 92, 330, W, H)} fill="url(#{neb})"/>')
    g.append(kit.stars(3, W, H, 150, avoid=(CX, CY, 150)))
    g.append(f'<rect class="lum" {canvas.extent(CX, CY, 300, W, H)} fill="url(#{core})"/>')
    g.append(stream(doc))

    back, lensed, front, now_xy, cells, angle, slot = disk(doc, data)
    # the bloom around the hole: two soft rings, as stacked strokes (see halo)
    glow = (halo(f'<ellipse cx="{CX}" cy="{CY}" rx="{RS * 2.1}" ry="{RS * 2.1 * FLAT * 1.4}" stroke="{AMBER}"/>', 10, .21, 8.4) +
            halo(f'<circle cx="{CX}" cy="{CY - 3}" r="{RS * 1.18}" stroke="{AMBER}"/>', 9, .176, 8.4))
    shadow = f'<circle cx="{CX}" cy="{CY}" r="{RS}" fill="#010102"/>'
    photon = (f'<g class="ring"><circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width="8" stroke-opacity=".08"/>'
              f'<circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width="4.4" stroke-opacity=".13"/>'
              f'<circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width="2.2" stroke-opacity=".14"/>'
              f'<circle cx="{CX}" cy="{CY - 1}" r="{RS + 1.6}" stroke="{EMBER}" stroke-width=".9"/></g>')
    g.append(f'<g transform="rotate({TILT} {CX} {CY})">{glow}{back}{lensed}{shadow}{photon}{front}{infall(doc)}{hotspot()}</g>')
    g.append(month_scale(doc, cells, angle, slot))

    # the scan: a faint band of light crossing the plate
    g.append(f'<g class="scan" transform="translate(-200 0)"><rect x="-60" width="120" height="{H}" fill="url(#scanG)"/>'
             f'<rect x="-.4" width=".8" height="{H}" fill="{AMBER}" fill-opacity=".18"/></g>')

    # melt into the shared canvas below, then let the shared glows reach up into the hero
    doc.define(f'<linearGradient id="melt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VOID}" stop-opacity="0"/>'
               f'<stop offset="1" stop-color="{VOID}"/></linearGradient>')
    g.append(f'<rect y="{H - 130}" width="{W}" height="130" fill="url(#melt)"/>')
    g.append(canvas.grade_strip(doc, H - 130))      # the page's colour grade, ramped in so it meets the slice below exactly
    g.append(canvas.glows(doc))

    # callouts: one physical, one real
    rot = math.radians(TILT)
    top = kit.ellipse_point(CX, CY - 1, 0, RS + 1.6, -math.pi / 2, rot)
    g.append(f'<g class="fin" style="animation-delay:1.2s">'
             + callout(doc, top[0] + 2, top[1], 136, "PHOTON SPHERE", "r = 1.5 rs  ·  light orbits") + '</g>')
    nx, ny = CX + (now_xy[0] - CX) * math.cos(rot) - (now_xy[1] - CY) * math.sin(rot), \
        CY + (now_xy[0] - CX) * math.sin(rot) + (now_xy[1] - CY) * math.cos(rot)
    last7 = sum(c[3] for c in cells[-7:])
    g.append(f'<g class="fin" style="animation-delay:3.3s">'
             + callout(doc, nx, ny, 396, "LAST 7 DAYS", f"{last7} contributions  ·  newest edge") + '</g>')

    # legend and totals
    active = sum(1 for c in cells if c[3] > 0)
    g.append(doc.text("RING = WEEKDAY  ·  ARC = WEEK  ·  GLOW = CONTRIBUTIONS", W - 40, H - 19, 9.5, "mono-400", SILVER, .6, "end", track=1.4))
    g.append(doc.text(f'{data["total"]} CONTRIBUTIONS  ·  {active} ACTIVE DAYS  ·  LAST 365 DAYS', W - 40, H - 36, 9.5, "mono-500", AMBER, .9, "end", track=1.4))

    x = 58
    g.append(f'<path class="dr" d="M{x} 116h22" stroke="{AMBER}" stroke-width="1.4"/>')
    g.append(rise(doc, doc.text(profile["kicker"], x + 34, 120, 10.5, "mono-500", AMBER, 1, track=3.2), 100, 130, .3, 40))
    first = doc.text(profile["first"], x - 3, 212, 80, "serif", WHITE)
    last = doc.text(profile["last"], x - 1, 290, 80, "serif-i", WHITE)
    g.append(rise(doc, first, 136, 238, .45, 130))
    g.append(rise(doc, last, 222, 316, .62, 130))
    ty = 350
    for i, line in enumerate(profile["tagline_lines"]):
        g.append(rise(doc, doc.text(line, x, ty + i * 30, 21, "sans-300", WHITE if i else SILVER, 1 if i else .95),
                      ty + i * 30 - 24, ty + i * 30 + 10, .95 + i * .14, 44))
    fy = 446
    cx = x
    chips = []
    for i, item in enumerate(profile["focus"]):
        chips.append(f'<rect x="{f(cx)}" y="{fy - 7}" width="5" height="5" fill="{AMBER}" transform="rotate(45 {f(cx + 2.5)} {fy - 4.5})"/>')
        chips.append(doc.text(item, cx + 14, fy, 10, "mono-400", WHITE, .78, track=2))
        cx += 14 + kit.measure(item, 10, "mono-400", 2) + 26
    g.append(rise(doc, "".join(chips), fy - 20, fy + 10, 1.4, 34))

    # a warm wave through the letters of the name every ten seconds: the same two lines again, one glyph at a time.
    # (Per-glyph opacity costs nothing while idle. A moving mask costs a full off-screen layer on every frame.)
    n_keep = len(kit.LAYOUT.keep)
    glint_txt = (glint_wave(doc.text(profile["first"], x - 3, 212, 80, "serif", "#FFC98A"), 0) +
                 glint_wave(doc.text(profile["last"], x - 1, 290, 80, "serif-i", "#FFC98A"), .35))
    del kit.LAYOUT.keep[n_keep:]                       # the text is already reserved above
    g.append(f'<g class="fx">{glint_txt}</g>')

    g.append(kit.registration(doc))
    g.append(kit.corner_labels(doc, tl="PLATE 00  /  EVENT HORIZON STUDY", tr=profile["handle"].upper() + "  /  2026",
                               bl=profile["coords"], br=""))
    doc.add(f'<g clip-path="url(#{clip})">{"".join(g)}</g>', kit.plate_border(doc))
    return doc
