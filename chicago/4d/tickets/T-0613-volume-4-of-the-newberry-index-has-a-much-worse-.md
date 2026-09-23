---
id: T-0613
title: Volume 4 of the Newberry index has a much worse text layer than volumes 1-3, and a tesseract re-OCR reads the cards it loses
state: split
epic: META
requested_by: loop
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T02:03:01.820Z
claimed_run: null
---

Volume 4 of the Newberry index has a much worse text layer than volumes 1-3, and a tesseract re-OCR reads the cards it loses.

FOUND BY T-0580, which read the volume by the shared method and measured what came back. The
numbers are in `data/research/newberry_index/coverage.json` and the volume-4 block of
`precision_sample.json`; the short version:

| volume | pages | cards assembled | per page | kept | Chicago/Cook | precision |
|---|---|---|---|---|---|---|
| 1 (A-C) | 987 | 58,488 | 59 | 2,579 | 581 | 0.975 |
| 2 (C-H) | 1,016 | 58,589 | 58 | 1,987 | 501 | 0.875 |
| 3 (H-P) | 1,003 | 68,552 | 68 | 2,131 | 520 | 0.900 |
| **4 (P-Z)** | **918** | **6,548** | **7** | **308** | **10** | **0.475** |

A rendered page of volume 4 carries about 100 cards, so volumes 1-3 assemble roughly 60 per cent
of what is printed and volume 4 assembles seven. The cause is the deposited PDF, not this
project's reading: volume 4 is the one file in the Internet Archive item without the Newberry's
`FL…_CP-130151_0N` scan id (it is `130151_04.pdf`), and its text layer returns
`s:'o'ddnrdmany.` where the card prints `Stoddard family.` T-0580 ruled the crop geometry OUT as
a cause — the gutters were measured at 192, 348 and 508 points over sixty pages, and boxes cut
to them moved heading detection by 7 per cent against an eight-fold shortfall.

**THE REPAIR IS TO OCR THE IMAGES OURSELVES, AND IT IS DEMONSTRATED TO WORK.** `tesseract` on a
300 dpi render of page 300 returns `Stoddard family.` on card after card where the text layer
returns mush. It is not free: 8.5 s a page to render at 300 dpi and 6.3 s a page to OCR is about
3.8 hours for 918 pages, which is more than one run's foreground budget and is why T-0580 did
not do it. Split it before claiming — by page band is the obvious cut, and the bands can be
committed one at a time.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)
- Volume 4's cards re-read from the page images, by a pass recorded in `text/MANIFEST.json` the
  same way the crop passes are, so the reading stays reproducible from a PDF this repo does not
  carry. The OCR engine, its version and its parameters are part of that record.
- `records/entries_vol_04.json` re-parsed from the new text, every record still
  `transcription_mediated` — an engine of our own choosing is still a machine reading a
  photostat, and the grade does not move — and `--check` still rebuilding every `as_read`.
- A FRESH forty-card sample for the re-read, appended to `precision_sample.json` as its own
  block. The 0.475 belongs to the text-layer reading and may not be carried forward.
- The cards assembled, kept and Chicago-or-Cook counts stated against the table above, so the
  gain is a number rather than an adjective.
- Volumes 1-3 are NOT re-read here. If the re-OCR beats their text layers too, that is a finding
  to report and a separate ticket, not scope to take on quietly.
