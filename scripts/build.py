#!/usr/bin/env python3
"""Render the whole profile: every SVG slice, scripts/canvas.json and README.md.

  python3 scripts/build.py

The profile is one tall dark canvas cut into horizontal slices, one image each, stacked in the README with
no gaps. A shared background (void, glows, stars, a living neural constellation) runs behind all of them in
page coordinates, so it continues across every seam. Two passes: the first records where every word and
illustration sits; the second draws the background around them. Standard library only.
"""
import json
import math

import arts
import canvas
import hero
import kit
import telemetry
from kit import AMBER, EMBER, SILVER, VIOLET, WHITE, f

P = json.loads((kit.ROOT / "scripts" / "profile.json").read_text(encoding="utf-8"))
DATA = json.loads(telemetry.CACHE.read_text(encoding="utf-8"))
W, M = 1000, 56                     # canvas width, text margin


class Dry(kit.Doc):
    """A throwaway document for measuring wrapped text without touching the layout."""

    def keep(self, *a):
        pass


def lines_of(segments, size, max_w):
    return kit.paragraph(Dry(W, 10, ""), segments, 0, 0, size, max_w, 1)[1]


def finish(doc, clip, parts, name, link=None):
    doc.add(f'<g clip-path="url(#{clip})">{"".join(parts)}</g>')
    doc.save(name, link)


# ================================================================================================ bands
BAND_CSS = (".sweep{animation:sweep 12s cubic-bezier(.6,0,.4,1) infinite}"
            "@keyframes sweep{0%{transform:translateX(-120px)}55%,100%{transform:translateX(1000px)}}"
            ".spin{transform-origin:64px 100px;animation:spin 9s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}")


def band(b, i):
    H = 150
    doc = kit.Doc(W, H, f'{b["n"]}. {"".join(b["title"]).strip()}', BAND_CSS)
    clip = kit.plate(doc, density=.95, glow=(880 if i % 2 == 0 else 120, 80, 430, VIOLET if i % 2 == 0 else AMBER, .075))
    g = [f'<circle cx="64" cy="100" r="11" stroke="{SILVER}" stroke-opacity=".55" stroke-width=".8"/>',
         f'<circle cx="64" cy="100" r="2.2" fill="{WHITE}"/>',
         f'<g class="spin" style="animation-delay:-{i * 1.3:.1f}s"><circle cx="75" cy="100" r="2.3" fill="{AMBER}"/></g>',
         doc.text(b["n"], M, 66, 11, "mono-500", AMBER, 1, track=2)]
    doc.keep(46, 82, 84, 118)
    lead, key = b["title"]
    x = 98
    if lead:
        g.append(doc.text(lead, x, 116, 50, "serif", WHITE))
        x += kit.measure(lead, 50, "serif")
    g.append(doc.text(key, x, 116, 50, "serif-i", WHITE))
    for k, line in enumerate(b["note"]):
        g.append(doc.text(line, W - M, 94 + k * 17, 9.5, "mono-400", SILVER, .9, "end", track=2))
    y = 138
    ticks = "".join(f"M{f(M + t)} {y}v{-5 if t % 120 == 0 else -2.5}" for t in range(0, W - 2 * M + 1, 24))
    sw, cl = doc.uid("sw"), doc.uid("rc")
    doc.define(f'<linearGradient id="{sw}" x1="0" x2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>'
               f'<stop offset=".8" stop-color="{AMBER}"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>'
               f'<clipPath id="{cl}"><rect x="{M}" y="{y - 3}" width="{W - 2 * M}" height="6"/></clipPath>')
    g += [f'<path d="M{M} {y}H{W - M}" stroke="#2A2F3E"/>', f'<path d="{ticks}" stroke="#2A2F3E"/>',
          f'<path d="M{M} {y}H{M + 44}" stroke="{AMBER}" stroke-width="2"/>',
          f'<g clip-path="url(#{cl})"><rect class="sweep" style="animation-delay:-{i * 1.7:.1f}s" x="0" y="{y - 1}" '
          f'width="110" height="2" fill="url(#{sw})"/></g>']
    doc.keep(M - 8, y - 8, W - M + 8, y + 6)
    finish(doc, clip, g, f'band-{b["n"]}-{b["id"]}.svg')


