# The West Division's lot figures, read off the Thompson plat

**Record:** none — a reading, not a building ·
**Data:** `data/traces/thompson_west_division_lots.json` ·
**Source:** `data/sources/thompson_plat_1830.json`, the copy of the sheet held at
`chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` ·
**Gate:** `tools/read_west_division_lots.py --check`, in `tools/check.sh` ·
**Ticket:** T-0689, filed 2026-09-04 when the owner closed T-0444 with its point 1 unpaid

---

## 1. The debt

T-0444's acceptance, restated with the owner's plat ruling in it, opened:

> The West Division's lot dimensions and block lot-counts are read off
> `chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` and committed as data, each
> reading with the region of the sheet it was taken from — **not inferred from the South
> Division.**

PR #681 answered everything else in T-0444 and said in its own words that this was still
owed: *"The next run on T-0444 reads the West Division's lot dimensions and lot-counts off
that sheet…"* The run never came, T-0444 closed, and T-0689 was filed to keep the debt from
closing with it. This memo is the run.

Why it was worth keeping: the whole West Division question is whether its grid sits one
street west of where this project draws it, and the answer is supposed to rest on figures
read off a sheet rather than on the South Division's spacing carried across. Until now the
two load-bearing inputs to that answer — a 180 ft lot depth and "two lots across by five
down" — were labelled inferences in `west_division_module.md` and were exactly that.

## 2. What the sheet actually says

Both are printed on it, and so is a third figure nobody had.

| figure | value | read where |
|---|---|---|
| street width | **80 ft** | the legend, and again in every street along the south town line |
| alley width | **18 ft** | the legend |
| lot **depth** | **180 ft** | the north face of block 29 (both columns), the west column of block 44, and the south face of blocks 48, 49, 50 and 51 |
| lot **frontage** | **75 ⅗ ft** | the west margin of block 47, five rows, and block 26, five rows |
| lots to a block | **ten**, two columns of five | counted, block by block, on all six tiers |
| the alley runs | **north–south**, between the two columns | drawn on every standard block |
| scale | 160 ft to an inch | the legend |

Twenty-two blocks and two hundred and three lots are in the data file, each with the pixel
region it was read on, in `x,y,w,h` against a 2728 × 1944 scan whose sha256 is committed
beside the reading. Change the scan and every citation goes red at once rather than quietly
pointing at coordinates nobody checked.

## 3. The closure, which is why this is a reading and not a transcription

The block's **east–west** width comes from three printed figures — 180 at a block face, the
legend's 18 ft alley, 180 again:

> 180 + 18 + 180 = **378 ft**

Its **north–south** height comes from a different printed figure, in a different margin,
multiplied by numerals counted inside the block:

> 5 × 75 ⅗ = **378 ft**

The two sums share no input. They meet to the foot. **The five-row West Division block is
square**, 378 ft each way, and each reading checks the other — which is worth more than
either alone, because the sheet was never going to hand over a figure that could not be
misread at this resolution.

Add the street and the module follows:

> 378 + 80 = **458 ft = 139.598 m**

## 4. #681's memo, re-read against the figures — acceptance point 3

**It survives, exactly, to three decimal places.**

`west_division_module.md` derived 458 ft on 2026-09-03 from *2 × 180 ft lot depth + 18 ft
alley + 80 ft street*, and graded two of those four inputs as inferences it would have to
give up if the sheet were ever read:

- *lot depth 180 ft* — "recovered from this project's own committed east-west street
  spacings". **Read. 180, printed, on six block faces.**
- *two lots across by five down* — "the owner's reading, carried in T-0443". **Read. Ten
  numerals, two columns of five, on every standard block of six tiers.**

So the module does not move by a foot, and the three findings that stand on it stand
unchanged: `canal` about 21 m too far west of the plat's own arithmetic, the committed
`clinton → canal` pair 90 ft too close together, and three of the five streets held by
nothing. The gate asserts the agreement in metres rather than leaving it to be noticed
(`tools/read_west_division_lots.py`, `MODULE_M_IN_THE_MEMO`), so if either the memo or the
reading is ever edited away from the other, the commit that does it goes red.

**The swap test is untouched.** It never used the module — it used the *ceiling* of 263 ft
that the committed west bank imposes, and that ceiling stands on the bank alone. Nothing
here moves it, and the swap stays excluded.

## 5. What the reading adds that nobody had — acceptance point 2, the other way round

**The West Division lot does not front 80 ft.** The South Division block is four lots to a
face of about 320 ft, which is 80 ft of frontage, and 80 is the number an inference carries
west. The sheet prints **75 ⅗**, the same figure in every row of both margins that carry
one. Four and a half feet per lot, ten lots a block, over six tiers. The gate now refuses an
80 ft West Division frontage outright so the inference cannot return as a tidy-up.

