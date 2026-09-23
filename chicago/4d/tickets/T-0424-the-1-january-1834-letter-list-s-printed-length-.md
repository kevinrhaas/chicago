---
id: T-0424
title: The 1 January 1834 letter list's printed length, and the names all nine printings lost, need the page images
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-10
pr: 1089
claimed_by: run 9/10/2026, 4:36:39 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T22:39:30.770Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34532032273
---

T-0331 settled which return the 1834-03-04 crop carries — the Chicago post office's
**1 January 1834** return, printed for the ninth time — and repaired twenty-five of its
fifty-seven cut forenames from the eight concordant printings, without a page image.
Two questions it could not answer that way survive, and both need the images.

**1. THE PRINTED LENGTH IS STILL A FLOOR.** Seventy-eight personal names are extracted
from the 1834-03-04 crops and seventy-eight are hand-counted in them, but the crops are
not the printed list: `Anderson`, `Abbott`, `Austin`, `Axtell`, `Bertrand`, `Barrows`,
`Bowen`, `Bradford` and `Britton` all stand in No. 7's printing at line 645 and in none
of the March crops. The concordance cannot measure the shortfall, because the regions it
reads carry the interleaved advertisement as well as the list, so a surname census over
them counts `Athenian` and `Blankets` too. A count off the page images would settle the
printed length of a list this project is treating as a census proxy.

**2. THIRTY-TWO CUT READINGS ARE STILL CUT**, and `tools/letter_list_printings.py`
states the reason for each: twelve where no two printings set the same forename, four
where the surname stands TWICE in the list (Bennett, Miner, Temple — a crop that lost
both forenames cannot say which line is which), fifteen with no witness at all, and one,
Tuller, reported as a disagreement because Alden Tuller and Elam Tuller both stand in
the list, at No. 13 lines 3137-3138.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The printed length of the 1 January 1834 Chicago return is COUNTED off the page
  images, and the extracted 78 is stated against it as a shortfall rather than a floor.
- Each of the thirty-two still-cut readings is completed at the image or reported
  unreadable at the image, by name.
- Claims c026 and c027 of `chicago_democrat_1834_03_04` take `reading: scan_verified`
  for whatever the images settle, and keep `transcription_mediated` for the rest.
- The two Bennetts, two Miners and two Temples are resolved to their own lines, or the
  ambiguity is recorded as permanent.

**Links:** T-0331 (which return it is, and the twenty-five repairs) · T-0312 (the month,
and the two claims) · T-0299 (mint one list once — and these names are January's, so
they mint WITH January's) · `tools/letter_list_printings.py` · `data/research/newspapers/README.md`
§ the letter-list sweep.

## Folded in from T-0318 (2026-09-10) — one letter-list page-image pass, as T-0428 itself says

*T-0318: The January 1834 letter list: the third printing repairs the A-H half, and the images are needed only for the rest*

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

## Folded in from T-0428 (2026-09-10) — one letter-list page-image pass, as it says itself

*T-0428: The 1 April 1834 letter list has three positions no printing reads, and only the page images can say how long it was*

The 1 April 1834 letter list has three positions no printing reads, and only the page images can say how long it was.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The residue of T-0321, which raised the 1 April 1834 Chicago letter list from 179 names to
191 by reading a THIRD printing nobody had found — `chicago_democrat_1834_04_16` page 4
columns 2 and 3, c016 and c017. Sixteen of T-0321's nineteen debris lines are closed at the
transcription, without a page image. These are what is left, and no transcription can
settle them:

- **1834-04-01 line 2869** (`is Bet i`), between Thos. W. Bradley and Lewis Benton. Neither
  reprint has a line there at all — both run Bradley straight into Benton — so whether a
  name stood there is not known, and nothing was supplied.
- **1834-04-01 line 2921** (`Jeter Porter ae`), debris in all three printings: `Jeter oats`
  at 1834-04-16 line 3855, `tl. Jaiee pried Pet` at 1834-04-08 line 2475.
- **A position between James S. Cook and Leander Collins** that no ticket had named until
  T-0321's pass: `? Cook` at 1834-04-01 line 2901, `p, Cock` at 1834-04-16 line 3835,
  swallowed at 1834-04-08. A name stands there in two printings and is legible in neither.

And the question none of the three answers: **how long the printed list actually was.** 191
is a floor. Each printing loses names the other two carry — the third printing's A-J half
is cut narrower than 1834-04-01's and drops eleven the others hold; 1834-04-01 drops four
of the P surnames the others print — so the union of three impressions is still a lower
bound on one printed column.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The page images for Vol. I Nos. 18, 19 and 20 read at name level, the way
`data/sources/chicago_democrat_1833_11_26.json` was read for Vol. I No. 1 — a
`scan_verified` pass, which outranks all three transcriptions (ruling 2). It states the
printed length of the 1 April 1834 list, resolves or writes off each of the three positions
above by name, and the coverage note stops calling the cohort a floor or says why it still
is. **Sibling to T-0316 and T-0318**, which ask the same of the 1 January 1834 list; if the
images are fetched once, all of them should be read in the same pass.

## What the image said (2026-09-10, PR #1089)

The scan was fetched and read: Internet Archive `chicago1835-newspaper-chicago-democrat-1834`,
`Jan1834-Mar1834.pdf`, jp2 page 0019 — page 4 of Vol. I No. 15, the same impression the crops
were cut from. All 170 printed lines are committed in
`data/research/newspapers/letter_list_1834_01_01_printed.json`, with the IIIF regions read.

- **THE PRINTED LENGTH IS 170**, eighty-five per sub-column. The extracted 78 is 46 per cent
  of it; the shortfall is 92 lines and is the segmenter's, not the paper's.
- **31 of the 32 still-cut readings are completed at the image**, including all four the
  doubled-surname guard blocked — position settles them on one impression. The list holds
  THREE Bennetts, not two.
- **12 readings are overturned**, three of them concordance completions: `[Ori]nda Miner` is
  Miranda (Orinda is Orinda Garyl, a different line on the same page), `[Ne]stor Marshall` is
  Chester, `John Monroe` is John Monreou.
- **One fragment stays unplaced**: no line reads `Leena`, and its three candidates are named.
  It keeps `transcription_mediated` while every other entity takes `scan_verified`.
- The two Bennetts, Miners, Temples and Tullers are each resolved to their own line.

Not done here, and filed as **T-1008**: the 92 lines are read but unminted, the 97 residents
minted from the 1834-01-28 printing are a floor of the same return, and three cards
(`hh_crisey_william`, `hh_pease_h`, `hh_plumer_f`) lost a ladder rung when their names stopped
agreeing with the corrected evidence.
