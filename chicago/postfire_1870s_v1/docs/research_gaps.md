# Research gaps and next-pass queue

## What “complete” means in this version

The annual CSVs aim to be comprehensive for **named or otherwise source-identifiable** Chicago building projects recoverable from the consulted city, institutional, contemporary, and retrospective sources. They are not—and no surviving evidence can make them—a literal enumeration of every dwelling, shed, stable, shanty, or unpermitted structure standing in each year.

Andreas explicitly states that first-year counts omitted temporary business shanties and innumerable North Side cottages built without permits. The 1877–1879 table reports more than one thousand buildings per year but does not name them. Converting those totals into anonymous “building” rows would invent identities, locations, owners, and footprints. This package instead preserves the counts in `annual_stock_estimates.csv` and the source-resolvable projects in `buildings.csv`.

## Priority gaps

1. Transcribe surviving building-permit ledgers and Board of Public Works reports at record level, where extant.
2. Search 1872–1879 newspapers and the *Real Estate and Building Journal* by owner, street, architect, and project notice; record negative searches.
3. Decompose grouped commercial blocks, school campuses, hospitals, stockyard works, breweries, and railroad facilities into component structures only when the sources distinguish them.
4. Resolve historical street numbers through the 1909 renumbering and parcel history before adding point coordinates.
5. Entity-resolve post-fire predecessor names against `pre_fire_v1`; do not infer same fabric merely from a reused institution or hotel name.
6. Georeference every annual map against stable control points, digitize effective-dated city/shore/rail/fire geometries, and attach uncertainty/error statistics.
7. Acquire licensed or public-domain building images from the Library of Congress, Chicago History Museum, HABS/HAER, university collections, and contemporary publications; record rights per derivative.

## Known source biases

- Landmark inventories favor surviving or architecturally distinguished properties.
- Andreas favors prominent public, commercial, institutional, industrial, and biographical subjects.
- Directories prove occupancy/existence more readily than construction year.
- Anniversary histories can compress a multi-phase complex into one date.
- Bird’s-eye views are pictorial evidence, not survey geometry.

Blank fields and `needs_review=true` are intentional research states, not zero values.
