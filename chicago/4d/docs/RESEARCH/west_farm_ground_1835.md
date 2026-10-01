# The West farm ground — what the owed farm households could stand on (T-1793)

DERIVED figures: `data/reconstruction/1835_west_farm_ground.json`, rebuilt by
`tools/measure_west_farm_ground_1835.py --build` and gated by `--check` in `tools/check.sh`.
First piece of T-1784; T-1794 deals on it. Nothing here raises a roof or seats a household.

## The question

The off-plat deal (`1835_off_plat_seats.json`, T-1614) owes **44 households** to the band
`west/farms_and_country_seats`, all handed to T-1615 for the same reason: the twelve off-plat
D1/A2 roofs the West has are already taken by labourers, whom the placement policy ranks first,
and no off-plat parcel may raise a new one. T-1784 asked for them to be dealt as a D1 cabin and A2
barn recipe on the extended ground. Before raising anything, four things had to be known.

## What the measurement found

**1. Who they are.** All 44 are `policy_only`. Each is a name from the post office's letter lists
with no address. Its division was dealt from the order book's household target, and its class from
the town model's employment distribution: the `Agriculture` column, which the 1840 county schedule
fills with the whole country round. No source puts any of them on any ground.

**2. Where a farm could stand.** The West is read on a 10 m lattice west of the committed river
(the forks, both branches, and the South Branch below Twelfth Street), inside the box
(E −705 … , N −3800 … 1120). The ground is then cut two ways. One cut is the Trustees' bounds of
7 November 1833, resolved by `measure_corporation_limits.py`; its West line is Jefferson Street.
The other is the survey tracts. A tract laid out in lots or blocks before the scene date counts as
**subdivided**. That covers the Original Town's plat, Wabansia (1831) and the School Section, which
was sold by the block in 1833. The register holds 336 block rows for the School Section, at
1.87–6.75 acres each.

| West ground (m²) | inside the limits | outside | outside, in forties | subdivided |
|---|---:|---:|---:|---|
| below the School Section (south of Twelfth) | 0 | 1,608,100 | 9.93 | no |
| School Section | 148,400 | 1,172,600 | 7.24 | yes |
| Wabansia | 62,100 | 201,900 | 1.25 | yes |
| Canal Section 9 remainder (the Des Plaines edge) | 10,400 | 165,500 | 1.02 | no |
| Original Town plat west of Jefferson | 276,200 | 84,000 | 0.52 | yes |
| on no tract | 0 | 3,500 | 0.02 | no |

The farm ground is the West ground outside the limits and off every subdivided tract:
**177.7 ha, 10.98 forties.** Most of it lies below Twelfth Street, past the committed ground
control. That ground is "beyond the committed control" in the parent's own words.

**3. How big a farm is.** One forty, 40 acres or 16.19 ha. Two records name that holding on or near
this ground: Edmond Roberts' W2NW of section 9 (register ls0054, read at 40.00 acres, entered
1830) and the 40 acres advertised in the *Chicago American* of 27 June 1835 (c003). Using a forty
as a farmstead's holding is an *inferred* reading, so every count below is a **ceiling**. Roberts'
forty is the only farm-size register row that reaches the West ground outside the limits, and only
5,500 m² of it is unsubdivided.

**4. What the programme carries.** A farmstead is two roofs. The West's target is 135, with 49
left to build. Of those, **0 are D1 and 3 are A2.** The 22 remaining dwellings belong to T-1783
and the 7 barns to T-1212. A farmstead for every owed household would need 88 roofs.

## The ceilings T-1794 deals within

- **At most 10 farmsteads** fit on the modelled ground at one per forty. At least **34 of the 44**
  have to be stated as farming beyond the box.
- **13 roofs already stand on the farm ground**: the Des Plaines edge cluster
  (`recon_1835_west_039` … `_055`). Seven are D1 cabins and two are A2 barns, which makes **2 cabin-and-barn pairs**
  that are a farmstead's two roofs already. A farm household seated in one draws on no programme
  headroom. The seating order gives them to labourers today, and that is the lever.
- **0 new farmsteads** fit the programme as it stands. A new D1 cabin means re-familying part of
  T-1783's cell or reading the West target again. Neither is this file's to decide.

## Not done here

No roof is raised and no household is seated or moved. The School Section's town blocks are not
counted as farmland. If T-1794 wants them, they add at most 7.24 forties: the box would hold 18
farmsteads, still fewer than 44.
