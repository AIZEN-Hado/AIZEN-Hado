#!/usr/bin/env python3
"""Fetch contribution data from GitHub into a JSON file. Run daily by .github/workflows/telemetry.yml.

  GITHUB_TOKEN=... GH_LOGIN=AIZEN-Hado python3 scripts/telemetry.py data/telemetry.json
  python3 scripts/telemetry.py out.json --mock       # random data, for checking the layout only
"""
import datetime
import json
import os
import random
import sys
import urllib.request


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

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]


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
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
