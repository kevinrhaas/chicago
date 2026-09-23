# Phase 2 South Division — commercial core and mixed-block recipe

**Status:** proposed, not generated · **Scene date:** 1 July 1835 · **Roofs:** 84
(66 principal/functional + 18 ancillary) · **All individual slots:** recommended and
conjectural

## Decision

The next South Division slice should add visual weight where the documentary record and the
owner's production specification both put it: the river-facing commercial belt and Lake Street.
It should then lose density quickly toward Randolph and Washington. The accompanying recipe,
`data/reconstruction/1835_phase2_south_core_and_mixed_recipe.json`, therefore proposes:

| Cluster | Zone | Principal | Ancillary | Total |
|---|---|---:|---:|---:|
| South Water gap frontage | A | 16 | 0 | 16 |
| Core rear trade/cargo yards | A | 10 | 8 | 18 |
| Lake Street gap frontage | A | 12 | 0 | 12 |
| Market–Franklin mixed block | B | 9 | 3 | 12 |
| Randolph–Washington loose blocks | B–C | 19 | 7 | 26 |
| **Total** |  | **66** | **18** | **84** |

This is a parcel recipe, not an instruction to increase the current scene count immediately.
The project still needs to reconcile named records, compound records and non-roof records to
physical roof units. Only after that reconciliation can 84 anonymous slots be decremented from
the South target of 370. A newly identified building replaces a slot; it does not sit on top of
the 665-roof target.

## What the evidence can and cannot carry

### Primary geometry witnesses

