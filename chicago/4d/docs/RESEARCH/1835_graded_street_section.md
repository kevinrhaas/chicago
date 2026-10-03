# The graded street section (T-1812, piece 2 of T-1770)

T-1811 laid every opened street as full-width packed earth. It said that grading the roadbed
below an entrance-level walk shelf, with the terrain and the walker's collision moved, was
T-1812's job, and nothing in it claimed that. This is that grading.

## What changed, and where the one elevation contract lives

- **The terrain.** `generators/terrain_gen.py` reads a new `street_sections` block in the 1835
  spec and, before the bridge approaches, lowers the worked width of each of the 28 opened
  streets in `data/streets/1835.json`. The line is the one `streets.js` draws
  (`drawn_track_local_enu_m`, else `path_local_enu_m`). The width is the class's `worked_share`
  of the corridor, which `tools/check_street_section.py` holds equal to `streets.js`'s
  `WORKED_SHARE`. Where streets cross, the deeper cut wins, so an intersection has no seam.
- **The walker.** It stands on `terrain.walkHeight()`, which is this heightfield, so its
  collision moved with the ground. There is no second surface. The road ribbon drapes on the
  same field.
- **Walks and doors.** The cut reaches nothing one 2.5 m cell inside the worked edge
  (`shelf_clear_m`). The renderer reads the field bilinearly, so a lowered sample at the edge
  would drag the ground down across the plank walk's own strip. Held clear, the frontage
  generator re-derives the same 44 plank walks, 3 decked walks, 46 posts and 107 refusals as
  dev.
- **Crossings.** A board crossing over a lowered bed now steps down each shoulder in flat
  treads (`EDGE_CROSS_TREAD_M`, 0.6 m grain). Its boards already followed the ground. All 44
  crossings are laid, as on dev, on 348 walking decks where dev had 294.
- **Structures in a road.** Four buildings and one bridge stand inside a worked width:
  Beaubien's trading post, Hogan's store, the Newberry & Dole slaughterhouse and the slough log
  bridge. The cut is held off each (`keep_clear`), and `tools/validate.py`'s ground-contact
  check is what named them.
- **Inputs hash.** The 1835 ground's staleness hash now carries the street fields the section
  reads, and only those (`STREET_SECTION_FIELDS` in `generators/terrain_inputs.py`). Renaming a
  street does not cost a bake, but moving one does.

## A measured South Water section

This section is at E +499.8 N +8.4, between Wells and LaSalle, read from the committed
heightfield before (dev) and after. The + offsets are on the river side.

| offset (m, + = river side) | ground before (m) | ground after (m) | lowered by (m) | what stands there |
|---:|---:|---:|---:|---|
| -13 | 0.701 | 0.701 | 0.000 | lot / bank beyond the corridor |
| -12 | 0.685 | 0.685 | 0.000 | shelf: verge and plank walk |
| -11 | 0.669 | 0.669 | 0.000 | shelf: verge and plank walk |
| -10 | 0.649 | 0.649 | 0.000 | shelf: verge and plank walk |
| -9 | 0.629 | 0.629 | 0.000 | worked earth at shelf level (held one cell clear) |
| -8 | 0.607 | 0.568 | 0.038 | worked earth at shelf level (held one cell clear) |
| -7 | 0.583 | 0.448 | 0.134 | gutter, then the shoulder rising |
| -6 | 0.559 | 0.328 | 0.230 | gutter, then the shoulder rising |
| -5 | 0.535 | 0.306 | 0.229 | crowned bed |
| -4 | 0.511 | 0.294 | 0.217 | crowned bed |
| -2 | 0.466 | 0.284 | 0.182 | crowned bed |
| +0 | 0.426 | 0.264 | 0.162 | the line streets.js draws (crown) |
| +2 | 0.393 | 0.216 | 0.177 | crowned bed |
| +4 | 0.370 | 0.134 | 0.237 | crowned bed |
| +5 | 0.366 | 0.173 | 0.193 | crowned bed |
| +6 | 0.362 | 0.221 | 0.141 | gutter, then the shoulder rising |
| +7 | 0.360 | 0.268 | 0.092 | gutter, then the shoulder rising |
| +8 | 0.360 | 0.312 | 0.048 | worked earth at shelf level (held one cell clear) |
| +9 | 0.360 | 0.356 | 0.004 | worked earth at shelf level (held one cell clear) |
| +10 | 0.360 | 0.360 | 0.000 | shelf: verge and plank walk |
| +11 | 0.360 | 0.360 | 0.000 | shelf: verge and plank walk |
| +12 | 0.360 | 0.360 | 0.000 | shelf: verge and plank walk |
| +13 | 0.358 | 0.358 | 0.000 | lot / bank beyond the corridor |

