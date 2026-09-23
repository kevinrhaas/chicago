---
id: T-0189
title: A house on Washington is told it is 'one unit of the party-line river row'
state: done
epic: TOWN
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 385
claimed_by: run 8/26/2026, 11:45:35 PM CT
blocked_on: null
needs_bake: false
---

A house on Washington is told it is 'one unit of the party-line river row'.

**Acceptance:** the location line a visitor reads on a party-line unit names the face it
actually stands on, every committed frontage record re-derives with the corrected line, and the
gates stay green.

`tools/generate_block_infill.py` composes a frontage unit's `symbolic_location` with the literal
phrase *"standing ON the <Street> Street frontage itself, one unit of the party-line river row"*.
That was written for the South Water row, where it is true. It is now on 23 records across three
faces, including three houses on Washington Street that are 400 m from the water and one block
from a street the phrase does not name. `tools/block_faces.py`'s own docstring calls it "a
party-line **street** row", which is the vocabulary to converge on.

Cheap, but not free: it rewrites the visitor-facing prose of 23 committed records, and a
confidence-bearing note change stales nothing while a prose change stales nothing either — check
`validate.py --stale` rather than assuming, and regenerate the sidecars and the published mirror
in the same commit.
