# CryoLean pitch format (taken from LeanKeel_pitch.pdf)

The reference deck is `pitch/reference/leankeel-01.png` … `leankeel-14.png` (the original, rendered at 1456 × 819).
Open several of them before you build anything. Match their look, density and tone. Do not copy their content.

## Canvas and files

- One `deck.html` per version, one `<section class="slide">` per page. Link `../shared/deck.css` and
  `../shared/check.js` (relative to the version folder). Layout reference: `shared/template.html`
  (rendered: `shared/_template_png/`).
- Design canvas 1456 × 819 CSS px. `deck.css` prints it on 1440 × 810 pt pages, the LeanKeel page size.
- Margins 97 px left and right. Eyebrow at the top (97 px). Headline under it. Content between y ≈ 205 and y ≈ 715.
  Footer source line at the bottom (46 px from the edge).
- Fonts: Arial (sans; bold headlines) and Consolas (mono). Nothing else, and no network resources (no CDN fonts, scripts
  or images). Images must be local files inside the version folder or `shared/`.

## Every content slide has exactly four parts

1. **Eyebrow**: `/ SECTION · SUBTOPIC`, mono, uppercase, letter-spaced. Orange by default; purple for Lean/proof slides,
   teal for physics/data slides (LeanKeel colours its eyebrows by section).
2. **Headline**: one sentence that states the claim, not a topic label ("Each check passes. Together they fail."
   rather than "Coupled constraints"). One line if possible, two at most, at 44 px.
3. **One main visual**: a chart from real data, a theorem/code panel, a verdict card, a table, or a diagram drawn in code.
   Next to it, at most 2–4 stat cards or short text blocks.
4. **Footer**: one grey line, two at most, giving the source: repo paths (relative to the CryoLean repo), what is real
   and what is synthetic or illustrative, and the honest limit ("proofs cover our model of the machine, not the machine").
   LeanKeel uses this line on every slide to earn trust. Write it with the same care.

## Title slide (LeanKeel slide 1)

Two-line event eyebrow, a 104 px `CryoLean` hero, a subtitle of 40 px or less (two lines at most), 2–3 coloured pills
naming the parts, the author line, then a mono footer with links plus "generic cryostat drawn in code, no real model".
The right half holds an illustration drawn in code: `shared/cryostat.svg`, or a variant made with
`shared/make_cryostat_svg.py --ring N --ring-color pink|orange|teal|purple --out <your folder>/x.svg`, or your own SVG
in the same flat style.
Authors (from git history): **Hanah Rahman · Nicholas Brandenburg**. Add no affiliations.

## Numbers

- Big numbers use `.num` (mono bold), with an 18 px label under them. Put units in the number: "12 µW", "839".
- Every number must appear in `pitch/facts/FACTS.md` (verified against origin/main b2b80ff), or be computed by your
  own chart script from repo data whose path goes in the footer. Never invent a number or round it in a misleading way.
  If FACTS.md flags a number as stale or conflicting, use the corrected value it gives.

## Colours (the same in every deck)

| colour | meaning |
|---|---|
| teal `--teal` | **Requirements met**, safe, cold |
| amber `--amber` (= orange) | **Need more information**; also AI proposers, attention |
| pink `--pink` | **Does not meet requirements**, failure, unsafe |
| purple `--purple` | Lean, proof, math |
| silver / blue / green | neutral data series only, never a verdict |

Show verdict words the way LeanKeel shows YES-IF: `.verdict-word.met` / `.info` / `.not`. Use the app's own labels:
"Requirements met", "Does not meet requirements", "Need more information". Use mono for raw kernel output
(`REQUIREMENTS_MET`, `NEED_MORE_INFORMATION`, …).

## Words

- Say it in plain English first, then the technical term. LeanKeel explains every theorem "in words".
- Short sentences, active voice, no hype words, no emoji, no exclamation marks.
- Body text at least 18 px, footer 16–17 px, chart labels at least 13 px as they appear on the slide.

## Charts

- Build them with `shared/chartstyle.py`: dark, transparent background, Arial/Consolas, verdict colours. Size each figure
  to the slot it fills, in pixels (`cs.figure(w, h)`), save it as SVG with `cs.save`, and embed it with `<img>` inside a
  `.panel`.
- Plot from the repo's own data (`CryoLean-main/paper/data/*.json`, `site/*.json`, `docs/examples/*.json`, `data/…`).
  Never paste the light-background paper PNGs.
- One message per chart. Write the key number on the chart itself (like LeanKeel's "nobody acts: over the limit after 61 s").
- Keep each version's chart scripts in its folder (`build_charts.py`) so the deck can be rebuilt.

## Density

LeanKeel slides leave about 40 % of the space empty: one visual and at most four cards. If text only fits at a smaller
size, cut text instead.

## Render and check

```
C:/Users/User_1/Desktop/CryoLean/CryoLean/pitch/.venv/Scripts/python.exe C:/Users/User_1/Desktop/CryoLean/CryoLean/pitch/shared/render.py <deck.html> --pdf <out.pdf>
```

The output must end with `RESULT: OK`: no layout issues (outside, overflow, overlap, broken image), page count equal to
slide count, page size 1440 × 810. Then open every `png/slide-N.png` with the Read tool and look at it. Fix clipped or
cramped text, ragged alignment, uneven gaps, orphan words, chart labels too small to read, and anything that looks less
finished than the LeanKeel pages. Repeat until clean. An intended overlay (a label on a chart, for example) can be
excluded from the overlap check with `data-allow-overlap` on its container.
