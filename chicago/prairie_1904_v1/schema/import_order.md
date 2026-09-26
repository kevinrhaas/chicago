# Portable research schema

Load `sources.csv`, `buildings.csv`, `building_events.csv`, `building_sources.csv`, `assertions.csv`, `map_frontages.csv`, `occupancy_candidates.csv` and `address_crosswalk.csv`. Source IDs in this atlas resolve in its own `data/sources.csv`; 4D `data/sources/` requires an explicit import before model ingestion. They are not silently treated as existing 4D IDs.

`library.json` contains the same browser-facing evidence plus full nested event/candidate lists. CSV nested lists are JSON strings. All dimensions are feet when stated; unknown is null/blank, never zero. Building IDs identify research records, not surveyed cadastral parcels. Addresses retain historical spellings/aliases. Crosswalks are candidate matches by number, never proof of identity. Preserve source IDs, dates, locator and confidence on any import.
