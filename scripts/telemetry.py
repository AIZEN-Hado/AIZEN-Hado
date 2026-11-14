#!/usr/bin/env python3
"""Live GitHub data for the profile, and the night-sky panel (assets/telemetry.svg) that shows it.

  GITHUB_TOKEN=... GH_LOGIN=AIZEN-Hado python3 scripts/telemetry.py     # fetch into scripts/telemetry.json
  python3 scripts/build.py --fetch                                       # fetch, then rebuild everything

The cache lets a design change be re-rendered without an API call. Nothing is estimated: every figure is
from the GraphQL/REST APIs (public repositories only) or derived from them. Private-repository activity is
never named; it appears only as the unnamed cluster computed from the calendar total minus public commits.
Standard library only.
"""
import datetime
import json
import os
import sys
import math
import random
import urllib.error
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
        "commits": fetch_commits(login, token),
    }


def rest(path, token):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "User-Agent": "profile-telemetry"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 409:                      # empty repository
            return []
        raise


def fetch_commits(login, token, days=365):
    """Public commits by the user, per repository and day: {repo: [[YYYY-MM-DD, count], ...]}.

    Uses the REST API (public repositories you own, no forks), so the sky shows exactly what any visitor
    could verify from the repositories themselves.
    """
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    repos, page = [], 1
    while True:
        batch = rest(f"/users/{login}/repos?type=owner&per_page=100&page={page}", token)
        repos += [r["name"] for r in batch if not r["fork"]]
        if len(batch) < 100:
            break
        page += 1
    out = {}
    for name in repos:
        per_day, page = {}, 1
        while True:
            batch = rest(f"/repos/{login}/{name}/commits?author={login}&since={since}&per_page=100&page={page}", token)
            for c in batch:
                day = c["commit"]["author"]["date"][:10]
                per_day[day] = per_day.get(day, 0) + 1
            if len(batch) < 100:
                break
            page += 1
        if per_day:
            out[name] = sorted(per_day.items())
    return out


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


LANG_TONES = [AMBER, "#FFA27A", VIOLET, "#B9A6FB", SILVER, "#4A5163"]
PRIVATE = "#8B5CF6"
CSS = (kit.TWINKLE_CSS +
       ".pulse{animation:pulse 4.2s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}"
       ".halo{transform-box:fill-box;transform-origin:center;animation:halo 4.2s ease-out infinite}"
       "@keyframes halo{0%{transform:scale(.6);opacity:.7}100%{transform:scale(3.2);opacity:0}}"
       ".drift{animation:drift 90s linear infinite}@keyframes drift{from{transform:rotate(0)}to{transform:rotate(360deg)}}")

SKY = (40, 232, 960, 566)            # x0, y0, x1, y1 of the star field (local coordinates)
SYNODIC = 29.530588853


def moon(date):
    """Phase fraction 0..1 (0 = new) and illuminated fraction for a UTC date, from the mean synodic cycle."""
    new_moon = datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)
    noon = datetime.datetime(date.year, date.month, date.day, 12, tzinfo=datetime.timezone.utc)
    p = (((noon - new_moon).total_seconds() / 86400) / SYNODIC) % 1
    return p, (1 - math.cos(2 * math.pi * p)) / 2


def moon_name(p):
    names = ["NEW MOON", "WAXING CRESCENT", "FIRST QUARTER", "WAXING GIBBOUS", "FULL MOON", "WANING GIBBOUS",
             "LAST QUARTER", "WANING CRESCENT"]
    return names[int((p * 8 + .5) % 8)]


def moon_svg(doc, cx, cy, r, p):
    """The moon as seen from the northern hemisphere: the lit limb is on the right while waxing."""
    k = math.cos(2 * math.pi * (p if p <= .5 else 1 - p))        # +1 new .. -1 full
    lit = (f"M{f(cx)} {f(cy - r)}A{r} {r} 0 0 1 {f(cx)} {f(cy + r)}"
           f"A{f(abs(k) * r)} {r} 0 0 {0 if k > 0 else 1} {f(cx)} {f(cy - r)}Z")
    flip = f' transform="translate({f(2 * cx)} 0) scale(-1 1)"' if p > .5 else ""
    gid = doc.uid("mg")
    doc.define(f'<radialGradient id="{gid}" cx="{f(cx)}" cy="{f(cy)}" r="{f(r * 3.2)}" gradientUnits="userSpaceOnUse">'
               f'<stop offset="0" stop-color="{EMBER}" stop-opacity=".16"/><stop offset="1" stop-color="{EMBER}" stop-opacity="0"/></radialGradient>')
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r * 3.2)}" fill="url(#{gid})"/>'
            f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{r}" fill="#0B0D16" stroke="{SILVER}" stroke-opacity=".5" stroke-width=".8"/>'
            f'<path d="{lit}" fill="{EMBER}" fill-opacity=".92"{flip}/>')


