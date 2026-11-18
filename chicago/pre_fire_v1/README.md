# Chicago Before the Fire — research database v1

This package is a sourced, importable foundation for modeling Chicago's built environment from the earliest documented settlement through the Great Chicago Fire of October 1871. It combines independently researched period tranches, field-level provenance, aggregate stock estimates, dated historical maps, and a static year explorer.

## Start here

- `viewer/notebook.html` — primary-source field notebook: 203 observations from 23 pages in three contemporary books, with historical locations, dates, quantities, scan links and eight proposed scene studies.
- `data/field_notebook_1871.json` — canonical observations, source-page register, book-level rights/limitations, source-image hashes, scene studies and revisions to the earlier pass.
- `viewer/notebook-reading.html` — complete static reading edition, including sources and scene studies; works without JavaScript. `viewer/field-observations-1871.csv` and `viewer/field-notebook-1871.json` provide portable exports.
- `viewer/research.html` — the 1871 preparation dossier: searchable evidence, scene-by-scene lessons, and rendering acceptance criteria.
- `data/research_1871.json` — canonical research cards with claim-level sources, locators, access status, limits, and next actions; kept separate from building records until entity/attribute evidence is resolved.
- `docs/research_1871.md` — generated full-text dossier; `docs/rendering_year_audit.md` — detailed audit of the other modeled scenes and all Atlas periods.
- `viewer/year-coverage.csv` — generated coverage for every year 1674–1871 using the viewer's inclusive year rule, not a census or exact-day presence ruling.
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

For the 1871 research expansion, edit `data/research_1871.json`, then run:

```sh
python3 tools/build_research.py
python3 tools/build_research.py --check
python3 tools/build_notebook.py
python3 tools/build_notebook.py --check
bash tools/publish.sh
bash tools/publish.sh --check
PW_EXECUTABLE=/usr/bin/chromium node tools/smoke_research.mjs
PW_EXECUTABLE=/usr/bin/chromium node tools/smoke_notebook.mjs
```

The research build validates claim/source integrity and regenerates the viewer JSON, full Markdown dossier, and annual coverage CSV. `publish.sh` carries the new viewer files into the existing `site/pre-fire/` mirror. It is a local publishing step, not a live deployment: the repository's existing owner-promotion workflow controls production. No 1871 3D scene or measured city geometry is created by this research expansion.

For field observations, edit `data/field_notebook_1871.json`. The notebook build checks unique IDs, observation-to-page and page-to-book references, scene/dossier references, quantities and local scan SHA-256 hashes, then regenerates JSON, CSV and the reading edition. Printed page numbers differ from archive scan indices; retain both. Eleven unmodified original page scans live under `media/research/`, with publication rights and per-page download URLs recorded in the notebook. They are document evidence, not building photographs, and are deliberately separate from the building-image registry.

The second pass resolves selected acquisition leads into readable evidence: directory locations and occupations, nominal 1871 horsecar intervals, the July 15 canal opening, named congregations and schedules, reported park work, and street-level utilities. A directory listing, scheduled activity, reported completion, measured count and proposal remain distinct evidence types. Transcriptions may normalize punctuation or expand abbreviations; original scans control. Municipal fiscal-year dates are not October 8 inspections. Source bibliographic metadata can be wrong: the ninth Board report's title page is for the fiscal year ending March 31, 1870, despite an 1861 archive date.

“Documented” means the cited source supports that statement; it does not automatically mean primary evidence, a measured footprint, or exact-day occupancy. “Inferred” marks a reconstruction proposal; “open” marks an unresolved question. Access status separately records a read source, catalog-only inspection, or a lead. Do not promote a catalog title into a visual observation. New image assets require their own rights/provenance records.

Do not overwrite uncertainty with a single guessed value. Add new evidence to `sources.csv`, link it through `building_sources.csv`, and append or revise field claims in `assertions.csv`. For moved, raised, enlarged, burned, or rebuilt structures, preserve the entity and add effective-dated events rather than cloning a timeless row.

This is version 1 of an expandable city model. The next pass should prioritize georeferencing, address normalization, parcel/property versioning, and systematic extraction from contemporary directories and fire-insurance materials.
