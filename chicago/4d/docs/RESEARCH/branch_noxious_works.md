# The works behind the four documented noxious trades

**T-1709, of T-1203.** What this reading answers: the four documented packing, slaughter and
noxious-trade places on the branches each record, in their own words, that the WORKS are missing.
This is the reading that says which of those works can honestly be built, where they can stand,
and which one is refused.

It is not a page of any source. **No source is read here**, and nothing below upgrades a
confidence. Every building it justifies is graded `reconstructed`, and `docs/LIBERTIES.md` **L284**
owns the invention.

## The four plants, and what each one says is missing

| record | district | what its own note says is outside the polygon |
|---|---|---|
| `newberry_dole_slaughterhouse_south_branch` | south | "the pens, the yard and the barrelling and salting space that a packing operation needs are outside the footprint and outside this archetype, which builds a building rather than a works" |
| `miller_tannery` | north | "a tannery is its yard — bark mill, lime pits, tan vats, drying sheds, and a water supply — and none of that is in this polygon or in the model" |
| `elston_soap_candle_manufactory` | north | a shed sized for "a rendering kettle, a cooling and moulding floor and an ash leach", and nothing beside it |
| `clybourn_slaughterhouse` | north | "what is not modelled is arguably the bigger half": the killing pens, the stock yard that later gave the trade the Bull's Head name |

`data/reconstruction/1835_off_plat_ledger.json` is where the four are counted as a group:
*"no committed off-plat parcel record names a branch frontage. The four documented noxious trades
stand on the branches by their own positions, not by a parcel line, and this ledger authors no
parcel for them."* That sentence is why this band has no lot line to seat against and why the rule
below is a setback from a building instead of a corner off a plat.

## The works rule

1. **Behind the plant, away from the water.** Each plant's own bearing puts its working face on
   the water, so the ground behind it is what is left.
2. **5.20 m between walls.** The cart yard T-1640 derived from `data/yard/town_trade_goods.json` —
   1.00 m of clearance from the wall a wagon stands at, plus the 3.20 m a parked wagon needs, plus
   1.00 m from the wall opposite. The same figure separates one works building from the next, so
   the whole band is set out on one committed number.
3. **The plant's own bearing**, so the yard is square and the doors face it.
4. **Where the ground behind the plant is a platted corridor, the band runs ALONG the bank
   instead**, in the order the work runs, on a line 0.50 m clear of that corridor's edge.

## Clause 4 is the South Branch, and this is the measurement that forced it

`tools/plat_corridors.corridors()` at the reach of the Newberry & Dole plant:

| corridor | extent at this reach | the plant's own intrusion |
|---|---|---|
| `market` | local E 73.00 → E 97.00 | **1.30 m** inside its west edge |
| `randolph` | local N -265.00 → N -241.00 | **11.45 m** inside (`tools/corridor_intrusion_baseline.json` records it) |

The plant stands at local E 64.30–74.30, N -265.80 to -253.80. So behind it is Market Street and
north of it is Randolph Street, and a works building on either would repeat a breach this project
already carries and its corridor gate exists to find. **The band therefore runs south**, every
building with its east wall on local **E 72.500** — 0.50 m clear of Market's west edge — so the
three read as one row rather than three seatings, which is the idiom `south_bank_shed_dearborn_e2`
established on the south bank.

## The six seats, and the four predicates each was held to

Measured on a 25 × 25 lattice over the placed polygon (`tools/validate.world_footprint`'s own
transform: the recorded coordinate is the polygon's origin corner, `rotation_deg` clockwise from
grid north). Dry means above the committed water surface of
`data/terrain/epochs/e1834_harbor_cut`; the relief clause is the generators' own 0.30 m
(`generate_block_infill.MAX_RELIEF_M`).

| building | family | bearing | anchor (local ENU) | extent | ground | relief | corridor | nearest committed footprint |
|---|---|---|---|---|---|---|---|---|
| `newberry_dole_packing_house_south_branch` | W3 | 270 | E 72.5000 / N -277.0960 | E 63.97–72.50, N -277.10 to -271.00 | 0.442–0.698 m | 0.256 m | clear | 5.20 m (the plant) |
| `newberry_dole_salt_house_south_branch` | A4 | 270 | E 72.5000 / N -284.7344 | E 67.62–72.50, N -284.73 to -282.30 | 0.583–0.710 m | 0.127 m | clear | none within 14 m |
| `newberry_dole_stock_shed_south_branch` | A1 | 270 | E 72.5000 / N -295.4208 | E 64.58–72.50, N -295.42 to -289.93 | 0.465–0.695 m | 0.230 m | clear | none within 14 m |
| `miller_tanyard_bark_shed` | A4 | 180 | E 20.8768 / N 88.0768 | E 18.44–20.88, N 83.20–88.08 | 1.141–1.145 m | 0.004 m | clear | 2.00 m (the drying shed) |
| `miller_tanyard_drying_shed` | A5 | 180 | E 16.4384 / N 87.4672 | E 14.00–16.44, N 83.20–87.47 | 1.138–1.140 m | 0.002 m | clear | 5.20 m (the tannery) |
| `elston_ash_house` | A5 | 270 | E -3.2328 / N 187.9808 | E -7.50 to -3.23, N 187.98–190.42 | 1.116–1.121 m | 0.005 m | clear | 5.20 m (the works) |

