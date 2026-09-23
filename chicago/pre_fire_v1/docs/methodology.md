# Methodology and evidence standard

## Scope

Version 1 covers source-identifiable buildings, civil structures, and building complexes from the earliest documented settlement episode through October 9, 1871. It is a research-grade seed database, not a fabricated parcel census. Surviving narratives, directories, maps, designation records, and fire accounts often name only notable structures while reporting ordinary construction as an aggregate count.

## What constitutes a record

A row requires a defensible identity: a name, owner/occupant plus type and location, an explicitly enumerated compound component, or a distinct documented construction episode. Complexes are retained where the evidence cannot reliably distinguish their component buildings. Bridges and infrastructure appear because the supplied guide and historical sources treat them as material parts of the built city; `building_type` makes them separable.

Unnamed totals belong in `stock_estimates.csv`, not `buildings.csv`. This prevents a reported count—such as annual construction or the Great Fire loss—from being converted into invented names, addresses, or footprints.

## Provenance

Every building links to at least one record in `sources.csv`. `assertions.csv` repeats the source keys for identity, date, address, architect/builder, demolition, and 1871 fire-fate fields when those values exist. Confidence applies to the assembled record; `needs_review=true` marks unresolved entity identity, date conflict, indirect construction evidence, OCR sensitivity, or uncertain fire exposure.

Reliability tiers follow the supplied Chicago guide:

1. Official designation records, NRHP/NPS, HABS/HAER, and equivalent primary public records.
2. Scholarly architectural histories and institutional reference works.
3. Trade press, contemporary directories, maps, newspapers, and near-contemporary city histories.
4. Secondary compilations and lead sources requiring stronger confirmation.

## 1871 fire fate

No blanket rule terminates every structure in central or north Chicago on October 9, 1871. A loss is recorded only when a direct account states it, a reliable source gives the loss date/cause, or a future georeferenced property point or footprint falls inside a defensible fire polygon. Unknown, uncertain, and not-established values remain explicit.

## Maps and the year model

`map_references.csv` distinguishes the year depicted from the year a map was actually created. Contemporary cadastral and engineering maps, pictorial bird's-eye views, and later historical reconstructions have different evidentiary value. The included viewer selects the closest dated reference, but it does not imply that the image exactly represents every intervening year.

`city_extent_events.csv` and `landform_events.csv` are effective-dated scaffolds for a future 4D city model. Entries marked `needs_geometry` or `reference_map_only` must be georeferenced and digitized before spatial analysis. Street raising, shoreline fill, river works, annexations, and the fire are modeled as changes over time, not as one timeless basemap.

## Known limitations

- Demolished ordinary wood buildings and pre-fire permit records are severely incomplete.
- Historical street names, renumbering, and relocated buildings complicate entity resolution.
- Occupancy evidence does not always prove new construction; such rows are flagged.
- Approximate present-day coordinates identify a landmark vicinity, not an archaeological footprint.
- Downloaded map images are practical derivatives; source pages should be used for archival-resolution masters and metadata.
