# West Division anonymous infill — 1835-07-01

**Status:** research recipe only; no structure record or mesh is emitted by this parcel
**Data:** `data/reconstruction/1835_phase2_west_wolf_point_approaches.json`
**Proposed first parcel:** **55 roofs** — 44 principal/functional, 11 ancillary
**Controlling district target:** **135 roofs** in the supplied reconstruction specification

## Decision

Build the West Division outward from the already researched Wolf Point buildings, but do not
pretend that the 1834 plats are building maps. The first anonymous parcel should contain 55
roofs in five increasingly loose clusters from the Canal/Lake approach to the Desplaines edge.
It deliberately contains no generic inn and no generic institution. Those scarce West totals
must first be reconciled against the named Wolf Point taverns, hotels, and Walker meeting house
already in the dataset.

The present terrain cannot carry the parcel. Its west edge is local **E −320 m**; 35 of the 55
recommended centres lie west of E −300 m. Before those records exist, extend the common terrain,
collision, flora, water-mask, and minimap box to **E −700 m**, preserving the current north and
south bounds for this stream. The farthest recommended centre is E −668 m. The new boundary
therefore leaves roughly 30 m beyond that barn centre and about 26 m beyond its recommended
footprint, enough to show prairie rather than terminate at a wall. A separate North Division
study should decide whether N +400 m moves; this memo does not borrow that decision.

## What the evidence does and does not say

### The plat envelope is real; its occupancy is not mapped

Two 1834 cadastral witnesses control the street and lot envelope:

