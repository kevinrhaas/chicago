# West Water seated, and Jefferson and Des Plaines refused by the ground

**T-0445, piece 2 of 4 of T-0443. 2026-09-05. Extended by T-0768, 2026-09-12,
which carried the reach past the turn at Wolf Point and refused the rest with the
clearance — § 1.** Every number here is recomputed
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

## 2. Jefferson and Des Plaines are refused, and the refusal is a measurement

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

## What this changes in the town

One new street, on ground that had none: the block the eye expects between the
river and Canal Street — the absence T-0444's memo named as the third of the West
Division's three faults — now has its riverfront edge drawn, and the South Branch
raft bridge's west landing now lands on a street instead of on bare ground.
