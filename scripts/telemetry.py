#!/usr/bin/env python3
"""Render assets/telemetry.svg from live GitHub data. Run daily by .github/workflows/telemetry.yml.

  GITHUB_TOKEN=... GH_LOGIN=AIZEN-Hado python3 scripts/telemetry.py     # fetch, cache, render
  python3 scripts/telemetry.py --cached                                  # re-render from scripts/telemetry.json

(scripts/build.py also renders this panel, from the cache, as part of the full canvas.)

The fetched numbers are cached in scripts/telemetry.json so a design change can be re-rendered without
an API call. Nothing here is estimated: every figure is either from the GraphQL API or derived from it.
Standard library only.
"""
import datetime
import json
import os
import sys
import urllib.request

import kit
from kit import AMBER, EMBER, SILVER, VIOLET, WHITE, f

CACHE = kit.ROOT / "scripts" / "telemetry.json"
CANVAS = kit.ROOT / "scripts" / "canvas.json"     # page position + keep-out zones, written by build.py

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-telemetry"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors") or not (body.get("data") or {}).get("user"):
        raise SystemExit(f"GitHub API error: {body.get('errors') or 'user not found'}")
    user = body["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    langs = {}
    for repo in user["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {
        "total": cal["totalContributions"],
        "repos": user["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in user["repositories"]["nodes"]),
        "days": [[d["date"], d["contributionCount"], d["contributionLevel"]]
                 for w in cal["weeks"] for d in w["contributionDays"]],
        "langs": langs,
        "synced": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ------------------------------------------------------------------------------------------- derived figures
def is_active(day):
    return (day[1] or 0) > 0 or day[2] not in ("NONE", None)


def longest_streak(days):
    best = run = 0
    for d in days:
        run = run + 1 if is_active(d) else 0
        best = max(best, run)
    return best


def weekly(days):
    """Per calendar week: contribution count when counts are known, else active days."""
    have_counts = all(d[1] is not None for d in days)
    weeks, cur, cur_start = [], 0, None
    for d in days:
        date = datetime.date.fromisoformat(d[0])
        if cur_start is None or date.isoweekday() % 7 == 0 and date != cur_start:
            if cur_start is not None:
                weeks.append((cur_start, cur))
            cur, cur_start = 0, date
        cur += (d[1] or 0) if have_counts else int(is_active(d))
    weeks.append((cur_start, cur))
    return weeks, have_counts


LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
LANG_TONES = [AMBER, "#FFA27A", VIOLET, "#B9A6FB", SILVER, "#4A5163"]
CSS = (kit.TWINKLE_CSS +
       ".cursor{animation:cursor 16s linear infinite}@keyframes cursor{from{transform:translateX(0)}to{transform:translateX(880px)}}"
       ".now{transform-box:fill-box;transform-origin:center;animation:now 2.6s ease-out infinite}"
       "@keyframes now{0%{transform:scale(.8);opacity:.9}100%{transform:scale(2.6);opacity:0}}"
       ".draw{animation:draw 3.2s cubic-bezier(.3,0,.2,1) both}@keyframes draw{from{stroke-dashoffset:var(--l)}to{stroke-dashoffset:0}}")


def render(data):
    W, H = 1000, 540
    days = data["days"]
    active = sum(1 for d in days if is_active(d))
    streak = longest_streak(days)
    weeks, counted = weekly(days)
    alt = (f'Development telemetry: {data["total"]:,} public contributions in the last 12 months, {active} active days, '
           f'longest streak {streak} days, {data["repos"]} public repositories. Last sync {data["synced"][:10]}.')
    doc = kit.Doc(W, H, alt, CSS)
    clip = kit.plate(doc, density=.3)
    g = [kit.panel(doc)]

    # readouts
    readouts = [(f'{data["total"]:,}', "CONTRIBUTIONS · 12 MO"), (str(active), "ACTIVE DAYS"),
                (str(streak), "LONGEST STREAK · DAYS"), (str(data["repos"]), "PUBLIC REPOSITORIES")]
    for i, (value, cap) in enumerate(readouts):
        x = 58 + i * 228
        g.append(doc.text(value, x - 2, 118, 56, "serif", WHITE))
        g.append(f'<rect x="{x}" y="{134}" width="10" height="1.5" fill="{AMBER}"/>')
        g.append(doc.text(cap, x + 18, 139, 9, "mono-400", SILVER, .95, track=1.9))
        if i:
            g.append(f'<path d="M{x - 26} 72V140" stroke="{WHITE}" stroke-opacity=".07"/>')

    # weekly trace, drawn like an oscilloscope
    x0, x1, top, base = 60, 940, 196, 290
    peak = max((v for _, v in weeks), default=0) or 1
    step = (x1 - x0) / max(len(weeks) - 1, 1)
    pts = [(x0 + i * step, base - (base - top) * v / peak) for i, (_, v) in enumerate(weeks)]
    line = "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts)
    area = line + f"L{f(pts[-1][0])} {base}L{f(pts[0][0])} {base}Z"
    ag = doc.uid("ag")
    doc.define(f'<linearGradient id="{ag}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity=".28"/>'
               f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>'
               f'<filter id="tg" x="-5%" y="-40%" width="110%" height="180%"><feGaussianBlur stdDeviation="3"/></filter>')
    for k in range(4):
        y = top + (base - top) * k / 3
        g.append(f'<path d="M{x0} {f(y)}H{x1}" stroke="{WHITE}" stroke-opacity="{.1 if k == 3 else .045}"/>')
    g.append(doc.text("CONTRIBUTIONS / WEEK" if counted else "ACTIVE DAYS / WEEK", x0, top - 14, 9, "mono-400", SILVER, .9, track=1.9))
    g.append(doc.text(f"PEAK {peak}", x1, top - 14, 9, "mono-400", AMBER, .95, "end", track=1.9))
    length = sum(((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** .5 for i in range(len(pts) - 1))
    g.append(f'<path d="{area}" fill="url(#{ag})"/>')
    g.append(f'<path d="{line}" stroke="{AMBER}" stroke-width="3" stroke-opacity=".45" filter="url(#tg)"/>')
    g.append(f'<path class="draw" style="--l:{f(length)}" d="{line}" stroke="{EMBER}" stroke-width="1.4" '
             f'stroke-linejoin="round" stroke-dasharray="{f(length)}"/>')
    g.append(f'<g class="cursor"><path d="M{x0} {top - 4}V{base}" stroke="{AMBER}" stroke-opacity=".5"/>'
             f'<rect x="{x0 - 30}" y="{top - 4}" width="30" height="{base - top + 4}" fill="{AMBER}" fill-opacity=".04"/></g>')
    # month ticks
    seen = set()
    for i, (start, _) in enumerate(weeks):
        key = (start.year, start.month)
        if key in seen or i == 0:
            seen.add(key)
            continue
        seen.add(key)
        x = x0 + i * step
        g.append(f'<path d="M{f(x)} {base}v4" stroke="{SILVER}" stroke-opacity=".5"/>')
        g.append(doc.text(start.strftime("%b").upper(), x, base + 17, 8.5, "mono-400", SILVER, .75, "middle", track=1.2))

    # daily field: one cell per day, a column per week
    first = datetime.date.fromisoformat(days[0][0])
    offset = first.isoweekday() % 7
    cols = (offset + len(days) + 6) // 7
    fy, fx, pitch, rpitch = 328, x0, (x1 - x0) / max(cols - 1, 1), 12     # columns sit under their week on the trace
    cells = {0: [], 1: [], 2: [], 3: [], 4: []}
    for i, d in enumerate(days):
        col, row = divmod(offset + i, 7)
        lvl = LEVEL.get(d[2], 0)
        if lvl == 0 and is_active(d):
            lvl = 1
        cells[lvl].append((fx + col * pitch, fy + row * rpitch))
    sizes = {0: 1.1, 1: 2.0, 2: 2.8, 3: 3.6, 4: 4.4}
    alphas = {0: .16, 1: .5, 2: .7, 3: .88, 4: 1}
    for lvl, pts_ in cells.items():
        col = WHITE if lvl == 0 else (EMBER if lvl == 4 else AMBER)
        circles = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="{sizes[lvl]}"/>' for x, y in pts_)
        g.append(f'<g fill="{col}" fill-opacity="{alphas[lvl]}">{circles}</g>')
    lx, ly = fx + ((offset + len(days) - 1) // 7) * pitch, fy + ((offset + len(days) - 1) % 7) * rpitch
    g.append(f'<circle class="now" cx="{f(lx)}" cy="{f(ly)}" r="4.5" stroke="{AMBER}"/>')
    for row, name in ((1, "MON"), (3, "WED"), (5, "FRI")):
        g.append(doc.text(name, fx - 12, fy + row * rpitch + 3, 7.5, "mono-400", SILVER, .6, "end", track=1))

    # language spectrum
    by = 450
    langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs) or 1
    top5 = [kv for kv in langs if kv[0] != "Other"][:5]
    rest = total - sum(v for _, v in top5)
    if rest > 0:
        top5.append(("Other", rest))
    g.append(doc.text("LANGUAGE SPECTRUM · BY BYTES, PUBLIC REPOS", 60, by - 12, 9, "mono-400", SILVER, .9, track=1.9))
    x = 60.0
    for (name, v), tone in zip(top5, LANG_TONES):
        w = 880 * v / total
        g.append(f'<rect x="{f(x)}" y="{by}" width="{f(max(w - 2, 1))}" height="5" rx="1" fill="{tone}"/>')
        x += w
    slot = 880 / max(len(top5), 1)
    for i, ((name, v), tone) in enumerate(zip(top5, LANG_TONES)):
        lx = 60 + i * slot
        short = {"Jupyter Notebook": "Jupyter"}.get(name, name).upper()
        g.append(f'<rect x="{f(lx)}" y="{by + 20}" width="6" height="6" fill="{tone}"/>')
        g.append(doc.runs([(short + "  ", WHITE, .85, "mono-400"), (f"{100 * v / total:.0f}%", SILVER, .9, "mono-400")],
                          lx + 13, by + 27, 9, track=1.4))

    g.append(kit.registration(doc))
    synced = data["synced"].replace("T", " ")[:16] + " UTC"
    g.append(kit.corner_labels(doc, tl="FIG. 5  /  STATION TELEMETRY", tr="PUBLIC ACTIVITY ONLY",
                               bl=f"LAST SYNC  {synced}", br="SOURCE  ·  GITHUB GRAPHQL API"))
    doc.add(f'<g clip-path="url(#{clip})">{"".join(g)}</g>', kit.plate_border(doc))
    return doc


def main():
    if "--cached" in sys.argv:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
    else:
        token, login = os.environ.get("GITHUB_TOKEN"), os.environ.get("GH_LOGIN")
        if not token or not login:
            raise SystemExit("Set GITHUB_TOKEN and GH_LOGIN, or pass --cached.")
        data = fetch(login, token)
        CACHE.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    # The panel is one slice of the shared canvas: draw it at its page position so the background lines
    # up with the slices above and below it.
    lay = kit.LAYOUT
    lay.load(CANVAS)
    lay.phase = "draw"
    lay.reset()
    lay.cursor = lay.frozen["slices"]["telemetry.svg"][0]
    print(render(data).save("telemetry.svg"))


if __name__ == "__main__":
    main()
