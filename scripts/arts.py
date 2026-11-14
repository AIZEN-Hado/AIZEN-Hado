"""Illustrations drawn inside the panels: research vectors and project schematics."""
import json
import math
import random

import kit
from kit import AMBER, EMBER, SILVER, VIOLET, VOID, WHITE, f

GRID_CSS = (".shift{animation:shift 7s ease-in-out infinite alternate}"
            "@keyframes shift{from{transform:translateX(0)}to{transform:translateX(-9px)}}"
            ".cell{animation:cell 4.8s ease-in-out infinite}@keyframes cell{0%,100%{opacity:.25}35%{opacity:1}}"
            ".orbit{animation:orbitspin 10s linear infinite}@keyframes orbitspin{to{transform:rotate(360deg)}}"
            ".path{animation:path 6s ease-in-out infinite}@keyframes path{0%{stroke-dashoffset:var(--l)}45%,80%{stroke-dashoffset:0}100%{stroke-dashoffset:calc(var(--l) * -1)}}"
            ".blink{animation:blink 3.2s steps(1) infinite}@keyframes blink{50%{opacity:.2}}")


def art_eval(doc, cx, cy):
    """Baseline vs candidate pass-rate distributions with a significance gate."""
    def bell(mu, sd, amp, w=150):
        pts = []
        for i in range(61):
            x = -w / 2 + w * i / 60
            pts.append((cx + x, cy + 40 - amp * math.exp(-((x - mu) ** 2) / (2 * sd * sd))))
        return "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts)
    gid = doc.uid("ev")
    doc.define(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity=".35"/>'
               f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>')
    out = [f'<path d="M{cx - 78} {cy + 40}H{cx + 78}" stroke="{SILVER}" stroke-opacity=".5" stroke-width=".8"/>',
           f'<path d="{bell(18, 17, 66)}" stroke="{SILVER}" stroke-opacity=".75" stroke-width="1"/>',
           f'<g class="shift"><path d="{bell(-14, 19, 58)}L{cx + 75} {cy + 40}L{cx - 75} {cy + 40}Z" fill="url(#{gid})"/>'
           f'<path d="{bell(-14, 19, 58)}" stroke="{AMBER}" stroke-width="1.3"/></g>',
           f'<path d="M{cx + 2} {cy - 44}V{cy + 46}" stroke="{WHITE}" stroke-opacity=".6" stroke-dasharray="2 3"/>',
           doc.text("α = .05", cx + 7, cy - 38, 8.5, "mono-400", WHITE, .7, track=.6),
           doc.text("A", cx + 18, cy + 56, 8.5, "mono-500", SILVER, .9, "middle"),
           doc.text("B", cx - 14, cy + 56, 8.5, "mono-500", AMBER, 1, "middle")]
    return "".join(out)


def art_lora(doc, cx, cy):
    """W (frozen) + B·A (trainable, low rank)."""
    s, n = 66, 6
    c = s / n
    x0, y0 = cx - 82, cy - s / 2
    out = []
    cells = []
    for i in range(n):
        for j in range(n):
            cells.append(f'<rect x="{f(x0 + j * c + .8)}" y="{f(y0 + i * c + .8)}" width="{f(c - 1.6)}" height="{f(c - 1.6)}"/>')
    out.append(f'<g fill="{SILVER}" fill-opacity=".16">{"".join(cells)}</g>')
    out.append(f'<rect x="{f(x0)}" y="{f(y0)}" width="{s}" height="{s}" stroke="{SILVER}" stroke-opacity=".6" stroke-width=".8"/>')
    out.append(doc.text("W", x0 + s / 2, y0 + s / 2 + 8, 22, "serif-i", WHITE, .9, "middle"))
    px = x0 + s + 13
    out.append(doc.text("+", px, cy + 6, 18, "sans-300", SILVER, .9, "middle"))
    bx = px + 13                                     # B : d x r
    for i in range(n):
        out.append(f'<rect class="cell" style="animation-delay:{i * .22:.2f}s" x="{f(bx + .8)}" y="{f(y0 + i * c + .8)}" '
                   f'width="{f(c - 1.6)}" height="{f(c - 1.6)}" fill="{AMBER}"/>')
    out.append(f'<rect x="{f(bx)}" y="{f(y0)}" width="{f(c)}" height="{s}" stroke="{AMBER}" stroke-width=".9"/>')
    ax = bx + c + 6                                  # A : r x d
    for j in range(n):
        out.append(f'<rect class="cell" style="animation-delay:{1.4 + j * .22:.2f}s" x="{f(ax + j * c + .8)}" y="{f(y0 + .8)}" '
                   f'width="{f(c - 1.6)}" height="{f(c - 1.6)}" fill="{AMBER}"/>')
    out.append(f'<rect x="{f(ax)}" y="{f(y0)}" width="{s}" height="{f(c)}" stroke="{AMBER}" stroke-width=".9"/>')
    out.append(doc.text("B", bx + c / 2, y0 + s + 16, 9, "mono-500", AMBER, 1, "middle"))
    out.append(doc.text("A", ax + s / 2, y0 + c + 16, 9, "mono-500", AMBER, 1, "middle"))
    out.append(doc.text("LOW RANK", ax + s / 2, y0 + s - 4, 8, "mono-400", SILVER, .8, "middle", track=1.2))
    out.append(doc.text("FROZEN", x0 + s / 2, y0 + s + 16, 8, "mono-400", SILVER, .7, "middle", track=1.4))
    return "".join(out)


def art_agent(doc, cx, cy):
    """A plan-act-observe loop visiting tools on an orbit."""
    R = 50
    out = [f'<circle cx="{cx}" cy="{cy}" r="{R}" stroke="{SILVER}" stroke-opacity=".45" stroke-width=".8" stroke-dasharray="1.5 4"/>']
    labels = ["SEARCH", "CODE", "FILES", "API"]
    for k, lab in enumerate(labels):
        a = math.radians(-45 + 90 * k)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        out.append(f'<path d="M{cx} {cy}L{f(x)} {f(y)}" stroke="{SILVER}" stroke-opacity=".22" stroke-width=".7"/>')
        out.append(f'<rect x="{f(x - 4.5)}" y="{f(y - 4.5)}" width="9" height="9" fill="{VOID}" stroke="{WHITE}" stroke-opacity=".8" stroke-width=".9"/>')
        tx = x + (12 if math.cos(a) > 0 else -12)
        out.append(doc.text(lab, tx, y + 3, 7.5, "mono-400", SILVER, .85, "start" if math.cos(a) > 0 else "end", track=1))
    out.append(f'<circle cx="{cx}" cy="{cy}" r="13" stroke="{AMBER}" stroke-opacity=".5" stroke-width=".8"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{AMBER}"/>')
    out.append(f'<g class="orbit" style="transform-origin:{cx}px {cy}px"><circle cx="{cx + R}" cy="{cy}" r="3" fill="{EMBER}"/>'
               f'<path d="M{cx + R} {cy}A{R} {R} 0 0 0 {f(cx + R * math.cos(-.7))} {f(cy + R * math.sin(-.7))}" '
               f'stroke="{AMBER}" stroke-width="1.4" stroke-linecap="round"/></g>')
    return "".join(out)


def art_graph(doc, cx, cy):
    """A knowledge graph; a query lights a multi-hop path."""
    rng = random.Random(5)
    pts = [(-60, -38), (-22, -50), (20, -34), (58, -46), (-48, 4), (-6, -2), (38, 8), (70, 2),
           (-30, 44), (12, 40), (54, 48)]
    pts = [(cx + x + rng.uniform(-3, 3), cy + y + rng.uniform(-3, 3)) for x, y in pts]
    edges = [(0, 1), (1, 2), (2, 3), (0, 4), (1, 5), (2, 5), (2, 6), (3, 7), (4, 5), (5, 6), (6, 7), (4, 8),
             (5, 9), (6, 9), (6, 10), (8, 9), (9, 10), (7, 10)]
    route = [4, 5, 6, 10]
    out = [f'<g stroke="{SILVER}" stroke-opacity=".32" stroke-width=".8">' +
           "".join(f'<path d="M{f(pts[a][0])} {f(pts[a][1])}L{f(pts[b][0])} {f(pts[b][1])}"/>' for a, b in edges) + "</g>"]
    d = "M" + "L".join(f"{f(pts[i][0])} {f(pts[i][1])}" for i in route)
    ln = sum(math.dist(pts[route[i]], pts[route[i + 1]]) for i in range(len(route) - 1))
    qx, qy = cx - 82, cy + 4
    out.append(f'<path d="M{qx} {qy}L{f(pts[4][0])} {f(pts[4][1])}" stroke="{AMBER}" stroke-opacity=".6" stroke-dasharray="2 3"/>')
    out.append(f'<path d="{d}" stroke="{AMBER}" stroke-opacity=".25" stroke-width="1.6"/>')
    out.append(f'<path class="path" style="--l:{f(ln)}" d="{d}" stroke="{EMBER}" stroke-width="1.8" stroke-linecap="round" '
               f'stroke-dasharray="{f(ln)}" stroke-dashoffset="0"/>')
    for i, (x, y) in enumerate(pts):
        on = i in route
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{3.2 if on else 2.3}" fill="{AMBER if on else WHITE}" '
                   f'fill-opacity="{1 if on else .65}"/>')
    out.append(f'<rect x="{qx - 4}" y="{qy - 4}" width="8" height="8" fill="{AMBER}" transform="rotate(45 {qx} {qy})"/>')
    out.append(doc.text("QUERY", qx, qy + 18, 7.5, "mono-400", AMBER, .9, "middle", track=1))
    return "".join(out)


