# The West Division's north-south module, and the owner's shift report answered

**T-0444, piece 1 of 4 of T-0443. 2026-09-03.** Every number here is recomputed
from committed files by `tools/measure_west_division_module.py`, which carries the
assertions as `--self-test`. Nothing in this memo moves a street: moving lines is
T-0445.

## The report

The owner, 2026-08-31, from the dev preview against the Thompson plat sheet:

> "you have the whole west of the river section off … where you have what you say
> is canal, is where I am fairly sure where Clinton should be, the Canal street is
> missing and all of the buildings would be positioned further east along Canal
> correctly … I think you have Clinton where maybe Des Plaines is from the
> Thompson plat."

## The answer, in plain words

**The two lines are not mislabelled, and the reading that says they are is
excluded by the river.** But the report is right that the West Division is wrong,
and it is wrong in three ways at once, which is very likely what the preview
showed:

1. **`canal` sits about 21 m too far west** of where the plat's own arithmetic
   puts it — a fifth of a block, not a whole one.
2. **The pair is 90 ft too close together.** `clinton → canal` is committed at
   112.13 m (367.9 ft) where the plat's module is 458 ft. Every building seated
   between them is packed into ground about 20 % too narrow.
3. **Three of the five streets are not held by anything** — West Water, Jefferson
   and Des Plaines are in no committed file, so the block the eye expects between
   the river and `canal` is simply absent, and a missing street reads exactly like
   a shifted one.

Correcting 1–3 moves the buildings east along a properly spaced Canal Street,
which is the outcome the report asks for. It arrives by fixing the spacing and
supplying the missing lines, not by renaming the two that are held.

## Why the swap is excluded

The test needs no judgement. If the line committed as `canal` (local east
−170.12 m) were really **Clinton**, then Canal lies one module east of it and
**West Water** two modules east. West Water is the West Division's riverfront
street: it cannot lie east of the river.

The committed west bank of the South Branch, sampled at the three South Division
tiers that reach it, sits at local east **+2.42 m** (Lake +10.91, Randolph +2.90,
Washington −6.56). Putting West Water's *east kerb* on that bank — the furthest
east the street can possibly be — leaves its centreline at −9.78 m. So:

> two modules must fit between −170.12 and −9.78, giving a module of at most
> **80.17 m = 263.0 ft**.

The plat's module is **458 ft**. The swap needs one 195 ft smaller than that, and
263 ft will not even hold a two-lot-deep block with no alley (2 × 180 + 80 = 440 ft).
There is no lot arithmetic that makes the committed `canal` into Clinton.

## The module, and the five centrelines that follow

The plat legend states 80 ft streets and 18 ft alleys. The West Division's blocks
are drawn **two lots across by five down**, so a north-south street module is a
block *depth* plus a street:

> 2 × 180 ft lot depth + 18 ft alley + 80 ft street = **458 ft = 139.598 m**

Anchored on the committed west bank, east to west:

| street | derived east (m) | committed | delta |
|---|---|---|---|
| `west_water` | −9.78 | absent | — |
| `canal` | −149.37 | **−170.12** | 20.75 m too far west |
| `clinton` | −288.97 | **−282.25** | 6.72 m too far east |
| `jefferson` | −428.57 | absent | — |
| `des_plaines` | −568.17 | absent | — |

**The grade is inherited and is not better than its anchor.** The bank line comes
from `data/terrain/epochs/e1834_harbor_cut/river.geojson`, traced from Wright 1834
and graded `inferred` there; every derived centreline above is `inferred` for the
same reason. The spacing finding in §1 of the answer is stronger than that: a
distance between two centrelines does not depend on where the grid is pinned, so
"short by 90 ft" holds whatever the anchor turns out to be.

## What this memo did NOT establish — READ 2026-09-13, and it survives

**T-0689 read the sheet.** Everything below this line is the 2026-09-03 text, kept because
it is the record of what the module rested on before the reading; what it rests on now is
`docs/RESEARCH/west_division_lot_figures.md` and
`data/traces/thompson_west_division_lots.json`, 22 blocks and 203 lots with the pixel region
of each figure.

Both of the inferences this section owns up to are now printed figures:

- **lot depth 180 ft** — printed on six block faces (29 north, 44 west column, and the south
  faces of 48, 49, 50, 51).
- **two lots across by five down** — ten numerals, two columns of five, counted on every
  standard block of six tiers.

So the 458 ft module does not move by a foot, and `tools/read_west_division_lots.py` asserts
the agreement in metres — edit either the memo or the reading away from the other and the
commit goes red. The three findings in the answer above stand unchanged, and the swap stays
excluded on the bank, which is what it always stood on.

Two things the sheet adds that this memo could not have guessed. **The West Division lot
fronts 75 ⅗ ft, not 80** — 80 is the South Division's figure and the one an inference
carries west. And **the six tiers are not the same tier**: Fulton–Lake is four rows and
eight lots, Carroll–Fulton's south row is deeper (96 ft printed against it), and the north
tier is truncated by the town line into eight lots with a run no other tier uses. Only the
Lake, Randolph and Washington tiers are the 458 ft square this memo's arithmetic describes.

The negative search below is also closed: the sheet was in the repository the whole time,
and the owner pointed T-0444 at it on 2026-09-03.

---

### The 2026-09-03 text, as written

Acceptance 1 asks for the West Division's **lot dimensions and block lot-counts
read off the plat sheet** and committed as data. That is not done here, and the
reason is that the sheet is not available to this repository:

- no plat survey is committed — `chicago/reference/images/chicago/` holds views and
  engravings, not a plat;
- this project's own rule refuses to trace the 1834 sheets in any case
  (`data/traces/vectors/thompson_lots.json`: *"never traced off the 1834 sheets,
  whose 3.7–4.5 % anisotropic stretch would arrive as 4 % of wobble in every block
  face"*);
- a search of archive.org for the Thompson plat on 2026-09-03 returned nothing
  usable. **Negative search recorded**: archive.org advancedsearch, query
  `thompson plat chicago 1830`, 2026-09-03, no usable result.

So the two inputs that are not the legend's are inferences, and they are labelled
as such rather than dressed as plat readings:

- **lot depth 180 ft** — recovered from this project's own committed east-west
  street spacings, where the South Division is two lots deep with an alley between;
- **two lots across by five down** — the owner's reading, carried in T-0443.

Both are load-bearing for the 458 ft module. If the sheet is later read and either
is different, the module and every derived line above change with it, and the swap
test changes with them: it is the *ceiling* of 263 ft that excludes the swap, and
that ceiling stands on the bank alone, so the swap stays excluded either way.
