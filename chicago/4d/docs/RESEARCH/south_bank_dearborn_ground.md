# The south bank at the Dearborn reach: is there ground for the plate's warehouses?

**T-0134. Settled 2026-08-28, against the committed plat, the traced 1834 waterline and
the committed heightfield. The answer is no, and the reason is not the one the refusal
was originally written on.**

**RE-READ 2026-09-26 BY T-1636, ON GROUND THAT MOVED, AND THE ANSWER IS NOW TWO ANSWERS.**
T-1629 filled the town slough's mouth this project had cut west of State Street, and the
reading below fired: 91 positions appeared where there had been none. On the frontage this
note is about the refusal HOLDS, and one clause harder than when it was written. East of
that frontage there is now buildable ground, and there is one building on it. Read § The
re-read at the end before quoting any number from the middle of this page.

## The question

Image 3 of the owner's brief of 2026-08-18
(`data/sources/assets/owner_brief_2026_08_18/README.md`) is an engraving of the reach
below the Dearborn Street drawbridge. It draws **low warehouses on BOTH banks**. T-0133
built the north side — `north_bank_shed_dearborn_{w,e1,e2,e3}`, four freight sheds
standing back from North Water Street — and left the south side empty, with one sentence
repeated in all four records:

> the platted South Water Street corridor reaches to within about 1.7 m of the traced
> 1834 waterline at the Dearborn reach, so there is no ground there for a building that
> is not standing in the platted street.

That was a spot reading, taken by hand at one station (local E 697), and the whole south
bank of the reach was refused on it. T-0134 was opened to settle it properly. The
acceptance clause offered two ways out: build the warehouses clear of whatever the
corridor turns out to be, or hold a written finding that the corridor reaches the water
and the plate's buildings cannot be sited without settling it first.

## The measurement

`tools/measure_south_bank_ground.py` walks the south bank from the Dearborn crossing —
`dearborn_street_drawbridge`'s own committed position, local E 699.2 — east to the United
States Reservation's west line at E 842.0, the line `tools/measure_no_build_ground.py`
already resolves from the State & Madison section corner. Both ends are resolved from
committed records rather than typed, for the reason `data/datum.json` is re-derived
rather than stored.

At every station it asks whether the **smallest footprint family F1 allows** — 18 × 32 ft
(5.486 × 9.754 m), the freight shed of the plate, read out of
`data/reconstruction/1835_building_inventory.json` — can be put down on ground that is
above the water surface in the committed heightfield, outside every platted street
corridor (`tools/plat_corridors.py`, the module the placement gate itself asks), and off
the refused ground of the Reservation and the sand bar.

**Every bound is the permissive one.** The rectangle may stand at any bearing rather than
square to the street. It is the smallest the family allows rather than the median. "Dry"
means one millimetre above the water surface rather than any freeboard. And the relief
clause is reported four ways: at the 0.30 m walker step tolerance three infill generators
hold themselves to (`generate_block_infill.MAX_RELIEF_M`), at the 0.35 m the north bank
sheds' own notes quote, at a full metre, and with the clause switched off entirely.

## The reading

    the south bank from dearborn_street_drawbridge (E 699.2) east to the
    Reservation's west line (E 842.0)
    124 of 143 stations carry ANY dry ground outside a platted corridor
    the widest such strip is 26.50 m, at E 813.2 (N 0.0 to 26.0, 1.30 m of relief)
    positions the smallest F1 footprint would stand at, at any bearing:
       relief <= 0.30 m       0
       relief <= 0.35 m       0
       relief <= 1.00 m       6
       no relief clause      26
    BESIDE THE PLATTED STREET — west of South Water's own east end (E 805.0),
    which is the frontage the plate draws:
       the widest free strip is 8.00 m, at E 804.2
       relief <= 0.30 m       0
       relief <= 0.35 m       0
       relief <= 1.00 m       3
       no relief clause       3

## What it says, and what it corrects

**1. The refusal holds, and it holds far more strongly than the 1.7 m reading did.** Not
one position on the whole reach, at any bearing, takes the smallest footprint the family
allows on ground flat enough for the walker — 0 at 0.30 m of relief, 0 at 0.35 m. The
plate's south-bank warehouses cannot be sited outside the platted corridor at this reach.