ARTS = {"eval": art_eval, "lora": art_lora, "agent": art_agent, "graph": art_graph}


CARD_CSS = (".flowx{animation:flowx linear infinite}@keyframes flowx{to{stroke-dashoffset:0}}"
            ".glow{animation:glow 4s ease-in-out infinite}@keyframes glow{0%,100%{opacity:1}50%{opacity:.45}}"
            ".fill{transform-box:fill-box;transform-origin:bottom;animation:fill 6s cubic-bezier(.6,0,.3,1) infinite}"
            "@keyframes fill{0%{transform:scaleY(.15)}60%,100%{transform:scaleY(1)}}"
            ".gauge{animation:gauge 6s cubic-bezier(.6,0,.3,1) infinite}"
            "@keyframes gauge{0%{stroke-dashoffset:var(--l)}60%,100%{stroke-dashoffset:var(--e)}}"
            ".caret{animation:caret 1.1s steps(1) infinite}@keyframes caret{50%{opacity:0}}"
            ".scan{animation:scanY 3.6s ease-in-out infinite alternate}@keyframes scanY{from{transform:translateY(0)}to{transform:translateY(88px)}}")


def label(doc, s, x, y, color=SILVER, op=.8, anchor="start", size=8):
    return doc.text(s, x, y, size, "mono-400", color, op, anchor, track=1.3)


