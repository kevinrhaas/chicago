# The South Branch south of the forks window — what was traced, and what was not

**Traced:** 2026-09-12 · **Ticket:** T-1071 (the south half of T-0794) · **Epoch:**
`e1834_harbor_cut` · **Tool:** `tools/trace_south_branch.py` · **Output:**
`data/terrain/epochs/e1834_harbor_cut/branches.geojson`

Re-derivable end to end:

```
python3 tools/trace_south_branch.py            # re-trace and write
python3 tools/trace_south_branch.py --check    # re-trace and diff against committed
python3 tools/trace_south_branch.py --debug    # + a PNG overlay of the trace
python3 tools/trace_south_branch.py --check-properties   # the offline half; check.sh runs it
```

---

## 1. What was missing

`tools/trace_river.py` traces the forks inside a 1120 px window of the BPL master scan of
J. S. Wright's 1834 survey, and `tools/trace_shoreline.py` traces everything east of it out to
the lake. Between them they left the whole of the South Branch above nothing and below nothing:
the committed water simply ended on the forks window's own south edge, at local **N −405 m**,
a little south of Washington Street. Wright draws the branch on from there — out of the
Original Town between Canal and Market, across Madison, and down through the School Section's
blocks 70, 71, 78 and 83–88 — for another **1,744 m**.

The owner asked for it in as many words on 2026-09-05: *"and the whole path of the river going
south and all of those."*

## 2. Why a third window, and where the splice is

A window is not free. The segmentation that finds a 50 m channel in a town of coloured ward
washes measures "darker than paper" against a **local** block percentile, and the morphology
that closes the channel across its unshaded middle is computed over the whole window. Widening
the forks window would therefore have moved vertices the forks trace has already committed —
and the terrain is carved from those vertices, so that is a re-bake of the ground for no better
reading of the paper. The project has been here before: `trace_shoreline.py` is a separate
window for the same reason, and says so.

So this trace's window is `(1150, 2372, 800, 2578)` in BPL resource pixels, and its **north
edge is the forks window's south edge**: `trace_river.py`'s region is `(868, 1252, 1120, 1120)`
and 1252 + 1120 = 2372. The tool asserts that arithmetic at run time, so if the forks window
ever moves, this trace fails rather than publishing a splice that has quietly come apart.

That makes the join a **declared line rather than a tolerance**. `river.geojson` is not read,
not written and not touched by this tool. Measured on the committed files, the two polygons
meet like this:

| | east side | west side |
|---|---|---|
| forks trace, last vertices | E 35.92, N −404.33 | E −8.08, N −405.24 |
| this trace, first vertices | E 35.92, N −405.06 | E −8.07, N −405.97 |

The eastings agree to a centimetre — they are the same pixel column through the same affine —
and the northings differ by 0.72 m, which is **one map pixel at 0.7115 m**: row 2371 is the
last row inside the forks window and row 2372 is the first row of this one.

## 3. The setting that had to change, and the 285 m it was hiding

`wash_mask` separates Wright's grey bank wash from his coloured ward washes by asking whether a
pixel departs in hue from the local paper, estimating that paper as a percentile over a block
of `hue_block` pixels. At the forks, 280 px at the 40th percentile *is* paper.

Through the School Section it is not. From map row 3580 to row 3985 the channel runs directly
alongside the yellow wash of the reserved blocks 87 and 88; a 280 px block straddles channel
and reservation, and the 40th percentile of it is the **yellow**. Measured over that reach:

| reach | median hue departure | fraction passing the ≤ 11 tolerance |
|---|---|---|
| above it (rows 3200–3560) | 5.4 | 0.79 |
| **alongside blocks 87/88 (rows 3600–3960)** | **27.1** | **0.28** |
| below it (rows 4050–4400) | 4.0 | 0.70 |

So 400 px of bank wash — **285 m of river, the whole stretch between two of Wright's bridge
symbols** — was thrown away as if it were a ward colour, and the channel came out in two
disconnected pieces with a hole in the middle. The fix is to read the paper off the **least**
tinted part of a **smaller** neighbourhood: `hue_block` 160 at `hue_pct` 15. The reach then
comes out whole, from a single seed, with no hand-placed waypoints down its length.

