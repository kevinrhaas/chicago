# Annual post-fire research schema (1872–1879)

Each year is researched as an independent tranche and later normalized into the longitudinal Chicago database.

## Building/event CSV

Exact column order:

`year_record_id,canonical_name,alternate_names,year_started,year_completed,completion_precision,year_opened,year_demolished,demolition_precision,demolition_cause,status,address_historical,address_modern,latitude,longitude,building_type,original_use,architect_or_builder,owner_or_developer,structural_system,stories,height_ft,construction_or_event_type,predecessor_or_rebuild_of,postfire_code_context,notes,source_keys,confidence,needs_review`

Rules:

- Include a structure when it was completed in the assigned year, or when a distinct, materially documented construction/reconstruction phase occurred in that year.
- Retain start-year projects completed later, but do not count them as completed in annual statistics.
- Separate new construction, reconstruction, addition, relocation, raising, conversion, temporary building, infrastructure, and complex phases through `construction_or_event_type`.
- Use `predecessor_or_rebuild_of` to connect replacements to pre-fire identities without assuming the same physical fabric.
- Record occupancy-only evidence as such and flag it for review; opening is not automatically construction.
- Every row must have one or more resolvable source keys. Do not use the supplied chronology as sole evidence.
- Separate multiple `source_keys` with semicolons; the normalizer also accepts legacy pipe separators during this tranche migration.
- Preserve conflicts and unknowns. Never manufacture ordinary-building identities from aggregate permit or annual-construction totals.

## Source CSV

Exact column order:

`source_key,title,author,publisher,publication_date,url,source_type,reliability_tier,locator,accessed_at,rights_notes,notes`

## Notes

Each annual notes file must include scope, methods, validation results, completion/event counts, confidence counts, review flags, source limitations, annual stock/construction-flow evidence, map and media candidates with rights, and the next research queue.