# ================================================================================================ identity
def identity():
    t = P["identity"]
    segs = [(t["lead"], "sans-300", WHITE, .86), (" " + t["bold"], "sans-500", WHITE, 1), (" " + t["tail"], "sans-300", WHITE, .86)]
    size, lead, top = 23, 37, 58
    n = lines_of(segs, size, 860)
    H = top + (n - 1) * lead + 150
    alt = f'{t["lead"]} {t["bold"]} {t["tail"]} {t["rule_lead"]} {t["rule"]}'
    doc = kit.Doc(W, H, alt)
    clip = kit.plate(doc, density=.8)
    body, _ = kit.paragraph(doc, segs, M, top, size, 860, lead)
    y = top + (n - 1) * lead + 56
    rl = t["rule_lead"] + "  "
    g = [body, doc.text(rl, M, y, 19, "sans-300", SILVER, .95),
         doc.text(t["rule"], M + kit.measure(rl, 19, "sans-300"), y + 1, 25, "serif-i", WHITE),
         f'<rect x="{M}" y="{y + 32}" width="10" height="1.5" fill="{AMBER}"/>',
         doc.text(t["meta"], M + 18, y + 37, 10, "mono-400", SILVER, .95, track=2)]
    finish(doc, clip, g, "identity.svg")


