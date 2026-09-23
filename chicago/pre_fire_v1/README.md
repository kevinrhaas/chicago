# Chicago Before the Fire — research database v1

This package is a sourced, importable foundation for modeling Chicago's built environment from the earliest documented settlement through the Great Chicago Fire of October 1871. It combines independently researched period tranches, field-level provenance, aggregate stock estimates, dated historical maps, and a static year explorer.

## Start here

- `data/buildings.csv` — one row per named or source-identifiable building, structure, component, or complex.
- `data/sources.csv` and `data/building_sources.csv` — source registry and many-to-many provenance links.
- `data/assertions.csv` — key field claims with confidence and review state.
- `data/stock_estimates.csv` — counts whose individual building identities do not survive.
- `data/media.csv`, `data/media_buildings.csv`, and `data/media_checksums.csv` — sourced visual assets, many-to-many building subjects, rights/provenance, and local-file integrity.
- `maps/map_references.csv` — depicted year, actual creation date, map type, rights, local derivative, and spatial readiness.
- `viewer/index.html` — static year slider that pairs the closest map reference with active records and city/landform events.
- `docs/statistics.md` — generated totals and coverage indicators.
- `docs/methodology.md` — evidence standard, fire-fate rules, and limitations.
- `schema/import_order.md` — relational load order.

## A necessary definition of “complete”

This is comprehensive for the named and source-identifiable evidence reviewed in this phase; it is not a fictional list of every anonymous cabin, shop, shed, or house. The historical record often preserves a period-wide total without names or parcels. Those totals are retained separately so later permit, directory, tax, atlas, and newspaper extraction can add identities without corrupting the evidence.

The Great Fire reportedly consumed 17,450 structures. That figure is an aggregate loss benchmark, not 17,450 recoverable building records. Likewise, a contemporary report of hundreds of buildings erected in a year cannot be expanded into invented rows. The database explicitly records what is known, what is probable, and what needs review.

## Viewer

Serve this folder over HTTP, then open `/viewer/`:

```sh
python3 -m http.server 8765
```

The viewer is intentionally static and dependency-free so it can be placed on GitHub Pages later. It uses dated raster references and sourced building-image galleries, not a finished geospatial overlay. Map rows marked `needs_georeferencing` or `reference_map_only` must be digitized before spatial inference. Retrospective building illustrations are labeled and must not be mistaken for contemporary photographs or measured elevations.

## Versioning and extension

Do not overwrite uncertainty with a single guessed value. Add new evidence to `sources.csv`, link it through `building_sources.csv`, and append or revise field claims in `assertions.csv`. For moved, raised, enlarged, burned, or rebuilt structures, preserve the entity and add effective-dated events rather than cloning a timeless row.

This is version 1 of an expandable city model. The next pass should prioritize georeferencing, address normalization, parcel/property versioning, and systematic extraction from contemporary directories and fire-insurance materials.