Cells lowered: 21,127 (13.2 ha); deepest 0.305 m; mean over lowered cells 0.136 m.

Run `python3 tools/check_street_section.py --section south_water@500` to print this section
at 0.5 m. The river-side shelf is lower than the town side because the plain falls to the bank.
That is the natural cross-fall, and the cut follows it.

## Coverage: every opened corridor

`python3 tools/check_street_section.py` measures the bed below the shelf every 10 m along all
28 opened streets. It skips crossings, approaches, kept-clear structures and water. The median
depth equals each class's crown: principal 0.14–0.16 m (crown 0.152 m), ordinary 0.13 m
(0.122 m), light 0.08–0.10 m (0.076 m). The 51 unopened platted corridors are not cut, because
nobody had worn them.

21 stations read the bed above its shelf. Fourteen are on North Water along the bank brow, one
is on each of five cross streets, and two are on the fort bank track. There the natural crest
outweighs a 0.1 m cut. The gate reports them and does not fail on them.

## What else moved, and why each move is the ground's

The cut moved several readings and derivations, and all were re-derived:

- Viewpoints: `data/render/anchor_ground_reading.1835.json`. Eight anchors now stand 0.02 to
  0.22 m lower.
- West tiers: the notes for Carroll, Fulton, Lake, Randolph and Washington, and
  `west_tiers_west_reach.json`, which give the lowest dry sample.
- North Division tier: `north_division_tier_lots.json` (min 1.09 → 0.99 m).
- Bridge-head timber and yard goods: `town_trade_goods.json`. **Six wagon stands are now
  refused, 84 → 78.** They stand on low riverside verges of South Water, Market, Wells, LaSalle,
  Clark and Dearborn. The lowered bed there fell under the yard rule's 0.60 m "not in the river"
  proxy. That proxy is about the bank, not a road bed. Filed as a follow-up rather than bent
  here.
- Woody planter reach: 1,580,965 → 1,580,502 nodes, rebanked. These are road cells near the
  water that fell under the planter's dry floor. Trees do not belong in a worked road anyway.
- South-bank ground (T-0134): rebanked. Its finding still holds: zero free building positions
  at 0.30 m or 0.35 m relief.

## Frame cost

The ground mesh went from 1,131,566 to 1,164,920 triangles (+2.9 %). The published terrain
derivative went from 2,906,264 to 3,041,168 bytes (+135 KB). The heightfield stays 3,792,294
bytes.

**The road ribbon is the real cost.** `streets.js` refines a panel wherever its vertices miss
the ground by more than 3 cm (T-0110). A crowned bed with gutters is not flat across, so
nearly every graded panel refined. With the old rule, which halved both axes together, the
streets layer went from 59 k to 466 k triangles. Refinement now halves across the street
first and along it only if that is not enough. That brings the layer to 296 k. The section
needs about four to eight columns, and that is the floor for this shape.

| stand (1280×800, `full`) | before: draws / triangles | after |
|---|---|---|
| Clark North, walker | 87 / 976,870 | 86 / 1,435,155 (within the 1,460,000 budget) |

The other stands were shot before the ribbon fix, so their "after" triangle counts in
`graded-street-section-proof/` overstate the shipped cost.