def art_savyis(doc, ox, oy):
    """Dataset records stream into a frozen base model; each layer carries a trainable LoRA adapter."""
    out = []
    for i in range(6):                                  # dataset rows
        y = oy + 52 + i * 18
        w = [44, 36, 48, 30, 42, 38][i]
        out.append(f'<path d="M{ox} {y}h{w}" stroke="{WHITE}" stroke-opacity=".55" stroke-width="2" stroke-linecap="round"/>')
        out.append(f'<circle cx="{ox - 7}" cy="{y}" r="1.4" fill="{AMBER}"/>')
    out.append(label(doc, "JSONL / CSV", ox - 9, oy + 32))
    mx = ox + 120                                        # model stack
    path = f"M{ox + 56} {oy + 97}H{mx - 6}"
    out.append(f'<path d="{path}" stroke="{SILVER}" stroke-opacity=".35"/>')
    out.append(f'<path class="flowx" style="animation-duration:2.4s" d="{path}" stroke="{AMBER}" stroke-width="2" '
               f'stroke-linecap="round" stroke-dasharray="2 10" stroke-dashoffset="24"/>')
    for i in range(6):
        y = oy + 46 + i * 18
        out.append(f'<rect x="{mx}" y="{y}" width="92" height="12" rx="2" stroke="{SILVER}" stroke-opacity=".6" '
                   f'stroke-width=".8" fill="{WHITE}" fill-opacity=".04"/>')
        out.append(f'<rect class="glow" style="animation-delay:{i * .35:.2f}s" x="{mx + 96}" y="{y + 2}" width="12" '
                   f'height="8" rx="1.5" fill="{AMBER}"/>')
    out.append(label(doc, "BASE MODEL · FROZEN", mx, oy + 32))
    out.append(label(doc, "LORA", mx + 102, oy + 170, AMBER, 1, "middle"))
    ax = mx + 150                                        # exported adapter artifact
    p2 = f"M{mx + 114} {oy + 97}H{ax - 6}"
    out.append(f'<path d="{p2}" stroke="{SILVER}" stroke-opacity=".35"/>')
    out.append(f'<path class="flowx" style="animation-duration:2.4s" d="{p2}" stroke="{EMBER}" stroke-width="2" '
               f'stroke-linecap="round" stroke-dasharray="2 10" stroke-dashoffset="24"/>')
    out.append(f'<path d="M{ax} {oy + 74}h34l10 10v36h-44Z" stroke="{AMBER}" stroke-width="1"/>'
               f'<path d="M{ax + 34} {oy + 74}v10h10" stroke="{AMBER}" stroke-width="1"/>')
    out.append(label(doc, "ADAPTER", ax + 22, oy + 140, AMBER, 1, "middle"))
    out.append(label(doc, "SIGNED EXPORT", ax + 22, oy + 152, SILVER, .7, "middle"))
    return "".join(out)