def spanning_tree(pts):
    """Prim's minimum spanning tree over points: the constellation lines."""
    if len(pts) < 2:
        return []
    done, edges = {0}, []
    while len(done) < len(pts):
        best = min(((i, j) for i in done for j in range(len(pts)) if j not in done),
                   key=lambda e: math.dist(pts[e[0]], pts[e[1]]))
        edges.append(best)
        done.add(best[1])
    return edges


def place_clusters(names, weights, box):
    """Deterministic, non-overlapping anchor points: heavier clusters get more room. Greedy farthest-point."""
    x0, y0, x1, y1 = box
    rng = random.Random(404)
    pts, out = [], {}
    for name in sorted(names, key=lambda n: (-weights[n], n)):
        r = min(24 + 9 * math.sqrt(weights[name]), 92)
        best, best_d = (x0 + r + 60, y0 + r + 12), -1e9
        for _ in range(260):
            x, y = rng.uniform(x0 + r + 40, x1 - r - 90), rng.uniform(y0 + r * .8 + 6, max(y0 + r * .8 + 7, y1 - r * .8 - 34))
            d = min([math.dist((x, y), (px, py)) - pr - r for px, py, pr in pts] + [1e9])
            if d > best_d:
                best, best_d = (x, y), d
        pts.append((best[0], best[1], r))
        out[name] = (best[0], best[1], r)
    return out


