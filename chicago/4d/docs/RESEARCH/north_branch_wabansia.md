# The North Branch north of the forks window — what was traced, and what was not

**Traced:** 2026-09-12 · **Ticket:** T-1072 (the north half of T-0794) · **Epoch:**
`e1834_harbor_cut` · **Tool:** `tools/trace_north_branch.py` · **Output:**
`data/terrain/epochs/e1834_harbor_cut/branches.geojson`

Re-derivable end to end:

```
python3 tools/trace_north_branch.py            # re-trace and write
python3 tools/trace_north_branch.py --check    # re-trace and diff against committed
python3 tools/trace_north_branch.py --debug    # + a PNG overlay of the trace
python3 tools/trace_north_branch.py --check-properties   # the offline half; check.sh runs it
```

---

## 1. What was missing

`tools/trace_river.py` traces the forks inside a 1120 px window of the BPL master scan of
J. S. Wright's 1834 survey. T-1071 carried the South Branch out of the bottom of that window
to the School Section's south line. The North Branch had the same hole at the other end: the
committed water stopped dead on the forks window's **north** edge, map row 1252, a little
north of Kinzie Street — and everything Wright draws above that row, the whole length of the
river through Wabansia, was not in the project at all.

That is the reach the town looks at. Wabansia's river-front water lots — Kain's and Hight's
subdivision, the lots numbered 6 to 19 on the sheet — front on this water, and until now they
fronted on nothing.

## 2. A fourth window, and where the splice is

Same argument as the third, mirrored. `trace_river.py` finds a 70 m channel in a town of
coloured ward washes by working at a LOCAL block percentile, so enlarging its window would
move every vertex the forks trace has already committed — and the terrain is carved from
those vertices. So this is a separate window whose **south edge is the forks window's north
edge**:

| | window (resource px of the BPL master, 4204 × 5166) |
|---|---|
| forks (`trace_river.py`) | x 868, y 1252, 1120 × 1120 |
| **North Branch (this trace)** | **x 640, y 0, 780 × 1252** |
| South Branch (`trace_south_branch.py`) | x 1150, y 2372, 800 × 2578 |

Row 1252 is a line both tools name, not a tolerance either of them hopes for.
`river.geojson` is neither read nor rewritten here, and `trace_north_branch.py` asserts
`trace_river.REGION[1] == 1252` before it segments a pixel, so moving the forks window breaks
this trace loudly instead of quietly unsticking the splice.

**How well the two polygons actually meet**, measured on the splice row against Wright's own
inked bank lines (at row 1251 the ink stands at x 1120–1122 and x 1234–1237):

| | west bank | east bank |
|---|---|---|
| committed forks polygon | x 1124 — **2.1 m** east of the ink | x 1247 — **8.2 m** east of the ink |
| this trace | x 1117 — **2.8 m** west of the ink | x 1188 — **33.8 m** west of the ink |
| the two polygons' disagreement | **4.9 m** | **60.1 m** |

The west side of the splice is as good as the sheet allows. The east side is not, and § 5
says what it is and what it is not.

## 3. The setting that had to change: green and grey, thirteen units apart

The forks settings carry north unchanged except one — `hue_tol`, 11 → 7.

`wash_mask` separates Wright's grey bank wash from his coloured ward washes by how far a
pixel's hue departs from the LOCAL paper's. On Wabansia's river front that separation is the
narrowest it is anywhere on this sheet. Medians over a 13-row band at map row 745, across the
west bank:

| | R−B | G−B |
|---|---|---|
| green wash on the river-front lots | 27 | **31** |
| grey bank wash beside it | 32 | **19** |
| paper of the channel between the banks | 40 | 26 |

One channel, thirteen units, and a tolerance of 11 swallows it. This is not a rounding error
in the result. At `hue_tol` 8 the traced west bank steps **131 px — 93 m — into the lots** at
map row 800, and the polygon published as river would have covered ground Wright drew as
platted lots with lot lines ruled across it. That is a categorical mistake, not a graded one:
a reader of `branches.geojson` cannot tell a bank the tool got 93 m wrong from a bank Wright
drew there.

Going the other way, at `hue_tol` 5 the upper reach's own bank wash starts leaving with the
colours and the trace breaks at row 764 — the channel comes out in two pieces and the seed
keeps only the southern one. **The whole usable band is `hue_tol` 6 and 7**, which is why the
value is argued from the pixels in the table above rather than tuned to a pretty picture. 7 is
taken because 6 sits one step from the break.

