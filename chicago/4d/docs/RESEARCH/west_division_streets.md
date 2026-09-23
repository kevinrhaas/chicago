# West Water seated, Jefferson and Des Plaines seated after it, and the five tiers carried off the clip

**T-0445, piece 2 of 4 of T-0443. 2026-09-05. Extended by T-0768, 2026-09-12,
which carried the reach past the turn at Wolf Point and refused the rest with the
clearance — § 1. §2's refusal was ANSWERED by T-1430, 2026-09-20, once T-1416 built
the ground out to local east -705.0: both streets are drawn and the section below
says how, keeping the refusal that stood for fifteen days because it is the
derivation of the seating.** Every number here is recomputed
from committed files by `tools/measure_west_division_streets.py`, which carries
the assertions as `--self-test` and which `tools/check.sh` runs. Unlike T-0444's
memo, this one moves something: one street is seated, and §3 says why the other
two are not.

## The ask

T-0445, measured on T-0444's own reading of the plat:

> `data/streets/1835.json` holds 19 streets, of which exactly two are west of the
> South Branch — `canal` and `clinton`. The Thompson plat's West Division carries
> five north-south streets: **West Water, Canal, Clinton, Jefferson, Des
> Plaines**. Three of them are held by nothing — not a line, not a refusal, not a
> queued node.

Acceptance 1 is explicit that **absent is not an answer**: each of the three
either exists with sources and a stated `geometry_confidence`, or is refused in
writing with the reading that refuses it. The three do not get the same answer,
and what separates them is the modelled ground.

## 1. West Water is seated, off the waterline and nothing else

West Water Street is the West Division's riverfront street, and this project's
riverfront is committed data:
`data/terrain/epochs/e1834_harbor_cut/river.geojson` carries the west bank of the
South Branch as a 24-vertex traced line, from Wright 1834, graded `inferred`
there. The nine vertices from the scene's south edge to the bank's turn at Wolf
Point are its South Branch reach.

**The centreline is that bank offset one half-corridor — 12.192 m — to the
west**, so the street's *east kerb* stands on the 1834 waterline:

| local east | local north | from the bank |
|---|---|---|
| −20.21 | −404.02 | 12.192 |
| −15.68 | −359.15 | 12.192 |
| −17.32 | −322.26 | 12.293 |
| −13.08 | −302.60 | 12.192 |
| −9.29 | −253.85 | 12.192 |
| −9.58 | −205.60 | 12.228 |
| +1.10 | −134.02 | 12.192 |
| −0.08 | −117.10 | 12.192 |
| −7.92 | −106.17 | 12.192 |
| −39.48 | −86.63 | 12.192 |

The last two vertices are **T-0768's**, and they are the same derivation carried past the
turn — see below; the joint at −106.17 is where T-0445's line ended, mitred. The mitre joints
add at most 0.101 m, so the kerb reaches the waterline and does not cross it. **That placement is this line's one reconstruction, and what would
move it is stated rather than hidden:** the kerb-on-the-water reading is the
furthest east an 80 ft street on this bank can be — the same bound T-0444's swap
test rested on — and any wharf or landing strip between the kerb and the water
pushes the whole line west by its width. No source reached gives that width.

**The grade is inherited and is not better than its anchor.** The bank is
`inferred`, so the street is, and the self-test holds those two equal so a
re-grade of the bank cannot leave the street reading better than the thing it was
measured from.

### The reach past the turn — 39.55 m of it, and what stops the rest

**T-0768, 2026-09-12.** T-0445 ended the seated line at local north −104, where the traced
bank turns west into the junction pool, and left the continuation Fergus 1839 attests —
*"W. Water st north of West Lake st"* — unseated, because a bank-offset line past the turn
runs through the Wolf Point cluster. That was the right call on the evidence and it was
**one measurement short of the answer**: nobody had asked how far past the turn the line
gets *first*. It gets 39.55 m, and the town was short that frontage for no reason.

Two numbers say why it mattered. **West Lake Street's north kerb stands at local north
−97.41** at the easting of the old end, and **the old end stood at −104.20 — 6.79 m SOUTH
of it.** So the line did not merely stop short of the attested reach; it terminated *inside
the Lake Street intersection*, and the frontage the 1839 directory prints an address on had
zero length in this reconstruction.

