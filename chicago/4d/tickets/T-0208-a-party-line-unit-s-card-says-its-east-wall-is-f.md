---
id: T-0208
title: A party-line unit's card says its EAST wall is fixed by the WEST end of the run
state: done
epic: META
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-26
closed: 2026-08-27
pr: 410
claimed_by: run 8/27/2026, 2:34:22 PM CT
blocked_on: null
needs_bake: false
---

A party-line unit's card says its EAST wall is fixed by the WEST end of the run.

**Acceptance:** the position note on every committed party-line unit describes the wall the
anchor actually fixes, all frontage records re-derive with the corrected wording, and the gates
stay green.

`tools/generate_block_infill.py`'s `FRONTAGE_NOTE` says "its east wall is fixed by {anchor}",
which was written for the South Water runs — those anchor on the EAST end of the face and pack
west, so the east wall is the anchored one and the sentence is true. T-0079 opened the west
anchor for a corner lot that builds to the corner, and on a west-anchored run the generator sets
`east = along_min + clear_m + width`: the wall standing `clear_m` off the side lot line is the
**west** one. The card then reads "its east wall is fixed by the west end of the run's own
frontage, 1.5 m clear of the side lot line at that end", which invites a reader to put the east
wall against the west side line.

Found while fixing T-0189, which is the same class of fault in the same template — prose written
for one face printed verbatim on another — and left out of that unit deliberately: this one makes
no claim about 1835, only about the run's own machinery, so it did not belong in a change about
what a visitor is told the town was. Cheap, but it rewrites the visitor-facing prose of the same
23 records: regenerate the records, the sidecars and the published mirror in the same commit, and
check `validate.py --stale` rather than assuming a prose change stales nothing.
