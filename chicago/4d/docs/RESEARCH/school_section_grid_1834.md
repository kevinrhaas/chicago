# The School Section's grid, read off Wright's 1834 sheet

**T-0797, 2026-09-06.** Piece 1 of 2 of T-0791. The deliverable is
`data/traces/vectors/school_section_blocks_1834.json` — 142 numbered blocks, the twelve
east-west streets in `data/streets/1835.json`, and three reservations in
`data/reconstruction/1835_reserved_ground.json`. Everything here is derived by
`tools/generate_school_section_grid.py`, which re-runs in a second and whose `--check`
refuses a committed file that no longer matches its own derivation.

## What the section is

Section 16, T39N R14E — the section every Illinois township reserved for schools — is the
mile square immediately south-west of the Town of Chicago, bounded by Madison Street on
the north and State Street on the east. The state sold it lot by lot in **October 1833**,
two years before this scene, and Wright draws it whole on the 1834 sheet: ruled into a
grid, numbered block by block, with three blocks lettered *Reserved* and nothing built.
This project held **none** of it — no block, no street, and no ground under the 125
land-sale rows that already name its block numbers.

## Method

The reading is a **measurement**, not a re-use of the Thompson module.

1. **Resample.** The National Archives / Historic Urban Plans scan registered by T-0787
   (5050 × 6628 px at 600 dpi, sha256 `dbb92c01…`) is sampled on a half-metre grid in
   scene coordinates through the affine in
   `data/traces/gcp/wright_1834_nara_hup_gcps.json`. That deskews the drawing: the plat's
   own rules become the axes of the raster, so a ruled line is a peak in a
   one-dimensional darkness profile.
2. **Pick every line.** Each of the fourteen north-south and thirteen east-west lines was
   picked as the centroid of that peak in up to eight independent bands along its length,
   and the median taken. Where the sheet draws a corridor with a pair of rules the pair
   gives its drawn width; the per-line values are kept in the output as `drawn_w`, with
   the number of bands that agreed.
3. **Anchor on the section, not on the paper.** Madison and State cross at the PLSS corner
   of sections 9/10/15/16 — GCP G1 of the registration — and a section is a statute mile
   on a side. The measured interior lines are rescaled linearly onto that exact square.

### The residual, and it is a finding about the fit

| | measured on the sheet | statute mile | departure |
|---|---|---|---|
| east–west span | 1603.04 m | 1609.344 m | **−6.30 m** (−0.39 %) |
| north–south span | 1658.65 m | 1609.344 m | **+49.31 m** (+3.06 %) |

The east-west span is right to four tenths of one per cent and the north-south span is
three per cent long. That is the registration's own finding showing at the bottom of the
sheet — it measured 5.2 % x/y anisotropy on this scan against 3.7 % on the BPL copy, and
said the extra stretch is in the long axis, "along which the manuscript was torn and
backed". **A y-scale three per cent long over a mile is larger than any block in the
grid**, which is why this module anchors on the section. It is also worth carrying back
to the fit itself; filed as its own ticket.

Adopted corridor widths are the platted standards — 80 ft east-west, 66 ft north-south —
against measured medians of 23.3 m and 20.4 m. The scatter of individual picks is ±5 m and
no single one is worth more than the standard; every drawn separation is kept per line.

## The numbering, and its second witness

Thirteen tiers north-south by twelve east-west make **156 cells**. Ten are the South
Branch and carry no block; four more are the east halves of blocks 73, 74, 83 and 84,
each spanning two cells because Market Street stops at Adams. **156 − 10 − 4 = 142.**

The numbering is serpentine: 1–12 down the westernmost tier, 13–24 back up the next, and
so on to 131–141 up the easternmost. **140 numerals are ink on the sheet.** Two are not:
the corner blocks at Madison-and-the-west-line and at Madison-and-State are lettered
*Reserved* and carry no numeral, and take **1** and **142** from the sequence.

Then the check that was not designed and is worth more than the reading: the October 1833
sale, already committed at `data/research/land_sales/entries.json`, resolves **217** of its
section-16 rows to a block number, and the **27** distinct blocks it names —

