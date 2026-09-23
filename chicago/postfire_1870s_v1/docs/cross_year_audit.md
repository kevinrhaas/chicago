# Cross-year audit — 1872–1879

Status: **passed after targeted corrections**.

## Structural and provenance checks

- 8 annual building files use the exact 29-column header; 8 annual source files use the exact 12-column header.
- 312 annual records have unique IDs, controlled confidence/review values, and no `DictReader` overflow.
- All source keys resolve after normalizing legacy pipe separators.
- Two 1876 source-key collisions were removed by distinguishing the 1876 Sinai and Moody institutional sources from different 1875 resources.
- Four 1874 multi-source fields were migrated from pipe to semicolon delimiters.

## Cross-year phase matches

Twelve exact normalized-name groups span multiple years. They are legitimate phase candidates rather than safe duplicates: Briggs House II, DuPont-Whitehouse House, Grace Methodist Episcopal Church, Grand Pacific Hotel II, James Ward Public School original section, Lakeside Building, LaSalle Building, Palmer House II, Sherman House III, Tremont House IV, Washington Block, and William Waller House.

The package retains both annual observations and writes them to `potential_cross_year_matches.csv`. Database importers should resolve them into a stable building entity plus multiple project/event observations only after comparing site, owner, construction fabric, and source chronology.

## Pre-fire name continuity

Exact-name checks against `pre_fire_v1` surfaced St. Joseph's Catholic Church, Second Presbyterian Church, and Matteson House. These are not surviving unchanged pre-fire fabric. Predecessor text is present or was added so later entity resolution can express destruction, temporary replacements, new sites, and rebuilt institutions without merging physical buildings by name alone.

## Confidence corrections applied

Three high-confidence rows relied solely on Tier 3 compilations and were downgraded to medium with review flags:

- Perry H. Smith Mansion (1877)
- Interstate Exposition Building temporary Field & Leiter conversion (1877)
- Academy of Music II (1878)

## Pending entity work

- Resolve all 164 predecessor/rebuild name statements against stable pre-fire and post-fire entity IDs.
- Decide whether each exact-name phase group becomes one building with multiple events, one complex with components, or separate successor buildings.
- Preserve grouped row-house, hospital, stockyard, brewery, school, bridge, and rail records until component-level sources support decomposition.
- Retain the quarantined Fullerton bridge identity conflict and any occupancy-only events as review records; do not force a completion interpretation.

No annual row was deleted merely to improve counts, and no uncertain chronology was resolved by guesswork.