**What is seated here.** The same derivation, unchanged — the committed west bank offset one
half-corridor west, east kerb on the 1834 waterline — carried along the bank's next segment,
the junction pool's south face, and **cut where the roadway first reaches a committed
footprint**. The cut is derived by `measure_west_division_streets.py` from the structure tree
itself, so a building that moves moves the street's end:

| | |
|---|---|
| the bank's Wolf Point segment | 51.94 m long |
| the roadway is clear for | **39.55 m** of it |
| what stops it | `james_kinzie_house` (`dwelling_1830`, `inferred`) |
| where it enters the roadway | 39.55 m along, spanning **6.77–16.99 m** west of the bank |
| the roadway itself | 0–24.384 m west of the bank |
| new centreline | **37.12 m**, from [−7.92, −106.17] to [−39.48, −86.63] |
| of which north of Lake's north kerb | **20.30 m** |

James Kinzie's house does not front the street and is not clipped by its kerb: its footprint
spans the **middle** of the roadway, 6.77 m to 16.99 m into a 24.384 m corridor. A street
cannot be drawn through it, so the line stops at its face.

Joining the two reaches mitres the vertex at the turn, which is the one committed number this
ticket moves: **[−9.34, −104.20] now reads [−7.92, −106.17]**. It was the perpendicular end of
the last segment and it is now the mitre joint between two; it still stands 12.192 m from the
bank, and the self-test holds that for every vertex as before.

### …and why no line fits past the cut — the refusal, as a measurement

Past James Kinzie's house the answer is still no, and here is the number that refuses it.
Every distance is from each committed footprint's nearest and furthest corner to the traced
bank itself — not to one straightened segment, because past the junction pool the bank turns
again and a single frame would flatter the answer.

| placement | grade | nearest corner | furthest corner |
|---|---|---|---|
| `james_kinzie_house` | inferred | **6.77 m** | 16.99 m |
| `robert_kinzie_store` | inferred | **8.71 m** | 17.90 m |
| `wolf_point_tavern` | inferred | **3.76 m** | 15.99 m |
| `wolf_point_tavern_stable` | reconstructed | 23.50 m | 34.31 m |
| `robinson_caldwell_cabins` | reconstructed | **7.01 m** | 14.67 m |
| `walker_meeting_house` | reconstructed | **5.46 m** | 15.08 m |

**Riverward of the cluster there is at most 3.76 m of clear bank, against the 24.384 m an
80 ft street needs — short by 20.62 m, and short even of the 12.192 m half-corridor.** That
is the clearance this ticket could not find, and it is the answer the ask allowed: a refusal
that names it. Five of the six placements stand *across* the roadway rather than beside it,
which is the shape of the problem — the cluster is not a row of buildings fronting a street
this reconstruction forgot to draw, it is a row of buildings standing where the street would
be.

Going **west of** the cluster is geometrically available and is refused for a different
reason: the east kerb would have to stand 34.31 m west of the water to clear the tavern's
stable, which is one and a half street widths of unplatted ground between the street and the
river, on a line the plat draws as the *riverfront* street. Nothing reached attests a water-lot
strip here — the one this project has read is Kinzie's Addition's, on the north bank of the
main stem — and inventing one to make a line fit is the thing this file exists not to do.

**What would reverse the refusal, and it is not more geometry.** The clearance above is not
evidence; it is the residue of free choices. `wolf_point_tavern`'s own committed derivation
says so in as many words — `method: not_derivable`, *"an interpolation plus a free 40 m"* —
and its cross-bank setback was measured to the **modern** west-bank line read from
OpenStreetMap, not to the committed 1834 trace this street is offset from. So what stands
between West Water Street and the river at Wolf Point is a reconstruction refusing a
reconstruction. What would settle it is a source that fixes one of the cluster to something:
a measured description in Andreas pp. 626–631, the Braunhold retrospective view read at plate
level, or an 1830s conveyance giving a Wolf Point frontage in feet. Any of those moves the
cluster off its free coordinate, and this line can then be carried or refused on evidence.

