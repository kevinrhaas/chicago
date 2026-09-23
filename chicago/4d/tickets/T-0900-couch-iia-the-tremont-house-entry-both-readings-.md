---
id: T-0900
title: Couch, Iia — the Tremont House entry both readings of Norris 1844 fail on: read the printed token off the page image
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-10
pr: 1056
claimed_by: run 9/10/2026, 2:31:18 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T08:01:21.715Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34450132649
---

Couch, Iia — the Tremont House entry both readings of Norris 1844 fail on: read the printed token off the page image.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0695**, the pass that repaired the other eleven garbled forenames in Norris
1844 against Kim Torp's independent transcription. This one it could not touch.

    Couch, Iia, proprietor of the Tremont House, corner of Lake and Dearborn sts
      — n1844_e0415, archive.org's OCR
    Couch, (can't read), proprietor of the Tremont House, corner of Lake and Dearborn sts
      — 1844directory.txt:449, Kim Torp, typed from a different copy

Both hands fail on the same token, from two different copies, which is itself a finding:
the type is damaged or inked badly in the printing, not just in this scan. `Iia` is not
GARBLED in `name_agreement`'s sense — every character is a letter a compositor sets — so
the crosswalk refuses `Ira Couch` against it as two full forenames that differ, with no
note that the reading is in doubt.

Ira Couch of 1835 kept the Tremont House with his brother James, and `Couch, James, res
Tremont House` stands on the next line of the same page. That is exactly why the token
must be READ and not deduced: the match this project wants is sitting right beside it, and
reading `Ira` into the page because the match would be nice is the failure provenance
exists to prevent.

**Acceptance:** the printed token at printed page 30 of `generaldirectory19norr` is read off
the PAGE IMAGE, and whatever it says is what `normalized.given` carries — a repair row in
`read_norris_1844.py` cited to the image if it is legible, or a recorded refusal to guess if
it is not; `quote` keeps the damage either way; the Norris crosswalk is re-derived and what
moved is itemised; `bash tools/check.sh` green.

---

## What this run found, and did (2026-09-10)

**The token had already been read.** T-0903 answered this ticket the same day it was
opened — PR #997, `IMAGE_REPAIRS` in `tools/read_norris_1844.py` — and nobody closed
T-0900, so it sat at the top of the queue as work that looked undone. The page image
prints **Ira**; `normalized.given` has carried `Ira` since that merge, `quote` and
`as_printed` keep `Iia`, and `Ira Couch` is a match in the Norris crosswalk rather than
a forename refusal.

**Closing it on that say-so would have been the wrong move.** An image repair is one
hand on one token, and this project's whole case for a `documented` reading is that a
reader can go back to it. So all four page-image repairs were re-cropped from the leaf
images and read again, cold:

| line | leaf | word box | read again |
|---|---|---|---|
| `Couch, Iia` | 40 | `271,2163,358,2125` | **Ira** — the second stroke is an r, shoulder and no dot |
| `Abbott, VV.` | 31 | `248,1776,328,1742` | **W.** — one sort; the `Ward` two words along is the same one |
| `Day, VVm.` | 42 | `199,617,319,582` | **Wm.** — and no comma after it, as the row says |
| `Hequenbourg, G. VV.` | 49 | `495,1758,574,1725` | **G. W.** — one sort, spaced as an initial |

All four stand. Each row now carries the box it was cropped on and the second reading,
so the next reader reproduces the crop instead of trusting it.

**And the re-read found a defect in the citation itself.** `IMAGE_SOURCE` stated the
page images are "1592 x 2860, which is the coordinate space that XML is written in".
That is the size of leaf 31 only — the first leaf T-0903 read. Leaves 40, 42 and 49 are
1564 x 2912. A reader who took the quoted figure for the book's coordinate space and
cropped leaf 40 by it would land off the line and conclude the citation was invented.
The coordinate space is now stated as per-leaf, every row carries its own `leaf_px`,
and `--self-test` refuses a row whose box falls outside the leaf it names, or that cites
no box, or that was read by one hand only.

**What moved:** four claims in `norris_1844_directory_entries.json` gain
`given_repair.evidence.{leaf_px, word_box, coordinate_space, read_a_second_time}`. No
reading moved, `counts` is unchanged (15 repairs, 4 of them from the image), and
`norris_1844_crosswalk_1835.json` re-derives **byte-identical** — so no card, no
occupation and no address in the town moved. No bake.
