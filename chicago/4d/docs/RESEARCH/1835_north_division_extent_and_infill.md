# North Division extent and initial anonymous infill — July 1835

**Status:** research-backed reconstruction recipe, not a building census
**Companion data:** `data/reconstruction/1835_north_division_initial_parcel.json`
**Initial parcel:** 60 recommended anonymous roofs (45 principal/functional, 15 ancillary)
**Full North Division target:** 150 roofs

## Decision

Build the first 60 anonymous North Division roofs on the ground the project already models,
between the north bank, Kinzie Street, and Michigan Street. Do **not** place the remaining 90
north roofs yet. Before that second pass, extend the terrain, collision heightfield, water mask,
North Branch banks, vegetation zones, and streets together from local N +400 to at least N +760.

This is the defensible split because the primary maps establish a substantially larger **platted**
north side but do not show buildings. The first parcel uses the best-connected river/Kinzie band
and leaves most legal frontage empty. The outer addition stays visibly speculative rather than
being mistaken for an occupied city.

## What the maps do and do not prove

1. [James Thompson's 1830 plat](https://commons.wikimedia.org/wiki/File:Thompson_plat_of_Chicago_1830.png)
   fixes the original town module and its north edge at Kinzie Street. It is a lot plat, not a roof
   inventory.
2. [John Stephen Wright's 1834 survey](https://collections.leventhalmap.org/search/commonwealth:js9577436)
   is the project's master geometric source for streets, lots, river, shore, and survey-date
   colouring. Full-resolution inspection recorded in `data/sources/wright_1834.json` found no
   individual building footprints.
3. [Joshua Hathaway's cadastral map](https://www.loc.gov/item/2008621683/) names the School
   Section, Wabansia, and Kinzie's Addition and is the appropriate 1835 extent envelope. It also
   contains lots rather than roofs.
4. The Chicago Historical Society/Newberry [Map of Chicago, 1835](https://www.encyclopedia.chicagohistory.org/pages/3298.html)
   identifies the 1830 subdivision as the area south of Kinzie Street and shows additions by
   1835. The Encyclopedia's [Subdivisions](https://www.encyclopedia.chicagohistory.org/pages/1214.html)
   entry explicitly warns, by implication, against equating early speculative subdivision with
   urban occupation: subdivisions already extended north of the original core by 1834.
5. The Chicago Public Library's [Chicago City-Wide Collection finding aid](https://www.chipublib.org/fa-chicago-city-wide-collection/)
   lists a manuscript “Profile of a Section of Kinzie's Addition” dated about 1835. It is a
   high-value next research target for grade and lot geometry, but a catalog entry alone supplies
   no building count or footprint.

The attached reconstruction specification supplies the aggregate production model: 665 roofs
town-wide and 150 in the North Division, of which 113 are principal/functional and 37 ancillary.
It characterizes the North Division as scattered development around Kinzie properties and
crossings with substantial open ground. It explicitly labels the count a reconstruction, not a
surviving census. Therefore the 60 coordinates in the companion file are conjectural production
slots constrained by real cadastral geometry, not claims that a roof stood on a recovered lot.

## Coordinate evidence and proposed borders

The local frame begins at the verified Wolf Point datum. Committed ground control provides these
useful north-side anchors:

| Control | Local E | Local N | Use |
|---|---:|---:|---|
| Wolcott (modern State) × Kinzie | +827.0 | +275.7 | Original-town north edge and core addition approach |
| Cass (modern Wabash) × Illinois | +937.6 | +456.6 | Inner Kinzie's Addition control |
| Wolcott × Ohio | +822.5 | +633.0 | Outer north control |
| Cass × Ohio | +934.6 | +634.6 | Outer north control |
| Rush × Ohio | +1045.2 | +636.4 | Outer north/east control |

The present terrain ends at N +400. That is sufficient for the initial parcel, whose northernmost
footprint edge remains below N +390, but it cuts the documented addition between Michigan and
Illinois and stops more than 230 m short of Ohio Street. The recommended completion box reaches
N +760: about 127 m beyond the Ohio control, enough to show an outer block and open prairie rather
than ending the model on a street. The existing E +1700 edge already clears Wright's north-of-
harbour shoreline at roughly E +1331 to +1365, so no further eastern extension is justified.

The west edge remains E −320 for this parcel. Extending it for Wabansia or for land north-west of
the North Branch must be coupled to a new bank trace; the present authoritative North Branch water
geometry stops around N +402. Filling north of that endpoint as dry prairie would repeat the
terrain/water error this project is correcting elsewhere.

## Initial 60-roof inventory

The parcel takes 40% of the North district target while staying below every North district group
quota. It deliberately weights ordinary dwellings and yards and avoids a South-Division-like
commercial row.

| Group | Initial | Full North target | Remaining ceiling |
|---|---:|---:|---:|
| Ordinary dwellings | 33 | 90 | 57 |
| Larger/boarding houses | 3 | 8 | 5 |
| Stores/mixed use | 3 | 4 | 1 |
| Inns/taverns | 1 | 2 | 1 |
| Workshops | 3 | 7 | 4 |
| Warehouses/freight | 1 | 1 | 0 |
| Institutional/public | 1 | 1 | 0 |
| Barns/stables | 7 | 17 | 10 |
| Small outbuildings | 8 | 20 | 12 |
| **Total** | **60** | **150** | **90** |

Family totals are controlled in the JSON recipe. Dimensions stay inside the owner's family bands;
individual selections remain conjectural. The single F1 freight shed and I2 community roof consume
the full North quota for those groups, so later North parcels must not add another unless an explicit
district substitution is approved.

## Density and placement logic

The recipe uses four interrupted clusters:

- **North Water west:** an older, loose riverbank band from Clark toward Dearborn, with small work
  premises and rear service roofs. It must preserve the named school-house and never cross the
  authoritative water mask.
- **Wolcott–Kinzie core:** the strongest anonymous north cluster because it combines a river
  approach with Wolcott and Kinzie Streets. Even here, frontage alternates between roof and open
  yard; there is no continuous street wall.
- **Kinzie–Michigan interior:** scattered houses and service yards. At least half the plausible
  frontage stays open, making Michigan Street an outer edge rather than another built commercial
  corridor.
- **Rush/east fringe:** isolated roofs west of the 1834 shore, with explicit voids around the Lake
  House construction site, the harbour approach, and the Fort Dearborn reservation.

The recipe's footprints are centered coordinates, not lot corners. Before generation, the parent
workflow must run exact polygon collision tests against all named structures and must sample the
same visible/collision terrain used by buildings and vegetation. A 25 m review buffer is specified
around named structures; this is a production guard, not a historical distance.

## Shoreline, river, Fort, and vegetation constraints

- No roof may be accepted on a water-mask cell, even if a schematic street line or named proximity
  suggests a riverfront address.
- Buildings, foundation piers, plants, and walk collision must sample one heightfield. Local pad
  grading may flatten the immediate footprint only; it may not create a second visible ground plane.
- No ordinary anonymous infill belongs in the Fort Dearborn compound or its working yards.
- Preserve open ground around the Lake House construction site; do not make a conjectural residential
  block read through a documented landmark project.
- Woody vegetation remains outside the river. Reeds and emergent plants may occupy only shallow
  bank bands derived from true shore distance, not the full river polygon.

## Confidence and substitution rule

The district count and family schedule are an **inferred production model**. Street and lot geometry
are documented on primary cadastral maps. Density gradients are inferred. Every anonymous roof's
family, coordinate, dimensions, finish, and age are conjectural until a building-specific source
upgrades them.

When a named North Division building is documented, substitute it for the nearest anonymous slot in
the same district, group, and scale class. Never add the named roof on top of the 150-roof district
target. Existing named structures remain untouched and are not silently absorbed into this parcel;
the project-wide physical-roof reconciliation must decide how many of the 150 they already occupy.

## Next research/build order

1. Reconcile existing named North Division records to physical roof counts and reserve their lots.
2. Run collision, water-mask, terrain-coverage, and family-band validation on the 60-slot recipe.
3. Generate explicitly flagged placeholder massings for review; keep per-instance provenance at
   `recommended_anonymous`.
4. ~~Trace the North Branch beyond N +400 and extend terrain/hydrology/flora/collision to
   N +760.~~ **DONE (T-1722).** The branch and both its banks are traced to local N +1079.21
   and the lake margin to N +1117.30; the modelled field carries to N +1120, so terrain and
   collision reach this line and past it. The flora did not follow the terrain and does now:
   `z06_dense_forest`'s ring was still cut to the old box walls at N +340 and E +340, so the
   whole division above Michigan Street was matching the two prairie elevation bands and
   drawing as open prairie. It is derived from the committed North Division waterline by
   `tools/measure_northern_ground.py` and gated in `tools/check.sh` — 155.11 ha, north to the
   box wall. THE HYDROLOGY IS NOT SHORT AND WAS NOT EXTENDED: Wright draws one watercourse on
   this side, the unnamed north-side slough, and ends it at Michigan Street (local N +341.7).
   That is a documented end, not a tracing window, and carrying a channel past it would be an
   invention.
5. Add Illinois, Indiana, and Ohio street corridors and extend Wolcott, Cass, and Rush only from
   their 1834 cadastral controls.
6. Design the remaining 90 North roofs after the extent is visible, maintaining large open tracts
   and the exact remaining group ceilings above.

## The Rush–Pine fringe: settled at none, and settled by the schedule (T-1757, 2026-09-29)

T-1748 and then T-1754 asked, twice over, for "the scattered better houses on the Rush–Pine
fringe" — the eastern cells of Kinzie's Addition, beyond Cass Street and out toward Pine. The
ask is answered here rather than built, because **the 665-roof programme's district deal
apportions that fringe no roofs at all.**

Read off `data/reconstruction/1835_665_roof_programme.json` § `schedule`, for the north district:

| cell | lots | state | roofs apportioned | families |
|---|---|---|---|---|
| `blk_indiana_north_wolcott` | 12 | open | 27 | 14 |
| `blk_indiana_north_cass` | 12 | open | 20 | 11 |
| `blk_indiana_north_rush` | 12 | open | **0** | none |
| `blk_illinois_north_wolcott` | 12 | open | **0** | none |
| `blk_illinois_north_rush` | 12 | open | **0** | none |
| every cell east of Rush or north of Indiana | 0 | `unsubdivided` | **0** | none |

So the whole of the district's remaining allocation — 47 roofs — stands on the two cells this
memo calls the Wolcott–Kinzie core, and the three other lotted cells and the nineteen
unsubdivided ones get none. **The fringe is not under-built; it is not scheduled.** "The open
ground left honestly open" is what the schedule already says, and the honest way to settle the
ask is to say so in the memo that governs the district rather than to invent roofs the
programme does not hold and this memo would refuse.

**This is the memo agreeing with itself.** § *What the maps do and do not prove* holds that the
primary maps show a substantially larger *platted* north side with no buildings on it, and
§ *Density and placement logic* asks that most legal frontage stay empty and the outer addition
read as visibly speculative. A fringe with zero roofs apportioned to it is that reading carried
into arithmetic. If a later source puts a house east of Cass Street, the route is a source
record and a programme re-derivation, not a recipe entry against a cell the schedule leaves at
zero.

## The trade roofs go back to Kinzie Street (T-1205, 2026-10-03)

The order book owes the North three stores, one inn or tavern and two workshops, and it owes
them because T-1480 refamilied seven of this recipe's trade roofs as dwellings when T-1445
found them standing 9 to 48 m back from any street line. The 665-roof schedule then dealt their
families to `blk_indiana_north_wolcott` and `blk_indiana_north_cass`, where the block generator
refuses them: Wolcott is graded `light` and the Addition's other streets `none`, and no store,
warehouse or workshop is built on either grade. Those two blocks also stand at the ceiling this
memo's alternation puts on them.

Kinzie Street is graded `ordinary`, and its north face had nothing on the street line from Clark
to east of Wolcott. That is the Wolcott–Kinzie core this memo names as the strongest anonymous
cluster. So recipe rows 61–66 of `1835_north_division_initial_parcel.json` stand there, on the
street line with open ground between every pair: a T1 tavern nearest the Dearborn drawbridge
approach, a W3 wagon or cooper's shop, a C4 and a C3 on the two Kinzie corners of Wolcott, a W2
joiner's shop and a second C3. All six are reconstructed (L368).

**The warehouse is still owed.** The F3 belongs on the North Water bank, the one north street
graded `light`, and no committed clause seats a warehouse on a light street. Seating it needs a
bank-landing clause or a regrade of North Water argued on its own evidence.

## The Addition's 26 dwellings come south of Michigan Street (T-1746, 2026-10-05)

The order book owed the North 26 ordinary dwellings (`structures/ordinary_dwellings/north`:
target 84, standing 58), and the 665-roof schedule had dealt all 26 to the two subdivided
cells above: 20 to `blk_indiana_north_wolcott` and 6 to `blk_indiana_north_cass`. Both stand at
the ceiling this memo's alternation puts on them, four roofs each, and the seating pass had
asked for twenty roofs there. One of the two had to give way.

**Ruled: this memo stands, and the seating gives way.** The memo is the committed reading of
the July 1835 north side; the seating is a policy deal that reads no source about those
blocks. Nor does the memo refuse the roofs themselves: its own full North target is 90
ordinary dwellings against the inventory's 84. What it refuses is spending them north of
Michigan Street, where the primary maps draw lots and no buildings.

So the 26 stand, family for family as the schedule dealt them (D2 3, D3 3, D4 7, D5 7, D6 4,
D7 2), as recipe rows 68-93 of `1835_north_division_initial_parcel.json` (`addition_surplus`)
in this memo's three inner clusters:

| where | roofs |
|---|---:|
| north face of Kinzie Street, west of Dearborn and east of Wolcott | 9 |
| south face of Kinzie, in the North Water band | 5 |
| scattered through the Kinzie-Michigan interior | 12 |

Kinzie Street between Dearborn and Wolcott is left as T-1205 dealt it, with no house between
its trade roofs, and Michigan Street stays a sparse outer edge. Each centre was found by a
deterministic search against the generator's own tests and three more, measured at the deal:
at least 14 m from every committed roof (an open yard between every pair, no street wall), at
least 25 m from every named structure, and inside the initial occupied envelope. None is a
reading of a source (L389).

With no roof left to plan on the two cells, the schedule plans none, the platted deal requests
no slot there, and the thirteen households whose slots stood on them are seated by the
off-plat deal under standing North Division roofs, with thirteen more owed North households
beside them. All 26 new roofs are occupied.
