# What the other years teach us about rendering 1871

Repository audit: 18 November 2026. Inspected `kevinrhaas/chicago` at commit `137da5c8aef6152195d46fd569fc80c48f9ea369`, using current source data, compiled indexes and renderer code. This is an implementation inventory, not a fresh browser acceptance test. Counts below describe repository entries; they are not historic censuses or counts of figures simultaneously visible.

## The actual year inventory

The checkout contains exactly three scene files: **1812, 1835 and 1904**. All three retain `released: false` in their scene records, even though implemented scene content exists. A flag is not proof that a scene has no renderer, and a URL is not proof that a reconstruction exists. The planned **1880** door has no scene file. **1888** remains a superseded research date in the postfire terrain records; it is not a fourth implemented scene.

| Scene | Exact target date | Structure/component sidecars | People-directory records | Explicit standalone human instances |
|---|---|---:|---:|---:|
| Fort Dearborn | 14 August 1812 | 68 | 834 | 284 |
| Early town | 1 July 1835 | 687 | 3,891 | 4 |
| Prairie Avenue | 1 July 1904 | 284 | 445 | 8 |

Human-instance counts exclude separate transport actors and dynamically called residents. Directory entries include absent, uncertain and reconstructed people. The 1835 directory contains 3,584 resident entries plus 307 transient entries; neither figure is a measured street crowd. Structure entries include components, outbuildings and reconstructed forms, not just independently documented houses.

