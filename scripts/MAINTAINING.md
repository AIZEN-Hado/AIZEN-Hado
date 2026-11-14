# Maintaining the profile

The profile is **one tall dark canvas cut into 31 horizontal image slices**, stacked in `README.md` with no
gaps. Everything is generated; never hand-edit `README.md` or `assets/`.

| To change | Edit | Then run |
|---|---|---|
| Any text: name, tagline, identity, research vectors, stack, projects, frontier notes, contact | `scripts/profile.json` | `python3 scripts/build.py` |
| Layout or section order | `build_all()` in `scripts/build.py` | `python3 scripts/build.py` |
| Background (stars, colour grade, glows) | `scripts/canvas.py` | `python3 scripts/build.py` |
| The accretion-disk hero | `scripts/hero.py` | `python3 scripts/build.py` |
| The night-sky panel | `scripts/telemetry.py` | `python3 scripts/build.py` |
| Pull fresh GitHub data now | needs `GITHUB_TOKEN` and `GH_LOGIN` | `python3 scripts/build.py --fetch` |

Python 3.10+ standard library only.

## Two images are real data

- **The hero's accretion disk is your last 365 days.** Seven rings are weekdays (inner = Sunday), the 53 arcs
  around each ring are weeks (oldest to newest, ending at the "last 7 days" mark), and an arc's weight and glow
  come from that day's contribution count. A beam sweeps the disk; a month scale runs around it.
- **The night sky is your public commits.** Each star is a day of commits, joined into one constellation per
  public repository. Contributions that cannot be attributed to a public repository (private repositories,
  issues, reviews) appear as one unnamed cluster, computed as the calendar total minus public commits, so
  private repository names are never published. The moon is the real phase for the day of the last sync.

Data is cached in `scripts/telemetry.json`. Only public repositories are ever fetched (REST, `type=owner`, no
forks), and the daily workflow's token cannot see private ones.

## How the canvas works

- **One coordinate system.** Each slice knows its position on the page. The background (void, one slow colour
  grade from warm near the black hole to deep violet at the bottom, soft glows, sparse stars) is computed in
  page coordinates, so it continues exactly across seams.
- **Two passes.** Pass 1 records where every word and illustration sits; pass 2 draws the stars around them.
  The result is saved to `scripts/canvas.json`.
- **No gaps.** The README is one paragraph of `<img align="top" width="100%">` with no whitespace between
  images. Keep it that way, or GitHub's page colour shows through as grey lines.
- **Why there are no collapsible sections.** GitHub's `<details>` adds an arrow line and 16px of margin around
  every block, which would break the seamless canvas (tested).
- **Motion** is CSS only and stays inside a slice. Every slice has a frozen twin in `assets/static/`, swapped
  in through `<picture>` for visitors with `prefers-reduced-motion`.
- **Text is outlined** from `glyphs.json` (Instrument Serif, Inter, JetBrains Mono; SIL OFL), because
  GitHub's image proxy blocks web fonts. Rebuild it only to add characters: see `scripts/fonts.py`.

## Projects

`profile.json → projects[].show` picks what appears in Selected Work, numbered automatically. A project marked
`"private": true` cannot be shown (its link would 404): make the repository public, remove `"private"`, set
`"show": true`. Each needs an illustration in `CARD_ARTS` (`scripts/arts.py`).

## Daily refresh

`.github/workflows/telemetry.yml` runs at 03:17 UTC and on demand (Actions tab → telemetry → Run workflow),
executes `python3 scripts/build.py --fetch`, and commits only if something changed. If an API call fails the
job fails and the previous images stay up.

## Commits

Commits are authored with the GitHub no-reply address so they count on the contribution graph. The daily
refresh commits are authored by `github-actions[bot]` on purpose: automated commits should not inflate it.