**2. But "there is no ground" was wrong, and the correction matters.** 124 of 143 stations
DO carry dry ground outside a corridor. The reading at E 697 was the narrowest station on
the reach, not a typical one: the free strip beside the platted street widens eastward to
8.00 m by E 804. What defeats a building there is not width, it is **slope**. That strip
is the river bank itself, falling from about +0.6 m to the water inside its own width, and
the three positions on it that accept a footprint at all span 0.96–0.98 m of relief —
better than three times the walker's step tolerance. A building put there would not share
one walker surface without a cut or a fill, which is the same clause the north bank sheds
were held to and passed at 0.30 m.

**3. The widest free ground on the reach is not on the plate's frontage at all.** The
26.50 m strip at E 813.2 lies EAST of South Water Street's committed platted line, which
ends at E 805 — it is the east bank of the town slough, under `slough_log_bridge`, between
the slough and State Street's corridor. Ground there answers a different question from the
one the plate asks, which is why the tool reports the two apart rather than in one count
that would read as frontage the warehouses could have used.

## What is still open, and it is a decision rather than a number

The plate is not refuted by any of this. It draws warehouses on this bank, and the reason
they cannot be built is that **the platted 80 ft corridor of South Water Street occupies
the whole bank down to the water at this reach** — the roadway's legal reservation, not
its travelled way. `docs/LIBERTIES.md` L79 records that the visible tracks run 5.8–10.5 m
inside that 80 ft corridor, and `tools/plat_corridors.py` says in its own docstring that a
building inside a corridor is not necessarily a building in anybody's way. South Water
Street's travelled track is committed at 10.5 m, so about 7 m of legal corridor stands
between the wheel line and the corridor's north edge at this reach, on ground the
heightfield holds flat to within 0.05 m.

So the honest question this hands on is **not "where is the ground" but "may an invented
building stand on the river margin of a platted street corridor, where this town's own
warehouses and landings stood?"** That is a decision about what the dataset asserts, not a
missing measurement:

* it would be the first record in this project placed knowingly inside a corridor —
  the 29 that lap one today are documented records the plat was fitted around, and T-0009
  owns getting them out;
* `tools/measure_corridor_intrusion.py --gate` refuses a new lap by construction, and its
  written-refusal mechanism (T-0195) exists for documented records whose escape is
  blocked, not for admitting invented ones;
* and the five South Water landings (T-0062) and the two attested docks already stand on
  the wharfing-out practice of this bank, so the alternative reading — that what the plate
  draws on the south bank is wharfed out over the water rather than standing on it — is
  live and belongs to the wharf layer (T-0059), not to the ground.

That question is filed as its own ticket rather than answered here.

## What would replace this finding

A drawn width for South Water Street at the Dearborn reach on the 1834 sheets themselves,
measured against the traced bank; or a lot record on the river side of the street. Either
would move the corridor rather than the buildings, and the gate below is what would notice.

## The gate

`tools/measure_south_bank_ground.py --gate` runs in `tools/check.sh` against
`tools/south_bank_ground_baseline.json`. It fails if a fit appears — on the reach or,
separately, beside the platted street — because a fit appearing is this question
re-opening and not a number to bank. It is the assertion that fires the day the terrain is
extended, the plat is re-derived or the waterline is re-traced.

**Links:** T-0134 · T-0133 · T-0071 · T-0009 · T-0059 · T-0195 · `docs/LIBERTIES.md` L79,
L164 · `data/exclusions.json` → `south_bank_warehouses_dearborn_reach`.

---

## The re-read, 2026-09-26 (T-1636)

`tools/measure_south_bank_ground.py --gate` is the assertion this note ends on: *"It is the
assertion that fires the day the terrain is extended, the plat is re-derived or the waterline
is re-traced."* On 2026-09-26 the waterline was re-traced and it fired. T-1629 moved the town
slough's mouth to Wright's own re-entrant east of State Street and **filled the mouth this
project had cut west of it** — the old channel and its two approach cuts came up about a metre
above the water and dead flat — and the count went from 0 positions at 0.30 m of relief to
**91**. That PR banked the new figures into `tools/south_bank_ground_baseline.json` without
re-reading the finding, which the baseline's own note forbids; T-1636 is the re-read.

### 1. The instrument was wrong, and it was wrong in the town's only road to the fort

`plat_corridors.corridors()` carries the **platted** grid — 33 streets off James Thompson's
plat and its additions. It is the right module for "is this in a platted street" and it was
the wrong one for the question this reading asks, because **a road that is not on the plat is
still a road.** On this reach that road is `fort_road`: South Water Street stops at the United
States Reservation, so the way from the town's east end to the fort gate was never platted,
and it runs from local (805, 4) east-north-east across exactly the ground the fill opened.