Evidence: [scene directory](https://github.com/kevinrhaas/chicago/tree/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes), [compiled sidecars](https://github.com/kevinrhaas/chicago/tree/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/sidecars), [human instances](https://github.com/kevinrhaas/chicago/tree/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/humans/instances), [year doors](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/tools/write_entry_pages.mjs).

## 1812: the land, an exact day, and people with a purpose

The first fort scene stands on `e1830_natural`: the river turns south behind a continuous sand spit, before the harbor cut. Its natural mouth is derived from source readings with disputed alternatives retained. The terrain overlay explicitly removes later harbor works, bridges and streets. The heightfield, water and ground meshes exist despite the epoch retaining `planned`, a registry convention that permits only one active epoch. The useful pattern is a dated terrain overlay with every carried, replaced and omitted element explained.

The scene separates fort components, outer buildings, domestic compounds, fenced greens, gardens and lodge grounds. It supplies its own enclosures and yard directories rather than inheriting the 1835 town. Named camera anchors let reviewers inspect the fort, gardens, riverbank and distant landscape. Its late-summer date matters for the gathering, residence and military histories; a season change can also change whether a person is alive or in the settlement.

The latest implementation is substantially ahead of the scene's old prose note. The human instance index contains 284 entries. The routines dossier describes schedules for those figures plus 520 callable residents. The day engine supports work, short conversations, play, meals, indoor periods, door calls and returning home. It gates dates and seasons, retains guard duty and avoids overlapping bodies. The transport configuration includes two 1812 wagon routes with teamsters on foot; crossing boats compensate for the absence of bridges.

For 1871, reuse the **method** of exact dates, independently scoped layers, source conflicts, doors, paths and purposeful routines. Do not reuse the natural river mouth, lodge locations, August plant state, military timetable or individual identities. A source attesting a resident does not attest their face, clothes or activity at a particular minute. The routines' exact hours, outings and rendering compression are declared liberties; the 1871 simulation needs the same separation.

Evidence: [1812 scene](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1812.json), [epochs](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/terrain/epochs.json), [1812 routines](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/docs/RESEARCH/1812-routines-3540/README.md), [human day engine](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/renderers/web/js/human-days.js).

## 1835: a settlement is more than its named buildings

The 1835 scene provides the broadest layer checklist: terrain, water, structures, flora, fauna, streets, fences and other enclosures, signs, yard goods, gardens, frontage works, wharves, boats, wells, residents, businesses, researched exclusions, vehicles, humans, horses and night lights. Its 687 structure/component entries must be understood beside the reconstruction models that supplied ordinary roofs, businesses and households. A list of famous buildings alone does not produce a legible town.

Land and buildings have different temporal speeds. The harbor cut belongs to a ground epoch; a pier, bridge or relocated building has dated phases. Only one phase may resolve for a structure at a scene date. Buildings are placed from the source model through compiled sidecars; the renderer does not make a second historical decision. The ground mesh and walker heightfield come from the same grid. This prevents a visually correct street from having a mismatched walk surface.

The flora system models habitat, extent, ground appearance, plantable areas and strata. Areal cover, stems per square metre and clumps per hectare are not interchangeable units. Bare soil is not a universal multiplier that thins every plant. Fauna distinguish visible, audible, trace-only, absent and deliberately undepicted presence. The records explicitly describe July status. Importing these lists into October 1871 would import an unsupported season and a pre-urban habitat distribution.

The people directory separates research presence, homes, work, dated occupations, reconstructed households and transients. The card can say a person is known while their location remains uncertain. Four standalone human instances and a named wagon route demonstrate a renderer, not a population census. Night-light data distinguish evidence for candle/oil lighting from invented window-hour shares, brightness and exact lantern placement. Signs, loading goods, water access, fuel, privies and stable yards explain why people use places.

For 1871, reuse this complete environmental inventory and evidence plumbing. Replace the town's scale, street fabric, population distribution, trade shares, roof forms and all placements. Specify ordinary residential, commercial and industrial building families separately from individually documented landmarks. Any density model must preserve aggregate totals as totals, label synthetic placements, and leave unresolved parcels unresolved.

Evidence: [1835 scene](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1835.json), [flora manifest](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/flora/index.json), [fauna manifest](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/fauna/index.json), [night lights](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/night_lights/1835.json), [asset contract](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/docs/GLB-CONTRACT.md).

## 1904: parcel-scale urban fabric and several kinds of evidence

Prairie Avenue is the best existing example of an urban street section. Its scene selects street grid, trees, street furniture, front yards, back yards, district context, railway, vehicles, humans and night lights. Compiled structure indexes contain 284 entries. The scene note's old statement that exactly one structure stands there is stale and must not be used as the current inventory.

The research library deliberately distinguishes named-house histories, a 1911 frontage reading, 1904 directory candidates, map evidence and a Glessner dossier. The inspected library contains 63 named building records, 138 source records, 38 map records and 73 occupancy candidates. Those are different units from the 284 compiled components. Its sheet censuses allocate front buildings, wings, rear buildings, shared coach houses and service ground, record corrections, and ask whether a 1911 feature actually existed in 1904. A later map is not automatically a map of the target year.

The shoreline model carries an 1886 western bound and a 1911 eastern bound with the intervening spread retained. The displayed 1904 line is explicitly reconstructed. Graded terrain, lots, railway embankment and lake shelf have generated heightfields and baked meshes. This is an example of acknowledging uncertainty while still producing one renderable surface; neither the later line nor the modern ground is silently promoted to target-date fact.

Street trees combine rule-based placement with picture-specific corrections. A photographed empty interval can be evidence against placing a tree. Street furniture includes gas lamps, hydrants, poles and wires, tied to street geometry. Front and service yards occupy their own layers; alleys and carriage access are functional circulation. Photo-matching separates camera fit, building geometry, enclosures and vegetation. The research should be readable at the façade, parcel and street scales.

The current directory has 445 people, including 32 marked absent and 34 uncertain. Eight standalone instances are listed; drivers and callable people follow separate paths. The shared day engine handles indoor and outdoor life. A parked Brougham follows an 1893 catalogue design while explicitly declining to claim a particular historic owner or parking event. Its design date makes that exact asset unsuitable as evidence for 1871.

For 1871, reuse the parcel census, address reconciliation, camera evidence, street-section machinery, front/rear service distinctions and collision-aware transport. Re-research the shoreline, paving, utilities, street trees, façade dates, roofs, occupants and vehicles. Do not backdate 1904 houses, later photographs' additions, 1893 carriage designs, railway geometry or the 1911 survey line.

Evidence: [1904 scene](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1904.json), [Prairie library](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/prairie_1904_v1/README.md), [shoreline states](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/terrain/shoreline_states.json), [pictured tree overrides](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/street_trees/pictured_1904.json), [parked vehicle evidence](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/transport/parked/placements.json).

## Every other Atlas year is research coverage, not a rendered scene

The pre-fire viewer accepts **1674–1871**, backed by six researched tranches: pre-1830, 1830s, 1840s, 1850s, 1860s and 1870–71. It holds 324 named/source-identifiable records, only 15 with point coordinates, and 214 flagged for review. Its map CSV currently has **15** references, while the statistics page still reports 14. A selected year filters available spans and chooses nearby dated references; it does not certify exact conditions on every day of that year.

| Reference years | What the reviewed inventory contributes | What it cannot establish alone |
|---|---|---|
| 1830 | Thompson plat: blocks, lots and planned streets | Actual building occupancy or street improvement |
| 1833 | Conley–Stelzer reconstruction | Contemporary measured 1833 fabric: it was made in 1933 |
| 1834 | Wright survey and Hathaway cadastral reference | Every later shoreline, elevation or structure |
| 1836 | Mesier cadastral map | An unchanged 1871 parcel state |
| 1839 | Harbor engineering plan | Completed works merely because they were proposed |
| 1849 | Rees–Rucker city and vicinity map | Exact earlier or later shorelines |
| 1853 | Hart cadastral wall map | 1871 façade heights and occupants |
| 1857 and 1868 | Palmatary and Ruger bird's-eye views | Surveyed footprint coordinates from perspective art |
| 1870 | Mitchell city map | Building-by-building October 1871 state |
| 1871 | Four references: city map, burnt-district map and two additional bird's-eye/view records | A single interchangeable pre-fire basemap; creation date, depicted state and fire overlay must remain distinct |

The postfire package researches all eight years independently: **1872: 89; 1873: 53; 1874: 25; 1875: 38; 1876: 28; 1877: 26; 1878: 28; 1879: 25** source-identifiable project records. These are research-year counts, not completion-year counts. Its 312 records have 952 lifecycle events, 165 predecessor/rebuild links, 70 aggregate estimates and 174 review flags in the inspected statistics. Start, completion and opening remain distinct. A named hotel or church rebuilt after the fire is not the pre-fire physical building merely because the institution's name survived.

Each annual tranche is useful as a **negative date control** for 1871: reject later constructions; link verified predecessors without importing later geometry; check whether an account describes new construction, restoration, enlargement, relocation or reopening. The 1874 fire is a separate event. Postfire material standards cannot be imposed retroactively on every 1871 building. Unnamed building-loss totals remain aggregate evidence.

Evidence: [pre-fire map inventory](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/maps/map_references.csv), [pre-fire methodology](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/docs/methodology.md), [postfire annual counts](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md), [postfire methodology](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md).

## The concrete 1871 preparation contract

1. **Fix an instant and spatial scope.** An annual slider cannot distinguish pre-fire daylight, the prior night's burned blocks and the later Great Fire. Date and time must qualify each event. The existing `e1856_grade_raise` placeholder ends on 7 October 1871 and `e1871_postfire` begins on 10 October. **8–9 October is uncovered.** That is an actual model gap, not a ready terrain epoch. Establish a pre-fire state without borrowing the Prairie Avenue 1904 surface.
2. **Build the land before placing the city.** Establish a documented horizontal and vertical datum; shoreline, harbor, riverbanks, wharves, rail embankments, street crowns and parcel levels; preserve source bounds and disagreements. Treat proposed public works separately from completed ones. Bridges need water clearance and a usable deck surface.
3. **Create a parcel and component census.** Separate front, rear, attached and shared buildings; date construction, moves, grade raising, additions, use changes and losses. For every renderable structure gather footprint, façade orientation, storeys/heights, wall system, roof form/material, openings, chimneys, signage, entrance, yard and source images. A coordinate is not a footprint; a name is not a unique building across time.
4. **Model ordinary fabric explicitly.** Use documented block samples and aggregate stock to constrain reconstruction families. Record their geographic scope, density, lots, material mix and uncertainty. Do not manufacture individually documented addresses from a citywide total.
5. **Populate evidence before bodies.** Resolve people, household membership, presence, homes, workplaces and dated roles. Distinguish identity, appearance and clothing evidence from behavior assumptions. Do not derive faces, clothing or a precise street position from demographic categories alone.
6. **Make movement depend on physical routes.** Specify streetcar rails/routes, wagon and carriage envelopes, bridge openings, wharf access, rail crossings, doors and alley service. Reuse contact, clearance, support and interaction mechanisms; qualify new 1871 vehicle designs and harness separately.
7. **Give activities places, tools and intervals.** Unloading requires a berth and cargo; a dray requires an origin and destination; washing requires water and yard space; tending horses requires a stable or hitch. Work, shopping, deliveries, household tasks, play, worship and leisure need distinct temporal evidence. Exact loops/hours are reconstruction unless observed.
8. **Research October living cover and atmosphere.** Gather canopy placement, species confidence, crop/garden state, dry/bare ground, dust, wind, water appearance and fauna behavior. July prairie and 1904 parkway rules are reusable software examples, not October 1871 facts. Daylight, gas/candle light and smoke must be date/time qualified.
9. **Preserve inspectable uncertainty.** Ship citations and locators with individual claims; separate photo provenance, rights, observation date and upload date. Preserve exclusions and alternative readings. Expose liberties on the site rather than hiding them behind realistic rendering.
10. **Review the actual delivered scene.** Use fixed anchors, photo comparisons, mobile and desktop checks, door/route traversal, ground-contact checks, failed-load diagnostics and performance budgets. Published compressed assets require their own verification. Today's audit does not claim those 1871 checks have run.

## Documentation traps found during this audit

- `docs/EPOCHS.md` still describes 1812/1904 ground as unbuilt in places; `epochs.json` and generated files establish later work.
- The 1904 scene note still says one building, but its compiled index contains 284 entries.
- The 1812 scene note still describes one soldier/no Native figures, while current instance and routine records describe the later population implementation.
- `docs/RESEARCH/transport-human-candidates.md` is an explicitly dated older audit and describes missing 1812 people and only two 1904 people; it must not be read as the current roster.
- `pre_fire_v1/docs/statistics.md` reports 14 maps; the current map CSV has 15.
- `planned`, `traced`, `active`, `released` and 'has a URL' describe different parts of the workflow. None substitutes for checking the actual data, generated artifacts and runtime.

These discrepancies are recorded here without rewriting unrelated 4D records. Future work should derive readiness from the source indexes and disclose unresolved differences.
