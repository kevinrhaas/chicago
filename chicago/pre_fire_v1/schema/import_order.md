# Import order

1. `data/sources.csv`
2. `data/buildings.csv`
3. `data/building_names.csv`
4. `data/building_sources.csv`
5. `data/building_events.csv`
6. `data/assertions.csv`
7. `data/stock_estimates.csv`
8. `data/media.csv`
9. `data/media_buildings.csv`
10. `data/media_checksums.csv`
11. `maps/map_references.csv`
12. `maps/city_extent_events.csv`
13. `maps/landform_events.csv`

Primary identifiers are text and deliberately stable. Blank values mean “not established,” never zero. The many-to-many `building_sources.csv` table is the minimum provenance join; `assertions.csv` preserves field-level claims for later conflict resolution. `media_buildings.csv` allows a single scene to depict multiple structures without duplicating the underlying media asset.

Dates use a year or ISO-like date string plus a separate precision field. Import them as text first. A later database migration can add typed lower/upper bounds after the controlled precision vocabulary is finalized.
