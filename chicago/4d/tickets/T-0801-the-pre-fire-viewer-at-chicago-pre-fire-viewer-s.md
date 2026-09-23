---
id: T-0801
title: The pre-fire viewer at /chicago/pre-fire/viewer/ shows 1834 through Hathaway only: put the Wright sheet beside it as the year's second view, with its provenance row, its checksum, and the mirror re-copied
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-13
pr: 1264
claimed_by: run 9/13/2026, 1:34:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T18:55:21.339Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34774857229
---

**The owner, 2026-09-05:** *"can you add a ticket to update https://custom.polecat.live/chicago/pre-fire/viewer/ with that map."*

## What the viewer does today

`chicago/pre_fire_v1/viewer/` is the static research viewer: `app.js` picks the map nearest the
chosen year from `data.json` and offers every map of that `reference_year` as a *Map/view* variant.
`data.json` is regenerated from the CSVs by `tools/build_data_json.py` (`--check` fails if stale).
For **1834 it offers one view — Hathaway** (`MAP-1834-HATHAWAY`). The Wright sheet is in
`maps/images/1834-wright-map.jpg` but has **no row in `map_references.csv` and no row in
`image_checksums.csv`**, so the viewer cannot see it, and the published mirror at
`site/chicago/pre-fire/` (a hand copy — its last touch was T-0350; there is no publish script for
it) holds 14 images to the source's 15.

## The ask

1. **A `MAP-1834-WRIGHT` row** in `map_references.csv` in the shape of the Hathaway row: title
   *Chicago, drawn by Jas. S. Wright according to survey, 1834*; creator J. S. Wright; map type
   *manuscript survey*; coverage the Original Town, Wabansia, Kinzie's Addition, the School Section
   and the harbour; `georeference_status` = georeferenced in this project (the BPL copy carries the
   GCPs — cite `chicago/4d/data/traces/gcp/wright_1834_gcps.json`); `source_url` the National
   Archives / Historic Urban Plans provenance from the sheet's own caption, with the BPL Leventhal
   item as the open-rights sibling; `width_px,height_px` 5050,6628; a rights statement that is
   TRUE of this reproduction (the National Archives original is public domain; the Historic Urban
   Plans print is a reproduction — say which is being shown); `reliability` high; notes carrying
   the caption's *"two portions are missing"* sentence.
2. **A checksum row** in `image_checksums.csv` (sha256, path, map_id), the same registration
   T-0787 makes on the 4d side — the two must agree.
3. **Regenerate `viewer/data.json`** with `build_data_json.py`; `--check` green.
4. **Re-copy the mirror** `site/chicago/pre-fire/` from `chicago/pre_fire_v1/` — viewer, maps,
   media — so the published page shows it; and note in the PR that the mirror has no publish step,
   which is why it was a map behind.
5. Selecting 1834 in the viewer then offers *two* views; Wright is the default because it is the
   survey and Hathaway the derivative — or say why not.

**Acceptance:** the live viewer at 1834 offers the Wright sheet with its provenance line,
`build_data_json.py --check` and the viewer's `smoke.mjs` are green, the checksum row matches the
file, and the mirror equals the source tree.
