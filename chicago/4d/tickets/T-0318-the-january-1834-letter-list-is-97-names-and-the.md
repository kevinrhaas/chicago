---
id: T-0318
title: The January 1834 letter list: the third printing repairs the A-H half, and the images are needed only for the rest
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0424: one letter-list page-image pass, as T-0428 itself says
needs_bake: false
closed_at: 2026-09-10T04:20:06.440Z
claimed_run: null
---

T-0310 read the list of letters remaining in the Post Office at Chicago on 1 January 1834
(`chicago_democrat_1834_01_28`, page 4 column 2, lines 1105-1127) and minted **97 residents**
from it under ruling 1. Ninety-seven is a floor, not the printed length.

**THIS PLAN WAS REWRITTEN ON 2026-08-29 BY T-0323 AND NO LONGER STARTS AT THE PAGE IMAGES.**
As first written it said the two January printings "do not repair each other and the images
are the only route". There is a THIRD printing and it was not known then:
`chicago_democrat_1834_02_04` page 4 column 2, lines 2857-2943, claim c016 — the same list
over John S. C. Hogan's signature, in the ruled dialect, one name per line. Its first
alphabetical column survives at name level from Atkins to Harkness: **71 names**, with four
further lines of the same column lost to debris, so the printed first column was about 75.
That settles the floor question on its own — about 75 in the A-H half alone means the
printed list was very substantially longer than 97 — and it repairs most of the A-H damage
with no image at all.

## The count in this ticket's first paragraph was wrong, and by how much

It said "seven more are bare surnames with no initial". Counted off `c001`'s minted set on
2026-08-29 there are **ten** of the shape `[?] Surname` — Blodget, Breed, Devoe, Steele,
Sprague, Gay, Gooding, Temple, Goodrich, Warren — and two more that are bare surnames
carrying an uncertainty marker instead, `[uncertain: Childress]` and `[uncertain: Dagenet]`.
Twelve, not seven. The four cut surnames were counted right.

## What the third printing closes, name by name

The four debris lines of c016's first column are not scattered: each stands exactly where a
January name stands, which is why three of the failures below are failures of the SAME
witness rather than of the reading.

| January, as minted | the third printing at that row | status |
|---|---|---|
| `William Cr[…]` | William Criss | **closed** — merged by T-0323 into `William Crisey` |
| `Gustavus C[…]` | *debris*, `Mics ierve Otet`, between Criss and Chapman | needs the images |
| `Benj. Cl[…]` | `[Be]nj. Chapman` | reading **closed**; no Benj. Chapman is minted anywhere, so there is nothing to merge into |
| `Lewis Tem[…]` | second column, cut to forenames | needs no image: `[Lew]is Temple` from `chicago_democrat_1834_03_04` c027 closes it, and that merge is admissible |
| `[?] Blodget` | `A[l]vice Blodget` | reading **closed**; the merge into `[uncertain: Avice] Blodget` is refused by policy (below) |
| `[?] Breed` | `[A]. O. T. Breed` — and January's own `4.0.7: Breed` is that read badly | reading **closed**; merge refused by policy |
| `[?] Devoe` | `Samuel Devoe` | reading **closed**; merge into `[…]nel Devoe` refused by policy |
| `[uncertain: Dagenet]` | `Noel Dagenet` — January's `foal Dagenet` is that read badly | reading **closed**; nothing minted to merge into |
| `[uncertain: Childress]` | `Ja[m]es Childress` | reading **closed**; nothing minted to merge into |
| `[?] Gay` | the tail of the single name `Orinda Gary` | **closed** — merged by T-0323 into `[uncertain: Orinda Guryl]` |
| `[?] Gooding` | TWO Goodings stand here, `William [Good]ing 2` and `Jos. A. Gooding` | needs the images |
| `[?] Goodrich` | *debris*, `re Pp. ode rear` / `'omero'`, between `O. Grant` and `Luther Hatch` | needs the images |
| `[?] Steele`, `[?] Sprague`, `[?] Temple`, `[?] Warren` | second alphabetical column, cut to forenames and initials | needs the images |

**One lead, recorded and not acted on.** The third printing's second column keeps its
forenames where it loses its surnames, and at the row where January prints `[?] Warren` it
reads `Danie!`. If the row alignment holds across the two impressions — it holds exactly
either side of that row, `Jesse |` against `Jesse B. Winn` above and `Bally` against
`[uncertain: Sally] Weed` below — January's bare Warren is a Daniel Warren. Row alignment
across a cut column is not evidence enough to declare a name; the image settles it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The page images of `chicago_democrat_1834_01_28` page 4 column 2 are read, and a hand count
  of the printed list is stated against BOTH the 97 minted and the ~75 of the third
  printing's first column. `coverage.json`'s T-0310 note then states a count instead of a
  floor.
- The seven names the third printing cannot reach — `Gustavus C[…]`, `[?] Gooding`,
  `[?] Goodrich`, `[?] Steele`, `[?] Sprague`, `[?] Temple`, `[?] Warren` — are each either
  completed off the image or reported unreadable at the image too, and the `Danie[l] Warren`
  lead above is confirmed or refused.
- `Lewis Tem[…]` is merged into `[Lew]is Temple` with a `merge_rule`, which needs no image.
- The claim's `reading` becomes `scan_verified`, and the claims are not edited to agree
  (T-0299's rule).

**Links:** T-0323 (the third printing, and the two merges already declared) · T-0310 (the
month, and the claim) · T-0311 (the read that found the third printing) · T-0292 (mint once,
record the reprints) · T-0299 (the merge policy and the 298-people problem) ·
`data/research/newspapers/identity.json` (the family rule that refuses the four merges above)