**One thing this reach does not deliver, and it should be said plainly.** The address that
attests the continuation is Murphy & Titus's *"Rat's-castle Hotel, W. Water st north of West
Lake st"* (`fergus_1839_street_faces.json`, claim `f1839_e1081`), and `wolf_point_tavern`
carries *Rat Castle* among its aliases. If the two are the same house — this file does not
assert it, because nothing reached ties the 1839 firm to the 1835 building — then the
attesting address sits at 81–92 m past the turn, and the 37.12 m seated here still stops
short of its door. The reach is real and the frontage is real; the specific hotel is not on
it.

### What attests the street, all of it already committed here

- **Fergus 1839** prints three West Water addresses: a hotel at the Randolph
  corner, *"grocery and ship stores, West Water near Randoph"*, and Murphy &
  Titus's *"Rat's-castle Hotel, W. Water st north of West Lake st"*
  (`data/research/directories/fergus_1839_street_faces.json`, source
  `fergus_chicago_directory_1839`). This is 1839 evidence recalled in 1876. It
  attests the street and its name; **it is not backdated into the street's 1835
  wear**, which is why the traffic grade here is the light one Clinton carries
  rather than Canal's.
- **`south_branch_raft_bridge`**, committed since 2026-08-11, places the 1833
  crossing *"between Lake and Randolph Streets, its west landing on West Water
  Street … below Wolf Point"*, and its note has the war-dance procession coming
  south along West Water Street. The seated line runs under that landing: at
  local north −178, where the bridge stands, the street's east kerb is at east
  +6.87 and the bridge's committed position is (+6.9, −178.1).

### Nothing survives on the line, and the negative is recorded

An Overpass query for every named highway in the box 41.8825/−87.6395 to
41.8862/−87.6368 — which contains the whole seated reach — run **2026-09-05**,
returned 18 names: the cross streets (West Lake, West Randolph, West Washington),
Wacker Drive and its lower decks and service drives *on the east bank*, two
bikeways, four alley-scale places, and the Riverwalk. **No through street runs on
the west bank of the South Branch.** So `name_2026` on this record does not name
one.

That is also why one committed sentence had to be corrected rather than repeated.
`south_branch_raft_bridge`'s `symbolic_location` glossed the street as *"West
Water Street (now Canal Street)"*. **That gloss cannot be right for this line.**
The committed `canal` is fitted to modern Canal Street's own surviving
intersections (T-0446 records the OSM nodes), and it stands 131–159 m west of the
seated West Water over the reach the two share — 152.09 m at the bridge's own
northing — about one plat module, which is exactly how the plat draws them: as two
separate streets. It was filed as a ticket rather than fixed in passing.

**WITHDRAWN 2026-09-12, T-0770.** The gloss is gone from the record's prose, and
tracing it before withdrawing it is what made the withdrawal easy: it is not a
secondary-source *shorthand* in the vague sense, it is one identifiable sentence
in `chicagology_lastwardance` — *"south along West Water street (now Canal
street)"* — whose own source record had already ruled that the 1910 Tribune's
parentheses are "the newspaper locating the crossing for its readers, not the
witness, and no placement here uses it." One had been used. The measurement above
and that ruling agree, so the gloss is withdrawn rather than restated: there is
nothing for it to be restated as. `docs/RESEARCH/south_branch_raft_bridge.md`
§ 3a carries the trace and the per-station table.

## 2. Jefferson and Des Plaines were refused by the ground, and are seated now

Both survive on the ground, and their surviving control is *already committed to
this repository*: `fulton`'s note carries the four OpenStreetMap intersections
T-0446 fitted that tier to, of which two are the streets in question.

The modelled ground's west edge is **local east −320.0 m**
(`data/terrain/epochs/e1834_harbor_cut/heightfield.json`, `box_local_enu_m.e`).

| street | surviving control | past the ground's edge |
|---|---|---|
| `jefferson` | east −401.04 (OSM node 262247424) | **81.0 m** |
| `des_plaines` | east −524.88 (OSM node 258966841) | **204.9 m** |

Both lie west of the edge **over their whole length**, not partly. A street drawn
there would hang off the end of the terrain, and this project already refuses a
platted *block* for exactly that reason — `tools/measure_southern_ground.py`
fails on "committed platted block(s) stand off the modelled ground". The same
rule applies to a street, and it is applied.