**And the tiers are not all the same tier.** This is the part an inference would have got
most wrong, because an inference has no reason to expect it:

| tier | rows | lots | |
|---|---|---|---|
| north town line – Carroll | 4 | 8 | truncated by the town line; prints **7 \| 8** in its north row and then 2 \| 1, 3 \| 4, 6 \| 5 — a run no other West Division tier uses |
| Carroll – Fulton | 5 | 10 | its **south row is deeper**: block 11's margin prints **96** against it where the four above read the seventies figure |
| Fulton – Lake | 4 | **8** | the block simply ends under 7 \| 8, with Lake Street directly beneath |
| Lake – Randolph | 5 | 10 | the square block |
| Randolph – Washington | 5 | 10 | the square block; block 46 carries "Reserved" written across its lots 3 and 4 |
| Washington – south town line | 5 | 10 | the square block; its south face is the sheet's "Due East and West Line" |

**The riverfront is written as three numbers, north to south.** Block 29 prints 180 at both
its columns — at the Lake tier the branch has not reached the Canal-to-West-Water block at
all. Block 44 prints 180 and **150**. Block 51 prints 180 and **88**. And block 22, in the
Fulton tier, is not a block: one column of four lots, 2 3 6 7, each face narrower than the
one above — 17, 70, 118 — with lot 8 in a detached triangle whose south face reads 141.
Lots 1, 4, 5, 9 and 10 do not exist there.

## 6. The refusals — acceptance point 2

Fourteen of the twenty-two blocks print no dimension at all, and the sheet is not at fault:
a draughtsman dimensions the first block of a tier and lets the tier inherit. Five more
print a figure **this scan cannot resolve to a digit**:

- **blocks 11 and 25**, west margins. Unmistakably a two-digit number in the seventies with
  a fifths fraction, in the same hand and the same place as blocks 26 and 47's 75 ⅗, and
  unmistakably **not** 80 — but the second digit does not survive. Recorded as `7?3/5`.
- **block 48**, west margin. Five figures against five rows, smaller and fainter than 26's
  and 47's; tried at 7×, 9× and 26×, both rotations, auto-contrasted and nearest-neighbour.
  Two or three glyphs each and no more.
- **block 10**, west margin, three of four rows: two dark glyphs, nothing further.
- **block 22**, the upper river bearing: "North 3? West". The lower one, "North 51 West", is
  legible.

Each is named on its own block entry with the region it stands in and what shape the ink
holds, so a better scan of the same sheet resolves it without anyone re-deriving where to
look. A gap stated is worth more than a number carried across.

## 7. A correction this reading forces

`data/traces/thompson_block_numbering.json` § `lot_numbering.ten_lot_blocks` recorded, off
Wright's sheet, that the West Division block carries ten lots "in two rows of five, with the
numerals written across a **horizontal** alley rather than a vertical one" — while saying in
the same sentence that the numerals run "down its side". Thompson's sheet settles it: the
ten lots stand in **two columns of five**, each lot 180 ft deep east–west, fronting the
north–south street on the outer side of its column and backing on an alley that runs
**north–south** through the middle of the block. The count was right; the alley's bearing
was not. Corrected there, with a pointer here.

## 8. What this does not say — acceptance point 4

**Nothing moves.** Not a street, not a lot line, not a block. A lot dimension is a length,
and a length says nothing about where the length begins; where the West Division grid sits
is T-0445's, by T-0444's own point 4. No geometry is generated from these figures in this
commit, `data/traces/vectors/thompson_lots.json` still emits no West Division block, and the
grades in `west_division_module.md` are unchanged — every derived centreline there is still
`inferred`, because its anchor is the traced west bank and arithmetic does not upgrade its
anchor.

What changed is what the arithmetic is made of.

## 9. The sheet's own caveat, recorded because it is easy to miss

The N.B. in the sheet's top-right corner reads:

> "A Map of the Town of Chicago" is recorded in Book A page 318 with no certificates or date
> — it is generally similar or identical with the plat hereon, but has the N. line of Kinzie
> Street correctly laid down and contains a few more **dimensions which are noted in blue
> figures hereon**.

So the dimension figures in the margins and on the block faces are that later hand's
additions, not necessarily Thompson's own of 4 August 1830. They are still figures a
surveyor wrote on a tier-1 sheet, and they are what this reading reads; the sentence is
recorded on the data file so that nobody has to rediscover it. It is also, incidentally, why
the marginal frontages are fainter than the block numerals — a different pen.