- John S. Wright, *Chicago, drawn by J. S. Wright according to survey* (1834), held by the
  [Norman B. Leventhal Map & Education Center](https://collections.leventhalmap.org/search/commonwealth:js9577436),
  source id `wright_1834`.
- Joshua Hathaway, *Chicago with the School Section, Wabansia, and Kinzie's Addition* (1834),
  held by the [Library of Congress](https://www.loc.gov/item/2008621683/), source id
  `hathaway_1834`.

Both sheets have been inspected at native resolution in the datum work. They show streets,
blocks, numbered lots, additions, river, and survey geometry. **They do not show buildings.**
Consequently, a roof can be aligned to the platted module but cannot be assigned to a particular
1835 lot from either map. The exact centres in the recipe are conjectural layout controls.

The project’s measured street work strengthens only that geometric claim. Eleven corridors on
the Wright/Hathaway sheets read 75.7–92.8 ft, supporting the adopted 80 ft street module; the
west-side north–south pitch is about 116.6–123.2 m. It does not convert legal lots into occupied
lots. See `docs/RESEARCH/street_module_1830.md` and `data/traces/street_control.json`.

### The West character is witnessed, but the count is reconstructed

The May 1857 *Chicago Magazine* account, written from an 1832 resident drawing and Gurdon S.
Hubbard’s recollection, describes the West Side as open prairie entirely free from timber and
places the mixed Wolf Point fabric at the forks. It reaches the dataset through source id
`chicagology_prefire273`, graded as near-primary recollection rather than a modern web article.
Andreas, *History of Chicago*, vol. 1 (1884), source id `andreas_1884_v1`, supplies later
compiled named-building and town-development testimony. These sources support an older,
river-centred, timber-built settlement surrounded by open wet prairie. They do not enumerate 135
West roofs or locate 55 unnamed ones.

The **135-roof West total**, the family bands, and the type matrix instead come from the owner’s
modern `Chicago July 1835 Building Reconstruction Specification`, source id
`owner_chicago_1835_reconstruction_spec_2026`. That document calls the total moderate,
per-instance unnamed location low-to-moderate or interpretive, and requires 45% or more of the
enlarged/platted landscape to stay sparse or open. The recipe preserves those grades.

## Why the footprint reaches farther west

The current model ends around the Jefferson-side approach. The 1834 survey geometry continues
through Clinton and Desplaines. A West Division containing 135 roofs cannot read as a district
if all anonymous roofs are compressed into the narrow strip between the fork and E −320 m; doing
so would create false river-core density and erase the specification’s loose western edge.

The proposed E −700 m boundary is not a claim that every block to that line was built. It is the
opposite: it gives the west edge enough area to show sparse lots and then open prairie. The
recommended density falls in five steps:

| Cluster | Roofs | Zone | Reading |
|---|---:|---|---|
| Canal/Lake mixed approach | 13 | B | Small shop/work frontage, domestic lots, rear service roofs |
| Canal/Randolph teamster approach | 12 | B | Loose mixed roofs around, not inside, the named Western Hotel yard |
| Jefferson/Lake residence | 12 | C | One principal roof every one to three lots |
| Clinton work fringe | 10 | C | Dwellings plus one freight shed and extensive work ground |
| Desplaines open edge | 8 | D edge | Six small dwellings, two ancillary roofs, then open wet prairie |

This is an occupied-footprint recommendation inside a larger surveyed envelope. Streets should
continue beyond the last roof; buildings should not continue merely because streets do.

## Inventory control

### First-parcel groups

| Group | First parcel | Full West target | Treatment |
|---|---:|---:|---|
| Ordinary dwellings | 34 | 75 | Dominant anonymous fabric |
| Larger/boarding houses | 2 | 6 | One H1 and one H2; named houses reconcile later |
| Stores/mixed use | 2 | 6 | One C1 and one C2 only |
| Inns/taverns | 0 | 3 | Reserved for named West hotels/taverns |
| Workshops | 5 | 8 | One each W1–W5 to establish the work ecology |
| Warehouses/freight | 1 | 2 | One F1; named freight/storage records reconcile first |
| Institutional/public | 0 | 1 | Reserved for the named meeting-house/public record |
| Barns/stables | 7 | 20 | Five A1, two A2 |
| Small outbuildings | 4 | 14 | Two A3, one A4, one A5 |
| **Total** | **55** | **135** | **40.7% of the district target** |

### Family schedule

| Family | Count | Family | Count | Family | Count |
|---|---:|---|---:|---|---:|
| D1 | 9 | D2 | 5 | D3 | 7 |
| D4 | 6 | D5 | 4 | D6 | 2 |
| D7 | 1 | H1 | 1 | H2 | 1 |
| C1 | 1 | C2 | 1 | W1 | 1 |
| W2 | 1 | W3 | 1 | W4 | 1 |
| W5 | 1 | F1 | 1 | A1 | 5 |
| A2 | 2 | A3 | 2 | A4 | 1 |
| A5 | 1 |  |  | **Total** | **55** |

The family mix consumes only part of each town-wide family schedule. It is not a new master
total. Final family reconciliation must subtract named buildings and the South/North/Fort
parcels before expanding this recipe.

## Placement method

Every data row carries a local-ENU centre, family, footprint in feet, facade rotation, density
zone, and—where ancillary—a principal yard group. The numbers are reproducible recommendations,
not recovered addresses.

1. Place clusters on dry ground beside the 1830/1834 grid, with facades within three degrees of
   its axes. The small offsets keep the old approach from looking machine-perfect without
   asserting a measured skew.
2. Keep Zone B side gaps mainly inside the specification’s 10–35 ft band. Use larger breaks
   between yard groups, not a continuous frontage.
3. In Zone C, skip one or two potential lots between many principal roofs. The centre-to-centre
   numbers encode those absences as much as the roofs.
4. At the Desplaines edge, leave gaps larger than individual lots and stop. Do not start another
   evenly populated row.
5. Give ancillary rows a `yard_group`; never scatter a privy or shed as an independent landmark.

The recipe uses `center_local_enu_m` because a centre remains understandable across future
family implementations. A generator must convert the centre to its own origin convention after
choosing the final footprint and rotation.

## Terrain, river, and wet-ground rules

The user-visible ground, collision surface, vegetation roots, and building grade must all be the
same heightfield. This West parcel must not reintroduce the hidden-flat-plane fault that the
terrain work has removed.

- **River exclusion:** reject any footprint intersecting the authoritative 1834 water mask.
  Positive height on a decorative or fallback plane is not evidence of dry ground.
- **Anonymous setback:** principal roofs stay at least 8 m from the traced bank and ancillary
  roofs 5 m away unless a named source documents a landing. These are conservative modelling
  bands, explicitly not historical measurements.
- **Swales:** the two present west-prairie swales are themselves admitted conjectural
  alignments. Extend/review them first. If a proposed roof and swale conflict, move the roof;
  do not grade the wet ground flat to save the layout.
- **Vegetation:** the West is open prairie, not woodland. Do not generate a tree belt with the
  new terrain. Riverbank sedges/reeds may occupy the shore buffer, but woody stations remain on
  land and no grass fills the open-water channel.
- **Grade:** sample the final terrain at the entire footprint, not only at its centre. Use the
  highest defensible bearing surface or a small visible period foundation treatment; never let
  uphill terrain pass through walls.

Twenty proposed centres east of E −300 m already sample as dry on the current committed
heightfield. That is only a diagnostic. The recipe stays uninstantiated as one parcel until the
western extension and its water/vegetation masks pass together.

## Named-building reconciliation before generation

Before generating any of the 55 anonymous records:

1. Inventory every existing structure that belongs to the West district as zero, one, or more
   physical roofs. Bridges, yards, fences, and multi-part compounds cannot be counted as one
   roof merely because they are one JSON record.
2. Reserve the three inn/tavern slots against the named Wolf Point Tavern, Green Tree Tavern,
   Western Hotel, and any other named candidate. The fact that four names may compete for three
   schedule slots is a reconciliation problem, not permission to increase 135.
3. Reserve the one institutional/public slot against Walker’s meeting house or other better
   evidence.
4. Check existing named workshops, freight roofs, stables, and cabins against the corresponding
   West group totals. Delete an anonymous slot wherever a named record occupies its role.
5. Spatially buffer every documented footprint and its attested yard. A recommended centre may
   move within its cluster or disappear; a documented record does not move to preserve a recipe.

## Implementation slices

1. **West terrain extension:** E −320 → E −700 m; continue one collision/visual surface, water
   mask, prairie surface, minimap, and camera bounds. Re-derive rather than hand-stretching the
   current binary field.
2. **Named-roof reconciliation:** produce the West 135 ledger with explicit substitutions and
   reserved group counts.
3. **Dry-run placement audit:** footprint-vs-water, footprint-vs-swale, footprint-vs-existing,
   pairwise overlap, street-side gaps, and at least 45% open landscape.
4. **Generate records:** only then convert recipe rows to structure records, each visibly tagged
   `recommended_anonymous` with position and footprint conjectural.
5. **Geometry:** family archetypes sample grade across the footprint; ancillary roofs inherit
   their yard relationship; all temporary massing remains labelled placeholder.

## Acceptance checks

- Exactly 55 recipe rows; family, inventory, and cluster sums reproduce the headers.
- Exactly 44 principal/functional and 11 ancillary roofs.
- No T or I anonymous family appears before named-roof reconciliation.
- No footprint overlaps water, an existing footprint/attested yard, another proposed footprint,
  or an adopted swale exclusion.
- The terrain and collision queries agree at every footprint corner and centre.
- Tree stations in the West extension are absent except where a separate documented bank/grove
  zone licenses them; no tree station is in water.
- At least 45% of the enlarged/platted landscape remains sparse/open at the whole-model level.
- The visitor popup calls each generated instance a recommended anonymous reconstruction and
  does not imply a recovered owner, address, or footprint.

## Confidence summary

| Claim | Grade | Reason |
|---|---|---|
| Street/lot envelope | Documented | Two 1834 cadastral survey witnesses |
| West district total and type mix | Moderate | Modern reconstruction specification, explicitly not a census |
| Open-prairie West character | Documented/near-primary recollection | 1857 account using an 1832 drawing and Hubbard testimony |
| Density gradient | Low-to-moderate | Specification plus relationship of named Wolf Point fabric to open plat |
| Each unnamed centre | Conjectural | No period source maps building footprints |
| Each footprint | Interpretive | Selected inside the family’s recommended dimensional band |
| E −700 model edge | Inferred implementation boundary | Clears the outer recommended roofs and preserves visible open prairie |

This is therefore a serious build recipe, not a claim to have found 55 missing buildings.