def art_fisherman(doc, ox, oy):
    """Paired pass/fail per case for baseline A and candidate B; flips feed McNemar's exact test."""
    a = [1, 1, 1, 1, 1, 1, 0, 1]                         # 6 regression flips, 0 improvements (as in the
    b = [1, 0, 0, 0, 1, 0, 0, 0]                         # Fisherman README): exact p = 2 * 0.5**6 = .031
    out = [label(doc, "CASE", ox, oy + 32), label(doc, "A", ox + 66, oy + 32, SILVER, .9, "middle"),
           label(doc, "B", ox + 106, oy + 32, AMBER, 1, "middle")]
    for i, (pa, pb) in enumerate(zip(a, b)):
        y = oy + 50 + i * 15
        out.append(f'<path d="M{ox} {y}h{[30, 22, 34, 26, 30, 20, 32, 24][i]}" stroke="{WHITE}" stroke-opacity=".3" '
                   f'stroke-width="1.6" stroke-linecap="round"/>')
        for x, p, col in ((ox + 66, pa, WHITE), (ox + 106, pb, AMBER if pa != pb else WHITE)):
            if p:
                out.append(f'<rect x="{x - 4}" y="{y - 4}" width="8" height="8" fill="{col}" fill-opacity=".85"/>')
            else:
                out.append(f'<rect x="{x - 3.5}" y="{y - 3.5}" width="7" height="7" stroke="{col}" stroke-opacity=".8"/>')
        if pa != pb:
            out.append(f'<path class="glow" d="M{ox + 72} {y}H{ox + 100}" stroke="{AMBER}" stroke-width="1"/>')
    vx = ox + 150                                        # the gate
    out.append(f'<path d="M{ox + 120} {oy + 98}H{vx}" stroke="{SILVER}" stroke-opacity=".4"/>')
    out.append(f'<rect x="{vx}" y="{oy + 56}" width="118" height="84" rx="3" stroke="{WHITE}" stroke-opacity=".25"/>')
    out.append(label(doc, "MCNEMAR · EXACT", vx + 12, oy + 76, SILVER, .9))
    out.append(doc.text("6 : 0 flips", vx + 12, oy + 94, 12.5, "mono-400", WHITE, .92))
    out.append(label(doc, "p = .031  <  α", vx + 12, oy + 107, AMBER, .95))
    out.append(f'<rect x="{vx + 12}" y="{oy + 114}" width="58" height="16" rx="2" fill="{AMBER}"/>')
    out.append(doc.text("BLOCK", vx + 41, oy + 125.5, 8.5, "mono-500", VOID, 1, "middle", track=1.6))
    out.append(label(doc, "EXIT 2", vx + 78, oy + 125.5, AMBER, 1))
    return "".join(out)