The tanyard's two sheds stand on ONE front-wall line, local N 83.200: the drying shed's west wall
on the tannery's own east wall line (E 14.000), and the bark shed 2.00 m beyond it (E 18.438 to
E 20.877), so the pair reads as one back row.

**The bark shed was first drawn at the WEST end of that yard and had to move**, and the reason is
an instrument rather than a reading. At the west seat it stood **67.86 m** from the corridor it is
nearest — inside the empty band `FRONTAGE_REACH_M` is cut from. `tools/measure_frontage_fabric.py`
finds the body of the distance distribution continuous to 60.79 m and the next building anywhere at
74.65 m, and commits the midpoint of that 13.86 m gap (67.72 m) as the reach beyond which a
building fronts no street at all. A shed dropped into the middle of that gap does not break the
town; it breaks the instrument, by making the reach's own justification a 7.07 m band. Its
self-test caught it. **An invented building is not a reason to move a committed constant**, so the
building moved: at the east seat it stands 53.98 m out, inside the body where 388 others stand, and
the band and the reach are exactly what they were. The cost, stated: the two sheds no longer frame
the yard from its two ends; they stand as a pair, and the yard is open to the west.

## What was refused, and why

**`clybourn_slaughterhouse` gets no works.** Its own record says it is DISPLACED: the attested
site is the east bank of the North Branch south of the Bloomingdale Road, roughly 3 km
north-north-west of the forks, about 2.8 km beyond the edge of the 640 m terrain box this scene
models, and the record therefore stands at the edge of modelled ground with an error of kilometres
and says so. Six yard buildings placed 5.20 m from a building that is kilometres from its own site
would multiply that error rather than reconstruct anything, and the stock yard Andreas's plant
implies belongs on ground this scene does not have. Terrain reaching 3 km up the North Branch is
what would reopen it.

**No second cooperage on the South Branch.** The town's cooper's shop on that reach already stands
— `inf_cooperage_south_branch`, about 26 m north of the plant — so a barrel shop beside the packing
house would build the same claim twice. The packing house takes family W3 (the crosswalk's cooper,
wagon and wheelwright shop) for its visible content and not as a second cooperage.

**No pens, pits or vats.** The killing pens and the stock yard on the South Branch, and the lime
pits, tan vats and bark mill at the forks, are enclosures, pits and machinery.
`generators/archetypes/outbuilding_params.py` declines the class in as many words — *"a yard is an
enclosure — a fence line, two gateways and the ground between them — and building it out of an
outbuilding would mean calling a fence a building"* — and `docs/LIBERTIES.md` **L10** has been
carrying the same gap for the Western Hotel's wagon yard. **Adding six roofs does not discharge
it**, and each record says so on its own face.

## How the roofs are counted

All six are entered in `data/reconstruction/1835_existing_roof_reconciliation.json` as eligible
physical roofs that each **substitute one anonymous programme slot** in their own district and
family — three in the south (W3, A4, A1), three in the north (A4, A5, A5). The town's roof total
does not move for any of them; they are re-typings inside the programme's size, on the rule that an
authored anonymous slot yields to a record that names a building. The North's A5 remainder goes to
nil.

## What would replace these inventions

* Any description of the South Branch plant beyond Andreas's one sentence recording its erection
  (scan p. 1151).
* Any account of Miller and Hall's tanyard, or the Chicago Democrat's advertisements for it.
* An address for Elston & Co. in any printing of 1833–1835. The advertisement that attests the
  business gives none, which is why the ash house is the shakiest building in the band.

**Related:** `docs/LIBERTIES.md` **L284** (the invention), **L281** and **L274** (the cart yard
figure and the south-bank row), **L10** (the yard nobody models),
`docs/RESEARCH/south_bank_dearborn_ground.md`, T-1709, T-1203.