# ================================================================================================ research vectors
def research_grid():
    H = 500
    alt = "Currently exploring: " + "; ".join(f'{" ".join(v["title"])} ({v["keys"].replace("  ·  ", ", ").lower()})'
                                              for v in P["vectors"])
    doc = kit.Doc(W, H, alt, arts.GRID_CSS)
    clip = kit.plate(doc, density=.45)
    g = [kit.panel(doc),
         f'<path d="M{W / 2} 52V{H - 46}M44 {H / 2}H{W - 44}" stroke="{WHITE}" stroke-opacity=".08"/>',
         f'<path d="M{W / 2 - 5} {H / 2}h10M{W / 2} {H / 2 - 5}v10" stroke="{AMBER}" stroke-opacity=".8"/>']
    for k, v in enumerate(P["vectors"]):
        ox, oy = (k % 2) * 500, (k // 2) * (H / 2 - 6) + 16
        icx, icy = ox + 140, oy + 118
        g.append(f'<circle cx="{icx}" cy="{icy}" r="92" stroke="{WHITE}" stroke-opacity=".05"/>')
        g.append(arts.ARTS[v["art"]](doc, icx, icy))
        tx = ox + 262
        g.append(doc.text(v["n"], tx, oy + 66, 10, "mono-500", AMBER, 1, track=3))
        g.append(doc.text(v["title"][0], tx, oy + 108, 31, "serif", WHITE))
        g.append(doc.text(v["title"][1], tx, oy + 142, 31, "serif-i", WHITE))
        for i, key in enumerate(v["keys"].split("  ·  ")):
            g.append(f'<rect x="{tx}" y="{oy + 166 + i * 17}" width="3" height="3" fill="{AMBER}" fill-opacity=".8"/>')
            g.append(doc.text(key, tx + 11, oy + 171 + i * 17, 9.5, "mono-400", SILVER, .9, track=1.6))
    g.append(kit.registration(doc))
    g.append(kit.corner_labels(doc, tl="FIG. 2  /  RESEARCH VECTORS", tr="ACTIVE  ·  NOV 2026"))
    finish(doc, clip, g, "research-grid.svg")


# ================================================================================================ arsenal
def arsenal():
    rows = P["stack"]
    row_h, top = 62, 70
    H = top + row_h * len(rows) + 46
    alt = "Engineering arsenal. " + " ".join(f'{cat}: {", ".join(items)}.' for cat, items in rows)
    doc = kit.Doc(W, H, alt)
    clip = kit.plate(doc, density=.45)
    g = [kit.panel(doc)]
    for i, (cat, items) in enumerate(rows):
        y = top + i * row_h
        base = y + 38
        g.append(f'<path d="M44 {y + row_h}H{W - 44}" stroke="{WHITE}" stroke-opacity=".07"/>')
        g.append(doc.text(f"0{i + 1}", M, base - 1, 9.5, "mono-500", AMBER, 1, track=2))
        g.append(doc.text(cat, 84, base - 1, 9.5, "mono-400", SILVER, .95, track=2.6))
        x0, x1, size = 262, W - M, 20
        widths = [kit.measure(it, size, "sans-400") for it in items]
        gap = min(40, (x1 - x0 - sum(widths)) / max(len(items) - 1, 1))
        x = x0
        for j, (it, w) in enumerate(zip(items, widths)):
            if j:
                g.append(f'<rect x="{f(x - gap / 2 - 2)}" y="{base - 8}" width="4" height="4" fill="{SILVER}" '
                         f'fill-opacity=".45" transform="rotate(45 {f(x - gap / 2)} {base - 6})"/>')
            g.append(doc.text(it, x, base, size, "sans-400", WHITE, .94))
            x += w + gap
    g.append(f'<path d="M44 {top}H{W - 44}" stroke="{WHITE}" stroke-opacity=".07"/>')
    g.append(kit.registration(doc))
    g.append(kit.corner_labels(doc, tl="FIG. 3  /  STACK MANIFEST", tr="USED IN REAL PROJECTS"))
    finish(doc, clip, g, "arsenal.svg")


# ================================================================================================ selected work
def shown_projects():
    """Projects with "show": true. A private repository would 404 for visitors, so it is never shown."""
    out = []
    for pr in P["projects"]:
        if pr.get("show") and pr.get("private"):
            raise SystemExit(f'{pr["repo"]} is private: make it public before setting "show": true')
        if pr.get("show"):
            out.append(pr)
    return out


def card(pr, k, link):
    H = 250
    alt = (f'W.{k + 1:02d} {pr["name"]}: {pr["line"]}. {pr["status"].replace("  ·  ", ", ")}. '
           f'Stack: {pr["stack"].replace("  ·  ", ", ")}. Opens the repository.')
    doc = kit.Doc(W, H, alt, arts.CARD_CSS)
    clip = kit.plate(doc, density=.95, glow=(780, 125, 320, AMBER if k % 2 == 0 else VIOLET, .085))
    g = [kit.panel(doc)]
    n = f"W.{k + 1:02d}"
    g.append(doc.text(n, M, 58, 10, "mono-500", AMBER, 1, track=3))
    nw = kit.measure(n, 10, "mono-500", 3)
    g.append(f'<path d="M{f(M + nw + 12)} 54.5h26" stroke="{SILVER}" stroke-opacity=".5"/>')
    g.append(doc.text(pr["status"], M + nw + 48, 58, 9.5, "mono-400", SILVER, .9, track=2))
    g.append(doc.text(pr["name"], M - 2, 126, 62, "serif", WHITE))
    for i, line in enumerate(kit.balanced(pr["line"], 18.5, "sans-300", 470)):
        g.append(doc.text(line, M, 164 + i * 25, 18.5, "sans-300", WHITE, .82))
    g.append(doc.text(pr["stack"], M, 216, 9, "mono-400", WHITE, .6, track=1.8))
    g.append(f'<path d="M560 40V{H - 40}" stroke="{WHITE}" stroke-opacity=".07"/>')
    g.append(arts.CARD_ARTS[pr["art"]](doc, 612, 14))
    g.append(doc.text("OPEN REPOSITORY ↗", W - 40, H - 20, 9, "mono-500", AMBER, .95, "end", track=2))
    g.append(kit.registration(doc, inset=22, arm=7))
    finish(doc, clip, g, f'work-{k + 1}-{pr["art"]}.svg', link)


def caption(pr, k, link):
    about = [(pr["about"], "sans-300", WHITE, .86)]
    why = [(pr["why"], "sans-300", SILVER, 1)]
    na, nw = lines_of(about, 19.5, W - 2 * M), lines_of(why, 16.5, W - 2 * M)
    top = 46
    H = top + (na - 1) * 31 + 34 + 26 + (nw - 1) * 27 + 56
    doc = kit.Doc(W, H, f'{pr["about"]} Why it is interesting: {pr["why"]}')
    clip = kit.plate(doc, density=.85)
    a, _ = kit.paragraph(doc, about, M, top, 19.5, W - 2 * M, 31)
    y = top + (na - 1) * 31 + 40
    w, _ = kit.paragraph(doc, why, M, y + 26, 16.5, W - 2 * M, 27)
    lw = kit.measure("WHY IT'S INTERESTING", 9.5, "mono-500", 2.4)
    g = [a, doc.text("WHY IT'S INTERESTING", M, y, 9.5, "mono-500", AMBER, 1, track=2.4),
         f'<path d="M{f(M + lw + 14)} {y - 3.5}h40" stroke="{AMBER}" stroke-opacity=".45"/>', w]
    finish(doc, clip, g, f'work-{k + 1}-notes.svg', link)


def also():
    doc = kit.Doc(W, 70, "Also in orbit")
    clip = kit.plate(doc, density=.85)
    finish(doc, clip, [doc.text("ALSO IN ORBIT", M, 50, 10, "mono-500", AMBER, 1, track=3),
                       f'<path d="M{M} 64H{W - M}" stroke="{WHITE}" stroke-opacity=".1"/>'], "also-0.svg")
    for i, a in enumerate(P.get("also", [])):
        doc = kit.Doc(W, 56, f'{a["name"]}: {a["note"]}. Opens the repository.')
        clip = kit.plate(doc, density=.6)
        g = [doc.text(a["name"], M, 36, 24, "serif", WHITE),
             doc.text(a["note"], 300, 35, 15.5, "sans-300", SILVER, 1),
             doc.text("↗", W - M, 35, 16, "sans-400", AMBER, 1, "end"),
             f'<path d="M{M} 55H{W - M}" stroke="{WHITE}" stroke-opacity=".08"/>']
        finish(doc, clip, g, f'also-{i + 1}.svg', f'https://github.com/{P["handle"]}/{a["repo"]}')


# ================================================================================================ frontier
FRONTIER_CSS = (".rail{animation:rail 3.4s ease-out infinite}"
                "@keyframes rail{0%{transform:scale(.6);opacity:.7}100%{transform:scale(2.4);opacity:0}}")


def frontier():
    notes, x, width = P["frontier"], 132, W - 132 - M
    blocks = []
    for nt in notes:
        nb = lines_of([(nt["body"], "sans-300", WHITE, 1)], 18.5, width)
        na = lines_of([("WORKING ANSWER  " + nt["answer"], "mono-400", SILVER, 1)], 10.5, width)
        blocks.append((nb, na, 104 + (nb - 1) * 29 + 34 + na * 18 + 70))
    H = 30 + sum(b[2] for b in blocks)
    alt = "Research frontier. " + " ".join(f'{n["q"]}: {n["title"]} {n["body"]} Working answer: {n["answer"]}.'
                                           for n in notes)
    doc = kit.Doc(W, H, alt, FRONTIER_CSS)
    clip = kit.plate(doc, density=.8)
    g, y, ys = [], 30, []
    for nt, (nb, na, h) in zip(notes, blocks):
        ys.append(y + 30)
        g.append(doc.text(nt["q"], x, y + 30, 10.5, "mono-500", AMBER, 1, track=2.4))
        g.append(doc.text(nt["title"], x, y + 70, 31, "serif", WHITE))
        body, _ = kit.paragraph(doc, [(nt["body"], "sans-300", WHITE, .84)], x, y + 104, 18.5, width, 29)
        g.append(body)
        yy = y + 104 + (nb - 1) * 29 + 34
        ans, _ = kit.paragraph(doc, [("WORKING ANSWER ", "mono-500", AMBER, 1), (" " + nt["answer"], "mono-400", SILVER, 1)],
                               x, yy, 10.5, width, 18)
        g.append(ans)
        g.append(doc.text(f'INSTRUMENT  ·  {nt["instrument"]}', x, yy + na * 18 + 6, 10.5, "mono-400", SILVER, .7, track=1))
        y += h
    g.insert(0, f'<path d="M72 {ys[0]}V{ys[-1]}" stroke="{WHITE}" stroke-opacity=".12"/>')
    doc.keep(60, ys[0] - 14, 84, ys[-1] + 10)
    for i, yy in enumerate(ys):
        g.append(f'<circle cx="72" cy="{yy - 4}" r="6" fill="#050508" stroke="{AMBER}" stroke-opacity=".7"/>'
                 f'<circle cx="72" cy="{yy - 4}" r="2.4" fill="{AMBER if i == 0 else SILVER}"/>')
        if i == 0:
            g.append(f'<circle class="rail" style="transform-origin:72px {yy - 4}px" cx="72" cy="{yy - 4}" r="6" stroke="{AMBER}"/>')
    finish(doc, clip, g, "frontier.svg")


# ================================================================================================ contact
CONTACT_CSS = (".carrier{animation:carrier 6s linear infinite}@keyframes carrier{to{transform:translateX(-160px)}}"
               ".led{animation:led 2.4s ease-in-out infinite}@keyframes led{50%{opacity:.25}}"
               ".bar{transform-box:fill-box;transform-origin:bottom;animation:bar 1.8s ease-in-out infinite}"
               "@keyframes bar{50%{transform:scaleY(.35)}}")


def contact():
    H = 300
    c = P["contact"]
    doc = kit.Doc(W, H, "Uplink open. " + " ".join(c["headline"]) + " Transmitting from Bhopal, India.", CONTACT_CSS)
    clip = kit.plate(doc, density=.5, glow=(860, 70, 340, VIOLET, .15))
    g = [kit.panel(doc), f'<circle class="led" cx="62" cy="66" r="3.5" fill="{AMBER}"/>',
         doc.text("UPLINK OPEN", 76, 70, 10, "mono-500", AMBER, 1, track=3),
         doc.text(c["headline"][0], 54, 124, 40, "serif", WHITE),
         doc.text(c["headline"][1], 54, 168, 40, "serif-i", WHITE)]
    y0 = 236
    pts = []
    for i in range(0, 1361, 2):
        x = i - 40
        env = .25 + .75 * abs(math.sin(math.pi * x / 160)) ** 3
        pts.append((x, y0 - 16 * env * math.sin(2 * math.pi * x / 16)))
    d = "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts)
    fade = doc.uid("fd")
    doc.define(f'<linearGradient id="{fade}" gradientUnits="userSpaceOnUse" x1="40" x2="960" y1="0" y2="0">'
               f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".22" stop-color="#fff"/>'
               f'<stop offset=".78" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
               f'<mask id="wm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#{fade})"/></mask>')
    g += [f'<path d="M40 {y0}H960" stroke="{WHITE}" stroke-opacity=".08"/>',
          f'<g mask="url(#wm)"><g class="carrier"><path d="{d}" stroke="{AMBER}" stroke-width="1.2"/></g></g>',
          doc.text("TX", 56, y0 + 38, 9, "mono-500", SILVER, .8, track=2),
          doc.text(P["coords"], 82, y0 + 38, 9, "mono-400", SILVER, .6, track=1.6),
          doc.text("RX  ·  ANYWHERE", W - 56, y0 + 38, 9, "mono-400", SILVER, .7, "end", track=1.6)]
    for i, hgt in enumerate((8, 13, 18, 23)):
        g.append(f'<rect class="bar" style="animation-delay:{i * .2:.1f}s" x="{904 + i * 9}" y="{86 - hgt}" width="5" '
                 f'height="{hgt}" fill="{AMBER if i < 3 else SILVER}" fill-opacity="{1 if i < 3 else .4}"/>')
    g.append(doc.text("SIGNAL", W - 59, 102, 8.5, "mono-400", SILVER, .7, "end", track=1.6))
    g.append(kit.registration(doc))
    g.append(kit.corner_labels(doc, tl="FIG. 7  /  COMMUNICATIONS", tr=f'{("ZERO ONE TWO THREE FOUR FIVE SIX").split()[len(P["contact"]["channels"])]} CHANNEL{"" if len(P["contact"]["channels"]) == 1 else "S"} BELOW'))
    finish(doc, clip, g, "contact-terminal.svg")


def channel(ch, k):
    H = 76
    doc = kit.Doc(W, H, f'Channel {k + 1}, {ch["label"]}: {ch["detail"]}',
                  ".pin{animation:pin 3s ease-in-out infinite}@keyframes pin{50%{opacity:.3}}")
    clip = kit.plate(doc, density=.5)
    cx, cy = W - 62, H / 2
    g = [f'<rect x="12" y="4" width="{W - 24}" height="{H - 8}" rx="12" fill="#08090E" fill-opacity=".8" '
         f'stroke="{WHITE}" stroke-opacity=".07"/>',
         doc.text(ch["n"], M, 43, 10, "mono-500", AMBER, 1, track=2.4),
         f'<path d="M122 24V52" stroke="{WHITE}" stroke-opacity=".1"/>',
         doc.text(ch["label"], 146, 49, 30, "serif", WHITE),
         doc.text(ch["detail"], 350, 43, 12, "mono-400", SILVER, .95, track=1),
         doc.text("TRANSMIT", W - 98, 43, 9, "mono-500", AMBER, .9, "end", track=2.2),
         f'<circle cx="{cx}" cy="{cy}" r="15" stroke="{AMBER}" stroke-opacity=".55"/>',
         f'<circle class="pin" style="animation-delay:-{k * .7:.1f}s" cx="{cx}" cy="{cy}" r="20" stroke="{AMBER}" stroke-opacity=".22"/>',
         f'<path d="M{cx - 5} {cy + 5}l10-10M{cx - 3} {cy - 5}h8v8" stroke="{AMBER}" stroke-width="1.4" '
         f'stroke-linecap="round" stroke-linejoin="round"/>']
    doc.keep(6, 0, W - 6, H)
    finish(doc, clip, g, f'channel-{k + 1}-{ch["label"].lower()}.svg', ch["url"])


def footer():
    H = 140
    doc = kit.Doc(W, H, "End of transmission", ".spin{transform-origin:500px 60px;animation:spin 14s linear infinite}"
                  "@keyframes spin{to{transform:rotate(360deg)}}")
    clip = kit.plate(doc, density=.6, last=True)
    g = [f'<path d="M{M} 60H452M548 60H{W - M}" stroke="#2A2F3E"/>',
         f'<circle cx="500" cy="60" r="15" stroke="{SILVER}" stroke-opacity=".5" stroke-width=".8"/>',
         f'<ellipse cx="500" cy="60" rx="34" ry="8" stroke="{SILVER}" stroke-opacity=".35" stroke-width=".8" transform="rotate(-11 500 60)"/>',
         f'<circle cx="500" cy="60" r="3" fill="{WHITE}"/>',
         f'<g class="spin"><circle cx="515" cy="60" r="2.4" fill="{AMBER}"/></g>',
         doc.text("END OF TRANSMISSION", 500, 102, 9.5, "mono-400", SILVER, .9, "middle", track=3.4),
         doc.text(P["handle"].upper(), M, 50, 9, "mono-400", SILVER, .7, track=2),
         doc.text("BUILT AS SVG  ·  NO TRACKERS", W - M, 50, 9, "mono-400", SILVER, .7, "end", track=2)]
    doc.keep(M - 6, 52, W - M + 6, 68)
    finish(doc, clip, g, "footer.svg")


# ================================================================================================ assembly
def build_all():
    bands = {b["id"]: b for b in P["bands"]}
    hero.build(P, DATA).save("cosmic-hero.svg", P["contact"]["channels"][0]["url"])
    band(bands["identity"], 0)
    identity()
    band(bands["exploring"], 1)
    research_grid()
    band(bands["arsenal"], 2)
    arsenal()
    band(bands["work"], 3)
    for k, pr in enumerate(shown_projects()):
        link = f'https://github.com/{P["handle"]}/{pr["repo"]}'
        card(pr, k, link)
        caption(pr, k, link)
    also()
    band(bands["telemetry"], 4)
    telemetry.render(DATA).save("telemetry.svg")
    band(bands["frontier"], 5)
    frontier()
    band(bands["contact"], 6)
    contact()
    for k, ch in enumerate(P["contact"]["channels"]):
        channel(ch, k)
    footer()


def readme():
    """One paragraph of top-aligned, full-width images: they stack with no gaps into a single canvas."""
    items = []
    for name, _, alt, link in kit.LAYOUT.items:
        img = f'<img align="top" width="100%" src="assets/{name}" alt="{kit.esc(alt)}">'
        if (kit.ROOT / "assets" / "static" / name).exists():
            img = f'<picture><source media="(prefers-reduced-motion: reduce)" srcset="assets/static/{name}">{img}</picture>'
        items.append(f'<a href="{link}">{img}</a>' if link else img)
    note = ("<!-- Generated by scripts/build.py from scripts/profile.json. Do not edit by hand.\n"
            "     Every image is a slice of one canvas; keep them in one paragraph with no whitespace between. -->\n")
    (kit.ROOT / "README.md").write_text(note + "<p>" + "".join(items) + "</p>\n", encoding="utf-8")


def main():
    import sys
    if "--fetch" in sys.argv:
        telemetry.main()
        DATA.clear()
        DATA.update(json.loads(telemetry.CACHE.read_text(encoding="utf-8")))
    lay = kit.LAYOUT
    lay.phase = "collect"                 # pass 1: where does everything sit?
    lay.reset()
    build_all()
    lay.freeze()
    for old in list((kit.ROOT / "assets").glob("*.svg")) + list((kit.ROOT / "assets").glob("static/*.svg")):
        old.unlink()
    lay.phase = "draw"                    # pass 2: draw, keeping the background clear of all of it
    lay.reset()
    build_all()
    lay.dump(kit.ROOT / "scripts" / "canvas.json")
    readme()
    total = sum(p.stat().st_size for p in (kit.ROOT / "assets").glob("*.svg"))
    print(f"{len(lay.items)} slices, canvas {lay.cursor}px tall, {total / 1024:.0f} KB (plus static twins)")


if __name__ == "__main__":
    main()