def art_semigit(doc, ox, oy):
    """An AST with one changed subtree -> milestone score -> conventional commit."""
    nodes = {"r": (ox + 50, oy + 46), "a": (ox + 18, oy + 86), "b": (ox + 82, oy + 86),
             "a1": (ox + 4, oy + 126), "a2": (ox + 32, oy + 126), "b1": (ox + 66, oy + 126), "b2": (ox + 98, oy + 126),
             "b3": (ox + 82, oy + 160)}
    hot = {"b", "b2", "b3"}
    edges = [("r", "a"), ("r", "b"), ("a", "a1"), ("a", "a2"), ("b", "b1"), ("b", "b2"), ("b2", "b3")]
    out = []
    for p, c in edges:
        (x1, y1), (x2, y2) = nodes[p], nodes[c]
        on = c in hot
        out.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{AMBER if on else SILVER}" stroke-opacity="{.9 if on else .4}" '
                   f'stroke-width="{1.2 if on else .8}"/>')
    for k, (x, y) in nodes.items():
        if k in hot:
            out.append(f'<circle class="glow" cx="{x}" cy="{y}" r="4.2" fill="{AMBER}"/>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="3.4" fill="{VOID}" stroke="{WHITE}" stroke-opacity=".7"/>')
    out.append(label(doc, "AST DIFF", ox - 4, oy + 26))
    gx, gy, r = ox + 172, oy + 104, 30                    # milestone gauge
    circ = 2 * math.pi * r
    arc = circ * .75
    out.append(f'<circle cx="{gx}" cy="{gy}" r="{r}" stroke="{WHITE}" stroke-opacity=".12" stroke-width="5" '
               f'stroke-dasharray="{f(arc)} {f(circ)}" transform="rotate(135 {gx} {gy})"/>')
    out.append(f'<circle class="gauge" style="--l:{f(circ)};--e:{f(circ - arc * .82)}" cx="{gx}" cy="{gy}" r="{r}" '
               f'stroke="{AMBER}" stroke-width="5" stroke-dasharray="{f(circ)} {f(circ)}" '
               f'stroke-dashoffset="{f(circ - arc * .82)}" transform="rotate(135 {gx} {gy})"/>')
    out.append(label(doc, "SCORE", gx, gy + 3, WHITE, .85, "middle"))
    out.append(label(doc, "MILESTONE", gx, oy + 26, SILVER, .8, "middle"))
    out.append(f'<path d="M{ox + 112} {oy + 104}H{gx - r - 10}" stroke="{SILVER}" stroke-opacity=".4"/>')
    cx = gx + r + 16
    out.append(f'<path d="M{cx - 8} {gy}H{cx}" stroke="{SILVER}" stroke-opacity=".4"/>')
    out.append(f'<rect x="{cx}" y="{gy - 16}" width="112" height="32" rx="3" stroke="{WHITE}" stroke-opacity=".25"/>')
    out.append(doc.runs([("feat", AMBER, 1, None), ("(parser):", WHITE, .9, None)], cx + 9, gy + 4, 10.5, "mono-400"))
    out.append(f'<rect class="caret" x="{cx + 100}" y="{gy - 6}" width="5" height="11" fill="{AMBER}"/>')
    out.append(label(doc, "COMMIT", cx + 56, oy + 26, SILVER, .8, "middle"))
    return "".join(out)


def art_pseudocv(doc, ox, oy):
    """Job description keywords map onto a resume that is compiled until it fills exactly one page."""
    out = []
    jx, jy = ox, oy + 40                                  # job description
    out.append(f'<rect x="{jx}" y="{jy}" width="74" height="104" rx="2" stroke="{WHITE}" stroke-opacity=".35"/>')
    hot = {1, 3, 6}
    for i in range(8):
        w = [52, 40, 56, 34, 48, 54, 30, 44][i]
        y = jy + 14 + i * 11
        out.append(f'<path d="M{jx + 9} {y}h{w}" stroke="{AMBER if i in hot else WHITE}" '
                   f'stroke-opacity="{.95 if i in hot else .3}" stroke-width="2" stroke-linecap="round"/>')
    out.append(label(doc, "JD", jx, oy + 30))
    rx = ox + 132                                         # resume page
    for i in hot:
        y = jy + 14 + i * 11
        ty = jy + 22 + [0, 2, 5].__getitem__(sorted(hot).index(i)) * 11
        out.append(f'<path d="M{jx + 78} {y}C{jx + 104} {y} {rx - 26} {ty} {rx - 4} {ty}" stroke="{AMBER}" '
                   f'stroke-opacity=".55" stroke-width=".9"/>')
    out.append(f'<rect x="{rx}" y="{jy - 8}" width="84" height="120" rx="2" stroke="{WHITE}" stroke-opacity=".6"/>')
    lines = []
    for i in range(9):
        w = [44, 62, 56, 64, 38, 60, 58, 50, 62][i]
        lines.append(f'<path d="M{rx + 10} {jy + 6 + i * 11.6}h{w}" stroke-linecap="round"/>')
    out.append(f'<g stroke="{WHITE}" stroke-opacity=".45" stroke-width="2">{"".join(lines)}</g>')
    out.append(label(doc, "RESUME.TEX", rx, oy + 22))
    gx = rx + 104                                         # page-fill gauge
    out.append(f'<rect x="{gx}" y="{jy - 8}" width="6" height="120" rx="3" fill="{WHITE}" fill-opacity=".08"/>')
    out.append(f'<rect class="fill" x="{gx}" y="{jy - 8}" width="6" height="120" rx="3" fill="{AMBER}"/>')
    out.append(f'<path d="M{gx - 4} {jy - 8}h22" stroke="{WHITE}" stroke-opacity=".7" stroke-dasharray="2 2"/>')
    out.append(label(doc, "1 PAGE", gx + 20, jy - 5, WHITE, .85))
    out.append(label(doc, "MEASURED", gx + 20, jy + 7, SILVER, .7))
    return "".join(out)