**The layer was being paid for twice, and now it is paid for once, at about a third of the
size.** Read with `__chicago4d.stats()` at Lake Street at Canal after `goTo` (published mirror,
1280×800), which is the stand where smoke desktop **part 5**'s five-stand sweep (T-0135, `scene
detail '…' stays inside its own ceiling at the WORST stand`) finds every tier's worst frame:

| Lake Street at Canal | `full` | `light` | street layer |
|---|---|---|---|
| dev (b31dc146) | 1,508,838 | 874,131 | 59 k, drawn twice |
| branch, across-first, two passes | 1,994,929 | 1,361,014 | 296 k, drawn twice |
| branch, across-first, one pass | 1,698,562 | 1,064,647 | 296 k, once |
| **branch now: lattice columns, one pass** | **1,509,086** | **875,171** | **107 k, once** |
| ceiling | 1,460,000 | 825,000 | |

- **One pass.** The street material is transparent and `DoubleSide`, and three draws that
  combination in two passes: back faces first, then front faces. Each triangle is rasterised
  in only one of them, but both are submitted and counted. `forceSinglePass` draws the same
  triangles once, with the same lighting.
- **Columns at the lattice, not at halvings.** The ground is `surfaceHeight()`, a bilinear
  field on a 2.5 m lattice, and along a line it bends only where it crosses a lattice line. A
  panel that misses now puts its columns at those crossings on its middle row, and falls back
  to halving across only if that does not settle it. The layer is **106,891 triangles** over
  the same 6,937 panels, and the worst interior sink is 0.285 m (gate 0.35). Merging
  crossings closer than 15 % of the width, instead of 4 %, was tried and is worse: 275 k
  triangles and a 0.49 m sink. The columns are cheap only because they are exact.
- **A shared row is watertight.** Two panels that meet on a row with different column counts
  disagree about that row by a float32 rounding. At west_water's 7.7° bend at [−13.08,
  −302.6] that hairline was the mitre row itself, and the smoke's wedge stations fell into it
  (part 7). The finer panel's end-row midpoints are now stepped outward, one float32 at a
  time, until they stand on or just past the straight line between the row's corners. Each
  panel then reaches the shared line from its own side.

So the graded section now costs the frame what dev's flat ribbon did, to within 0.02 %.
**Both tiers are over their ceilings at this stand on dev as well.** Part 5 is red there for
dev's own reasons, by the same amount. The one-pass lever alone would bring dev to about
1,450 k / 815 k. Without the streets this branch reads 1,402,195 / 768,280 at this stand, 12 k
more than dev's 1,390,192 / 755,485. That 12 k is the ground mesh above.

(An earlier reading on this branch counted desktop part 4's reference stand as the gate. Part
4 holds the reference-stand checks; the worst-stand sweep is part 5.)

## Captures and critique

`graded-street-section-proof/before-*.jpg` and `after-*.jpg` were taken at fixed stands with
a frozen clock, chrome hidden, `full` detail and SwiftShader. Desktop is 1280×800 and mobile
390×780. The stands are South Water at walker height looking east (380.4, 5.4, 89.5°), across
South Water from its south shelf (500, −1.2, 35°), South Water from 16 m, and the town from
70 m. There were zero pageerrors at every stand.

- At walker height on South Water the eye stands 0.18 m lower (2.377 → 2.197 m over the
  datum), because the visitor walks the bed. The walks on both sides now stand proud of the
  road rather than flush with it. From the bed the shelf reads as a low bank with the boards on
  top, which is the relationship the Detroit and Cincinnati views show.
- From the south shelf looking across, the drop is legible but quiet. 0.2 m over 19.5 m of
  pale dust under noon sun is a soft shadowless dip, not a trench, and that is honest for a worn
  street. It reads better in low light. A wetter gutter tone would make it read better still.
  That belongs to the surface, and a later ticket can take it with T-1771's mud.
- From the air it is invisible, as it should be at 16 m and 70 m.
- Ruts are still colour only. Rut walls would need sub-cell relief, and the 2.5 m heightfield
  cannot carry them.

## T-1956 — the river walk keeps its bank

The river walk (`data/frontage/river_walk_frontage.json`) lies inside South Water's worked
width, north of the travelled track. So the cut above reached under it, and so did the
end-caps of Clark's and La Salle's cuts where they meet South Water at the bank. The bank
under the walk's south half fell by up to 0.22 m and tilted 0.16 m across the walk's 1.83 m.
On mobile part 2, "the plank decks tie into the ground they cross" read 0.191 m against its
0.18 m band.

`street_sections.keep_clear_lines` holds the cut off the walk. Each entry carries one reach's
committed centreline and names the streets whose cut it holds. Within `flat_m` of the line
those streets' section depth is zero, and it eases back to the full section by `outer_m`.
`flat_m` is 4.5 m: half the walk (0.915 m) plus the diagonal of one 2.5 m heightfield cell
(3.54 m). The renderer reads the ground bilinearly from the four samples round a point, so no
sample under any board is a lowered one. 3.5 m, one cell square, left 0.05 m at Clark's mouth,
so the diagonal is the bound. Dearborn is deliberately not named. The walk crosses it on its
own boards, and T-1955 seated that crossing on Dearborn's graded shoulders.

Measured every 0.5 m along each reach, at the centreline and both edges, against the
heightfield before T-1812 (`353f7898^`):

| reach | stations | dev, worst Δ | now, worst Δ | cross-tilt before / dev / now |
|---|---|---|---|---|
| crossing footway | 69 | 0.000 | 0.000 | 0.011 / 0.011 / 0.011 |
| east reach | 606 | 0.220 | 0.000 | 0.084 / 0.196 / 0.084 |
| west reach | 1,251 | 0.219 | 0.000 | 0.160 / 0.164 / 0.160 |
| wharf reach 1 | 582 | 0.164 | 0.000 | 0.115 / 0.125 / 0.115 |

What a visitor sees: along the river, South Water's lowered bed now stops short of the river
walk. The north half of the road climbs back to the bank the walk stands on, rather than the
bank tilting down under the boards.
