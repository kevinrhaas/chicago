---
id: T-0075
title: Hold the 2026-08-18 owner brief as source records
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-22
pr: 304
claimed_by: run 8/22/2026, 12:24:46 AM CT
blocked_on: null
needs_bake: false
---

Hold the 2026-08-18 owner brief as source records.

The T-0055 pattern, applied to the new set. The owner supplied eleven reference images
plus a render screenshot on 2026-08-18; they are described (only described — the
binaries are not committed) in `data/sources/assets/owner_brief_2026_08_18/README.md`,
and tickets T-0062 … T-0079 consume them by that path. That citation-by-path is the
same debt T-0055 is paying for the Kinzie plate.

For each image: identify it against chicagology's plate numbering and Andreas 1884
(several are certain already — the Braunhold Green Tree and Sauganash engravings are
Andreas plates; the jail, drawbridge and Wolf Tavern engravings are the same family;
"South Water Street in 1834" is a Chicago Historical Society postcard of a retrospective
painting; the Petford Sauganash watercolour is Chicago History Museum collection), then
create or extend the matching source records in `data/sources/` with tier (5, pictorial,
retrospective — except where a record argues otherwise), **rights_status** (the CHS
postcard carries a © line; the Petford is a museum object — `check_required` where in
doubt), what each attests and what it may never drive (no coordinates, no footprints).
Update the README with the identifications, and bring the binaries in when the owner
supplies files (or public-domain scans of the same plates are located).

**Acceptance:** every image in the owner_brief_2026_08_18 README resolves to a source
record with tier and rights status — or is explicitly marked unidentified-pending with
what was searched — and the README carries the identifications. Gates green.

**Links:** owner_brief_2026_08_18 README · T-0055 (the pattern, and the Kinzie sibling) ·
prefire_views_kevin_2026_08 README.
