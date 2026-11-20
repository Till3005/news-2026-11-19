# Design notes — THE WORLD DAILY, Thursday 19 November 2026

## Approach

Everything is procedural. `main.py` (Python 3.13, stdlib only: `math`, `os`,
`struct`, `zlib`) allocates a 1024×1024 RGB framebuffer, draws into it with a
handful of primitives, and encodes it as a PNG with its own chunk writer
(signature → IHDR (8-bit truecolor) → IDAT (`zlib` of filter-0 scanlines) →
IEND, each with a CRC-32). No fonts are loaded: the page is typeset with an
embedded 5×7 bitmap glyph table (A–Z, 0–9, and `: , . ' " - & + % : ; ! ? / ( ) * $`)
scaled ×1–×7 at draw time. No random, no clock: two runs produce byte-identical
files.

## Palette (fixed)

| role | hex | use |
|---|---|---|
| paper | `#f4eeda` | full-bleed newsprint ground, ticker text |
| ink | `#1c1a16` | masthead, headlines, card borders, pictogram bodies |
| crimson | `#b32b2b` | date line, kickers, lead kicker, stars, accents |
| blue | `#2f4a6b` | card deks, the four-points line, chart axes |

Four flat colors keep the file tiny (well under 1 MiB after zlib) and give the
crisp "pixel-editorial" look — everything sits on a strict integer-pixel grid.

## Layout (top → bottom)

1. **Masthead band** — hairline rule; folio row ("VOL. LXXXII - NO. 323",
   "( PRICE: ONE IMAGE )"); "THE WORLD DAILY" at 7× scale centered; the date
   "THURSDAY, 19 NOVEMBER 2026" in crimson at 3× (the page names its day twice —
   also in the bottom folio); thick-over-thin newspaper rules.
2. **Lead story** — crimson kicker, two 3× headline lines on the Shenzhen
   trilateral, two 2× dek lines ('Declaration Towards Peace', Berlin's
   "Yalta format" warning), a blue 1× summary of the four points, and a column
   rule separating text from the pictogram: three crimson stars over three
   silhouetted leaders at a round table.
3. **Story grid (3×3)** — bordered 320×170 cards: crimson kicker with underline,
   44px pictogram, 2× headline (≤3 lines), 1× blue dek (≤2 lines).
   Order: COURT (scales — ICJ/Myanmar), WORLD (tank crossing a dashed crimson
   line — Gaza), WORLD (suspension bridge — Kerch), BUSINESS (rising stock
   arrow — Anthropic), MIDEAST (tower with impact burst — Riyadh), US
   (baseball — Pete Rose), SPORT (football — Lyon 2–0 Arsenal), TECH
   (chip — Nvidia probe), SCIENCE (atom orbits — 105-qubit contextuality).
4. **Ticker strip** — solid ink band with a paper-colored hippo silhouette
   (Fiona) and four 1× bulletin items separated by asterisks.
5. **Folio** — "PAGE 01 - THE WORLD DAILY - THURSDAY, 19 NOVEMBER 2026"
   over closing rules.

## Constraints check

- ≤ 1024×1024 px, ≤ 1 MiB PNG (truecolor + flat colors compress hard).
- Deterministic output, runs in well under a second, ~30 MB RAM.
- All copy is factual per the verified 19 Nov 2026 wire; no invented quotes.
