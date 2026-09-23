# Map and media audit

Status: **passed with modeling cautions**.

## Structural checks

- 9 historical map/view records cover every year 1872–1879; 1874 has both a city map and a separate fire view.
- All 9 local JPEG derivatives exist.
- Actual pixel dimensions exactly match `map_references.csv` for every file.
- Every map record has a source URL, local path, creator/credit, rights statement, map type, and georeference status.
- All local map derivatives are labeled public domain in their source metadata; institutional credits remain attached.
- `annual_city_model.csv` contains exactly 8 unique year rows and all referenced map IDs resolve.
- `city_and_land_events.csv` parses without overflow and preserves city extent, reconstruction, economic-cycle, fire, transportation, and construction-technology events separately.
- Viewer paths resolve from `viewer/` through `../maps/images/...`.

## Modeling cautions

- None of the local derivatives is georeferenced. They cannot yet support parcel intersection, exact shoreline extraction, or fire-fate inference.
- The 1879 bird's-eye and 1874 fire view are pictorial. They support visual/massing or event research, not survey geometry.
- The 1873 and 1875 Warner & Beers maps are strong annual navigation/extent references but not systematic building-footprint surveys.
- Reduced derivatives should not replace archival masters for GIS control-point work or publication reproduction.
- The carried 1872–1879 city-extent state still requires transcription/digitization of controlling legal bearings; the modern boundary must not be substituted.

No metadata correction was necessary after pixel, ID, coverage, parsing, and rights-field review.