`open_r` also goes 9 → 12. A 4,000 px patch of stained paper in the West Division near block 51
hangs off the channel by a neck that a 9 px opening leaves standing; a 12 px opening severs it.
Measured at six stations down the reach the channel's own width is **unchanged to the pixel** by
that widening — which is why the knife is acceptable and why the numbers are printed.

## 4. The tear — and where it is not

T-0794 asked this trace to say where the manuscript's missing portion falls, because the
Historic Urban Plans reproduction of the NARA original carries the caption *"Two portions are
missing, the larger being near the lower center … the manuscript was mounted on cloth to repair
this tear"*, and the sheet's lower centre is exactly blocks 87 and 88.

**It is not on this scan.** Read at full resolution, the BPL master draws this reach whole:
both banks unbroken past the reserved blocks, both bridge symbols on it intact, and no repair
edge, patch or loss anywhere across the channel. The only thing the region carries that the
forks do not is the yellow reservation wash of § 3 — which is a fact about the hue reference,
not about the paper, and it is recorded here because for one afternoon it looked exactly like a
tear: a stretch of river that was simply absent.

So no reach of this trace is graded down for the tear and no gap is boxed. Whether the NARA
copy's loss falls here remains a question for that copy, and it belongs to T-0787.

## 5. What is published, and at what grade

| feature | kind | confidence |
|---|---|---|
| `south_branch_school_section` | water polygon, 91 vertices | `inferred` |
| `south_branch_west_bank` | bank line, 47 vertices | `inferred` |
| `south_branch_east_bank` | bank line, 43 vertices | `inferred` |

- **Planform only.** The drafted channel width at the seed station is **49.7 m (163 ft)**, and
  that is the width AS DRAFTED on a cadastral plat, not a sounded channel.
- **No bed depth is claimed at all**, and `--check-properties` fails if one is ever added by
  hand. The forks polygon carries a flat water surface at the datum and so does this one, for
  the same documented reason — the pre-reversal river had a near-zero surface gradient and
  stood at lake level through the downtown reach — but a traced bank must not be allowed to
  promote a bed, and a sheet that gives planform gives no soundings.
- **No crest heights on the banks.** South of local N −400 there is no committed heightfield
  for a crest to belong to; that ground is T-0219's and T-0465's.

## 6. What the southern end is

The polygon's south edge is the **limit of the survey**, not a river end. Wright's wash runs
straight into the School Section's south boundary line and stops on it, and the sheet ends a
little below. The two bank lines are cut short of that stretch and the drop is printed on every
run, exactly as `trace_shoreline.py` finds and drops the far edge of the lake wash. It cannot be
told apart by the ink the way that trace tells its shores, because at this terminus there *is* a
drawn line across the channel — the section's own boundary — so the cut is made on the reach's
last drawn row instead, and that decision is recorded here rather than hidden in a threshold.

## 7. What this unblocks

- **T-0791 / T-0858** — the School Section's blocks 70, 71, 78 and 83–88 can now close on
  water rather than on nothing. `tools/validate.py`'s `waterline_crossings` reads
  `branches.geojson` alongside `river.geojson` from this commit, so a street face or a block
  edge that declares it ends on the `e1834_harbor_cut` waterline down here is checked against a
  bank that exists.
- **T-0219 / T-0465** — the ground can be extended south to Madison and beyond onto a river
  that is already traced, instead of stopping because the water did.
- **T-1072** — the North Branch, through Wabansia to the sheet's top margin, is the other half
  of T-0794 and is not done here. It is a harder window than this one: the channel carries the
  sheet's own `N O R T H  B R A N C H` lettering inside it, the pink Kinzie ward band crosses
  it, and it runs between Wabansia's blue wash and the reservation's salmon one — so the hue
  reference that fixed this reach does not on its own fix that one. Measured while sizing it:
  with these settings the North Branch comes out only as far as Kinzie Street.
