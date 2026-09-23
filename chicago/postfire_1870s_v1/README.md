# Chicago Rebuilds — 1872–1879 database v1

This package extends the pre-fire Chicago database into eight independently researched post-fire years. It records named or otherwise source-identifiable construction, reconstruction, additions, conversions, temporary buildings, infrastructure, and complex phases while preserving start, completion, and opening as different events.

## Core files

- `data/buildings.csv` — normalized annual building/project records.
- `data/building_events.csv` — construction starts, completions, openings, and losses.
- `data/building_relationships.csv` — predecessor and rebuild links awaiting or carrying entity resolution.
- `data/potential_cross_year_matches.csv` — exact normalized-name candidates that require phase/duplicate review before entity merging.
- `data/sources.csv`, `data/building_sources.csv`, and `data/assertions.csv` — provenance from record to field claim.
- `data/annual_stock_estimates.csv` — aggregate construction/stock evidence that cannot honestly become named rows.
- `maps/map_references.csv` — one annual map for every year plus the 1874 fire layer.
- `maps/annual_city_model.csv` — effective-year city/land/transport/disaster interpretation and GIS instructions for every year.
- `viewer/index.html` — static annual explorer.
- `chicago_postfire_1870s.xlsx` — formatted multi-sheet companion for review and handoff; CSVs remain the import source of truth.
- `docs/statistics.md` and `docs/quality_report.md` — generated coverage and validation results.
- `docs/research_gaps.md` — explicit completeness limits and the next-pass archival queue.
- `research/source_scans/` — selected public-domain Andreas pages supporting aggregate rebuilding and permit statistics.
- `research/annual_tranches/` and `docs/annual_notes/` — independently researched year files and full handoff notes.
- `research/excerpts/` — the shared year schema, targeted Andreas statistics excerpt, and municipal landmark API snapshot used during research.

## Scope rule

Each year is a research tranche, not merely a completion-year filter. A building begun in 1874 and completed in 1876 can appear in the 1874 tranche as a documented start while retaining its later completion. Conversely, occupancy-only evidence is labeled and reviewed rather than silently converted into a construction date.

Anonymous annual building totals remain aggregate evidence. They are valuable denominators but do not supply names, owners, addresses, architects, or footprints.

## Viewer

Serve the package over HTTP and open `/viewer/`:

```sh
python3 -m http.server 8765
```

Map images are practical derivatives. Retrieve archival masters from the source URL before georeferencing.
