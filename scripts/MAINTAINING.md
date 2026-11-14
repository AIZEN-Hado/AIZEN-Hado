# Maintaining the profile

Everything visible on the profile is generated from two files. Edit those and rebuild; never hand-edit
`README.md` or anything in `assets/`.

| To change | Edit | Then run |
|---|---|---|
| Name, tagline, section titles, research vectors, stack, projects, contact channels | `scripts/profile.json` | `python3 scripts/build.py` |
| Prose: identity paragraph, research-frontier notes, section order | `scripts/readme.template.md` | `python3 scripts/build.py` |
| Telemetry design (not data) | `scripts/telemetry.py` | `python3 scripts/telemetry.py --cached` |

`build.py` needs only the Python 3.10+ standard library. It regenerates every SVG plus `README.md`.

## Projects

Each entry in `profile.json → projects` has `"show"`. Selected Work lists the shown ones in order and
numbers them W.01, W.02, … automatically. Every plate needs an illustration in `CARD_ARTS` (`build.py`);
reuse one or add a function. A project marked `"private": true` cannot be shown, because its link would be
a 404 for visitors: make the repository public first, then remove `"private"` and set `"show": true`.

## How the images work

- **Text is outlined.** GitHub serves README images through a proxy that blocks web fonts, so every glyph is
  a path from `glyphs.json` (Instrument Serif, Inter, JetBrains Mono; all SIL OFL). Regenerate it only to
  add characters or fonts: `pip install fonttools brotli uharfbuzz`, then `python3 scripts/fonts.py --serif DIR`.
- **Two image families.** Dark *plates* are self-contained and look intentional on light and dark GitHub.
  Transparent *bands* (section headers, footer) are rendered per theme as `*-dark.svg` / `*-light.svg`.
- **Motion is CSS only** and modulates a finished composition, so every frozen frame is complete. Each
  animated SVG has a frozen twin in `assets/static/`, and the generated README swaps it in for visitors with
  `prefers-reduced-motion` (browsers do not reliably apply that preference inside an SVG shown as an image).
- **No external requests.** No fonts, scripts or third-party stat services; nothing to break or track.

## Telemetry

`.github/workflows/telemetry.yml` runs daily at 03:17 UTC (and on demand from the Actions tab). It reads
public activity from the GitHub GraphQL API with the built-in `GITHUB_TOKEN`, caches it in
`scripts/telemetry.json`, and commits the re-rendered `assets/telemetry.svg` only when something changed.
If the API call fails, the job fails and the previous panel stays up.