Of the 91 positions the fill appeared to open, **81 stand in the fort road's own travelled
way** — every one of them, at every relief clause, because the road runs along the flattest
line of the new ground. A reading that reports them as free would have been spent building in
the road. `measure_south_bank_ground.py` now masks the travelled way of every committed street
`plat_corridors` does not carry, and reports what the same roads' reconstructed corridors
would additionally refuse beside it rather than gating on that. The mask is the **travelled
way** (`track_width_m`) and not the corridor, because every bound in this reading is the
permissive one and the corridor of an unplatted road is an invention twice over.

### 2. The reading, after the fill and with the road in it

    the south bank from dearborn_street_drawbridge (E 699.2) east to the
    Reservation's west line (E 842.0)
    126 of 143 stations carry ANY dry ground outside a platted corridor
    the widest such strip is 26.50 m, at E 813.2 (N 0.0 to 26.0, 1.30 m of relief)
    positions the smallest F1 footprint would stand at, at any bearing:
       relief <= 0.30 m      10        (was 0 before the fill)
       relief <= 0.35 m      15        (was 0)
       relief <= 1.00 m      81        (was 6)
       no relief clause     152        (was 26)
    BESIDE THE PLATTED STREET — west of South Water's own east end (E 805.0),
    which is the frontage the plate draws:
       the widest free strip is 8.00 m, at E 804.2
       relief <= 0.30 m       0        (was 0)
       relief <= 0.35 m       0        (was 0)
       relief <= 1.00 m       0        (was 3)
       no relief clause       3        (was 3)
    REFUSED FOR STANDING IN AN UNPLATTED TRAVELLED WAY — fort_road (5.5 m):
       81 at every relief clause, because the road holds the flattest line of the
       new ground
    and of the 10/15/81/152 above, those the fort road's RECONSTRUCTED 12 m
    corridor would also refuse (reported, not gated):
       10 / 15 / 32 / 32

### 3. What holds, and it is the finding this page was written for

**The plate's own frontage is still refused, and the refusal is one clause harder.** West of
South Water Street's east end the count is zero at 0.30 m, zero at 0.35 m and — new since the
fill — **zero at a full metre**, where the first reading found three. The three positions that
used to stand on the 8 m strip at E 804 are gone: the fill raised the ground inland of them and
steepened the strip's own fall to the water from 0.86 m to 1.05 m of relief. So paragraph 1 of
§ What it says above is unchanged and paragraph 2's correction — that width was never the
problem, slope was — is now more true than it was. **The question § What is still open puts to
this project is untouched:** whether an invented building may stand on the river margin of a
platted street corridor is still undecided, and nothing on this page has decided it.

### 4. What is new, and it is east of the frontage

The ten surviving positions run **E 806.2 to E 814.2, N 8 to N 17** — the window between South
Water Street's platted corridor, which ends at E 805.0, and State Street's, which begins at
E 814.5. That is 9.5 m of town ground with the fort road through the middle of it, and § What
it says paragraph 3 already said what it is: *"ground there answers a different question from
the one the plate asks."* It still does. What changed is that the different question now has
an answer, because before the fill this ground was a channel of this reconstruction's own
making and now it is the bank Wright drew.

**One building stands on it** — `south_bank_shed_dearborn_e1`, the westernmost of the ten, a
18 × 32 ft plank freight shed between the fort road and the water with 0.273 m of relief under
it and 1.23 m of clear ground between its wall and the road's wheel line. It is graded
`reconstructed` on every line and `docs/LIBERTIES.md` L274 owns it. It is the south-bank half
of L164's four north-bank sheds, and it is placed by the same kind of rule: an offset from a
committed travelled way, at the westernmost easting two committed corridors leave free, held
to the relief clause the infill generators hold themselves to.

**Which way this is wrong if it is wrong.** Toward a building on ground whose dryness is three
hours old. The fill is a correction rather than an invention — the channel was this project's,
the bank is Wright's — but it is recent, and if it is ever undone the shed goes back under
water and must go with it. The gate below is what would say so.

### 5. The gate, restated

`tools/measure_south_bank_ground.py --gate` now holds four readings rather than three: the
reach's fits, the fits beside the platted street, **the fits standing in an unplatted travelled
way**, and the two widest strips. A change in any of them is the question re-opening. The
in-the-road count is gated because the two ways it can move are both things this page would
want to know: the fort road moved, or the ground under it did.

**Added links:** T-1636 (this re-read) · T-1629 (the fill) · `docs/LIBERTIES.md` L274 ·
`data/structures/south_bank_shed_dearborn_e1.json`.

