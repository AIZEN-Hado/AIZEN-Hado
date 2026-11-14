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

from sf import AMBER, LINE, W, f, glyphs, mono, panel, svg_open

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
LEVELS = {  # level -> (radius, opacity)
    "NONE": (1.1, .10), "FIRST_QUARTILE": (2.0, .38), "SECOND_QUARTILE": (2.8, .58),
    "THIRD_QUARTILE": (3.6, .80), "FOURTH_QUARTILE": (4.4, 1.0),
}


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


def streak(days):
    counts = [c for _, c, _ in days]
    if counts and counts[-1] == 0:          # today may simply not have happened yet
        counts = counts[:-1]
    n = 0
    for c in reversed(counts):
        if c == 0:
            break
        n += 1
    return n


def render(data):
    H = 330
    live = data["total"] is not None
    style = (".col{animation:wave 7s linear infinite}"
             "@keyframes wave{0%,9%,100%{opacity:1}4.5%{opacity:.25}}"
             ".now{animation:now 2s ease-in-out infinite}@keyframes now{50%{opacity:.35}}")
    label = (f'{data["total"]} contributions in the last 12 months, {streak(data["days"])} day streak, '
             f'{data["repos"]} public repositories') if live else "Telemetry: awaiting first sync"
    s = [svg_open(W, H, label, style), panel(W, H)]

    stats = [(data["total"], "CONTRIBUTIONS / 12 MONTHS"), (streak(data["days"]) if live else None, "DAY STREAK"),
             (data["repos"], "PUBLIC REPOSITORIES")]
    for i, (value, caption) in enumerate(stats):
        x = 40 + i * 320
        paths, _, _ = glyphs(str(value) if value is not None else "---", x, 40, 5.5)
        s.append(f'<g {LINE} stroke="#f4f7fb" stroke-width="2.4">{paths}</g>')
        s.append(mono(caption, x, 104, size=12, opacity=.45, spacing=3))

    # one dot per day, a column per week
    pitch, y0 = 16.4, 144
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
            cols[col].append(f'<circle class="now" cx="{f(cx)}" cy="{f(cy)}" r="{max(r, 2.6)}" fill="{AMBER}"/>')
        else:
            cols[col].append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{r}" opacity="{op}"/>')
    s.append('<g fill="#fff">')
    for c, dots in enumerate(cols):
        s.append(f'<g class="col" style="animation-delay:{c * 0.06:.2f}s">{"".join(dots)}</g>')
    s.append("</g>")

    if not live:
        s.append(mono("AWAITING FIRST SYNC", 500, 296, size=12, opacity=.45, spacing=4, anchor="middle"))
    elif data["langs"]:
        total = sum(data["langs"].values())
        top = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:5]
        rest = total - sum(v for _, v in top)
        if rest > 0:
            top.append(("Other", rest))
        shades = [1, .7, .5, .34, .22, .12]
        x = 40.0
        for (name, size), shade in zip(top, shades):
            w = 920 * size / total
            s.append(f'<rect x="{f(x)}" y="276" width="{f(max(w - 3, 1))}" height="3" fill="#fff" fill-opacity="{shade}"/>')
            x += w
        slot = 920 / len(top)
        for i, ((name, size), shade) in enumerate(zip(top, shades)):
            lx = 40 + i * slot
            s.append(f'<rect x="{f(lx)}" y="296" width="8" height="8" fill="#fff" fill-opacity="{shade}"/>')
            short = {"Jupyter Notebook": "Jupyter"}.get(name, name).upper()[:13]
            s.append(mono(f"{short} {round(100 * size / total)}%", lx + 16, 304, size=11, opacity=.55, spacing=1.5))
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