def render(data):
    W, H = 1000, 650
    days = data["days"]
    active = sum(1 for d in days if is_active(d))
    streak = longest_streak(days)
    synced = datetime.datetime.fromisoformat(data["synced"].replace("Z", "+00:00"))
    p, illum = moon(synced.date())
    commits = data.get("commits", {})
    public_total = sum(n for v in commits.values() for _, n in v)
    pub_by_day = {}
    for v in commits.values():
        for day, n in v:
            pub_by_day[day] = pub_by_day.get(day, 0) + n
    private = [(d[0], max(0, (d[1] or 0) - pub_by_day.get(d[0], 0))) for d in days]
    private = [(a, b) for a, b in private if b > 0]
    private_total = sum(n for _, n in private)

    alt = (f'Development telemetry from the GitHub API, refreshed daily: {data["total"]:,} contributions in the last '
           f'12 months on {active} active days, longest streak {streak} days, {data["repos"]} public repositories. '
           f'Shown as a night sky: each star is a day of commits, grouped into one constellation per public '
           f'repository, with {private_total} contributions in private repositories and other activity as an '
           f'unnamed cluster. Moon: {moon_name(p).lower()}, {illum * 100:.0f}% lit. Last sync {data["synced"][:10]}.')
    doc = kit.Doc(W, H, alt, CSS)
    clip = kit.plate(doc, density=.2)
    g = [kit.panel(doc)]

    readouts = [(f'{data["total"]:,}', "CONTRIBUTIONS · 12 MO"), (str(active), "ACTIVE DAYS"),
                (str(streak), "LONGEST STREAK · DAYS"), (str(data["repos"]), "PUBLIC REPOSITORIES")]
    for i, (value, cap) in enumerate(readouts):
        x = 58 + i * 228
        g.append(doc.text(value, x - 2, 118, 56, "serif", WHITE))
        g.append(f'<rect x="{x}" y="134" width="10" height="1.5" fill="{AMBER}"/>')
        g.append(doc.text(cap, x + 18, 139, 9, "mono-400", SILVER, .95, track=1.9))
        if i:
            g.append(f'<path d="M{x - 26} 72V140" stroke="{WHITE}" stroke-opacity=".07"/>')

    # ---- the sky: one cluster per repository, plus the unnamed private cluster
    x0, y0, x1, y1 = SKY
    g.append(f'<path d="M{x0} {y0 - 20}H{x1}" stroke="{WHITE}" stroke-opacity=".07"/>')
    g.append(doc.text("NIGHT SKY  ·  EACH STAR IS A DAY OF COMMITS  ·  LINES JOIN A REPOSITORY'S DAYS", x0, y0 - 6, 9, "mono-400", SILVER, .9, track=1.4))
    series = {name: [(d, n) for d, n in v] for name, v in commits.items()}
    if private:
        series["\u0000private"] = private
    weights = {k: sum(n for _, n in v) for k, v in series.items()}
    anchors = place_clusters(list(series), {k: len(v) for k, v in series.items()}, SKY)   # room by number of stars
    today = datetime.date.fromisoformat(days[-1][0])
    for name in sorted(series, key=lambda n: -weights[n]):
        ax, ay, rad = anchors[name]
        pts_days = series[name]
        rng = random.Random(sum(map(ord, name)) * 31)
        pts = []
        for k, (d, n) in enumerate(pts_days):
            ang = k * 2.399963 + rng.uniform(-.3, .3)                     # golden-angle spread
            rr = min(rad, 9 + math.sqrt(k + 1) * rad / math.sqrt(len(pts_days) + 1) * .98)
            pts.append((ax + rr * math.cos(ang), ay + rr * math.sin(ang) * .78))
        is_private = name == "\u0000private"
        tone = PRIVATE if is_private else AMBER
        edges = spanning_tree(pts)
        lines = "".join(f'<path d="M{f(pts[a][0])} {f(pts[a][1])}L{f(pts[b][0])} {f(pts[b][1])}"/>' for a, b in edges)
        g.append(f'<g stroke="{tone}" stroke-opacity="{.28 if is_private else .35}" stroke-width=".8">{lines}</g>')
        ages = [(today - datetime.date.fromisoformat(d)).days for d, _ in pts_days]
        for (x, y), (d, n), age in zip(pts, pts_days, ages):
            fresh = max(0, 1 - age / 365)
            r = 1.1 + math.sqrt(n) * .85
            col = EMBER if (not is_private and age < 30) else (WHITE if not is_private else "#C4B5FD")
            op = .45 + .55 * fresh
            if age == min(ages) and not is_private and age <= 14:                  # the newest star breathes
                g.append(f'<circle class="halo" cx="{f(x)}" cy="{f(y)}" r="{f(r + 2)}" stroke="{AMBER}" stroke-width=".9"/>')
                g.append(f'<circle class="pulse" cx="{f(x)}" cy="{f(y)}" r="{f(r + .6)}" fill="{AMBER}"/>')
            else:
                g.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col}" fill-opacity="{f(op)}"/>')
        label = "PRIVATE  ·  UNNAMED" if is_private else (name.upper() if len(name) <= 20 else name.upper()[:18] + "..")
        total = weights[name]
        g.append(doc.text(label, ax, ay + rad * .78 + 17, 8.5, "mono-500", "#C4B5FD" if is_private else WHITE, .8, "middle", track=1.3))
        g.append(doc.text(f"{total} {'CONTRIBUTIONS' if is_private else 'COMMITS' if total != 1 else 'COMMIT'}", ax, ay + rad * .78 + 29, 8, "mono-400", SILVER, .75, "middle", track=1.2))
    doc.keep(x0, y0, x1, y1 + 6)

    # ---- the moon over Bhopal, on the day of the last sync
    mx, my, mr = 894, 296, 17
    g.append(moon_svg(doc, mx, my, mr, p))
    g.append(doc.text("MOON  ·  BHOPAL", mx, my + 34, 8, "mono-500", SILVER, .85, "middle", track=1.4))
    g.append(doc.text(f"{moon_name(p)}  ·  {illum * 100:.0f}%", mx, my + 46, 8, "mono-400", SILVER, .7, "middle", track=1))

    # ---- language mix
    by = 594
    langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs) or 1
    top5 = [kv for kv in langs if kv[0] != "Other"][:5]
    rest = total - sum(v for _, v in top5)
    if rest > 0:
        top5.append(("Other", rest))
    xx = 60.0
    for (name, v), tone in zip(top5, LANG_TONES):
        w = 880 * v / total
        g.append(f'<rect x="{f(xx)}" y="{by}" width="{f(max(w - 2, 1))}" height="4" rx="1" fill="{tone}"/>')
        xx += w
    slot = 880 / max(len(top5), 1)
    for i, ((name, v), tone) in enumerate(zip(top5, LANG_TONES)):
        lx = 60 + i * slot
        short = {"Jupyter Notebook": "Jupyter"}.get(name, name).upper()
        g.append(doc.runs([(short + "  ", WHITE, .85, "mono-400"), (f"{100 * v / total:.0f}%", SILVER, .9, "mono-400")],
                          lx, by + 20, 8.5, track=1.3))

    g.append(kit.registration(doc))
    stamp = data["synced"].replace("T", " ")[:16] + " UTC"
    g.append(kit.corner_labels(doc, tl="FIG. 5  /  STATION TELEMETRY", tr="PUBLIC ACTIVITY ONLY",
                               bl=f"LAST SYNC  {stamp}", br="SOURCE  ·  GITHUB API"))
    doc.add(f'<g clip-path="url(#{clip})">{"".join(g)}</g>')
    return doc


def main():
    """Fetch fresh data into scripts/telemetry.json. `build.py` renders it (python3 scripts/build.py --fetch)."""
    token, login = os.environ.get("GITHUB_TOKEN"), os.environ.get("GH_LOGIN")
    if not token or not login:
        raise SystemExit("Set GITHUB_TOKEN and GH_LOGIN.")
    data = fetch(login, token)
    CACHE.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"cached {data['total']} contributions, {sum(n for v in data['commits'].values() for _, n in v)} public commits")


if __name__ == "__main__":
    main()