This is the third time the hue reference has been the thing that mattered and the second time
it decided a reach: T-1071 moved `hue_block`/`hue_pct` because the School Section's yellow
reservation wash was standing in for paper. There the reference was wrong; here the reference
is right and the tolerance around it was too loose. Both are the same fact about this sheet —
Wright's washes are close to his paper and to each other, and the segmentation is only ever as
good as the local statement of what paper is.

## 4. What is published, and at what grade

Three features, all `inferred`, all sourced to `wright_1834`:

| id | what |
|---|---|
| `north_branch_wabansia` | the water polygon — 64 ring vertices, **4.8 ha** |
| `north_branch_west_bank` | Wabansia's river front — **799 m**, 31 vertices |
| `north_branch_east_bank` | the unplatted ground east of the river — **782 m**, 30 vertices |

Drafted channel width at the seed: **62.6 m (205 ft)**, against the forks trace's own 72.9 m for this
reach inside its window, 69.7 m for the main stem and 57.3 m for the South Branch, and 49.7 m
for the South Branch up in the School Section. The branch narrows as it leaves the forks, which
is what the sheet draws; no gauging record is claimed for it.

**No bed depth is claimed here at all**, and `--check-properties` fails if one ever appears.
A cadastral plat gives planform and not soundings; the water surface is flat at the datum for
the same reason the forks are, because the pre-reversal river had a near-zero surface gradient
and stood at lake level through this reach. **No crest heights** either: north of the modelled
terrain box there is no heightfield for a crest to belong to.

## 5. The east bank, where it was short — one stretch repaired, one refused

`hue_tol` 7 bought the west bank at a price on the east one. Measured per row against Wright's
inked east bank over all 932 rows of the reach (`tools/measure_north_branch_banks.py`, whose
committed baseline carries both columns), the trace as T-1072 published it sat a median
**1.4 m** inside the ink, p90 **8.5 m**, and was short of it by more than 10 m on **81 rows**,
in exactly two places. **T-1078 read both stretches off the scan, and they are not one fault.**

| all 932 rows, east bank | median | p90 | max | rows > 10 m short |
|---|---|---|---|---|
| T-1072, as published | 1.42 m | 8.54 m | 32.73 m | **81** — rows 728–779 and 1222–1251 |
| T-1078, `seam_wash` | 1.42 m | 6.40 m | 14.94 m | **51** — rows 728–779 only |

### rows 1222–1251, the splice — repaired, and it is T-0834's fault with a wider seam

A **dry band ten to fifteen pixels wide** runs between the channel and the east bank over the
reach's last thirty rows: unwashed paper, reading 15 to 17 units *lighter* than its own block's
paper percentile. East of it stands 402 px of unmistakable bank wash — `tint` 0 to 6 against a
tolerance of 7, `dark` 15 to 40 — and because 402 is under the 500 px speckle floor it went out
with the specks, leaving the 40 px close nothing to bridge to. This is exactly the fault
`south_branch_spike_1834.md` measures and `bank_wash()` repairs; `bank_wash()` refuses it here,
on both of its width terms, and the refusal is measured rather than assumed: its `bank_seam_px`
is 3 against a seam of 10–15, and its `bank_ink_px` is 1.5 against a wash that stops 5.0 px
short of Wright's pen line. It puts **one** fragment back anywhere on this reach, 274 px, and
**the east boundary does not move**.

So the repair asks the question those two numbers were standing in for, and asks it of the scan
(`tools/trace_river.py` → `seam_wash`): **is there a path from the fragment to the channel that
crosses nothing Wright drew?** A path may run over bare paper and over grey bank wash; it may
not cross ink, and it may not cross a wash of another colour. Three fragments qualify — 479,
402 and 274 px — and the rule introduces no tolerance of its own: its reach is `close_r`, the
radius the channel morphology already bridges across unwashed mid-channel, and the same three
fragments come back at every radius from 10 px to 40 px.

**The splice row, re-measured against the ink on both sides** (acceptance 3). At row 1251
Wright's east bank is inked at resource x 1234:

| | boundary | nearest ink | against the ink |
|---|---|---|---|
| east, T-1072 | x 1188 | x 1234 | **32.7 m inside** |
| east, T-1078 | x 1225 | x 1234 | **6.4 m inside** — within the polygon's declared `uncertainty_m` 20 |
| west, both | x 1117 | x 1120 | **2.1 m OUTSIDE**, unmoved — § 2's reading, and see the leak test |

