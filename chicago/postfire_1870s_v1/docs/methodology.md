# Annual post-fire methodology

## Research design

The years 1872 through 1879 were assigned and researched independently. Every annual tranche uses the same 29-column schema and source registry. This makes annual completeness, confidence, construction flow, and review work measurable without erasing cross-year projects.

## Inclusion

Records include named or source-identifiable new construction, rebuilding after the 1871 fire, additions, conversions, relocations, structural raising, temporary buildings, major infrastructure, and distinct phases of institutional or industrial complexes. A row requires a defensible identity and at least one resolved source key.

The supplied chronology is a lead list, not evidence. City landmarks, NPS/NRHP/HABS material, contemporary directories, newspapers and trade publications, Andreas volume III, and institutional histories are used to verify or reject leads.

## Dates and events

Start, completion, and opening are separate fields and events. Opening or first directory appearance does not prove new construction. Projects that cross a year boundary retain both dates and are counted by the assigned research year separately from completion-year statistics.

## Rebuild identity

`predecessor_or_rebuild_of` preserves the historical name of a fire-destroyed or earlier building. It does not assume identical fabric, parcel, owner, or design. `building_relationships.csv` keeps name-only links unresolved until they can be joined to a specific pre-fire entity.

## Fire and code context

The 1871 and 1874 fires are discrete spatial events. A loss requires direct documentary evidence or a future property/footprint intersection with a georeferenced fire layer. `postfire_code_context` stores source-specific construction and regulatory observations; it is not a blanket claim that every building met one uniform “fireproof” standard.

## Aggregate evidence

Annual building totals, permit/value totals, and statements such as “more than” or “about” are stored in `annual_stock_estimates.csv`. They are never expanded into anonymous placeholder buildings. Geography, unit, metric, lower/upper bounds, source locator, and interpretation remain explicit.

## Maps

Every year has a dated citywide map or bird's-eye reference. Map type controls use: surveyed or guide maps can support streets, railways, boundaries, and districts after georeferencing; bird's-eye views support visual/massing research; neither proves a completion year by itself. The separate 1874 fire view is retained as an event candidate requiring spatial calibration.