## The road moved, 2026-09-26 (T-1637)

Section 5 above said the in-the-road count is gated because either of two things could move it:
the fort road, or the ground under it. **It was the road, three hours later, and for a reason
that had nothing to do with this page.**

`fort_road` crossed the State slough's new mouth in open water — 3.60 m of its centreline below
the water surface between local E +849.1 and E +852.7, 162 of the drawn track's 16,614 samples
wet — so `renderers/web/js/streets.js` clipped the wet panels and the town's way to the fort was
severed. Nothing says the town laid anything over it: the one sentence this project has about
crossing this drain puts a log bridge where the town's *graded street* met it, and
`slough_log_bridge` is that crossing. A second crossing was refused and the invented line moved
instead, onto State Street at the toe of that bridge's own southern approach (local E +826.84
N -24.36). Its reach across this strip is gone.

### What that does to the reading on this page

| reading | T-1636 banked | now | why |
|---|---|---|---|
| `fits` 0.30 / 0.35 / 1.00 / none | 10 / 15 / 81 / 152 | **91 / 96 / 162 / 233** | the road no longer masks anything here |
| `fits_in_an_unplatted_track` | 81 / 81 / 81 / 81 | **0 / 0 / 0 / 0** | the road is not on the reach |
| `fits_beside_the_street` | 0 / 0 / 0 / 3 | **0 / 0 / 0 / 3** | unchanged |
| widest free strip | 26.50 m at E 813.2 | **26.50 m at E 813.2** | unchanged |

**Not one square metre of ground moved.** The mask moved. And the reading this page was written
for is the third row: beside the platted street — west of South Water Street's committed east end,
which is the frontage image 3 draws warehouses on — the answer is still zero at every relief
clause. **T-0134's refusal stands, on the same figures, one clause harder than when it was
written.**

### What is genuinely re-opened, and it is filed rather than answered

The 81 positions the road held are released, and they are all EAST of the platted frontage, on
the unplatted reservation ground between E +805 and the Reservation's west line at E +842. That
is section 4's ground, not the plate's, and section 4's own conclusion — one shed, sized and
seated by rule — was reached with the road in it. Two questions follow and neither is this run's:

1. whether anything more of the plate belongs on ground whose only reason for being empty was a
   road that is no longer there;
2. whether `south_bank_shed_dearborn_e1` is re-seated or re-faced, since its northing, bearing
   and door side were read off that road's travelled way. **It has not been moved** — its easting,
   its ground and its relief test are independent of the road, and re-seating it is a change of
   geometry and a re-bake. `docs/LIBERTIES.md` L274 carries the revision.

**Added links:** T-1637 (the road's move) · `tools/measure_fort_road_way.py` (the gate that holds
the road out of the water) · `docs/LIBERTIES.md` L140.

## The shed stood on the river walk, 2026-09-27 (T-1643)

The section above filed the second of its two open questions as "whether
`south_bank_shed_dearborn_e1` is re-seated or re-faced." **It is re-seated, and the reason is not
the one that was filed.** The question was asked because the road the northing, the bearing and
the door side were read off had gone, which is a loss of re-derivability. What answering it found
is a defect: **the position that road had chosen stood across the town's own riverside plank
walk.**

### 1. What was standing on what

`river_plank_walk_crossing_footway` — the riverside walk's east end, in
`data/frontage/river_walk_frontage.json` — runs from local E +803.6 to E +815.0 at N +14.2 and is
1.83 m wide, so its boards occupy **N +13.285 to N +15.115**. The footprint T-1636 seated spanned
**N +8.164 to N +18.455** between E +805.4 and E +812.0, and took the whole width of them:

| corner | E | N |
|---|---|---|
| north-east | 810.896 | 18.455 |
| north-west | 805.442 | 17.860 |
| south-west | 806.500 | 8.164 |
| south-east | 811.954 | 8.759 |

**No dataset gate could see it, and that is half the finding.** A walk in this project is boards
laid on ground the reconstruction has already built; a building is a mesh seated on the same
ground. Nothing compared the two. `plat_corridors` carries the platted grid, this page's own
reading had learned about unplatted travelled ways for T-1636, and neither module knows what a
plank walk is.