And the corroboration nobody arranged: `tools/trace_river.py` measures the North Branch's
drafted width just SOUTH of the splice row, this trace measures it just NORTH of it, and the two
windows share nothing but that line. Before the repair they read **62.6 m** and **72.9 m** — a
10.3 m step at the seam, because the east bank was short exactly there. After it they read
**72.6 m** and **72.9 m**. `tools/check.sh` now holds them to within 1 m of each other.

### rows 728–779 — refused, and what it would take

There is no seam here and no fragment to put back. What stands between the bank wash and the
ink is 17 to 19 px of **coloured wash** — `dark` 26 to 67, `tint` 12 to 61 against a tolerance
of 7 — so no path exists that does not cross something Wright drew, and `seam_wash` correctly
declines. Reading it as bank would be precisely the error `hue_tol` 7 exists to prevent (§ 3:
93 m into Wabansia's platted lots). The 51 rows are left short, stated here, and not graded up
to cover: the water polygon carries `uncertainty_m: 20` like its neighbours and these rows
exceed it.

**T-1082 asked the legend what that colour is, and the answer is that it is not one of the
nine.** § 5a has the reading; the short version is that the band lies on no chip's dilution ray
— the nearest comes 21.0 RGB units off it, and only at t 3.4, which is three times the solid
swatch and not a dilution at all — and it is not the reach's own bank wash either (21.3 off,
t 1.22). So the stretch is not held open waiting on the tract layer any more. The reading is
the one the ticket predicted: **the sheet does not draw a bank there**, and the rows stay short.

### the leak test, which is the one that could have gone badly

A repair to the east bank is only safe in one direction, and "the west median improved" does not
show it. Nor does a one-sided ray: where the boundary has slipped PAST Wright's pen line the
bank ink stands on the water side of it, and a ray that only looks outward walks over the line
and reports the distance to the next one beyond. That is the splice row's west side exactly — 2.1 m
outside the ink, reported as 41.3 m *inside* it by an outward-only reading, and § 2 had the
true number all along. So the measurement takes the nearest ink on EITHER side and signs it:
positive inside the ink, negative over it into the ground beyond.

Signed that way, the repair improves the west bank on both halves of the question and worsens
neither:

| all 932 rows, west bank | median inside | p90 | rows > 10 m short | rows OUTSIDE the ink | worst outside |
|---|---|---|---|---|---|
| T-1072, as published | 3.56 m | 8.54 m | 63 | **42** | **14.23 m** |
| T-1078, `seam_wash` | 2.85 m | 7.83 m | 35 | **34** | **9.96 m** |

**No row is further outside the ink than it was: 0, worst deepening 0.00 m.** That is the test
acceptance 2 was reaching for, and it is the one `tools/check.sh` now runs on every commit
(`measure_north_branch_banks.py --check-properties`), alongside a ceiling of 14.23 m held as a
ratchet — it may come down and may not go up. Acceptance 2's own figure of 8.5 m could not be
used as written: that p90 is the EAST bank's, and the west bank already stood 14.23 m outside
its own inked line before anything was repaired.

The west bank's five remaining outside-the-ink stretches — 707–710, 715–717, 922–939, 948–951
and 1247–1251, the west side of the splice — were filed here as having the same cause as the
east bank's survivor: a coloured wash between the grey bank wash and the ink. **Measured, they
do not** (T-1082, § 5a). Three of the five are the reach's own grey bank wash laid a little
heavier, one is a legend wash, and the last is three pixels of ink shoulder. None of them is
the east stretch's colour, and no boundary moves for any of them.

## 5a. What the wash is — the legend asked, on the sheet the band is actually on

**Read:** 2026-09-13 · **Ticket:** T-1082 · **Tool:**
`tools/read_north_branch_bank_wash.py` · **Record:**
`data/traces/north_branch_bank_wash.json` · **Gated:** `tools/check.sh`, offline

```
python3 tools/read_north_branch_bank_wash.py --report            print the reading
python3 tools/read_north_branch_bank_wash.py --build             re-read both rasters
python3 tools/read_north_branch_bank_wash.py --check-properties  the gate; no raster, no network
```

### The thing that had to be settled first: the two sheets are two different colour records

`tools/read_wright_legend_swatches.py` read Wright's nine legend chips on the **National
Archives / Historic Urban Plans facsimile**, because at 600 dpi a chip is 54 px wide there.
Every stretch in question is located on the **Boston Public Library master** and nowhere else.
Carrying the facsimile's answer across fails twice, and both failures are measured:

