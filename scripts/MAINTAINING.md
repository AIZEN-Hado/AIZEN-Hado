# Maintaining the profile

The profile is **one tall dark canvas cut into 31 horizontal image slices**, stacked in `README.md` with no
gaps. Everything is generated; never hand-edit `README.md` or `assets/`.

| To change | Edit | Then run |
|---|---|---|
| Any text: name, tagline, identity, research vectors, stack, projects, frontier notes, contact | `scripts/profile.json` | `python3 scripts/build.py` |
| Layout or section order | `build_all()` in `scripts/build.py` | `python3 scripts/build.py` |
| Background constellation (density, reach, motion) | `scripts/canvas.py` | `python3 scripts/build.py` |
| Telemetry design (not data) | `scripts/telemetry.py` | `python3 scripts/build.py` |

Python 3.10+ standard library only.

## How the canvas works

- **One coordinate system.** Each slice knows its position on the page. The background (void, soft glows,
  stars and the neural constellation) is computed in page coordinates, so lines and glows continue exactly
  across seams. Nodes are generated per 150 px row from fixed seeds, so every slice agrees with its neighbours.
- **Two passes.** Pass 1 records where every word and illustration sits; pass 2 draws the constellation
  around them. Nodes and amber signals never sit behind text; faint edges may pass behind it, and panels
  mask the background with their own fill. The result is saved to `scripts/canvas.json`.
- **No gaps.** The README is a single paragraph of `<img align="top" width="100%">` with no whitespace
  between images. Keep it that way, or GitHub's page colour shows through as grey lines.
- **Motion** is CSS only and stays inside a slice: each image starts animating when it loads, so anything
  that crossed a seam would fall out of step. Signals run only on edges wholly inside one slice.
- **Reduced motion.** Every slice has a frozen twin in `assets/static/`, swapped in through `<picture>` for
  visitors with `prefers-reduced-motion` (browsers ignore that preference inside an SVG shown as an image).
- **Text is outlined** from `glyphs.json` (Instrument Serif, Inter, JetBrains Mono; SIL OFL), because
  GitHub's image proxy blocks web fonts. Rebuild it only to add characters: see `scripts/fonts.py`.

## Projects

`profile.json → projects[].show` picks what appears in Selected Work, numbered automatically. A project marked
`"private": true` cannot be shown (its link would 404): make the repository public, remove `"private"`, set
`"show": true`. Each needs an illustration in `CARD_ARTS` (`scripts/arts.py`).

## Telemetry

`.github/workflows/telemetry.yml` runs daily at 03:17 UTC and on demand. It reads public activity with the
built-in `GITHUB_TOKEN`, caches it in `scripts/telemetry.json`, and re-renders `assets/telemetry.svg` at its
page position from `scripts/canvas.json`, so it still lines up with its neighbours. After any layout change,
run `build.py` so `canvas.json` is current.

## Commits

Commits are authored with the GitHub no-reply address so they count on the contribution graph. The daily
telemetry commits are authored by `github-actions[bot]` on purpose: automated commits should not inflate it.
