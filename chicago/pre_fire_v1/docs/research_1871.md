# Chicago immediately before the fire — 1871 reconstruction research

Research snapshot: 2026-11-18

Prepare Chicago for October 8, 1871 before the evening outbreak, with the exact local hour still open. An October 7 intact-city baseline is a separate state: Sunday already includes damage from the Saturday Night Fire.

This document is generated from `data/research_1871.json` by `tools/build_research.py`.

## Reading the evidence

Documented means the cited source supports the stated claim; it does not certify measured geometry, primary-source status, or exact presence on the scene date. Inferred marks a reasoned reconstruction. Open marks an unresolved question. Source access is recorded separately: read, catalog only, or lead. Rendering implications are proposals unless independently attested. No new image assets or geometry are claimed by this dossier.

## Other years: what the existing project teaches

Implementation audit: published/main snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369, inspected November 18, 2026. Development may be ahead; counts describe this audited snapshot, not the latest dev build or a historical census.

### 1812 — Implemented scene; released flag remains false

Date: 1812-08-14

First Fort Dearborn on natural ground before the harbor cut. Current indexes contain 68 structure/component entries, 834 people records and 284 standalone human instances; these are dataset units, not simultaneous visible counts.

- Use an exact day and independent terrain state. The pre-cut mouth, sand spit and natural banks have their own derived geometry; remove later streets, piers and bridges explicitly.
- Keep buildings, outer compounds, gardens, enclosures, yard goods and crossings separately inspectable. Camera anchors let reviewers test the same places repeatedly.
- Current routines support 284 drawn and 520 callable residents, with dates, seasons, duties, work, conversations, play, meals and indoor periods. These schedules and rendering limits are declared liberties.
- Keep identity, presence, appearance and action separate. A named person is not evidence for their exact face, outfit or minute-by-minute behavior.
- Reuse the day engine, door access, spacing and route systems for 1871; research new households, occupations, clothes and routes. Do not carry 1812 ground or individual placements forward.
- The scene note mentioning only one soldier is stale. Current human indexes and the routines dossier establish the later implementation.

- [1812 scene](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1812.json)
- [Structure index](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/sidecars/1812/index.json)
- [Current routines](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/docs/RESEARCH/1812-routines-3540/README.md)
- [Human day engine](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/renderers/web/js/human-days.js)

### 1835 — Implemented scene; released flag remains false

Date: 1835-07-01

The broadest existing settlement layer inventory: 687 structure/component sidecars and 3,891 people-directory entries, including 307 transients. Four standalone instances and a wagon route demonstrate actors; the directory is not a street crowd.

- Research all layers: land, water, ordinary buildings, streets, fences, signs, goods, gardens, frontage, wharves, boats, wells, businesses, people, horses and lights.
- Use slow terrain epochs and faster dated structure phases. Resolve exactly one phase on the target date and compile that historical decision into the sidecar.
- Preserve natural habitat, planted ground, bare soil and strata separately. Areal cover and stems per square metre are different units.
- Fauna distinguish seen, heard, trace-only, absent and undepicted presence. July species/activity records cannot automatically represent October 1871.
- People records distinguish home, work, presence, dated roles, reconstructed households and transients. Apply new 1871 sources rather than carrying old trade shares and names.
- Use aggregate totals to constrain explicitly reconstructed ordinary fabric; never turn them into individually documented addresses.
- Night-light records separate evidence for candles/oil from reconstructed brightness, window-hour shares and exact placements.

- [1835 scene](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1835.json)
- [Structure index](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/sidecars/1835/index.json)
- [Flora manifest](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/flora/index.json)
- [Fauna manifest](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/fauna/index.json)
- [Asset and evidence contract](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/docs/GLB-CONTRACT.md)

### 1904 — Implemented Prairie Avenue scene; released flag remains false

Date: 1904-07-01

A parcel-scale urban model with 284 structure/component sidecars, 445 directory records and eight standalone human instances. The separate research library has 63 named building records, 138 sources, 38 maps and 73 occupancy candidates.

- Distinguish source map date from scene date: 1911 frontage readings are explicitly adjudicated for 1904, and the 1886/1911 shoreline bounds remain visible.
- Count front buildings, wings, rear buildings, shared coach houses and service parcels separately. Name continuity does not prove unchanged fabric.
- Use street sections, curbs, walks, alleys, front and rear yards, railways, trees, lamps, hydrants, poles and wires as dated urban infrastructure.
- Combine rule-based tree placement with picture-specific overrides; an empty photographed interval can rule a tree out.
- Use independent camera and façade evidence, preserving uncertainty in ground and shoreline. A reconstructed line is not a surveyed line.
- The parked Brougham follows an 1893 catalogue while its owner and exact stop remain reconstructed. That exact design is too late to substantiate an 1871 vehicle.
- Reuse urban rendering machinery; re-research 1871 parcels, materials, occupants, utilities, rails and plants.
- The scene note saying only one building is stale; current compiled indexes contain 284 components.

- [1904 scene](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1904.json)
- [Structure index](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/sidecars/1904/index.json)
- [Prairie research library](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/prairie_1904_v1/README.md)
- [Shoreline bounds](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/terrain/shoreline_states.json)
- [Vehicle evidence](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/transport/parked/placements.json)

### 1880 / 1888 — Planned door / superseded research date; no separate implemented scene

Date: No single implemented scene date

The 1880 URL is deliberately generated as a pending year. The 1888 representative date survives in research records after the Prairie Avenue target moved to 1904.

- Do not count a navigable year URL as an existing reconstruction.
- Do not treat a historical representative date as evidence that geometry exists for it.
- For 1871, the grade-raise epoch is a placeholder ending 7 October; the postfire epoch starts 10 October. An 8 October pre-fire instant needs an explicit terrain/date decision.
- Current 1904 ground must not be backdated to fill that gap.

- [Year-door generator](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/tools/write_entry_pages.mjs)
- [Epoch registry](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/terrain/epochs.json)

### 1674–1871 Atlas — Research viewer coverage, not annual 3D reconstructions

Date: No single implemented scene date

Six pre-fire research tranches supply 324 named/source-identifiable records. Only 15 have point coordinates; 214 are flagged for review. The current map inventory has 15 references, although the older statistics page says 14.

- The year slider filters known spans and nearby reference maps; it does not certify every selected day.
- 1830 plat: planned parcels and streets. The 1833 Conley–Stelzer map is a 1933 reconstruction. The 1834 Wright/Hathaway maps, 1836 Mesier map, 1839 harbor plan, 1849 Rees–Rucker map and 1853 Hart map have distinct purposes and dates.
- 1857 Palmatary and 1868 Ruger views help with appearance and massing, not measured footprint coordinates.
- 1870 Mitchell and four 1871 references support the near-fire study, but pre-fire views, city plans and burnt-district evidence must remain separate.
- Preserve named structures separately from unnamed stock totals, and unknown fire fate as unknown.
- Resolve addresses and georeference sources before claiming parcel placement.

- [Pre-fire buildings](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/data/buildings.csv)
- [Map inventory](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/maps/map_references.csv)
- [Evidence methodology](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/docs/methodology.md)

### 1872 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

89 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

### 1873 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

53 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

### 1874 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

25 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.
- The 1874 fire is a separate event; do not combine its losses or footprint with the 1871 disaster.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

### 1875 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

38 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

### 1876 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

28 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

### 1877 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

26 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

### 1878 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

28 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

### 1879 — Independently researched postfire tranche; no scene file

Date: No single implemented scene date

25 named/source-identifiable project records assigned to this research year within the 312-record postfire package. These are not annual building-stock or completion counts.

- Keep research-year assignment distinct from start, completion and opening dates. A directory appearance or reopening is not automatically new construction.
- Use this tranche to exclude later construction from the 1871 scene and to identify explicit predecessor/rebuild relationships.
- Do not merge buildings by surviving institutional names or import later elevations and materials into the pre-fire building.

- [Annual statistics](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/statistics.md)
- [Annual method](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/docs/methodology.md)
- [Project records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/postfire_1870s_v1/data/buildings.csv)

## Evidence and rendering requirements

### Choose the hour before choosing the scenery

`method-1871-date-contract` · scene design · **open**

Working target: Sunday, October 8, 1871, before the evening outbreak. Local hour remains undecided. An October 7 daytime intact-city baseline is a separate state. The existing terrain epochs end the grade-raise interval on October 7 and begin the postfire interval on October 10; October 8–9 is not covered.

**Applies to:** Preparation for a separately dated 1871 scene

**Rendering implication:** Create an explicit prefire day/time contract and a separate Saturday Night Fire overlay. Preserve source dates and historical local-time assumptions before calculating sunlight. Do not relabel the existing summer scenes as October.

**Limits:** This dossier chooses a research window, not a released scene or an exact eyewitness moment. No 1871 terrain has been built by this work.

**Next step:** Set scene extent, hour, weather scenario and event cutoff; resolve the epoch gap before adding a scene file.

**Sources:**

