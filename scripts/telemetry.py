#!/usr/bin/env python3
"""Render assets/telemetry.svg from live GitHub data. Run daily by .github/workflows/telemetry.yml.

  GITHUB_TOKEN=... GH_LOGIN=AIZEN-Hado python3 scripts/telemetry.py assets/telemetry.svg
  python3 scripts/telemetry.py out.svg --standby     # placeholder shown before the first sync
  python3 scripts/telemetry.py out.svg --mock        # random data, for checking the layout only
"""
import datetime
import json
import os
import random
import sys
import urllib.request

import sf
from sf import AMBER, W, f, svg_open

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
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
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "telemetry"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors") or not body.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {body.get('errors') or 'user not found'}")
    user = body["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    langs = {}
    for repo in user["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {"total": cal["totalContributions"], "repos": user["repositories"]["totalCount"],
            "days": [(d["date"], d["contributionCount"], d["contributionLevel"]) for d in days], "langs": langs}


def mock():
    rng = random.Random(4)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=364 + (today.isoweekday() % 7))
    names = list(LEVELS)
    days = []
    for i in range((today - start).days + 1):
        lvl = rng.choices(range(5), weights=[5, 4, 3, 2, 1])[0]
        days.append(((start + datetime.timedelta(days=i)).isoformat(), lvl * 2, names[lvl]))
    return {"total": sum(d[1] for d in days), "repos": 15, "days": days,
            "langs": {"Python": 520, "TypeScript": 260, "JavaScript": 180, "Java": 90, "Jupyter Notebook": 60, "CSS": 30}}


def standby():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=364 + (today.isoweekday() % 7))
    days = [((start + datetime.timedelta(days=i)).isoformat(), 0, "NONE") for i in range((today - start).days + 1)]
    return {"total": None, "repos": None, "days": days, "langs": {}}


def active_days(days):
    return sum(1 for _, count, _ in days if count)


LEVELS = {  # level -> (radius, opacity)
    "NONE": (1.1, .09), "FIRST_QUARTILE": (2.0, .35), "SECOND_QUARTILE": (2.8, .55),
    "THIRD_QUARTILE": (3.6, .78), "FOURTH_QUARTILE": (4.4, 1.0),
}
LANG_SHADES = [1, .66, .46, .32, .22, .12]


def render(data):
    name = "telemetry"
    _, H = sf.OFFSET[name]
    live = data["total"] is not None
    css = (sf.PARTICLE_CSS +
           ".col{animation:wave 7s linear infinite}@keyframes wave{0%,9%,100%{opacity:1}4.5%{opacity:.25}}"
           ".now{animation:now 2s ease-in-out infinite}@keyframes now{50%{opacity:.35}}")
    alt = (f'Telemetry: {data["total"]} contributions in the last 12 months, {active_days(data["days"])} active days, '
           f'{data["repos"]} public repositories') if live else "Telemetry: awaiting first sync"
    s = [svg_open(W, H, alt, css), sf.backdrop(name),
         f'<defs>{sf.GLOW}<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="9"/></filter></defs>',
         sf.particles(name)]
    s.append(sf.neon_heading(5, "TELEMETRY"))

    stats = [(data["total"], "CONTRIBUTIONS / 12 MONTHS"), (active_days(data["days"]) if live else None, "ACTIVE DAYS"),
             (data["repos"], "PUBLIC REPOSITORIES")]
    for i, (value, caption) in enumerate(stats):
        x = 60 + i * 310
        shown = f"{value:,}" if value is not None else "--"
        s.append(sf.text(shown, x, 236, 58, "inter-800", attrs=f'fill="{sf.INK}"')[0])
        s.append(sf.label(caption, x + 2, 266, sf.DIM, 1, size=12))

    # one dot per day, a column per week
    pitch, y0 = 16.4, 312
    first = datetime.date.fromisoformat(data["days"][0][0])
    offset = first.isoweekday() % 7                      # Sunday = row 0
    weeks = (offset + len(data["days"]) + 6) // 7
    x0 = (W - (weeks - 1) * pitch) / 2
    cols = [[] for _ in range(weeks)]
    for i, (_, count, level) in enumerate(data["days"]):
        col, row = divmod(offset + i, 7)
        r, op = LEVELS.get(level, LEVELS["NONE"])
        cx, cy = x0 + col * pitch, y0 + row * pitch
        if i == len(data["days"]) - 1 and live:
            cols[col].append(f'<circle class="now" cx="{f(cx)}" cy="{f(cy)}" r="{max(r, 3)}" fill="#fff"/>')
            continue
        cols[col].append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{r}" fill="#fff" opacity="{op}"/>')
    for c, dots in enumerate(cols):
        s.append(f'<g class="col" style="animation-delay:{c * 0.06:.2f}s">{"".join(dots)}</g>')

    if not live:
        s.append(sf.label("AWAITING FIRST SYNC", 500, 452, sf.DIM, 1, size=12, spacing=4, anchor="middle"))
    elif data["langs"]:
        total = sum(data["langs"].values())
        top = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:5]
        rest = total - sum(v for _, v in top)
        if rest > 0:
            top.append(("Other", rest))
        x = 60.0
        for (lang, size), shade in zip(top, LANG_SHADES):
            w = 880 * size / total
            s.append(f'<rect x="{f(x)}" y="436" width="{f(max(w - 3, 1))}" height="3" fill="#fff" fill-opacity="{shade}"/>')
            x += w
        slot = 880 / len(top)
        for i, ((lang, size), shade) in enumerate(zip(top, LANG_SHADES)):
            lx = 60 + i * slot
            short = {"Jupyter Notebook": "Jupyter"}.get(lang, lang).upper()[:12]
            s.append(f'<rect x="{f(lx)}" y="455" width="8" height="8" fill="#fff" fill-opacity="{shade}"/>')
            s.append(sf.label(f"{short} {round(100 * size / total)}%", lx + 16, 464, sf.BODY, 1, size=11, spacing=1))
    s.append("</svg>")
    return "".join(s)


def main():
    out = sys.argv[1]
    if "--mock" in sys.argv:
        data = mock()
    elif "--standby" in sys.argv:
        data = standby()
    else:
        token, login = os.environ.get("GITHUB_TOKEN"), os.environ.get("GH_LOGIN")
        if not token or not login:
            raise SystemExit("Set GITHUB_TOKEN and GH_LOGIN (or pass --standby / --mock).")
        data = fetch(login, token)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render(data))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