> 2, 23, 24, 25, 26, 47, 48, 49, 50, 70, 71, 72, 79, 80, 81, 82, 83, 84, 93, 94, 95, 96,
> 117, 118, 119, 120, 141

— are **exactly** the blocks read here in the four northern rows, with the two reserved
corners missing from both. A different hand, a different record, the same 27 numbers.

**And a second reading, made blind.** T-0875 read all 142 numerals off the same sheet
within hours of this one, on the sheet's own pixels rather than on the resampled raster,
and neither run could see the other's work. The two agree on **every one of the 142 cells**
— `tools/read_school_section_numerals.py`'s
`data/traces/school_section_block_numbering.json` against the table in
`tools/generate_school_section_grid.py`. That is now a gate rather than a remark: this
module compares the two on every run and refuses to write if they diverge. Its measured
grid lines agree with that reading's to within 13 m east-west and 18 m north-south, and
that reading independently records the same vertical stretch (it puts it at 2.6 %).

Three numerals are graded `inferred` rather than read, and each says why in its own entry:
**1** and **142** (lettered, not numbered) and **77**, whose second glyph is written
without a crossbar and reads as either 7 or 1 at 3×. 71 is read in ink two tiers west, the
sequence runs 73–76 down the tier to the west and back up this one through 78, and the
sale reached neither.

**The ticket asked for "block 119 at Madison and State".** 119 is read on the sheet one
tier *west* of that corner, with 141 between it and the reserved block; the corner block
is 142. The correction is written into the reservation's own record.

## The three reservations, tested against the sale

| reservation | sale test | result |
|---|---|---|
| block 1, Madison and the west line | the sale sells in every other block of the two northern rows and none here | **corroborated** |
| block 142, Madison and State | the sale sells in 119, 120 and 141 and none here | **corroborated** |
| blocks 87 and 88, on the South Branch | the sale never reached this far south — all 217 block-resolved rows lie in the four northern rows | **untested; its silence is silence** |

What the ground was reserved *for* is not on the sheet and is not supplied.

## What the streets are, and what they are not

Wright names four — **Madison, Monroe, Adams, Jackson** — and rules eight more tiers south
of Jackson with no name on them. All twelve are committed with `name_1835: null` where the
sheet is silent, because the later name of a line is not evidence about 1835.

All twelve carry the status the owner read off the sheet on 2026-09-05: *"no alleys and no
street names but still a grid that should have some wilderness trees"*. So
`opened: false`, `track_width_m: 0`, `alleys: false`. **A platted but unopened street had
no way to be said in this layer before now** — `compile_scene.py` required every record to
draw a worn strip inside its corridor — and the pair is now legal and must travel
together: a zero track without the declaration is still the old error, because it would
silently erase a street that existed.

Three consequences fell out, and two of them are bugs this parcel found rather than made:

- **`compile_register.py` seated the empty string as a street key.** `street_key(null)` is
  `""`, and the first unnamed street made `""` a live key: **62 businesses** the town
  cannot place moved from `unplaceable` to `street_only` on a tier no paper names. Guarded.
- **The town now holds Madison, Monroe, Adams and Jackson**, which T-0788 recorded as
  missing four days ago and filed as T-0858. One notice resolves on it immediately —
  Ebenezer S. More's, on Monroe Street — moving from `unplaceable` to `street_only`.
- `test_street_confidence.mjs` measures the gap between a street's line and the invented
  wear on its track. A street with no track is not in that measurement, and is excluded by
  name rather than by grading a wear nobody wore.

## What this does not do

No roof, no lot, no land-sale row placed on the ground — that is **T-0798**, piece 2, and
it is the visible parcel this one exists to unblock. Blocks 70, 71, 73, 74, 78 and 83–88
are emitted as their grid CELLS with `open_side` and `bank_pending: T-0794`: the South
Branch crosses them and their river side is a drawn bank rather than a ruled line.

---

## Do these lines run level, and what is a tier the fourth of?