def art_classly(doc, ox, oy):
    """A scanned answer sheet is read by OCR, routed to one of three LLM providers, and graded."""
    out = []
    px, py = ox, oy + 42
    out.append(f'<rect x="{px}" y="{py}" width="70" height="96" rx="2" stroke="{WHITE}" stroke-opacity=".45"/>')
    for i in range(6):                                    # handwriting
        y = py + 16 + i * 13
        w = [48, 40, 52, 30, 44, 36][i]
        d = "M" + " ".join(f"{f(px + 10 + t)} {f(y + 1.6 * math.sin(t / 3.2 + i))}" for t in range(0, w, 2))
        out.append(f'<path d="{d}" stroke="{WHITE}" stroke-opacity=".5" stroke-width="1.2" stroke-linecap="round"/>')
    out.append(f'<g class="scan"><rect x="{px - 4}" y="{py + 2}" width="78" height="2" fill="{AMBER}"/>'
               f'<rect x="{px - 4}" y="{py - 5}" width="78" height="7" fill="{AMBER}" fill-opacity=".1"/></g>')
    out.append(label(doc, "ANSWER SHEET", px, oy + 30))
    out.append(label(doc, "OCR", px + 35, py + 112, AMBER, 1, "middle"))
    hx, hy = ox + 128, oy + 90                            # provider router
    out.append(f'<path d="M{px + 76} {hy}H{hx - 9}" stroke="{SILVER}" stroke-opacity=".4"/>')
    out.append(f'<circle cx="{hx}" cy="{hy}" r="8" stroke="{AMBER}"/><circle cx="{hx}" cy="{hy}" r="3" fill="{AMBER}"/>')
    for i, name in enumerate(("OPENAI", "GEMINI", "ANTHROPIC")):
        y = hy - 30 + i * 30
        on = i == 2
        out.append(f'<path d="M{hx + 8} {hy}C{hx + 22} {hy} {hx + 18} {y} {hx + 34} {y}" stroke="{AMBER if on else SILVER}" '
                   f'stroke-opacity="{.9 if on else .35}"/>')
        out.append(f'<rect x="{hx + 34}" y="{y - 3}" width="6" height="6" fill="{AMBER if on else SILVER}" fill-opacity="{1 if on else .5}"/>')
        out.append(label(doc, name, hx + 46, y + 3, AMBER if on else SILVER, 1 if on else .75))
    out.append(label(doc, "PROVIDER", hx, oy + 30, SILVER, .8, "middle"))
    fx, fy = ox + 254, oy + 52                            # graded feedback
    out.append(f'<rect x="{fx}" y="{fy}" width="86" height="78" rx="3" stroke="{WHITE}" stroke-opacity=".25"/>')
    for i, ok in enumerate((True, True, False, True)):
        y = fy + 16 + i * 16
        out.append(f'<path d="M{fx + 30} {y}h{[40, 30, 36, 26][i]}" stroke="{WHITE}" stroke-opacity=".35" stroke-width="1.6" stroke-linecap="round"/>')
        if ok:
            out.append(f'<path d="M{fx + 10} {y}l3 3 6-6" stroke="{AMBER}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            out.append(f'<path d="M{fx + 11} {y - 3}l6 6m0-6l-6 6" stroke="{SILVER}" stroke-width="1.3" stroke-linecap="round"/>')
    out.append(label(doc, "FEEDBACK", fx + 43, oy + 30, SILVER, .8, "middle"))
    return "".join(out)


CARD_ARTS = {"savyis": art_savyis, "classly": art_classly, "fisherman": art_fisherman, "semigit": art_semigit, "pseudocv": art_pseudocv}