What found it was **the published walker**, in `tools/smoke_renderer.mjs` stage 2 at the mobile
viewport: standing on the walk at E +809.4, N +14.2 and walking west, a visitor was pushed out of
the shed's compiled collision footprint east to **E +811.5** instead of reaching past E +802. The
check was red on `dev` from the moment the shed was seated, reproduced on unmodified dev at
`b6c56c8` — 87 passed, 1 failed — and it was a PR validating something else entirely (T-1275)
that read the red properly.

### 2. What the instrument now does

`tools/measure_south_bank_ground.py` masks the **committed frontage walks** exactly as it masks
the unplatted travelled ways: by the walk's own width, which is the same rectangle
`renderers/web/js/frontage.js` publishes as that walk's keep-out. Unlike a road there is nothing
else it could be — a corridor is a reservation *around* a travelled way and can be argued about,
and boards are the surface itself. `data/frontage/index.json` is read as the manifest it says it
is, so the reader reads exactly what the renderer reads.

And the gate does one thing more, because a count is not a refusal: it **refuses outright any
committed building on this reach that stands on a committed walk**, reading the sidecars the
renderer seats from, and testing both containments — a building across a walk, and a walk running
wholly inside a building. That is the ratchet on the thing that went wrong rather than on the
ground, and `--self-test` asserts it fires by putting T-1636's own seating back and requiring the
gate to catch it.

### 3. What that does to the reading on this page

| reading | T-1637 banked | now | why |
|---|---|---|---|
| `fits` 0.30 / 0.35 / 1.00 / none | 91 / 96 / 162 / 233 | **47 / 47 / 64 / 104** | the committed walks' boards are masked |
| `fits_on_a_committed_walk` | — | **44 / 49 / 98 / 129** | the positions the boards take |
| `fits_in_an_unplatted_track` | 0 / 0 / 0 / 0 | **0 / 0 / 0 / 0** | unchanged |
| `fits_beside_the_street` | 0 / 0 / 0 / 3 | **0 / 0 / 0 / 3** | unchanged |
| widest free strip | 26.50 m at E 813.2 | **26.50 m at E 813.2** | unchanged |

**Not one square metre of ground moved, again.** Nothing counted out here was ever buildable — it
was already covered in boards — and the row this page exists for is the fourth: beside the platted
street the answer is still zero at every relief clause. **T-0134's refusal stands.**

### 4. Where the shed stands now

The easting rule is untouched, because it is the one number T-1637 left checkable: the westernmost
station on the reading's own half-metre lattice, between South Water Street's platted corridor and
State Street's, at which the whole rectangle stands on free ground. Squared to the walk that is
**E +805.5** for the west wall. The northing and the bearing are now read off the walk itself —
the committed line that is still on this reach and the one line this building has to be clear of.

| what | old (T-1636, off the fort road) | new (T-1643, off the walk) |
|---|---|---|
| rotation | 173.774° (the road's bearing here) | **180.000°** (square to the walk, which runs due east) |
| north wall | N +18.455, across the boards | **N +11.285**, 2.00 m south of them |
| setback kept | 1.25 m, the north bank's 2.00 m refused by relief | **2.00 m**, the same the north bank keeps |
| relief over 252 points | 0.273 m (1.027–1.300 m) | **0.097 m** (1.189–1.286 m) |
| clear of the nearest platted corridor | under 0.5 m | 0.30 m at the north-west corner |
| the wagon door | to the fort road | **to the landward side**, away from the boards |

Two things fall out of that and both are improvements rather than trades. The **setback stops
being a concession**: off the fort road this shed could not keep the 2.00 m the four north-bank
sheds keep from North Water Street's travelled edge, because at 2.00 m its back wall fell half a
metre further down the bank and the relief reached 0.353 m, past the 0.30 m clause — so the
setback came in to 1.25 m and the trade was stated. On the terrace south of the walk the trade
does not arise, and the reach's two shed rows are now set back by the same figure. And the **door
has a made approach again**: South Water Street's platted corridor ends 0.30 m west of the west
wall, so a cart comes east out of the street's end onto the terrace and stands on the landward
side, which is the side the door is on. Loading across a 1.83 m footway is the mistake this
re-seating undoes, not one to re-make at a smaller scale.

**Nothing about the evidence moved.** The plate, the `reconstructed` grade on every value, the
1834-08-01 to 1835-12-31 bracket, the 18 × 32 ft footprint and the total working uncertainty are
what they were. What moved is three numbers that were read off a line that has gone, onto a line
that is here.

**Added links:** T-1643 (this re-seating) · T-1275 (the PR whose validation read the red) ·
`data/frontage/river_walk_frontage.json` · `docs/LIBERTIES.md` L274 and L153.