* **Position.** Of the 116 coloured bands the facsimile reading committed, the nearest to any
  of these six stretches is **235 m** away, and the nearest to the east stretch — the one this
  ticket was opened on — is **481 m**. The facsimile's band map has nothing on this reach at
  all. (It could not have: the two sheets' affines carry 16.0 m and 17.5 m of RMS, so moving a
  17 px band between them costs about 33 px of positional uncertainty, twice the feature.)
* **Colour.** The same nine chips are **not the same nine colours**:

  | chip | the legend says | master | facsimile | apart |
  |---|---|---|---|---|
  | 1 | U.S. Military Reservation | 213, 194, 161 | 44, 65, 93 | **223** |
  | 2 | Surveyed by Canal Com. in 1830 | 226, 179, 161 | 176, 68, 48 | 166 |
  | 3 | Wabansia, surveyed in 1831 | 100, 123, 129 | 145, 38, 14 | 150 |
  | 4 | Kinzie's Addition, surveyed 1833 | 186, 182, 124 | 54, 44, 29 | 213 |
  | 5 | School Section, surveyed 1833 | 223, 185, 78 | 218, 136, 26 | 72 |
  | 6 | Surveyed ——— 1833, no tract named | 115, 134, 113 | 70, 67, 40 | 109 |
  | 7 | Fractional Section 15 | 102, 149, 144 | 135, 37, 11 | 177 |
  | 8 | Surveyed in 1833, no tract named | 217, 77, 64 | 180, 112, 39 | 57 |
  | 9 | Part of Canal Section No. 9 | 207, 133, 96 | 57, 50, 23 | 186 |

  Chip 1 is **bare paper** on the master and deep blue on the facsimile. The facsimile is a
  reprint and its publisher's inks are not Wright's washes. Neither reading is wrong; they are
  readings of two different objects, and **a wash on the master must be matched against the
  master's chips**. So this tool reads the legend again, off the master, at interior
  x 2682–2732 and the nine row runs the column's own darkness gives (stable at luminance 200,
  205 and 210). Grouped at the facsimile reading's own 35-unit threshold the master's chips
  fall into six separable colours as well, but **different** ones: `{1,2} {3,6,7} {4} {5} {8}
  {9}`. Nothing here revises the facsimile reading, which stays correct about its own sheet.

### How a wash is matched to a chip: the dilution ray, not the distance

A legend chip is a solid swatch; the ground is the same pigment laid thin. On the master the
ground washes sit 40 to 120 RGB units from their own chip **for being diluted**, so
nearest-colour — the facsimile reading's rule, which its uniform reprint inks justify — matches
nothing on this reach. What survives dilution is DIRECTION: a wash of chip *k* laid over paper
*p* lies on the ray *p → k*, a fraction *t* along it. Each band is projected onto every
reference's ray and carries two numbers: the perpendicular residual (is this the pigment?) and
*t* (how thin?). A band is that pigment when the residual is under **12 RGB units** and *t* is
in **(0.05, 1.25]** — below, it is bare paper and the direction is noise; above, it is darker
than the solid swatch itself. The references are the nine chips **and the reach's own grey bank
wash**, because "this is just the bank shading" is a live answer and had to be able to win.

An assignment names the **class**, never the chip: the classes are exactly what the chips can
separate, and this file refuses past them the same way the facsimile reading does.

### The six stretches

Band = the pixels between the traced boundary and the nearest ink, ink excluded. Paper is the
local unwashed paper beside each stretch. `perp`/`t` are of the best reference's ray.

| stretch | band | width | dark / tint | band RGB | best ray | perp | t | verdict |
|---|---|---|---|---|---|---|---|---|
| **east 728–779** | 886 px | 17.0 px | 41.7 / 26.1 | 182, 149, 121 | chip 1 | **21.0** | 3.38 | **not identified** |
| west 707–710 | 49 px | 12.2 px | 22.9 / 8.0 | 172, 161, 143 | bank wash | 2.7 | 1.05 | the bank wash |
| west 715–717 | 21 px | 7.0 px | 24.3 / 8.1 | 167, 156, 138 | bank wash | 2.3 | 1.19 | the bank wash |
| west 922–939 | 74 px | 4.1 px | 36.4 / 41.3 | 170, 172, 169 | chip 3 | 6.4 | 0.40 | class {3, 6, 7} |
| west 948–951 | 22 px | 5.5 px | 45.6 / 3.8 | 164, 155, 140 | bank wash | 6.5 | 1.17 | the bank wash |
| west 1247–1251 | 3 px | 0.6 px | 90.2 / 8.9 | 120, 119, 101 | bank wash | 9.1 | 2.35 | **not identified** |