- [Terrain epoch intervals](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/terrain/epochs.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/terrain/epochs.json.
- [Example exact-date scene](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1835.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/scenes/1835.json.

### Audit every year without confusing index coverage with a city census

`method-1871-coverage` · scene design · **documented**

The prefire index holds 324 source-identifiable records, 214 marked for review, 15 with point coordinates and 8 with linked media in the inspected snapshot. The generated annual coverage CSV audits every year 1674–1871 using the existing viewer rule. In 1871 that rule yields 269 records; it includes same-year losses and does not establish October 8 occupancy.

**Applies to:** Preparation for a separately dated 1871 scene

**Rendering implication:** Use the year explorer to find candidates, then apply day-level entity phases. Measure named structures, inferred ordinary stock, components, people and visible instances separately.

**Limits:** An inclusive demolition-year filter intentionally keeps 1871 fire losses visible. Unknown demolition dates are not positive survival evidence. Coordinates locate a vicinity, not measured corners. These counts are version-specific.

**Next step:** Resolve exact-day presence on selected pilot blocks and retain anonymous stock totals separately.

**Sources:**

- [Year-level active-record logic](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/viewer/app.js) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/pre_fire_v1/viewer/app.js.
- [Compiled source inventory](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/viewer/data.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/pre_fire_v1/viewer/data.json.

### A renderable building needs more than a name and an address

`method-1871-building-contract` · scene design · **inferred**

The existing model separates identity, dated phases, position, footprint, architectural form, and source confidence; compiled sidecars carry those decisions to renderers.

**Applies to:** Preparation for a separately dated 1871 scene

**Rendering implication:** Record footprint polygon and units; number of floors and heights; wall/roof material; roof pitch and parapets; windows, doors and thresholds; stoops, rear additions, sheds, fences, privies, stables, signs and service circulation. Cite each attribute, not just the whole building.

**Limits:** A floor count or address cannot supply exact dimensions, color, rear geometry, tenant sign or interior layout. Procedural repetition remains a declared liberty.

**Next step:** Complete one ordinary mixed-use block as well as a landmark. Keep absent dimensions null and add a reasoned reconstruction only when necessary.

**Sources:**

- [Identity, phases and sidecar architecture](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/docs/PLAN.md) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/docs/PLAN.md.
- [Atlas provenance and incomplete-building limitations](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/pre_fire_v1/docs/methodology.md) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/pre_fire_v1/docs/methodology.md.

### Resolve streets, yards and walking surfaces together

`method-1871-street-section` · land · **inferred**

The earlier scenes show why streets, enclosures, front yards, rear yards, terrain and transport paths need to agree. The 1871 city requires new evidence for raised grades, paving, drainage, rails, curbs, sidewalks and basement relationships.

**Applies to:** Preparation for a separately dated 1871 scene

**Rendering implication:** Author street cross-sections with width, datum, carriageway, track envelope, sidewalk, gutter, threshold and rear access. Keep render mesh, collision surface and navigation heightfield on the same source geometry.

**Limits:** Modern pavement, postfire grades and the 1835 natural surface are not safe defaults. Citywide street-material totals cannot locate a particular pavement.

**Next step:** Choose survey control points and record residuals; resolve at least one grade transition and one bridge/tunnel approach before wider procedural expansion.

**Sources:**

- [1904 urban street layers](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1904.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/scenes/1904.json.
- [1835 ground and street layers](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1835.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/scenes/1835.json.

### Research the small infrastructure that makes streets believable

`method-1871-utility-inventory` · structures · **open**

The existing urban scene separates street furniture and night lights. For 1871, gas lamps, hydrants, water access, sewers, telegraph poles and wires, fire-alarm boxes, station apparatus and refuse systems remain a distinct acquisition task.

**Applies to:** Preparation for a separately dated 1871 scene

**Rendering implication:** Link utilities to dated network plans and street edges. Model lamp construction and light source separately from invented brightness and operating hours; resolve apparatus type, station and horse/crew requirements before animating an emergency response.

**Limits:** This is an open research inventory, not evidence that each listed device stood on every street. Electric street lighting, telephone distribution, later fire engines and postfire hydrant layouts cannot be imported by analogy.

**Next step:** Extract Board of Public Works and Fire Department 1870–71 reports, gas-company records, street photographs and equipment inventories with page-level locators.

**Sources:**

- [Evidence and liberties in night-light records](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/night_lights/1835.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/night_lights/1835.json.
- [Separate street-furniture and light layers](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1904.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/scenes/1904.json.

### Track animals, traces and sound separately from visible placement

`method-1871-fauna-senses` · plants · **inferred**

The 1835 fauna system separates visible, audible, trace-only, absent and deliberately undepicted presence; its ecology is dated to a different season and landscape.

**Applies to:** Preparation for a separately dated 1871 scene

**Rendering implication:** For 1871 distinguish workhorses, household livestock, market animals, dogs, birds and pests by local evidence. Treat hoof sounds, bells, steam, dock activity, odors, manure and dust as independently justified sensory layers.

**Limits:** A regional species list does not establish a nest, flock, pest infestation, sound level or odor at a chosen address. Do not carry July abundance or pristine marsh habitat into an October industrial district.

**Next step:** Join animal and sensory observations to dated photographs, newspapers, household records and sanitary reports; mark sound design and population compression as liberties.

**Sources:**

- [Fauna evidence categories](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/fauna/index.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/fauna/index.json.
- [Habitat and seasonal flora inventory](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/flora/index.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/flora/index.json.

### Build three complete place–person–prop sequences before scaling

`method-1871-pilot-sequences` · actions · **inferred**

A full city reconstruction needs compatible places, actors, props, paths and schedules. The existing scenes offer machinery for routines and transport, but their identities, clothing, vehicle designs and calendar states belong to their own dates.

**Applies to:** Preparation for a separately dated 1871 scene

**Rendering implication:** Pilot a retail street with deliveries, a river crossing with a vessel and waiting road users, and a residential/service yard with household work. For each, record source, local time window, actor role, prop, origin/destination, door, collision envelope and confidence.

**Limits:** These pilots are authoring proposals, not observed October 8 episodes. Sunday business hours, named-person presence, appearance and exact motions remain separate claims.

**Next step:** Accept each pilot only after geometry, evidence cards, animation constraints and mobile performance agree; then expand the covered blocks.

**Sources:**

- [Shared daily-routine engine](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/renderers/web/js/human-days.js) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/renderers/web/js/human-days.js.
- [Dated actors and transport context](https://github.com/kevinrhaas/chicago/blob/137da5c8aef6152195d46fd569fc80c48f9ea369/chicago/4d/data/scenes/1812.json) — Repository snapshot 137da5c8aef6152195d46fd569fc80c48f9ea369. Project implementation inspected for this audit; access: read. Locator: chicago/4d/data/scenes/1812.json.

### October 8 is a distinct terrain state

`land-1871-temporal-baseline` · land · **documented**

An October 8 pre-outbreak scene already follows the destructive Saturday Night Fire. A fully intact summer city and Sunday afternoon cannot share the same damage mask.

**Applies to:** 1871-10-08 before the evening Great Fire outbreak

**Rendering implication:** Give the scene an explicit date and local hour; support separate intact-city and October 8 damaged-area states.

**Limits:** The proposed baseline time is an editorial choice. Sources establish earlier damage, not every surviving object or cleanup operation.

**Next step:** Choose the local scene hour and acquire a map of the October 7–8 burn perimeter.

**Sources:**

- [A Fiery Prelude](https://greatchicagofire.org/timeline/item/1871-10-07/) — 2011 site copyright. museum/university historical synthesis; access: read. Locator: Saturday, October 7, 1871 timeline entry.
- [Saturday Night Fire](https://greatchicagofire.org/landmarks/saturday-night-fire/) — 2011 site copyright. museum/university historical synthesis; access: read. Locator: Main two paragraphs and Andreas illustration caption.

### Saturday Night Fire damage polygon

`land-1871-saturday-fire` · land · **documented**

The museum timeline bounds the earlier fire area by the South Branch, Van Buren, Clinton, and Adams streets. It burned from late October 7 into Sunday afternoon.

**Applies to:** Near West Side, October 8 afternoon onward

**Rendering implication:** Create a separate earlier-burn layer for damaged industrial lots and streets; limited cleanup or residual smoke may be reconstructed only with explicit uncertainty.

**Limits:** The broad bounds do not establish parcel-level damage. Modern locator 209 South Canal Street must not be used as an 1871 facade address.

**Next step:** Inspect the Andreas fire illustration and period insurance sheets; record parcel survival separately.

**Sources:**

- [A Fiery Prelude](https://greatchicagofire.org/timeline/item/1871-10-07/) — 2011 site copyright. museum/university historical synthesis; access: read. Locator: Saturday, October 7, 1871 timeline entry.
- [Saturday Night Fire](https://greatchicagofire.org/landmarks/saturday-night-fire/) — 2011 site copyright. museum/university historical synthesis; access: read. Locator: Main two paragraphs and Andreas illustration caption.

### Use the NWS drought reconstruction

`weather-1871-drought` · weather · **documented**

NWS gives 3.55 inches of precipitation for July 7–October 8, 0.74 inches during September, and no precipitation September 29–October 8.

**Applies to:** Chicago, days before the October 8 outbreak

**Rendering implication:** Use dry exposed surfaces and drought-affected vegetation; do not add recent-rain puddles without local evidence.

**Limits:** These totals do not determine water content of every yard, wetland, lagoon, or irrigated garden.

**Next step:** Replace conflicting shorthand drought claims with these explicit date intervals and attribution.

**Sources:**

- [NWS Chicago: 150th Anniversary of the Great Chicago Fire of 1871](https://www.weather.gov/lot/1871fire) — 2021-10-08. institutional reconstruction using historical weather observations; access: read. Locator: Weather Prior to the Fire; Weather During the Fire—October 8th; Overview observation-record paragraph.

### Southwest wind, with estimated peaks

`weather-1871-wind` · weather · **documented**

NWS reports October 8 regional southwest wind peaks estimated around 35–45 mph, including Chicago.

**Applies to:** October 8, 1871; regional to city scale

**Rendering implication:** Wind may drive foliage, loose litter, clothes, flags, and ordinary smoke toward the northeast; represent gust variation.

**Limits:** Estimated peak range is not constant street-level speed, and no exact chosen-hour wind measurement is established.

**Next step:** Make the animation parameter a bounded reconstruction with sheltering by buildings.

**Sources:**

- [NWS Chicago: 150th Anniversary of the Great Chicago Fire of 1871](https://www.weather.gov/lot/1871fire) — 2021-10-08. institutional reconstruction using historical weather observations; access: read. Locator: Weather Prior to the Fire; Weather During the Fire—October 8th; Overview observation-record paragraph.

### Warm October conditions, without false precision

`weather-1871-temperature` · weather · **documented**

NWS describes low-to-middle-80s Fahrenheit highs across much of northern Illinois on October 8. Its 35–40 percent afternoon/evening humidity estimate comes from Aurora.

**Applies to:** October 8 afternoon and evening regional context

**Rendering implication:** Avoid cold-weather breath, frost, or universally heavy winter clothing; preserve variation in individual attire.

**Limits:** Neither regional high temperature nor Aurora humidity is a measured downtown Chicago value at the chosen scene hour.

**Next step:** Label any numeric environmental controls as regional estimates or render assumptions.

**Sources:**

- [NWS Chicago: 150th Anniversary of the Great Chicago Fire of 1871](https://www.weather.gov/lot/1871fire) — 2021-10-08. institutional reconstruction using historical weather observations; access: read. Locator: Weather Prior to the Fire; Weather During the Fire—October 8th; Overview observation-record paragraph.

### Weather records have a survival limit

`weather-1871-record-loss` · sources · **documented**

The Chicago observation station had to be abandoned and its records were lost in the fire; NWS reconstructed conditions using surviving observer material.

**Applies to:** Weather-source provenance for 1871

**Rendering implication:** Retain uncertainty for exact temperature, visibility, cloud, and gust timing; do not present a synthetic hourly dashboard as an original observation.

**Limits:** Regional smoke reports do not establish a measured haze opacity for a particular Chicago view.

**Next step:** Attach provenance to each chosen weather parameter and keep October 9 rain/cold-front conditions out of the October 8 daytime scene.

**Sources:**

- [NWS Chicago: 150th Anniversary of the Great Chicago Fire of 1871](https://www.weather.gov/lot/1871fire) — 2021-10-08. institutional reconstruction using historical weather observations; access: read. Locator: Weather Prior to the Fire; Weather During the Fire—October 8th; Overview observation-record paragraph.

### Lake Park includes water behind the railroad

`land-1871-lake-park-lagoon` · land · **documented**

CPL describes the 1852 Illinois Central trestle approximately 300 feet east of Michigan Avenue, a farther-out breakwater, and a lagoon extending south to 12th Street.

**Applies to:** Downtown lakefront south of Randolph, before postfire filling

**Rendering implication:** Model separate inland ground, lagoon, railroad support, breakwater, and open-lake polygons.

**Limits:** The approximate offset is not a uniform measured 1871 geometry. Modern Grant Park's broad land extent is unsuitable.

**Next step:** Trace a period shoreline and railroad map, then compare it with dated photographs.

**Sources:**

- [Chicago Public Library: History of Grant Park, 1830–1871](https://www.chipublib.org/blogs/post/history-of-grant-park-1830-1871/) — 2014-11-03. library historical synthesis with period illustrations; access: read. Locator: Final paragraphs beginning The State of Illinois owned the lakebed; 1865 train and 1868 map captions.

### Railroad depot fill north of Randolph

`land-1871-depot-fill` · land · **documented**

CPL distinguishes the lagoon to the south from railroad-created land and freight/passenger depots north of Randolph.

**Applies to:** Illinois Central lakefront depot district

**Rendering implication:** Use a separate depot-fill polygon and working rail zone; do not extend the southern lagoon continuously through the depot grounds.

**Limits:** Footprints, tracks, quay edges, and shoreline position require map-level inspection.

**Next step:** Acquire a prefire depot plan and dated exterior views.

**Sources:**

- [Chicago Public Library: History of Grant Park, 1830–1871](https://www.chipublib.org/blogs/post/history-of-grant-park-1830-1871/) — 2014-11-03. library historical synthesis with period illustrations; access: read. Locator: Final paragraphs beginning The State of Illinois owned the lakebed; 1865 train and 1868 map captions.

### An earlier river reversal preceded 1900

`land-1871-river-regime` · land · **documented**

IDNR describes Bridgeport pumping and 1867–1871 canal deepening that established gravity flow from the lake toward Lockport, with a reported 160–550 cubic feet per second range.

**Applies to:** Main river, South Branch, and I&M Canal context in 1871

**Rendering implication:** Treat river reaches separately; do not force all pre-1900 flow toward Lake Michigan.

**Limits:** The range is not an October 8 measurement and does not establish every reach's current. Drought, wind, and low lake levels complicate inference.

**Next step:** Verify the completion chronology and seek engineering observations for late summer/autumn 1871.

**Sources:**

- [IDNR: History of Flood Control & Drainage in Northeastern Illinois](https://dnr.illinois.gov/waterresources/historyoffloodcontroldrainageinnortheasternillinois.html) — undated page. state water-resources historical synthesis by Arlan Juhl; access: read. Locator: Opening historical section; Bridgeport pumps and 1867–1871 canal-deepening paragraphs.

### Verify the precise July canal opening

`land-1871-river-opening-lead` · sources · **open**

A Google Books search excerpt of the Board of Public Works report identifies July 15, 1871 for opening the temporary Bridgeport dam.

**Applies to:** 1871 canal chronology

**Rendering implication:** Potential exact epoch boundary, pending inspection.

**Limits:** The volume identity, page image, and context were not inspected; the exact day is a lead rather than an adopted attested date.

**Next step:** Open the report title page and printed page 17, record publication date and passage, and distinguish any later commentary.

**Sources:**

- [Annual Report of the Board of Public Works to the Common Council](https://books.google.com/books/about/Annual_Report_of_the_Board_of_Public_Wor.html?id=QgsAAAAAMAAJ) — volume identity and date require scan confirmation. primary-report discovery lead; access: lead. Locator: Search excerpt for page 17, opening the temporary dam at Bridgeport.

### Street and building levels need block-level evidence

`land-1871-raised-grades` · land · **open**

Archive and encyclopedia search excerpts describe raised streets, owner-controlled building raising, and surviving below-grade structures; the Archives identifies new grading requirements in 1855–1856.

**Applies to:** Built-up Chicago before 1871

**Rendering implication:** Research stairs, retaining edges, exposed basements, yard depressions, and sidewalk transitions rather than applying one citywide elevation increment.

**Limits:** Direct source retrieval failed in this pass; no exact block elevation or universal lift height is established.

**Next step:** Inspect archived pages and municipal grade profiles, then tie elevations to a stated vertical datum.

**Sources:**

- [Encyclopedia of Chicago: Street Grades, Raising](https://www.encyclopedia.chicagohistory.org/pages/1202.html) — 2005 encyclopedia. scholarly encyclopedia; direct open timed out; access: lead. Locator: Search excerpt on owner-controlled building raising.
- [Illinois State Archives: Estimate for Street Construction](https://www.ilsos.gov/departments/archives/teaching-packages/early-chicago/doc32.html) — document and teaching-page dates require inspection. state archive teaching page; direct open returned 403; access: lead. Locator: Search excerpt on grading requirements in 1855–1856.
- [Chicago Public Library: Chicago Sewers Collection](https://www.chipublib.org/fa-chicago-sewers-collection/) — undated finding aid. archival collection guide; direct open returned bot verification; access: lead. Locator: Search excerpt on Chesbrough's grade proposal and river dredgings.

### Wooden streets are not interchangeable with plank walks

`land-1871-wood-pavements` · land · **documented**

The Library of Congress account reports more than 50 miles of wooden street paving and wooden sidewalks.

**Applies to:** Citywide street-material context before the fire

**Rendering implication:** Keep wooden block pavement, plank sidewalks, unpaved ground, and locally evidenced stone paving as separate material classes.

**Limits:** Citywide mileage does not locate each surface or establish block dimensions. Do not texture all streets as long wooden planks.

**Next step:** Extract street-by-street paving from municipal reports and photographs, recording repairs and mixed surfaces.

**Sources:**

- [Library of Congress: The City Which Would Not Be Cowed](https://blogs.loc.gov/maps/2021/10/the-city-which-would-not-be-cowed-the-great-chicago-fire-of-1871/) — 2021-10. library historical synthesis; access: read. Locator: Discussion of wooden streets and sidewalks.

### Lincoln Park and uncleared cemetery coexist

`landscape-1871-cemetery` · landscape · **documented**

Northwestern's archival research shows that older cemetery grounds were not comprehensively cleared in 1871; subsequent 1874 condemnation and 1872 potter's-field disinterments demonstrate continuing burial parcels.

**Applies to:** Lincoln Park and former City Cemetery, October 1871

**Rendering implication:** Separate improved park, surviving cemetery, partially cleared parcels, and road/shore works.

**Limits:** The research pages have conflicting removal-date details and one damaged sentence; exact lot conditions and monument density remain unresolved.

**Next step:** Inspect original plats, commissioners' resolutions, and dated cemetery photographs before placing graves or buildings.

**Sources:**

- [Northwestern Hidden Truths: The Chicago Fire](https://hiddentruths.northwestern.edu/lincoln_park/chicago_fire.html) — 2008 site copyright. archival research by Pamela Bannos, linking/reproducing original records; access: read. Locator: Paragraphs on the old cemetery, potter's field, and 1871 commissioners' report.
- [Northwestern Hidden Truths: The Condemnations](https://hiddentruths.northwestern.edu/lincoln_park/condemnations.html) — 2008 site copyright. archival research by Pamela Bannos, linking/reproducing original records; access: read. Locator: April 1871 report; April 28, 1874 condemnation; September 1872 disinterment paragraphs.

### Cattle and browsing along the developing drive

`actions-1871-lincoln-cattle` · plants · **documented**

Bryan's 1899 commissioners' history, transcribed by Chicagology, reports an April 1871 expense for watching cows and cattle using the new drive while returning from northern grazing grounds.

**Applies to:** Lincoln Park and lakeshore-drive vicinity in 1871

**Rendering implication:** Cattle driving and localized browsing are supported activity types; animal paths can affect vegetation near the drive.

**Limits:** This is retrospective compilation, not a ledger inspected here. A cattle procession at a precise October 8 time is not attested.

**Next step:** Locate the cited expense entry and route; represent any chosen occurrence as inferred.

**Sources:**

- [Chicagology: Lincoln Park](https://chicagology.com/parksystem/lincolnpark/) — 1899 history transcribed on modern page; other excerpts separately dated. retrospective commissioners' compilation in modern transcription; access: read. Locator: Bryan commissioners' history: April 1871 cows, shore works, later maintenance and police passages.

### Do not borrow later Lincoln Park features

`landscape-1871-lincoln-exclusions` · landscape · **documented**

The same historical compilation dates park police to 1872, maintenance arrangements to 1873, and reported flower/plant spending to 1874; its gallery mixes much later maps and views.

**Applies to:** Lincoln Park reconstruction source selection

**Rendering implication:** Keep later uniformed park police, documented later flowerbeds, monuments, conservatory-era scenery, and later shoreline works out of the 1871 layer unless independently dated earlier.

**Limits:** First recorded spending does not prove absence of every flower before 1874.

**Next step:** Assign each image and feature its own depicted date instead of inheriting the page's broad title.

**Sources:**

- [Chicagology: Lincoln Park](https://chicagology.com/parksystem/lincolnpark/) — 1899 history transcribed on modern page; other excerpts separately dated. retrospective commissioners' compilation in modern transcription; access: read. Locator: Bryan commissioners' history: April 1871 cows, shore works, later maintenance and police passages.

### South Park begins as sparsely settled ground

`landscape-1871-south-park-existing` · landscape · **documented**

The March 1871 report describes the park tract beyond city limits, about six miles from the business center, in largely uncultivated and sparsely inhabited surroundings; the thousand-acre site contained no more than about a dozen small dwellings.

**Applies to:** South Park site in March 1871; continuity to October requires checking

**Rendering implication:** Preserve rural openness and avoid extending downtown density into the southern park study area.

**Limits:** The report is seven months before the fire and does not establish a complete October inventory.

**Next step:** Check construction progress and property acquisitions between March and October.

**Sources:**

- [Olmsted, Vaux & Co.: Report Accompanying Plan for Laying Out the South Park](https://rotunda.upress.virginia.edu/founders/default.xqy?keys=OLMS-print-02-01-02-0008) — 1871-03. primary landscape report in scholarly digital edition; access: read. Locator: Printed pp. 206–207, 211–213, 228–229; descriptions of existing site distinguished from proposals.

### Existing groves and wet soils, not finished park planting

`plants-1871-south-park-condition` · plants · **documented**

Olmsted and Vaux describe sizable but often struggling trees, wet/cold soils, and lake-wind exposure. They say about one-third of the Lower Division lay below high-water lake level.

**Applies to:** South Park's existing landscape, March 1871

**Rendering implication:** Use distinct groves, low wet ground, and coastal sandy areas; varying tree vigor is supported, but species and exact condition maps need evidence.

**Limits:** The report's high-water comparison does not establish October inundation, and no parcel-specific species list was found.

**Next step:** Inspect survey contours and vegetation descriptions before assigning water depth, species, or density.

**Sources:**

- [Olmsted, Vaux & Co.: Report Accompanying Plan for Laying Out the South Park](https://rotunda.upress.virginia.edu/founders/default.xqy?keys=OLMS-print-02-01-02-0008) — 1871-03. primary landscape report in scholarly digital edition; access: read. Locator: Printed pp. 206–207, 211–213, 228–229; descriptions of existing site distinguished from proposals.

### The 1871 park drawing is a proposal

`landscape-1871-south-park-proposal` · landscape · **documented**

The Olmsted–Vaux report presents proposed lagoons, avenues, boating connections, lawns, structures, and activities; the LOC account confirms that fire delayed construction.

**Applies to:** South Park plan and 1871 reconstruction

**Rendering implication:** Tag proposed features separately from existing land. Use the plan to guide research, not as completed terrain.

**Limits:** A feature's presence on the drawing does not prove construction. Exact implemented works need progress records.

**Next step:** Create an as-built versus proposed feature checklist; use South Park as the period label and modern Washington/Jackson names only for orientation.

**Sources:**

- [Olmsted, Vaux & Co.: Report Accompanying Plan for Laying Out the South Park](https://rotunda.upress.virginia.edu/founders/default.xqy?keys=OLMS-print-02-01-02-0008) — 1871-03. primary landscape report in scholarly digital edition; access: read. Locator: Printed pp. 206–207, 211–213, 228–229; descriptions of existing site distinguished from proposals.
- [Library of Congress: Chicago's South Park by Fredrick Law Olmsted](https://blogs.loc.gov/maps/2022/05/olmsted-bicentennial/) — 2022-05-05. library collection commentary; access: read. Locator: 1871 plan identification and construction-delay discussion.
- [National Park Service: Washington Park](https://www.nps.gov/places/washington-park.htm) — undated page. institutional history; search excerpt only; access: lead. Locator: Search excerpt identifying 1871 proposal, delayed construction, and 1881 naming.

### Vegetation needs habitat evidence before species precision

`plants-1871-distribution-gaps` · plants · **open**

Verified sources establish broad land use, wetness, disturbance, drought, cemetery retention, and tree condition, but not a citywide 1871 species or planting-density inventory.

**Applies to:** Street trees, yards, gardens, cemeteries, industrial lots, parks, and outskirts

**Rendering implication:** Separate street/front-yard trees, gardens, cemetery vegetation, improved park, disturbed banks, rural groves, and sandy/wet habitats; keep species, height, diameter, density, pruning, and leaf color unfilled until supported.

**Limits:** Modern inventories cannot be backdated. A photograph may attest tree presence and silhouette without proving species.

**Next step:** Acquire dated photographs, nursery records, household accounts, and park planting ledgers; label procedural scatter as reconstruction.

**Sources:**

- [Olmsted, Vaux & Co.: Report Accompanying Plan for Laying Out the South Park](https://rotunda.upress.virginia.edu/founders/default.xqy?keys=OLMS-print-02-01-02-0008) — 1871-03. primary landscape report in scholarly digital edition; access: read. Locator: Printed pp. 206–207, 211–213, 228–229; descriptions of existing site distinguished from proposals.
- [Northwestern Hidden Truths: The Chicago Fire](https://hiddentruths.northwestern.edu/lincoln_park/chicago_fire.html) — 2008 site copyright. archival research by Pamela Bannos, linking/reproducing original records; access: read. Locator: Paragraphs on the old cemetery, potter's field, and 1871 commissioners' report.
- [NWS Chicago: 150th Anniversary of the Great Chicago Fire of 1871](https://www.weather.gov/lot/1871fire) — 2021-10-08. institutional reconstruction using historical weather observations; access: read. Locator: Weather Prior to the Fire; Weather During the Fire—October 8th; Overview observation-record paragraph.

### Map publication date and depicted date differ

`sources-1871-map-control` · sources · **documented**

Rumsey catalog 4220.001 identifies a Blanchard publication of 1869 with an inset titled 1868, scale 1:25,344. Chicago's university catalog also lists 1863 and 1868 maps separately from postfire 1871 maps.

**Applies to:** Map acquisition and georeferencing

**Rendering implication:** Retain publication and depicted dates; use maps for networks and boundaries only after image inspection, and distinguish planned streets or parks from completed ones.

**Limits:** Catalog metadata was read, not map geometry. The digital-image rights statement needs review before redistribution.

**Next step:** Obtain scans, inspect marginalia and revisions, select control points, and record georeferencing residuals.

**Sources:**

- [David Rumsey: Guide Map of Chicago, Blanchard, 1869](https://www.davidrumsey.com/maps1877.html) — 1869 publication; inset title dated 1868. period-map catalog; scan not geometrically inspected; access: catalog_only. Locator: Catalog 4220.001; full title, publication description, scale and rights notice.
- [University of Chicago: Before and After the Fire](https://www.lib.uchicago.edu/e/collections/maps/chifire/home.html) — catalog covers 1860s–1880s. institutional map catalog; images not inspected; access: catalog_only. Locator: Map inventory rows for Flower/Van Vechten 1863, Shober 1868, and 1871 burned-district maps.

### Acquire genuinely prefire parcel sheets

`sources-1871-insurance-atlases` · sources · **open**

Newberry's guide search result identifies Chicago History Museum fire-insurance holdings from 1869 onward; many readily available digital Chicago series are later.

**Applies to:** Building footprints, yards, alleys, materials, and parcel evidence

**Rendering implication:** Do not import a later Sanborn or Rascher sheet as 1871 geometry merely because its title says Chicago.

**Limits:** The collection guide was inspected in the structures research pass; exact 1869 sheet coverage, legend and revision state were not inspected. Holdings dates do not establish a usable prefire sheet for every block.

**Next step:** Locate and inspect the prefire sheets, record edition and pasted revisions, and compare individual parcels against directories and photos.

**Sources:**

- [Newberry Library: Fire Insurance Maps](https://www.newberry.org/collection/research-guide/fire-insurance-maps) — undated guide. institutional collection-discovery lead; access: read. Locator: Search excerpt describing Chicago History Museum holdings from 1869 onward.
- [Chicago History Museum: Maps research guide](https://libguides.chicagohistory.org/research/maps) — undated guide. institutional collection-discovery lead; access: lead. Locator: Fire-insurance-map and Sanborn holdings section discovered in search.

### Court House and City Hall: the enlarged pre-fire building

`structure-1871-courthouse` · structures · **documented**

The 1853 combined Court House and City Hall occupied the block bounded by Randolph, Clark, Washington and LaSalle, with landscaped grounds around its relatively small footprint. By the fire it had a third floor, cupola, east and west wings, a new clock and a bronze alarm bell. Earlier images do not show every alteration.

**Applies to:** 1871-10-08 before the Great Fire

**Rendering implication:** Build the enlarged 1871 massing, landscaped square, boundary fence, entrances and raised relationship between street grade and basement. Use the Lovejoy & Foster 1871 view to check the wings against the earlier lithograph.

**Limits:** Museum interpretation identifies building phases; dimensions and exact landscape placement remain unmeasured. The 1885 and 1911 courthouses are different buildings.

**Next step:** Inspect ichi-64281 and ichi-62080 side by side; extract wings, roof profile, clock, openings, fence and paths into separately sourced attributes.

**Sources:**

- [Chicago History Museum / Northwestern: Court House](https://greatchicagofire.org/landmarks/court-house/) — Museum interpretation, 2011; referenced images 1866–67 and 1871. museum interpretation with identified primary images; access: read. Locator: Captions 'Courthouse Square' (ichi-62080) and 'The Court House Shortly Before the Fire' (ichi-64281).

### Chamber of Commerce: distinguish the 1865 building from its replacements

`structure-1871-chamber-commerce` · structures · **documented**

The Chamber of Commerce dedicated Edward Burling's building at the southeast corner of Washington and LaSalle on August 30, 1865. The Board of Trade conducted its commodities exchange there. A replacement accommodated the Board by October 9, 1872; the Board's later Jackson-and-LaSalle building belongs to 1885.

**Applies to:** 1865 through the October 1871 fire

**Rendering implication:** Use the 1866–67 Jevne & Almini view for exterior research; connect entrances and interior commercial functions without importing later Board of Trade architecture.

**Limits:** The lithograph is pictorial evidence, not a measured elevation. Its street figures do not establish a particular 1871 day's activity.

**Next step:** Inspect ichi-63073; reconcile footprint and entry positions with a pre-fire map and directory.

**Sources:**

- [Chicago History Museum / Northwestern: Chamber of Commerce](https://greatchicagofire.org/landmarks/chamber-of-commerce/) — Museum interpretation, 2011; lithograph 1866–67. museum interpretation with primary visual reference; access: read. Locator: Caption 'Chamber of Commerce' (ichi-63073); dedication and rebuilding paragraphs.

### Sherman House: six-story pre-fire hotel

`structure-1871-sherman` · structures · **documented**

The pre-fire replacement Sherman House was a six-story hotel designed by W. W. Boyington and faced with local limestone described as Athens Marble. Its main entrance faced Clark Street through a two-story portico. The museum identifies a John Carbutt stereograph, circa 1870, as the pre-fire reference; the hotel completed in 1873 was another building.

**Applies to:** 1871-10-08 before the Great Fire

**Rendering implication:** Research the portico, stone stair, façade rhythm and relationship to Court House Square using ichi-00761. Hotel loading, luggage and carriage arrivals are possible action systems but need their own evidence.

**Limits:** Do not use the 1858 predecessor, 1873 rebuilding, circa-1890 photograph or 1911 hotel as interchangeable façade references.

**Next step:** Inspect the circa-1870 stereograph and resolve footprint, roof profile and ground-floor business frontage.

**Sources:**

- [Chicago History Museum / Northwestern: Sherman House](https://greatchicagofire.org/landmarks/sherman-house/) — Museum interpretation, 2011; stereograph circa 1870. museum interpretation with primary photograph; access: read. Locator: 'Sherman House before the Fire' (ichi-00761), contrasted with the final rebuilding paragraph.

### First Methodist Episcopal Church Block: church above shops and offices

`structure-1871-first-methodist` · structures · **documented**

At the southeast corner of Washington and Clark, Edward Burling's pre-fire building combined retail on the first floor, offices on the second, and a sanctuary on the third and fourth. The exterior was faced in local limestone. The museum identifies a Lovejoy & Foster stereograph from circa 1871; the 1873 replacement is separately illustrated.

**Applies to:** 1871 before the Great Fire

**Rendering implication:** Model a mixed-use commercial-looking block, not a freestanding church surrounded by lawn. Keep ground-floor commerce, upper-floor worship and their circulation distinct.

**Limits:** The floor functions are documented, but a full floor plan and the exact placement of stairs are not established by the summary.

**Next step:** Inspect ichi-22330 and locate contemporary tenant listings before assigning signage and doors.

**Sources:**

- [Chicago History Museum / Northwestern: First Methodist Church](https://greatchicagofire.org/landmarks/first-methodist-church/) — Museum interpretation, 2011; stereograph circa 1871. museum interpretation with primary photograph; access: read. Locator: 'First Methodist Episcopal Church Block before the Fire' (ichi-22330).

### Palmer House: unresolved identity, opening-date and image attribution conflict

`structure-1871-palmer-conflict` · structures · **open**

The museum page identifies its Greene 1871 image as a second Palmer House at State and Monroe that opened in March 1871. Chicagology instead reproduces an 1871 directory entry locating the operating Palmer House at the northwest corner of State and Quincy, a September 27, 1870 newspaper account of its opening, and an editorial statement that the State-and-Monroe hotel was still under construction at the fire. These accounts must remain visibly conflicting.

**Applies to:** 1870–1871 Palmer properties; especially the October 1871 snapshot

**Rendering implication:** Maintain separate candidate physical entities for State/Quincy and State/Monroe. Do not attach all Palmer photographs, floor counts and opening dates to a single hotel.

**Limits:** The museum page also calls the first building four stories, while the period descriptions transcribed by Chicagology describe seven including mansard floors. The original scans and photograph identity were not adjudicated in this pass.

**Next step:** Read the original 1871 directory entry and September 27, 1870 Tribune scan; compare Greene's photograph with intersection geometry and the 1870 Land Owner engraving. Record a reasoned ruling only after that comparison.

**Sources:**

- [Chicago History Museum / Northwestern: Palmer House](https://greatchicagofire.org/landmarks/palmer-house/) — Museum interpretation, 2011; images cataloged 1871. museum interpretation and image captions; access: read. Locator: 'The Palmer House before the Fire' (ichi-39580) and 'The Palmer House after the Fire' (ichi-26749).
- [Chicagology: Palmer House I & II](https://chicagology.com/prefire/prefire061/) — Period documents 1870–1871, hosted in a modern compilation. transcribed period documents mixed with modern editorial interpretation; access: read. Locator: 1871 Edwards directory entry; Chicago Tribune September 27, 1870; The Land Owner October 1870; opening editorial paragraph.

### Field & Leiter store: pre-fire six-story retail landmark

`structure-1871-field-leiter` · structures · **documented**

The pre-fire Field & Leiter store stood at the northeast corner of State and Washington. The museum describes six stories and almost 150 feet of State Street frontage and identifies a P. B. Greene stereograph from circa 1871. Its earlier Lake Street premises, the post-fire rebuilding, and the later Marshall Field complex are distinct physical states.

**Applies to:** 1871 before the Great Fire

**Rendering implication:** Use the pre-fire stereograph to establish the façade, entrance hierarchy and storefront scale. Preserve the wide street geometry as a separate spatial question.

**Limits:** Almost 150 feet is approximate. The museum's 1868–69 Charles Tobey photograph shows a building removed for the new store and must not be instantiated simultaneously on the same site.

**Next step:** Inspect ichi-64398; verify lot limits and correlate signage with the 1871 directory.

**Sources:**

- [Chicago History Museum / Northwestern: Field & Leiter](https://greatchicagofire.org/landmarks/field-leiter/) — Museum interpretation, 2011; photograph circa 1871 and predecessor image 1868–69. museum interpretation with primary photographs; access: read. Locator: 'Field & Leiter Store before the Fire' (ichi-64398); 'Charles Tobey Furniture and Bedding' (ichi-64383).

### Crosby's Opera House: mixed-use frontage and a closed theater awaiting reopening

`structure-1871-crosby` · structures · **documented**

Crosby's stood on the north side of Washington between State and Dearborn. The five-story Italianate front with a mansard roof housed shops, offices and an art gallery; the auditorium was behind it. Renovations occurred in summer 1871 and a reopening concert was scheduled for October 9, after the fire began.

**Applies to:** October 8, 1871 before ignition

**Rendering implication:** Separate the street-front block from the rear auditorium. The October 8 scene should not casually show a normal evening opera performance; any workers, preparations or visitors require separate evidence.

**Limits:** The exterior sources do not settle the revised 1871 interior. A 1866–67 lithograph cannot automatically supply the summer-1871 renovation state.

**Next step:** Compare ichi-62079 and ichi-64360; locate renovation reports and the October 9 program before authoring interiors or event actions.

**Sources:**

- [Chicago History Museum / Northwestern: Crosby's Opera House](https://greatchicagofire.org/landmarks/crosbys-opera-house/) — Museum interpretation, 2011; images 1866–67 and circa 1871. museum interpretation with primary visual references; access: read. Locator: 'Crosby's Opera House' (ichi-62079), renovation paragraph, and 'View ... before the Fire' (ichi-64360).

### Tremont House III: raised brick hotel, not the 1833 or 1873 building

`structure-1871-tremont` · structures · **documented**

The Tremont standing in 1871 was the third hotel of that name, on the southeast corner of Lake and Dearborn. The museum describes a five-story brick building with 260 rooms, designed by John M. Van Osdel and raised during the city's grade changes. Its six-story post-fire successor opened in 1873.

**Applies to:** 1871 before the Great Fire

**Rendering implication:** Use the third hotel's massing and its altered street-level relationship. Maintain independent identities for all four Tremont buildings.

**Limits:** A known raising does not establish that raising machinery or exposed foundations remained visible in October 1871.

**Next step:** Inspect the 1866–67 lithograph ichi-61955; find a later photograph or renovation record to test unchanged façade assumptions.

**Sources:**

- [Chicago History Museum / Northwestern: Tremont House](https://greatchicagofire.org/landmarks/tremont-house/) — Museum interpretation, 2011; lithograph 1866–67; rebuilding image circa 1873. museum interpretation with primary visual references; access: read. Locator: 'Tremont House' (ichi-61955), contrasted with 'Rebuilt Chicago—The New Tremont House' (ichi-00772).

### Post Office and Custom House: pre-fire federal building

`structure-1871-post-office` · structures · **documented**

The pre-fire federal building stood at the northwest corner of Dearborn and Monroe, with its main entrance on Dearborn. Postal functions occupied the main floor and basement; customs and other federal offices occupied the second floor; courts used the upper floor. The museum identifies both a 1866–67 lithograph and a Greene pre-fire stereograph.

**Applies to:** 1871 before the Great Fire

**Rendering implication:** Research postal circulation, street entrance, basement access and shutters. Do not substitute the post-fire federal complex farther south.

**Limits:** The museum catalogs the stereograph as 1871 but suggests it may have been taken shortly after the earlier lithograph; capture date needs review. Descriptions calling buildings fireproof are contemporary claims, not a material-performance guarantee.

**Next step:** Inspect the imagery and period federal reports; separate shutter location, construction material and interior layout claims.

**Sources:**

- [Chicago History Museum / Northwestern: Post Office and Custom House](https://greatchicagofire.org/landmarks/post-office-and-custom-house/) — Museum interpretation, 2011; lithograph 1866–67 and stereograph cataloged 1871. museum interpretation, identified images and transcribed eyewitness letter; access: read. Locator: 'Custom House' (ichi-61956), pre-fire Greene stereograph caption, and Francis William Test letter excerpt.

### Nixon Block: construction in progress at the snapshot

`structure-1871-nixon` · structures · **documented**

The Nixon Block near the northeast corner of Monroe and LaSalle was under construction when the fire struck and was completed afterward. Its surviving structure should not be rendered as a fully occupied, finished pre-fire office block. Two additional stories belonged to a later phase.

**Applies to:** October 8, 1871 before the Great Fire

**Rendering implication:** Represent the documented unfinished state, while leaving the exact work stage, scaffolding and worker arrangement unresolved until supported.

**Limits:** The post-fire Hansen stereograph documents survival and a later visible state, not automatically the exact October 8 construction condition. The boast painted on the building after the fire must be excluded.

**Next step:** Inspect ichi-39576 and locate dated construction reports to establish roof, glazing, doors and finishing work present by October 8.

**Sources:**

- [Chicago History Museum / Northwestern: Nixon Block](https://greatchicagofire.org/landmarks/nixon-block/) — Museum interpretation, 2011; stereograph 1871 after the fire. museum interpretation with post-event primary photograph; access: read. Locator: 'Nixon Building after the Fire' (ichi-39576) and accompanying construction-state account.

### Lind Block: occupied wholesale building with later alterations

`structure-1871-lind` · structures · **documented**

The five-story Lind Block, built in 1852 at the northwest corner of Randolph and Market, survived the fire. Its principal tenant was wholesale grocer Z. M. Hall. A later twentieth-century photograph shows an altered building that had lost part of its eastern end to street widening.

**Applies to:** 1871 before the Great Fire

**Rendering implication:** Use the 1871 post-fire stereograph as evidence of surviving fabric, with an explicit post-event date. Recover the original extent before applying later photographic detail.

**Limits:** A popular fire illustration appears to show the building burning even though it survived; dramatic pictures cannot determine destruction or fabric condition by themselves.

**Next step:** Inspect Greene stereograph ichi-64152; reconcile the river edge and Market Street footprint with an earlier map.

**Sources:**

- [Chicago History Museum / Northwestern: Lind Block](https://greatchicagofire.org/landmarks/lind-block/) — Museum interpretation, 2011; images 1871 and 1951. museum interpretation with primary photographs; access: read. Locator: 'The Lind Block after the Fire' (ichi-64152); 'The Sergeant Building' (ichi-64373).

### Waterworks: tower, pumping station, lake tunnel and intake

`structure-1871-waterworks` · structures · **documented**

The Chicago Avenue waterworks combined the limestone Water Tower and Pumping Station on opposite sides of Pine Street with a two-mile lake tunnel and offshore intake crib. The museum's pre-fire lithograph places the pumping station close to the contemporary lake shore.

**Applies to:** 1871 before the Great Fire

**Rendering implication:** Treat the waterworks as a connected infrastructure system. Research the original shoreline and Pine Street width independently of the surviving buildings' modern surroundings.

**Limits:** The museum page conflates the 1867 cornerstone/system celebration with building dedication language; verify construction chronology separately. Modern Michigan Avenue widening and Streeterville fill are unsuitable spatial defaults.

**Next step:** Inspect ichi-06859 and the 1871 Pine Street view ichi-39581; obtain dated engineering plans and the Board of Public Works report for measured dimensions.

**Sources:**

- [Chicago History Museum / Northwestern: Water Tower](https://greatchicagofire.org/landmarks/water-tower/) — Museum interpretation, 2011; lithograph 1866–67. museum interpretation with primary visual reference; access: read. Locator: 'Chicago Water Works' (ichi-06859), infrastructure description, and later Michigan Avenue comparison captions.
- [Chicago History Museum / Northwestern: Before and After](https://greatchicagofire.org/ruined-city/and-after/) — Greene stereograph cataloged 1871. museum primary-image catalog; access: read. Locator: 'View North on Pine Street ... to the Water Tower before the Fire' (ichi-39581).

### LaSalle Street Tunnel: newly opened, originally for people and horse traffic

`structure-1871-lasalle-tunnel` · structures · **documented**

The LaSalle Street Tunnel opened July 4, 1871, with entrances at Randolph and Kinzie. The museum's account describes two directional passages for horse-drawn traffic and a separate pedestrian passage. Its sectional illustration comes from an 1877 guidebook. Cable operation and later enlargement belong to subsequent periods.

**Applies to:** July 4–October 8, 1871

**Rendering implication:** Include portals, approach gradients, gas lighting and distinct circulation channels as research targets. Do not render a cable-car or electric streetcar tunnel for 1871.

**Limits:** The section is six years later than the snapshot. Exact portal design, grade and internal dimensions need original engineering evidence.

**Next step:** Find the 1871 opening report and engineering drawings; corroborate the later section before turning it into measured geometry.

**Sources:**

- [Chicago History Museum / Northwestern: LaSalle Street Tunnel](https://greatchicagofire.org/landmarks/lasalle-street-tunnel/) — Museum interpretation, 2011; sectional illustration 1877; opening described as 1871-07-04. museum interpretation with later primary engineering illustration; access: read. Locator: 'Sectional View ... from J. M. Wing, Seven Days in Chicago, 1877'; opening and later-conversion paragraphs.

### South Water Street and Clark Street swing bridge

`structure-1871-south-water` · structures · **documented**

The 1866–67 Jevne & Almini view of Clark and Water shows the bridge turned for vessels and road traffic waiting. The museum describes pre-fire riverfront businesses including commission merchants, insurance firms and brokers; the later central produce-market district should not be projected backward wholesale.

**Applies to:** 1866–67 visual baseline for 1871

**Rendering implication:** Link bridge rotation to boat clearance and queues of carts, wagons, carriages and pedestrians. Research working wharves, commercial frontages and waiting space together.

**Limits:** The illustration supports a type of action and spatial relationship, not an exact traffic count or bridge-opening schedule on October 8.

**Next step:** Inspect ichi-62077; resolve the 1871 bridge identity, dimensions and adjacent tenants before implementing movement paths.

**Sources:**

- [Chicago History Museum / Northwestern: South Water Street](https://greatchicagofire.org/landmarks/south-water-street/) — Museum interpretation, 2011; lithograph 1866–67. museum interpretation with primary visual reference; access: read. Locator: 'Corner of Clark and Water Streets' (ichi-62077).

### Terrace Row: contiguous luxury houses and rear service buildings

`structure-1871-terrace-row` · structures · **documented**

Terrace Row comprised eleven contiguous four-story limestone-faced houses erected in 1856 along Michigan Avenue south of Van Buren. The museum identifies a Copelin & Melander stereograph from 1871. Its account of William Bross's escape also identifies stables behind the row.

**Applies to:** 1871 before the Great Fire

**Rendering implication:** Research repeated house bays, stoops, rooflines, rear yards and stables rather than treating the row as an undifferentiated palace. Preserve the contemporary lakefront relationship.

**Limits:** The later Auditorium, Fine Arts Building and Art Institute-related buildings are replacements, not pre-fire neighbors. The source does not determine each home's interior.

**Next step:** Inspect ichi-64156 and locate property plans; distinguish confirmed individual entrances from inferred repetition.

**Sources:**

- [Chicago History Museum / Northwestern: Michigan Avenue and Terrace Row](https://greatchicagofire.org/landmarks/michigan-avenue-and-terrace-row/) — Museum interpretation, 2011; photographs 1871. museum interpretation, primary photographs and eyewitness excerpt; access: read. Locator: 'Terrace Row' (ichi-64156) and 'Terrace Row after the Fire' (ichi-64279).

### O'Leary property: double cottage, rented frontage and rear working yard

`structure-1871-oleary-cottage` · structures · **documented**

The museum describes a double cottage: the O'Learys and their five children occupied the rear section, while the McLaughlin family rented the front. A barn behind the dwelling held animals connected to Catherine O'Leary's local milk business. The cottage survived the fire, unlike the barn.

**Applies to:** October 8, 1871 before ignition

**Rendering implication:** Treat the property as domestic and working space with separate households, a service yard, dairy animals and outbuildings. The surviving cottage image can support fabric research with its post-event date retained.

**Limits:** The exact ignition cause is not established by this property evidence. Do not animate a cow kicking a lamp as fact. The page warns that purported barn relics have uncertain authenticity.

**Next step:** Inspect Abbott stereograph ichi-02741 and the inquiry testimony; derive property geometry and animal inventory from explicit locators.

**Sources:**

- [Chicago History Museum / Northwestern: O'Leary Home](https://greatchicagofire.org/landmarks/oleary-home/) — Museum interpretation, 2011; stereograph 1871 after the fire. museum interpretation with primary photograph; access: read. Locator: 'The Cottage of Patrick and Catherine O'Leary' (ichi-02741); relic-authenticity discussion.

### 144–146 Lake Street: ordinary commercial frontage with changing tenants

`structure-1871-ordinary-lake-street` · structures · **documented**

Chicagology reproduces directory entries for druggists, photographer Charles Mosher and map publisher Rufus Blanchard at 144–146 Lake, between Clark and LaSalle. Its January 27, 1870 Western Rural transcription places Blanchard at 146 Lake. The page also identifies an 1860 image and an 1869 insurance-map crop.

**Applies to:** 1850s–1870 evidence baseline; 1871 occupancy still to verify

**Rendering implication:** Use this as a test case for ordinary shopfronts, upper-floor professional rooms, signs and mixed occupancy rather than filling every street with landmark architecture.

**Limits:** Earlier tenants do not automatically persist into October 1871. Map-crop attribution and image dates are host captions not yet checked against originals. Geometry has not been extracted.

**Next step:** Read the 1871 directory entries and inspect the full 1869 sheet; retain historical addresses without substituting modern numbering.

**Sources:**

- [Chicagology: 144–146 Lake Street](https://chicagology.com/prefire/prefire458/) — Documents 1855–1870, reproduced in a modern compilation. transcribed period documents and image-discovery page; access: read. Locator: Directory transcriptions 1855–1867; Western Rural January 27, 1870; image captions '1860' and 'Sanborn Fire Insurance Map 1869'.

### Illinois Central Land Department: measured commercial-office candidate

`structure-1871-ic-land-office` · structures · **documented**

Transcribed Tribune reports of July 21, 1864 and January 2, 1865 describe an Illinois Central Land Department building north of the Adams House, extending from Michigan to Central Avenue, 30 feet wide and 130 feet deep, with three stories, basement and an elaborate roof. The 1870 directory places it east of Michigan Avenue between Lake and South Water.

**Applies to:** 1865–1871 building state, pending later-change check

**Rendering implication:** A strong candidate for a narrow mixed-use block with documented dimensions, principal-floor store and offices above. Record the reported roof descriptions separately before resolving their terminology.

**Limits:** These are transcriptions, not checked newspaper scans. Contemporary fireproof claims proved unreliable; they do not justify noncombustible interiors everywhere.

**Next step:** Verify original newspaper pages, inspect the January 1866 Chicago Illustrated plate, and resolve the 1869 map crop to a full sheet.

**Sources:**

- [Chicagology: Illinois Central Land Department](https://chicagology.com/prefire/prefire209/) — Period evidence 1864–1870. transcribed period documents and primary-image references; access: read. Locator: Chicago Tribune July 21, 1864 and January 2, 1865; Edwards 1870; Chicago Illustrated January 1866; map caption 1869.

### Aetna Building: dated office occupancy and insurance-company signage

`structure-1871-aetna` · structures · **documented**

The Aetna Building page identifies 84–86 LaSalle between Randolph and Washington. Its reproduced 1871 Edwards entry places Aetna Insurance Company's agents Goodwin & Pasco at 86 LaSalle. An 1865 Tribune notice places a meeting in room 28 of Boyington & Foster's new building at 84 LaSalle, opposite the Court House.

**Applies to:** 1865 construction reference and 1871 directory occupancy

**Rendering implication:** An ordinary office-building target with evidence for numbered rooms and contemporary business identity; useful for distinguishing office entrances from hotel and retail frontage.

**Limits:** Directory evidence confirms a listed office, not its precise floor, window sign, or presence on a particular October day. The page's 1869 map crop remains an acquisition lead.

**Next step:** Verify the directory scan and historical address range; inspect full-block imagery before assigning façade dimensions or signage.

**Sources:**

- [Chicagology: Aetna Building](https://chicagology.com/prefire/prefire473/) — Documents 1865 and 1871; map caption 1869. transcribed period documents with image-discovery references; access: read. Locator: Edwards 1871 entry; Chicago Tribune November 1, 1865; 'Sanborn Fire Insurance Map 1869' caption.

### Primary photograph acquisition register: fabric, ordinary houses and street sections

`source-1871-photo-register` · sources · **documented**

The museum's Before and After gallery identifies Greene's pre-fire Pine Street/Water Tower view (ichi-39581), George F. Rumsey house (ichi-29595), St. James Episcopal Church (ichi-22327), and Lovejoy & Foster's Booksellers' Row (ichi-29598). These are concrete catalog targets for pre-fire streetscape and building research.

**Applies to:** Images cataloged 1871 or circa 1871

**Rendering implication:** Use distinct image records to investigate setbacks, fences, paving, rooflines, storefront depth and scale. Link each observation to the specific image and visible region.

**Limits:** This pass read the catalog captions, not full-resolution images. No species, colors, measurements or individual identities should be inferred from the titles alone. Asset rights require separate checks.

**Next step:** Retrieve authorized high-resolution copies and record creator, catalog ID, depicted date, capture-date uncertainty, camera direction, rights and a crop locator for every extracted claim.

**Sources:**

- [Chicago History Museum / Northwestern: Before and After](https://greatchicagofire.org/ruined-city/and-after/) — Museum catalog, 2011; primary images 1871 or circa 1871. primary-image catalog; access: read. Locator: Six-item gallery list beneath 'The fire makes quick work of the city that was'.

### Survey-map baselines: 1863 and 1868, followed by dated change extraction

`source-1871-planimetric-map-register` · sources · **documented**

The University of Chicago catalog lists Flower and Van Vechten's 1863 Chicago map drawn from Davie's atlas at 1:6,000, Shober's 1868 guide map at about 1:24,000, and Van Vechten and Snyder's 1868 Chicago and Environs at about 1:12,000 in seven sheets. It also separately identifies circa-1871 burned-district maps.

**Applies to:** 1863–1868 spatial baselines; changes through October 1871 must be reconciled

**Rendering implication:** Prioritize the larger-scale maps for street/block control and use 1871 directory, construction and shoreline evidence to update them. Keep post-fire damage overlays distinct from the pre-fire base.

**Limits:** Catalog scales are not proof of parcel-level accuracy. No map in this entry has been georeferenced or digitized in this pass. Pictorial and planimetric sources need different treatment.

**Next step:** Acquire original scans through the library's Luna access, record control points and residuals, and create a dated change ledger for 1868–1871.

**Sources:**

- [University of Chicago Library: Before and After the Fire](https://www.lib.uchicago.edu/e/collections/maps/chifire/) — Catalog of original maps dated 1863, 1868 and circa 1871. holding-library catalog; access: read. Locator: Map table, first three entries; subsequent circa-1871 burned-district entries; use/credit statement.

### Insurance maps: verify edition and revisions before using footprints

`source-1871-insurance-map-controls` · sources · **documented**

The Newberry guide explains that insurance maps can identify footprints, materials and uses, but individual atlas copies contain different dated revisions. It lists Chicago History Museum holdings extending back to 1869; its description of freely digitized Library of Congress Chicago volumes concerns 1894–1897 material, not an automatic 1871 baseline.

**Applies to:** All proposed insurance-map evidence for 1871

**Rendering implication:** Extract only from a verified pre-fire sheet or a clearly labeled later source with a reasoned continuity argument. Separate publication date, revision date, depicted state and scan date.

**Limits:** The statewide database title '1867–1970' does not establish that a particular Chicago block is documented in 1867. Small web crops often omit title, sheet number, legend and revision marks.

**Next step:** Resolve the Chicagology 1869 crops to holding institution, atlas title, volume, sheet, legend and revision state before tracing geometry.

**Sources:**

- [Newberry Library: Fire Insurance Maps](https://www.newberry.org/collection/research-guide/fire-insurance-maps) — Current library research guide; holdings include atlases dated 1869–1928 and 1894–1897. holding-library research guide; access: read. Locator: Introduction; 'Chicago Fire Insurance Maps at Other Institutions'; Chicago History Museum and Library of Congress entries.

### Ruger's 1868 panorama: visual baseline with a three-year gap

`source-1871-ruger-panorama` · sources · **documented**

The Library of Congress catalogs A. Ruger's Chicago in 1868 from Schiller Street north side to 12th Street south side. Its geographic coverage and date make it a useful city-form reference preceding the target snapshot.

**Applies to:** 1868, with explicit reconciliation required for 1871

**Rendering implication:** Use as a visual cross-check for prominent structures and broad urban form, not as an unqualified measured parcel map.

**Limits:** Catalog metadata was available through search; direct item retrieval returned 403 in this pass. The full image was not inspected here, and later additions must not be omitted merely because absent in 1868.

**Next step:** Open the existing project copy or retrieve the cataloged resource, inspect the image and register individual observations with locations.

**Sources:**

- [Library of Congress: Chicago in 1868](https://www.loc.gov/item/73693350/) — 1868. primary-map catalog; access: catalog_only. Locator: Catalog title and creator; resource g4104c.pm001480.

### Edwards' 1871 annual directory: building use, addresses and named occupants

`source-1871-edwards-directory` · sources · **open**

The University of Illinois digital-book catalog identifies volume 14 (1871) of Edwards' annual directory of Chicago. This is the appropriate contemporary acquisition target for reconciling office tenants, hotels, businesses and historical addresses; its catalog existence is verified, but the volume has not been read in this pass.

**Applies to:** Directory publication and canvass period in 1871; not a guaranteed October 8 census

**Rendering implication:** Connect listed businesses and residents to evidence-backed building entities; use listings to prioritize signage and activity research without treating every listing as a separate structure.

**Limits:** A directory is neither a complete population census nor proof of construction date. Modern address numbers and same-name post-fire businesses cannot be substituted without a crosswalk.

**Next step:** Download the scan and searchable text, record printed-page locators, and verify OCR against page images for every imported name and address.

**Sources:**

- [University of Illinois: Edwards' annual directory of Chicago, volume 14](https://libsysdigi.library.illinois.edu/oca/Books2008-03/edwardsannualdir/edwardsannualdir141871chic/) — 1871. digitized-primary-book catalog; access: catalog_only. Locator: Catalog title and volume field: 14 (1871).

### Population: use the census as a baseline, not a street crowd count

`life-1870-population-baseline` · people · **documented**

The 1870 federal census counted 298,977 Chicago residents. Illinois State Archives reports 144,557 foreign-born residents, or 48.35 percent. These are citywide counts from the year before the fire, not a count of people present on October 8, 1871.

**Applies to:** Citywide population context; 1870 census baseline for the 1871 scene

**Rendering implication:** Build a varied population rather than a uniform frontier-town crowd. Separate resident population, commuters, visitors, street occupancy, indoor occupancy, and time of day. Citywide demographic proportions do not determine the composition of every block.

**Limits:** The census does not directly specify October 1871 street density, clothing, spoken language, or the appearance of particular people.

**Next step:** Extract ward-level census tables and selected household schedules; pair them with dated addresses before assigning local population weights.

**Sources:**

- [History and the Census: 1871 Great Chicago Fire](https://www.census.gov/about/history/stories/monthly/2021/october-2021.html) — 2021-10-01; describes the 1870 census. Federal statistical agency historical summary; access: read. Locator: Opening paragraph and section 'History and the Census: 1871 Great Chicago Fire'.
- [Illinois State Archives, Document 48: Invitation to a Columbus Day Celebration](https://www.ilsos.gov/departments/archives/teaching-packages/early-chicago/doc48.html) — Document 1869-10-11; explanatory table describes 1870. State archives interpretation accompanying a primary document; access: read. Locator: Explanation following the October 11, 1869 document; foreign-born population table.

### Resolve demographic classifications before creating exact quotas

`life-1870-demographic-discrepancies` · people · **open**

Published summaries disagree on some detailed counts. The Illinois Archives table lists Germany as 59,299, while the Ninth Census Compendium's indexed Germany column reports 52,318; other birthplaces have their own columns. Such differences must be reconciled against the actual table headings and definitions rather than silently combined.

**Applies to:** Foreign-birth classifications and demographic documentation

**Rendering implication:** Keep birthplace, nationality, language, race, occupation, and costume as distinct fields. Do not infer a person's ethnicity from clothing or apply a modern national boundary to a historical census category.

**Limits:** The Compendium PDF text was read, but its dense table OCR is unreliable and screenshot extraction failed. The detailed counts are not approved for production quotas.

**Next step:** Read page images of Compendium Table XX, printed pages 448–449, Chicago row 5, including all column headings; document any regrouping.

**Sources:**

- [A Compendium of the Ninth Census, Table XX](https://www2.census.gov/library/publications/decennial/1870/compendium/1870e-21.pdf) — 1870 census; subsequent published compendium. Primary federal census tabulation; access: read. Locator: Printed pages 448–449; PDF pages 5–6; Table XX; Chicago row 5.
- [Illinois State Archives, Document 48](https://www.ilsos.gov/departments/archives/teaching-packages/early-chicago/doc48.html) — Describes 1870. State archives explanatory table; access: read. Locator: Explanation: birthplace table.

### Include Black Chicagoans without importing the later Great Migration city

`life-1871-black-chicago` · people · **open**

The National Park Service reports a Black population of 3,691 in Chicago in 1870. Other historical summaries round this to about 3,700 or 4,000. This establishes an existing community before the fire, not a population that arrived only in the twentieth century.

**Applies to:** People and community research for 1871

**Rendering implication:** Include Black residents in the research and actor inventory. Determine households, businesses, institutions, and occupations through specific records rather than assigning generic servant roles or importing twentieth-century Bronzeville geography.

**Limits:** The exact census count needs page-level reconciliation because some other summaries report 3,696. This source does not establish a particular person's street location or appearance on October 8.

**Next step:** Trace named households and businesses through the 1870 census and 1871 directory; use approximate population context until the original table is checked.

**Sources:**

- [Chicago's Black Metropolis: Understanding History Through a Historic Place](https://www.nps.gov/articles/chicago-s-black-metropolis-understanding-history-through-a-historic-place-teaching-with-historic-places.htm) — Modern NPS historical interpretation; describes 1870. National Park Service historical education resource; access: lead. Locator: Historical background; paragraph beginning 'By 1870'.
- [African Americans, Encyclopedia of Chicago](https://www.encyclopedia.chicagohistory.org/pages/27.html) — 2005; describes nineteenth-century Chicago. Scholarly historical encyclopedia; access: lead. Locator: Post-Civil War population and civil-rights discussion.

### The 1871 Edwards directory is the principal address-and-occupation extraction target

`life-1871-directory-primary-backbone` · people · **documented**

Internet Archive holds Edwards' annual directory of Chicago, volume 14 (1871), contributed by the University of Illinois Urbana-Champaign. Its catalog records 1,148 scanned pages and marks possible copyright status NOT_IN_COPYRIGHT. The scan notes warn of tight margins, skewed pages, and cropped advertising.

**Applies to:** Residents, occupations, businesses, institutions, addresses, advertisements, and transport

**Rendering implication:** Use directory entries to connect named activities to particular premises: a shopkeeper needs a shop, a stable needs access, and a transporter needs a destination. Preserve the historical address string before geocoding.

**Limits:** Catalog metadata was read; directory entries were not extracted in this pass. A directory is selective and is not a complete census of women, children, lodgers, or poorer residents. Publication date does not guarantee occupancy on the scene date.

**Next step:** Download OCR and page images; extract the introduction, street guide, transport tables, businesses, and selected blocks. Verify each used entry against the scan and join addresses through a historical address crosswalk.

**Sources:**

- [Edwards' annual directory of Chicago, volume 14 (1871)](https://archive.org/details/edwardsannualdir141871chic) — 1871. Digitized primary city directory; access: catalog_only. Locator: Catalog metadata, volume, contributor, scan notes, download options.
- [Chicago History Museum: Directories and Census Data](https://libguides.chicagohistory.org/familyhistory/directories) — Current research guide. Museum collection research guide; access: lead. Locator: City directories and their contents.

### Anchor horsecar movement to documented routes

`life-1870-horsecar-routes` · vehicles · **documented**

Chicagology transcribes Edwards' 1870 City Railway and Omnibus Routes. It lists State Street service from State and Randolph, North Chicago services toward the city limits, Sedgwick, Clybourn/Larrabee and Graceland, and West Division services on Randolph, Madison, Blue Island, Milwaukee, and Clinton/Jefferson.

**Applies to:** Transport network baseline immediately preceding 1871

**Rendering implication:** Create route-constrained vehicle paths, terminals and waiting locations. The same source lists a 2½-minute State Street headway to Twenty-second Street; treat that as a dated timetable attribute, not a universal spawning interval.

**Limits:** This is a modern transcription of the 1870 directory, not inspection of the original page and not confirmation of Sunday October 8, 1871 service. Authorized track and operating track must remain distinct.

**Next step:** Check the 1871 directory and map for operating segments, terminal changes, Sunday service and exact track geometry.

**Sources:**

- [1859–1871—Chicago City Railroad Company](https://chicagology.com/prefire/prefire372/) — Transcribes 1870. Modern transcription of primary directory material; access: read. Locator: Section 'Edwards’ Annual Directory in the City of Chicago, for 1870'; 'CITY RAILWAY AND OMNIBUS ROUTES'.

### Hotel–depot omnibuses continued alongside street railways

`life-1870-omnibus-transfer` · vehicles · **documented**

The same 1870 directory transcription describes Parmelee omnibuses linking principal hotels with railroad depots at train arrivals and departures.

**Applies to:** Hotel entrances, depot forecourts, transfer traffic

**Rendering implication:** Add luggage handling, boarding and unloading at verified endpoints as reconstructed actions. Omnibus movements should respond to a train schedule rather than circulate like horsecars.

**Limits:** Vehicle dimensions, liveries, precise stops, train times and October 1871 operations remain unverified.

**Next step:** Extract depot timetables, hotel advertisements, operator addresses and dated vehicle imagery.

**Sources:**

- [1859–1871—Chicago City Railroad Company](https://chicagology.com/prefire/prefire372/) — Transcribes 1870. Modern transcription of primary directory material; access: read. Locator: 1870 directory section; final paragraph headed 'Omnibus Line'.

### A surviving Chicago horsecar provides a measured comparison

`life-1859-horsecar-measured-reference` · vehicles · **documented**

Illinois Railway Museum records North Chicago Street Railroad 8 as a single-truck, Bombay-roof horsecar with 18 seats, hand brakes, and listed dimensions of 12 feet long, 7 feet 5 inches wide, and 9 feet 6 inches high. Its driver stood on the front platform; one or two horses hauled it.

**Applies to:** Horsecar asset research

**Rendering implication:** Use this compact vehicle as a dimensional comparison and model the exposed driver, horse coupling and hand-brake operation. Confirm what the listed length measures before building a complete envelope.

**Limits:** The museum prints its construction year as '1859?' and says the car was rebuilt for the 1933 Century of Progress exhibition. Current fabric and dimensions cannot automatically certify its exact 1871 condition or the whole fleet.

**Next step:** Compare the museum photographs and dimensions against dated Chicago street photographs and builder drawings; record any reconstruction explicitly.

**Sources:**

- [North Chicago Street Railroad 8](https://www.irm.org/player/ncsr8/) — Object catalog; construction date recorded as 1859?. Museum collection record for a surviving vehicle; access: read. Locator: Equipment Information; Details; final paragraph under Horse Cars.

### Horse traffic requires stables and care, not just moving animals

`life-1871-horse-support-system` · actions · **inferred**

The museum's horsecar history describes the support burden of horse traction: food, water, hostlers, veterinary care and manure. Exact stable operations in an 1871 Chicago block need separate records.

**Applies to:** Street railways, drayage, omnibuses, private carriages and service yards

**Rendering implication:** Create linked care actions: harnessing, unhitching, watering, feeding, grooming, resting and cleaning. Place them only where an appropriate yard, stable, water source and access route exist.

**Limits:** These are proposed behavior systems, not witnessed actions at a particular time or proof of stable locations. Do not model all horses as identical or make every horse continuously work.

**Next step:** Find stable and livery entries in the directory and footprints on insurance maps; obtain period harness and vehicle-specific references.

**Sources:**

- [North Chicago Street Railroad 8](https://www.irm.org/player/ncsr8/) — Modern museum interpretation. Museum technical history; access: read. Locator: Horse Cars discussion of operational support.

### The river needs commercial schooners as well as steam vessels

`life-1871-sailing-freight` · vehicles · **documented**

Chicago Maritime Museum describes the city's grain and lumber trades as heavily dependent on schooners, with lumber arriving from Michigan and Wisconsin. It identifies Wolf Point as a location where arriving lumber cargoes were inspected and sold.

**Applies to:** River, docks, grain elevators, lumber yards and harbor approaches

**Rendering implication:** Distinguish inbound lumber cargo, outbound grain, docked vessels, and vessels under way. Represent the commercial chain with cargo-specific berths and destinations rather than distributing decorative boats uniformly.

**Limits:** The museum gives broad traffic magnitudes, not an October 8 vessel manifest. Its port-ranking claims should not become exact simultaneous vessel counts.

**Next step:** Acquire dated arrival/clearance columns, vessel registers, berth photographs and insurance-map waterfront facilities; name ships only after confirming their presence.

**Sources:**

- [Grain and Lumber Trade](https://www.chicagomaritimemuseum.org/maritime-history/grain-and-lumber-trade) — Modern museum interpretation; describes the nineteenth century and 1870–1871. Maritime museum historical synthesis; access: read. Locator: Opening four paragraphs.

### Use Great Lakes schooner forms rather than ocean-ship defaults

`life-1871-schooner-form` · vehicles · **documented**

Chicago Public Library describes wooden centerboard schooners with fore-and-aft rigs as characteristic Lake Michigan cargo craft. Centerboards helped them navigate shallow harbor bars; the fore-and-aft rig could be handled by comparatively small crews.

**Applies to:** Comparative vessel morphology

**Rendering implication:** Research hull proportions, centerboard cases, masts, booms, rigging, cargo stowage and working decks. Distinguish furled sails at a berth from a sailing configuration and obtain specific evidence for towing or maneuvering.

**Limits:** This is a regional type description, not proof of a named vessel, exact hull dimensions, sail state or berth on October 8.

**Next step:** Choose a documented vessel or narrowly defined class and connect its plan to a dated Chicago image.

**Sources:**

- [Schooners: Technology That Changed Chicago](https://www.chipublib.org/blogs/post/technology-that-changed-chicago-schooners/) — 2014-02-24. Public library historical interpretation with bibliographic references; access: read. Locator: Introductory paragraphs defining schooners and centerboards.
- [Grain Elevators and Cargo Ships on Chicago River, c.1865](https://encyclopedia.chicagohistory.org/pages/3387.html) — Cataloged c.1865 / before 1871. Historical image catalog; access: catalog_only. Locator: Image title and caption.

### Animate commodity handling as linked tasks

`life-1871-commercial-labor-actions` · actions · **inferred**

The documented grain, lumber, hotel-transfer and livestock economies support a research program for freight labor. The precise motions below are reconstruction proposals until matched to a workplace and period technique.

**Applies to:** Wharves, warehouses, freight depots, lumber yards and commercial streets

**Rendering implication:** Create task sequences with props and destinations: inspect cargo, handle lines, move a load, stack material, receive delivery, record a transaction, and return equipment. Each sequence should require a compatible cart, load, doorway, platform, ramp or berth.

**Limits:** Do not assume every task occurred on Sunday, every commodity used sacks or barrels, every dock had the same lifting machinery, or every worker had the same occupation and clothing.

**Next step:** Attach each proposed action to a dated image, trade manual, newspaper description, business record or surviving tool before marking it documented.

**Sources:**

- [Grain and Lumber Trade](https://www.chicagomaritimemuseum.org/maritime-history/grain-and-lumber-trade) — Modern synthesis of nineteenth-century trade. Museum historical context; access: read. Locator: Commodity and Wolf Point discussion.

### Separate livestock-market activity from downtown street life

`life-1871-stockyards-boundary` · actions · **documented**

The Union Stock Yard and Transit Company was incorporated in 1865 to consolidate stockyard operations. This is a major economic system to research, but its site and transport links must be represented separately from downtown commerce.

**Applies to:** Southern industrial and livestock districts; regional economic context

**Rendering implication:** If the modeled extent reaches the stockyards, investigate pens, gates, watering, feeding, weighing, rail loading and animal movement. For a downtown-only extent, show only locally evidenced supply and transport connections.

**Limits:** Published summaries describe different acreages for different dates or definitions. Do not project the later, much-expanded stockyards, later gate, or mature refrigerated-meat system backward into 1871.

**Next step:** Read the incorporating act and a dated 1871 yard plan; establish the scene boundary before commissioning yard assets.

**Sources:**

- [An Act to Incorporate the Union Stock Yard and Transit Company of Chicago](https://www.ilsos.gov/departments/archives/online-exhibits/100-documents/1865-incorp-stock-transit-chicago.html) — 1865. State archives presentation of a primary incorporating act; access: catalog_only. Locator: Document 41; Background.
- [Union Stock Yard, Encyclopedia of Chicago](https://encyclopedia.chicagohistory.org/pages/2218.html) — 2005; describes opening in 1865 and later development. Scholarly historical encyclopedia; access: lead. Locator: Opening description.

### A documented household dairy links residents, animals and work

`life-1871-household-dairy` · people · **documented**

Chicago History Museum identifies Catherine O'Leary as a local milk seller whose barn held five cows and a horse. The O'Learys and five children occupied the rear of a double cottage; the McLaughlin family rented the front.

**Applies to:** O'Leary property on DeKoven Street; comparative household-economy research

**Rendering implication:** Research shared occupancy, rear-yard access, dairy animals, storage and household work. Milk handling, animal care and deliveries are possible reconstructed routines, requiring separately verified implements and timing.

**Limits:** This establishes a specific household economy, not that every urban yard kept cows. The museum explicitly identifies the cow-and-lamp origin scene as mythic; do not depict it as witnessed fact. The cited cottage stereograph is from 1871 after the fire.

**Next step:** Compare the cottage image, lot records, census household and inquiry testimony; distinguish surviving cottage evidence from speculative barn geometry.

**Sources:**

- [O'Leary Home](https://greatchicagofire.org/landmarks/oleary-home/index.html) — 2011 interpretation; 1871 stereograph and ca.1872 lithograph. Museum interpretation with cataloged historical images; access: read. Locator: Caption for J. H. Abbott stereograph ichi-02741; discussion of the ca.1872 origin lithograph.

### Date clothing from object records and distinguish comparison from local proof

`life-1871-clothing-comparative-objects` · people · **documented**

The Metropolitan Museum catalogs an American wool-and-cotton suit dated 1870–73, object 2009.300.7719a–e, and an American silk dress dated 1870–73, object 1979.346.113a,b. Both records provide public-domain collection images.

**Applies to:** Comparative clothing materials, cut and construction

**Rendering implication:** Build reference sheets with front, side and back views, garment components, fabric and provenance. Use the records as period comparators, then match attire to role, wealth, age, weather and activity through local evidence.

**Limits:** Neither catalog establishes a Chicago wearer in October 1871. Date ranges can include later manufacture. The suit's garment type and intended wearer require visual inspection before assigning it to an actor. Museum survival favors certain garments over ordinary working clothes.

**Next step:** Inspect all object photographs and local dated portraits or street images; source working clothes, headwear, footwear, children's clothing and repairs separately.

**Sources:**

- [Suit, American, 1870–73](https://www.metmuseum.org/art/collection/search/174758) — Object dated 1870–73. Museum collection object; access: read. Locator: Artwork Details; object 2009.300.7719a–e.
- [Dress, American, 1870–73](https://www.metmuseum.org/art/collection/search/107603) — Object dated 1870–73. Museum collection object; access: read. Locator: Artwork Details; object 1979.346.113a,b.

### Early bustle silhouettes differ from the later 1880s form

`life-1871-walking-dress-silhouette` · people · **documented**

The Met's American walking dress, dated 1870–75, is a silk ensemble with an overskirt contributing decoration and bustle fullness. The museum describes it as clothing for promenading and visiting.

**Applies to:** Fashionable walking and visiting clothing as a comparative type

**Rendering implication:** Study the early bustle profile, layered skirt construction and movement envelope. Keep this as one wardrobe option; do not dress an entire population in a single fashionable silhouette.

**Limits:** The 1870–75 range overlaps but does not prove manufacture before the fire. This is not Chicago provenance or evidence of ordinary labor clothing. A separately found summer dress, Met 2002.252a,b, is dated 1872–75 and should remain a later comparison, not a prefire exemplar.

**Next step:** Pair the object with 1870–71 fashion plates and Chicago-specific portraits, identifying which features are directly observed and which are reconstructed.

**Sources:**

- [Walking dress, American, 1870–75](https://www.metmuseum.org/art/collection/search/156667) — Object dated 1870–75. Museum collection object and interpretation; access: read. Locator: Curatorial description; object 2009.300.1900a–c.
- [Dress, American, 1872–75](https://www.metmuseum.org/art/collection/search/85161) — Object dated 1872–75. Later comparative museum object; access: read. Locator: Artwork Details; object 2002.252a,b.

### Retail activity was moving toward State Street before the fire

`life-1871-retail-location` · actions · **documented**

The museum's State and Madison page identifies Booksellers' Row, on State north of Madison, as a five-story marble-front retail building associated with the late-1860s shift of upscale shopping from Lake Street to State.

**Applies to:** State and Madison retail district

**Rendering implication:** Research shops, window displays, signs and entrances from the ca.1871 Lovejoy & Foster stereograph. Shopping, browsing and deliveries can then be attached to specific premises as reconstructed actions.

**Limits:** The same webpage also contains postfire and much later images. Its photograph with four horsecars is explicitly after the fire; its 1878–79 carriage-trade view cannot certify prefire façades, traffic or attire.

**Next step:** Inspect prefire image ichi-29598 at high resolution, transcribe legible signs and cross-check businesses against the 1871 directory.

**Sources:**

- [State & Madison](https://greatchicagofire.org/landmarks/state-madison/) — Prefire stereograph cataloged ca.1871; 2011 interpretation. Museum interpretation and historical image catalog; access: read. Locator: Caption 'View of Booksellers’ Row before the Fire'; ichi-29598, contrasted with later image captions.

### October 8 was Sunday: schedules need a date, not just a year

`life-1871-sunday-and-event-scheduling` · actions · **documented**

The museum timeline dates the fire's beginning to Sunday, October 8, 1871. Crosby's Opera House was scheduled to reopen on October 9 after refurbishment; that planned concert never took place.

**Applies to:** Scene calendar and cultural activity

**Rendering implication:** Make weekday/Sunday, hour and event status explicit inputs. Worship, visiting, recreation and transport should be researched against Sunday schedules. Do not populate Crosby's with an audience for the unrealized October 9 reopening.

**Limits:** Sunday does not prove all shops were closed or that all residents attended church. Churchgoing, visiting and leisure actions remain reconstruction choices until tied to local services or testimony.

**Next step:** Collect October 7–8 newspaper advertisements, church notices, railroad timetables, entertainment listings and eyewitness accounts of the hours before ignition.

**Sources:**

- [Timeline: Chicago in 1871](https://greatchicagofire.org/timeline/index.html) — 2011 interpretation of 1871 events. Museum historical chronology; access: read. Locator: The Great Conflagration; Sunday, October 8, 1871.
- [Crosby's Opera House](https://greatchicagofire.org/landmarks/crosbys-opera-house/) — 2011 interpretation; describes 1871. Museum landmark history; access: read. Locator: Discussion of refurbishment and planned October 9 reopening.

### Immediately before the Great Fire was already after another major fire

`life-1871-saturday-fire-state` · actions · **documented**

The museum timeline places the Saturday Night Fire on October 7 in the area bounded by Van Buren, Clinton, Adams and the South Branch. It reports twenty destroyed buildings and firefighting continuing into October 8 afternoon, leaving crews exhausted and equipment needing repair.

**Applies to:** October 8 scene cutoff; Near West Side; firefighting readiness

**Rendering implication:** A scene late on October 8 must account for this earlier burn area. Research surviving fire crews, damaged apparatus, blocked access and spectators before adding them as actions.

**Limits:** The chronology does not provide parcel-level damage, exact surviving structures, smoke opacity or the location of each crew at a chosen hour.

**Next step:** Digitize the earlier fire footprint from contemporary reporting and compare it with the intended scene time; distinguish this damage from the subsequent Great Fire.

**Sources:**

- [Timeline: Chicago in 1871](https://greatchicagofire.org/timeline/index.html) — 2011 interpretation of October 7–8, 1871. Museum historical chronology; access: read. Locator: A Fiery Prelude; Saturday, October 7, 1871.

### Operational rules offer behavior constraints without proving compliance

`life-1871-rail-and-fire-watch` · actions · **documented**

The museum timeline records a January 30, 1871 request to enforce the six-mile-per-hour city train-speed limit, and a January 24 order extending station-tower fire watches from nightfall until 9:30 p.m., when the regular night watch began.

**Applies to:** Rail crossings, stations and fire-watch behavior

**Rendering implication:** Treat rail crossings as shared conflict points and investigate watchtower sightlines. Store legal speed limits separately from reconstructed movement speed and actual observed compliance.

**Limits:** A rule documents an intended practice, not universal obedience or the exact roster on October 8. This does not specify locomotive type, track elevation or every watchtower's geometry.

**Next step:** Find the original council and fire-commission records, dated track maps, apparatus inventories and station locations.

**Sources:**

- [Timeline: Chicago in 1871](https://greatchicagofire.org/timeline/index.html) — 2011 interpretation of January 1871 records. Museum chronology summarizing municipal actions; access: read. Locator: Extending the Fire Watch, January 24; Intracity Train Speed Limits, January 30.

### Every populated scene needs an action-and-prop evidence record

`life-1871-action-evidence-contract` · actions · **inferred**

The researched sources establish people, vehicles, commodities, premises and dated events at different levels of specificity. They do not jointly establish a fully observed street scene at a single moment. Animation requires an explicit reconstruction layer.

**Applies to:** All people, animals and moving vehicles

**Rendering implication:** For each action record actor role, location, time window, destination, required props, motion constraints, source, confidence and exclusions. Useful candidate routines include walking, waiting, boarding, alighting, carrying luggage, receiving goods, tending animals, shopping, visiting, handling dock lines and recording transactions.

**Limits:** These are proposed authoring requirements and candidate actions, not a claim that each occurred at the chosen location and moment. Keep named historical people separate from anonymous reconstructed actors.

**Next step:** Choose one documented block, wharf and residential lot as pilots. Build complete actor–prop–place chains and expose unresolved evidence before expanding crowd density.

**Sources:**

- [Edwards' annual directory of Chicago, volume 14 (1871)](https://archive.org/details/edwardsannualdir141871chic) — 1871. Primary directory; catalog inspected; access: catalog_only. Locator: Directory extraction target for people, businesses and locations.
- [State & Madison](https://greatchicagofire.org/landmarks/state-madison/) — ca.1871. Dated local visual reference; access: catalog_only. Locator: Prefire Booksellers' Row stereograph ichi-29598.

## Before rendering 1871

### P0 · Scene contract · Fix the date, hour and modeled extent

An explicit October 8 pre-ignition scene specification, with a separate October 7 intact-city comparison if useful.

Acceptance: Day, local time convention, bounding extent, Saturday Night Fire state and terrain interval agree; no scene is called rendered by this dossier.

### P0 · Evidence · Acquire and register primary sheets and photographs

Verified map editions, uncropped image masters, 1871 directory and municipal-report page records.

Acceptance: Every extracted attribute has a source, date, locator, access status and rights decision; catalog-only leads remain distinct from inspected pixels.

### P0 · Terrain · Build the 1871 ground state

Georeferenced shoreline, lagoon, depot fill, river reaches, street grades, bridge/tunnel approaches and earlier-burn footprint.

Acceptance: Control points and residuals recorded; terrain, water and walking heights agree; neither natural 1835 ground nor 1904 fill is silently reused.

### P0 · Structures · Resolve physical building identities and date conflicts

Dated parcel/structure register with original and replacement hotels, churches and institutions kept separate.

Acceptance: Palmer conflict is ruled on or visibly unresolved; Nixon construction state and Crosby closure are honored; every included phase covers the cutoff.

### P1 · Urban fabric · Complete a landmark and an ordinary block

Measured/reconstructed footprints, heights, roofs, openings, storefronts, rear buildings, yards and service access.

Acceptance: Attribute-level confidence survives compilation; no anonymous citywide total is expanded into invented named buildings.

### P1 · People · Prepare people and clothing evidence

Household/business address joins, role inventory, comparative garment sheets and dated local image readings.

Acceptance: Identity, presence, location, occupation, appearance and action confidence are separate; aggregate census counts never masquerade as street density.

### P1 · Transport · Connect vehicles, paths and infrastructure

Verified horsecar routes, omnibus transfers, dray/rail/boat types, bridge opening rules and stable support.

Acceptance: Vehicle dates precede cutoff; dimensions and route provenance are explicit; no cable cars, elevated trains or later catalogue assets slip in.

### P1 · Living landscape · Map plants, animals and October conditions

Plantable habitat masks, cemetery/park phases, photographed trees, drought condition and independently sourced fauna.

Acceptance: No mature proposed park or modern tree inventory; species, density, phenology and weather uncertainty remain exposed.

### P1 · Actions · Author dated activity pilots

Retail, waterfront and household pilots with actor–prop–place records and Sunday/hour constraints.

Acceptance: Each motion has compatible paths and objects; documented activities remain separate from reconstructed timing, crowd density and named-person performance.

### P2 · Acceptance · Review the reconstruction at street and city scale

Named camera anchors, source-image comparisons, mobile/desktop checks, evidence cards and visible liberties.

Acceptance: Zero missing assets or page errors, no terrain/footprint collisions, inspectable provenance, reproducible builds and an explicit list of unresolved gaps.