- John Stephen Wright's **1834 surveyed map** supplies the street grid, block/lot subdivision,
  river and shoreline. The project georeferenced it with a 17.5 m RMS residual. [Leventhal Map &
  Education Center item](https://collections.leventhalmap.org/search/commonwealth:js9577436)
- Joshua Hathaway's **1834 Chicago plat** independently supplies the grid, lots and enlarged
  platted envelope. [Library of Congress item](https://www.loc.gov/item/2008621683/)

Both maps are first-rank geometry evidence and neither map draws buildings. Their silence is
important: a coordinate in this recipe is measured within a documented block, but it is not a
documented roof position. Exact positions are consequently `conjectural`, with the existing
roughly 20 m working horizontal uncertainty retained.

### Inventory and type synthesis

The owner-supplied *Chicago · July 1835: Building Inventory and Architectural Reconstruction
Specification* is the recipe's aggregate control. It calls for 370 South Division roofs and
describes the river commercial core as dense but not continuously attached, followed by mixed
blocks and a large sparse/open share. It supplies the family dimension bands used here. It is a
modern production synthesis, not a period enumeration, so the aggregate mix is moderate while
an individual anonymous roof remains conjectural.

Alfred T. Andreas's 1884 history is a retrospective witness, not a contemporary map. The
project's South Water dossiers preserve two useful constraints from it: a 55 ft South Water lot
width and an address expressed by counting doors. Those details support a readable run of
commercial premises and cap ordinary single-lot frontage. They do not document any new slot.
[Andreas volume 1](https://archive.org/details/historyofchicago01andr)

No building census, tax improvement roll, insurance plan or July 1835 footprint survey was
located in the supplied evidence. Every phase-two slot must therefore surface as “Recommended
reconstruction — anonymous,” with no occupant name and no claim that the exact building existed.

## Programme mix

The 84-roof slice deliberately includes 30 commercial, tavern, workshop or freight roofs against
31 ordinary dwellings. It gives the core the trading-town weight that a landmark-only scene
lacks, while the southern bands remain overwhelmingly domestic and open.

| Family group | Families | Count | Placement logic |
|---|---|---:|---|
| Ordinary dwellings | D1–D7 | 31 | Almost entirely Lake Street transition and mixed blocks; no uniform cottage carpet |
| Larger/boarding houses | H1–H3 | 4 | Lake and selected mixed frontage, never a tall row |
| Stores/mixed use | C1–C4 | 14 | South Water and Lake gaps; only two wide C4 roofs |
| Inns/taverns | T1–T2 | 2 | One better river-core inn and one neighborhood public house |
| Workshops | W1–W5 | 6 | Mostly rear working yards; W5 remains in the river trade belt |
| Freight/warehouse | F1–F4 | 8 | South Water rear cargo band; only two large F3 roofs and one open F4 shed |
| Civic/service | I3 | 1 | Anonymous adapted public-service roof south of Randolph, not a courthouse |
| Barns/stables | A1–A2 | 8 | Yard-bound ancillary roofs |
| Small outbuildings | A3–A5 | 10 | Rear-lot privies, sheds and utility roofs |

Exact family counts are machine-readable in the recipe and remain below the master family
schedule after the 48-roof first parcel:

| Families | Phase 2 count |
|---|---:|
| D1 / D2 / D3 / D4 / D5 / D6 / D7 | 3 / 3 / 6 / 7 / 5 / 4 / 3 |
| H1 / H2 / H3 | 2 / 1 / 1 |
| C1 / C2 / C3 / C4 | 3 / 3 / 6 / 2 |
| T1 / T2 | 1 / 1 |
| W1 / W2 / W3 / W4 / W5 | 1 / 2 / 1 / 1 / 1 |
| F1 / F2 / F3 / F4 | 2 / 3 / 2 / 1 |
| I3 | 1 |
| A1 / A2 / A3 / A4 / A5 | 5 / 3 / 4 / 4 / 2 |

## Coordinates and dimensional control

Every recipe coordinate is a **footprint center** in the project's local ENU metres. Add the
datum origin to recover UTM:

```text
UTM east  = 447072.7 + local_e_m
UTM north = 4637395.8 + local_n_m
```

Dimensions remain in feet in the recipe because they are sampled from period-oriented family
bands; generation must convert them once to metres. All sizes stay inside the owner's family
bands. The slot schema is compact but exact:

```text
[slot_id, local_e_m, local_n_m, family, frontage_ft, depth_ft,
 facade_bearing_deg, inventory_class]
```

South Water and Lake frontages use almost no yaw at this planning stage. The later deterministic
generator may introduce the specification's ±1.5° core variation only after collision testing.
Mixed blocks may use up to ±4°. Finished floors and every footprint corner must sample the same
visible terrain that carries the walker and vegetation; there is no authorization for a hidden
flat pad or collision plane.

## Overlap and extent review

The proposed footprint-center rectangles were tested locally with an oriented separating-axis
check against one another and against every active 1 July 1835 footprint in
`data/structures/`. One initial South Water slot crossed the Dearborn drawbridge envelope and
was moved; the checked recipe has **zero exact polygon overlaps** before setbacks, steps, porches
or uncertainty buffers are added.

That is only a screen, not proof of historical parcel ownership. Three stricter rules apply at
adoption:

1. Reserve protected named envelopes first. This includes the South Water stores and offices,
   Sauganash, Exchange, Old Bank, the churches, Tremont, Mansion House, Dole warehouse, the
   drawbridge, Public Square buildings and estray pen.
2. Preserve the Public Square and its surroundings. No phase-two north-band roof is placed from
   local E 445–595 m between Randolph and the next southern band. The recipe does not backdate a
   finished courthouse.
3. Stop at Washington Street. This slice does not use speculative southward extension to make
   its count and makes no new north or west map-border claim. The easternmost centers at E 840 m
   are transition slots near State/Fort approaches, not a declaration of dense settlement farther
   east.

The recipe also retains full vacant lot runs and open interiors. “Platted” never means “built.”
Terrain screening can delete or move a slot without replacement if wet ground, riverbank slope or
street geometry makes it implausible.

## Adoption sequence

1. Complete the existing-record roof reconciliation and calculate the true South remainder.
2. Convert recipe centers and rectangles to oriented candidate polygons; test protected
   footprints with practical buffers for porches, steps and cargo aprons.
3. Sample visible terrain at every corner. Move/reject water, steep-bank and street-track hits.
4. Bind each A-family roof to a principal yard group so ancillary roofs cannot become independent
   premises.
5. Generate structure records and simple massings with explicit recommended/placeholder flags and
   one append-only liberty covering existence, position and footprint for each adopted slot.
6. Review the 132 phase-one-plus-phase-two anonymous roofs as a whole. If the skyline reads as a
   continuous mature city, remove roofs and enlarge yards before proceeding south, west or north.

## Research that would upgrade the plan

The highest-value next evidence is parcel-specific: 1834–35 deeds mentioning improvements,
assessment or tax lists, town-lot auction books, surviving *Chicago Democrat* and *Chicago
American* advertisements, merchant account books, and construction notices. Any named result
should substitute for the nearest compatible anonymous slot. Later pictorial maps may guide a
search, but should not by themselves convert one of these positions into documented geometry.