**The east stretch, which is the ticket's own question, is refused.** No reference's ray comes
within 21 RGB units of it, and the one that comes closest needs *t* 3.38 — three times the
solid swatch, which is not a dilution. It is not the bank wash either (21.3, *t* 1.22). Its own
colour says what it is not: against its paper it reads (−40, −58, −62), a near-neutral brown,
where every chip that could plausibly wash this ground departs its paper far harder in one
channel. The colour is not one of the nine, and this file does not guess a tenth.

**Three of the five west stretches are the grey bank wash.** Residuals 2.3, 2.7 and 6.5 against
a nearest rival ray of 10.2 — Wright's own bank shading, laid at *t* 1.05 to 1.19, a little
heavier than the reach's median. They are **not** the coloured-wash fault § 5 filed them under.
Their `tint` medians say the same thing from the other side: 8.0, 8.1 and 3.8 against a
tolerance of 7, which is the tolerance's own margin rather than a colour. What they are is the
opposite fault — bank wash brushed a few pixels past Wright's pen line, which is why the
boundary there stands OUTSIDE the ink by 0.7 to 10.0 m rather than short of it.

**One is a legend wash.** Rows 922–939 sit 6.4 off chip 3's ray at *t* 0.40, inside class
{3, 6, 7} — Wabansia 1831, the unnamed 1833 survey, or Fractional Section 15. The class is as
far as the chips go, and separating within it is the tract layer's polygon work (T-1097), not
a colour's. Either way it is ground with a name, which is exactly what `hue_tol` 7 refuses to
draw a bank over.

**One is three pixels** on the splice row, where the boundary already stands 2.1 m outside the
ink (§ 2). At *t* 2.35 it is twice the bank wash's strength: an ink shoulder, not a wash. The
rule refuses it for having nothing to read rather than for what it is.

### What moves, and what does not

**Nothing in the trace.** Every stretch either refuses identification or lands on ground with a
name, and both answers leave the boundary where it is. `tools/measure_north_branch_banks.py
--check` was re-run against the committed baseline and reproduces it exactly — east median
1.42 m, p90 6.40, 51 rows over 10 m; west median 2.85, 34 rows outside the ink, worst 9.96 m,
0 rows worse than before.

**`LEAK_BUDGET_M` stays at 14.23.** T-1082 offers to bring the ratchet down "if the west bank
improves", and it has not: no boundary moved this pass. The committed post-repair worst is
9.96 m, so there is 4.27 m of headroom a future pass may claim — but claiming it for work that
did not move a pixel would tighten a gate on someone else's measurement.

**Both refusals are gated.** `check.sh` fails if a future edit ever makes the two sheets' chips
agree, or puts a facsimile band within 100 m of this reach, or identifies the east stretch's
colour without this note moving with it — because those are the three things the reading above
rests on, and a refusal that is not gated is a refusal that quietly expires.

## 6. What the northern end is

Wright ruled a line across the top of his survey and washed the river up to it. The channel's
north end at map row 309 is therefore **where he stopped drawing, not where the river stopped
running**: the North Branch ran on north for miles, to the Skokie marshes, past anything on
this plat. The terminal stretch is dropped from both bank lines for exactly the reason
T-1071's southern one is — publishing it would assert a river end this sheet never drew — and
it cannot be told by the ink, because at this terminus there IS a line: the survey's own north
boundary, drawn across the channel. Six ring vertices come off, three on the splice row and
three on the survey limit, and the trace prints both counts on every run.

## 7. What this unblocks

* Wabansia's water lots (T-1069) get the water they front on. Until now the lot strip's river
  side was a boundary with nothing on the other side of it.
* The two branches now run from the sheet's north margin to the survey's south line in one
  connected chain of three polygons, which closes **T-0794** — both halves of it.
* `validate.py`'s waterline crossings already read every polygon in `branches.geojson`
  (T-1071), so a face that ends on the North Branch now meets a bank that exists.

## 8. What was NOT done

* **No terrain.** The heightfield box stops far south of here; this is planform only.
* **No bathymetry, no crests, no revetment**, and no claim about the bank's material.
* **Nothing east of the river.** The unplatted ground Wright washes on that side is a tract
  question (T-0792), not a water one — and § 5a now says what the colour along its edge is
  *not*: measured on the master, it is none of the legend's nine at any dilution, so calling
  it "salmon", as this note did until T-1082, was an eye's word and not a reading.