**T-0959, 2026-09-12.** Two reconstructions of this grid, `#977` (committed above) and
`#978` (closed under T-0930), found the same 142 blocks and the same eight unnamed tiers
and disagreed about two things: what to call them, and whether they run level. `#977`'s
first ruled line south of Jackson is `school_section_tier_4`, level, `inferred`; `#978`'s
is `school_section_tier_05`, skewed by 25.7 m over 1,588 m, `attested`. At the west end the
two put the same line **48 metres apart**. This section settles both.

### The ordinal was never a reading — it is a count, and it now says what from

South of Jackson the sheet rules the tiers and **letters none of them**, so no ordinal here
is read off the paper. Both files were counting, from different places: `#977` from the
first line south of Madison, `#978` from Madison itself. Both are true and they differ by
one. The ids now carry the datum —
`school_section_tier_4_south_of_madison` — and Madison is the datum because it is the
section's own north line, the town's south boundary, and one of the four lines Wright does
name. An unlettered line's ordinal is a claim about a named line; the id states it, and the
`name_note` on each record states both counts so neither reading has to be guessed at again.

### The lines are NOT level on the sheet, and the tilt is not Wright's

`tools/measure_school_section_tier_skew.py` re-takes the measurement off the same
registered raster and **keeps the bands** the generator above throws away. The generator
picks each line as the median of six to eight bands along its length, and a median cannot
say whether the bands trended. They do. Every one of the thirteen east-west lines tilts the
same way — median **0.573°**, 16.0 m of rise across the mile.

On its own that would have settled it for `#978`. It does not, because **all fourteen
north-south lines tilt the same way too**, median **0.669°**. That is the test:

> A rotation of the drawing under its registration tilts the two families equally and
> **oppositely**. A same-signed tilt in both is not a rotation. It is a grid that has
> stopped being square.

And the evidence that it is the *frame* that un-squared it needs no assumption about what
Wright ruled. **Section 16's four boundaries are PLSS lines**: they run true north and true
east on the ground by definition of the survey that laid them, and one of their corners is
GCP G1 of this very fit. Measured exactly as the interior lines are, they tilt **+0.692°**
in this frame, against **+0.556°** for the interior. A frame that tilts its own cardinal
control is describing itself.

The mechanism is in the fit and was already on the record. It is a general affine with two
axis scales **6.2 per cent apart** at 1.894° of rotation — the same anisotropy the residuals
block blames for the 3 per cent north-south overrun — and such a map does not preserve
angles: a right angle ruled on the paper leaves it at **91.62°**.

### What follows

- **Level is right**, and right for a stated reason rather than because a median was
  carried. The committed lines are rescaled onto the section's own statute-mile square, and
  that anchoring takes the frame's shear out with the rest of its distortion. Nothing moves:
  no tier, no block, no reservation.
- **`inferred` is right** and is now earned. The northing of a tier is a measurement carried
  onto a PLSS square, not a figure any record states.
- **`#978`'s `attested` was not earned.** Its 0.93° sits inside the spread measured here and
  is the same artefact read as evidence. A tilt the registration puts on lines the PLSS
  guarantees are cardinal is not attested by the survey.

The measurement is committed at `data/traces/vectors/school_section_tier_skew_1834.json` —
every band, both families, the cardinal control and the conformality arithmetic — so the
ruling can be re-run rather than taken on trust.

### One bug two tickets found the same morning

`generate_school_section_grid.py`'s `splice()` promised to leave "every byte of the rest of
the file exactly as it was" and did not: it cut each target file at the first record it owned
and rewrote to the end. That was only ever correct while its records were the last in the
file. Twenty-two streets have been appended after them since — the North Division, the
Michigan St tract, Kinzie west of the town — so re-running the generator **deleted every one
of them, silently**, which is what this ticket's first regeneration did before the fault was
spotted. **T-0877 hit it the same morning and its fix is the one in force**: the replaced span
now ends at the first record the tool does not own, and an id of the tool's own shape that it
no longer mints is a hard error rather than a tail — which is the case a RENAME makes, and
this ticket renames eight ids.

What this ticket adds is the reason neither of us found it earlier: **the grid had no gate at
all**. Nothing re-derived the file, so nothing could notice. `check.sh` now runs
`generate_school_section_grid.py --check`.