**What would reverse the refusal is one thing and it is already a known parcel:**
extending the terrain box west. That is the same extension that holds 35 of the
West Division recipe's 55 roofs (ROADMAP K15, admitted at `docs/LIBERTIES.md`
L90 — *"their centres lie west of local E −300 m and the committed ground stops
at E −320 m"*). When the box moves, both lines are seatable from control that is
already in this file, with no new research.


### The seating — T-1430, 2026-09-20

The box moved. `tools/measure_west_of_box.mjs` (T-1415) derived the wall the held
slots need at **local east −705.0 m**, and T-1416 regenerated the heightfield,
collision surface and water mask out to it. That is the one thing §2 said would
reverse the refusal, and nothing else about either street changed: **no new source
was read to place these lines.**

| street | control (already in `fulton`'s note) | inside the wall by |
|---|---|---|
| `jefferson` | east −401.04, north +13.11 (OSM node 262247424) | **304.0 m** |
| `des_plaines` | east −524.88, north +13.72 (OSM node 258966841) | **180.1 m** |

**Position from control, bearing from Clinton, and the two are held apart because
they are held differently.** Each committed path passes through its own surviving
intersection — 0.4 mm and 0.0 mm off it — and each carries the committed `clinton`
line's own east-per-north, −0.02395833. One intersection fixes a *point*, not a
*direction*, so the direction is inherited from the neighbouring north-south street
of the same plat, fitted to the same modern control family. `geometry_confidence`
is **`inferred`** for that inheritance and not because the street is doubtful: the
Thompson plat draws it, which under T-0713 is the sheet's own claim that it ran
here. **What would raise it to `attested` is a second surviving intersection on the
line**, which would fit the bearing from control the way Fulton's four do for its
tier.

**The reach is inherited too.** Both paths span local north −400.0 to +80.0, which
is Clinton's own committed extent. A line whose direction is borrowed from Clinton
should not claim more ground than Clinton does; the plat rules both streets further
north and south, and whatever extends Clinton extends these.

**The ground, measured and not assumed.** Sampled at 25 stations 20.0 m apart along
each committed path, the heightfield reads **1.305–1.325 m** (Jefferson) and
**1.290–1.325 m** (Des Plaines) above the 1835 water surface, and **not one station
is at or below it**. That is the test the refusal was written against, taken on the
lines as drawn.

**What is drawn is a corridor, not a road.** `track_width_m` is 0, `opened` and
`worn` are false, the surface is `unworn_prairie` — the School Section grid's
reading, carried here for the same reasons: nothing committed fronts either line,
nothing reached attests traffic or wear on them, and the West Division beyond Canal
Street was open prairie in 1835. What would change that is a building seated on one
or a source giving it traffic; the 35 placements `tools/generate_west_infill.py`
still holds for want of ground are the nearest candidates, and they are T-1431's.

**One disagreement this does not settle.** South of Madison the School Section's own
grid carries `jefferson_school_section` at east −379.98 and
`des_plaines_school_section` at −506.45, both due north–south. Carried to Madison's
northing the West Division lines would stand 8.3 m west of the first and 19.2 m east
of the second. Two surveys, two records, and no line is bent to join them — which is
how this file has always held the School Section's streets.

**The eighteen numeral crops did not move, and that is deliberate.**
`tools/read_west_division_numerals.py` cuts blocks 8–13, 22–27 and 46–51 from
`clinton` stepped one and two modules west, because when those numerals were READ no
Jefferson or Des Plaines line existed. Those crops are citations of a reading already
taken; re-cutting them from the seated lines would re-read eighteen numerals to no
purpose. The step's own corroboration — it lands 8.70 m and 8.22 m from the two
surviving intersections — is unchanged by the seating, and now reads as an agreement
between two instruments rather than as the licence for one.

## 3. Acceptance 2: nothing else moves, and here is the measurement that says so

Acceptance 2 makes the additions and any correction of a shifted grid one
re-derivation. **This ticket makes no correction, and the reason is that the
finding it would act on has been overtaken by a better instrument.**

T-0444 found `canal` "20.75 m too far west" and `clinton` "6.72 m too far east".
Both figures are the residual of an arithmetic grid anchored on the bank and
stepped at a **458 ft** module derived from an inferred 180 ft lot depth and the
owner's two-lots-across block count. T-0446 then measured the West Division's
east-west tier band on **surviving intersection control** and got 405 ft — the
same figure as the committed `canal → clinton` gap that T-0444 called 90 ft
short — and stated plainly that nothing committed here can choose between the two
readings.

The line seated in §1 is a **third measurement of the same module**, and it is
the first one taken between two lines fitted to *different* instruments: the
traced 1834 bank and modern intersection control.

| probe (local north) | `west_water` | `canal` | gap |
|---|---|---|---|
| −400 | −19.80 | −150.80 | 131.00 m = 429.8 ft |
| −300 | −12.88 | −153.84 | 140.96 m = 462.5 ft |
| −250 | −9.31 | −155.36 | 146.05 m = 479.2 ft |
| −178 | −5.46 | −157.55 | 152.09 m = 499.0 ft |
| −120 | +0.12 | −159.32 | 159.44 m = 523.1 ft |

> **Mean 145.91 m = 478.7 ft, against the plat's 458 ft module — 20.7 ft over.
> Over the same five probes `canal → clinton` measures 124.73 m = 409.2 ft, 48.8
> ft under.**

So the riverfront module is on the plat's side of the argument and the
`canal → clinton` module is not. That does not settle T-0446's open question and
this memo does not pretend it does — the gap here *widens* northward, from 429.8
ft at the scene's south edge to 523.1 ft at Lake, because `canal` and the bank
are not parallel, so a mean over it is a coarser instrument than either of the
two before it. What it does is **move the anomaly**: the number that is out of
family is the `canal → clinton` gap, not the module.

Moving `canal` 20.75 m east on the strength of the 458 ft module — the correction
acceptance 2 contemplates — would therefore be acting on the weaker of two
readings the project has explicitly refused to choose between, and would move
every building, lot, frontage and street-face adoption seated between the two
west lines. **Nothing is moved here.** What would settle it is stated instead: a
reading of the Thompson plat sheet's own West Division lot dimensions and block
lot-counts, which the owner's 2026-09-03 ruling puts within reach at
`chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` and which T-0444's
acceptance 1 already asks for.

## 4. The five east-west tiers came off the clip, and Fulton's own control was waiting there

**T-1443, 2026-09-20, piece 1 of 2 of T-1431 out of T-1417.** §2 above answered the
refusal that had kept `jefferson` and `des_plaines` off the map. The same ground answers
a second one, and this one was written into a committed record rather than into a memo.
`fulton`'s note said it:

> WHY THE LINE STILL STOPS AT EAST -320 like `kinzie`, `lake`, `randolph` and
> `washington`, when the control runs 200 m further west: the west clip is this
> reconstruction's own extent, not a statement that the street ended there, and moving it
> would move five streets rather than one.

Both halves of that sentence have expired. T-1416 built the modelled field out to local
east -705, so the extent that did the clipping is gone; and moving five streets is exactly
what this section does, in one generator, with one gate. Every number below is recomputed
from committed files by `tools/carry_west_tiers_west.py`, which `tools/check.sh` runs as
`--check`.

### Where each line stops, and what it crosses

Each tier stops where it meets the committed `des_plaines` centreline §2 seated — the
westernmost platted street of the West Division. Not at the field's west wall: that is a
fact about this reconstruction's extent and would be the same mistake one ticket later.
The plat's own west boundary line is not committed to this repository, so the lines stop
on the last committed control rather than on an inferred edge. `carroll` stops at
`fulton`'s west end instead, because an interpolation may claim no more ground than the
pair it lies between — §2's rule about borrowed lines, turned through ninety degrees.

| street | old west end | new west end | carried (m) | kink at the retained vertex (deg) | lowest ground on the reach (m) |
|---|---|---|---|---|---|
| `carroll` | [-320.0, 137.85] | [-524.877, 139.16] | 204.88 | 0.0013 | 1.22 |
| `fulton` | [-320.0, 12.59] | [-524.877, 13.588] | 204.88 | 0.0000 | 1.23 |
| `lake` | [-320.0, -107.1] | [-522.025, -105.461] | 202.03 | 0.0029 | 1.05 |
| `randolph` | [-320.0, -249.9] | [-518.603, -248.288] | 198.61 | 0.0164 | 1.30 |
| `washington` | [-320.0, -385.2] | [-515.361, -383.615] | 195.37 | 0.0000 | 1.30 |

1006 m of street, and not one metre of it off the modelled box or under water: every
reach is sampled against the committed heightfield and the lowest sample on any of them
stands 1.05 m above the summer-1835
water surface.

### The bearing each line is carried on, which is the one judgement here

`lake`, `randolph` and `washington` are three lines of the Thompson plat's own east-west
grid and they share ONE bearing exactly — **-0.008115**, to six decimals, which is the
number `tools/measure_no_build_ground.plat_bearing` asserts and the tract layer stands on.
They are carried on it. The alternative — each line's own westernmost *segment* — is worse
evidence dressed as precision: that segment's west end **was the clip itself**, an artefact
of this reconstruction's extent rather than a surveyed point, and on `randolph` it leans
3.5% off the grid the same street carries at its other end. Carried that way the three
would arrive at Des Plaines not parallel, in a plat that draws them parallel.

`fulton` is not on that grid and is not forced onto it: its own four-point fit runs at a
different slope, a committed disagreement (T-0446) and not this ticket's to reconcile.

`plat_bearing` itself had to move with this, and the move is the point: it read the chord
from each line's first vertex to its last, which was the Original Town's reach only for as
long as the lines stopped at the town's west line. It now drops vertices west of -320
before taking the chord. A derived reach may not redefine the grid it was derived from.

### What corroborates it: control the record already carried

`fulton`'s note lists four surviving OpenStreetMap intersections, read on 2026-09-04 and
fitted at RMS 0.35 m. **Two of the four stand WEST of the old clip.** The carry is
derived from the committed bearing and reads neither of them:

| node | local east | line stands | side of the clip |
|---|---|---|---|
| Canal (258020617) | -162.00 | -0.350 m | east |
| Clinton (258966840) | -282.18 | +0.576 m | east |
| **Jefferson (262247424)** | -401.04 | **-0.125 m** | **west** |
| **Des Plaines (258966841)** | -524.88 | **-0.132 m** | **west** |

The carried line passes 0.132 m from the worse of the two, inside the
0.35 m RMS of the four-point fit itself and tighter than either eastern residual.
The clip had been standing in front of 200 m of street that the record's own control
already held.

`carroll`'s bracket is re-measured at the new west end on the same rule as T-0446: one
Fulton-to-Lake module north of Fulton is 132.624, one module
south of Kinzie is 145.696, and the midpoint
139.16 sits between them — a half-bracket of **6.536 m**, still
the largest uncertainty of any West Division street. West of the clip the Kinzie term is
`kinzie_west`, T-1085's separate record, because that is the line that exists there.

### Nothing east of the clip moves

Each line KEEPS its old west vertex — the reach is carried from it, not fitted through it —
so every committed vertex from local east -320 eastward stands exactly where it stood. No
platted lot line moves, no corridor is re-cut, and the corridor-intrusion count is
untouched. What the carry does add is a change of direction at that retained vertex, and
it is measured rather than rounded away: the largest is `randolph`'s
0.0164 deg, and `fulton` and `washington` have none at all.

### What it moves in the town

`tools/measure_north_of_box.mjs` re-reads the drawn street on the grid at
15,944.12 m against 14,938.34 m — the 1006 m added, all of it on modelled ground,
which is the same answer the heightfield sampling gives from the other side.

The town wagons re-deal, because their lattice is anchored at each street's west end and
stepped by the street's traffic class: 25 further stands are offered on the new reaches
and **every one of them is refused off-town**, more than 16 m from any committed footprint —
"past that the street is running out into the prairie", which is `generate_yard_goods.py`'s
own words and exactly right here. What changes inside the town is the lattice's phase:
66 wagons become 65 and the enumerated refusals fall from 43 to 40. No wagon stands west of
the old clip.

## What §1 changed in the town

One new street, on ground that had none: the block the eye expects between the
river and Canal Street — the absence T-0444's memo named as the third of the West
Division's three faults — now has its riverfront edge drawn, and the South Branch
raft bridge's west landing now lands on a street instead of on bare ground.
