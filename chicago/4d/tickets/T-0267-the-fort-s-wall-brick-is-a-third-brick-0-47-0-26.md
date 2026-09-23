---
id: T-0267
title: The fort's wall brick is a third brick, 0.47/0.26/0.20 against the sheet's 0.45/0.23/0.17
state: done
epic: RENDERING
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 498
claimed_by: run 8/28/2026, 7:59:21 PM CT
blocked_on: null
needs_bake: true
---

The fort's brick walls are painted a brick the sheet does not hold.

`generators/archetypes/fort_structure.py::WALL_RGBA["brick"]` is **0.47 / 0.26 / 0.20**
linear. `generators/common/materials.py::CHIMNEY_BRICK` — the town's one brick, read off
the Petford watercolour and moved into the sheet by T-0008 so that there would be exactly
one — is **0.45 / 0.23 / 0.17**. About 13 % apart in linear green and 18 % in blue.

Found while T-0137 put the fort's STACKS on the sheet's brick. That parcel deliberately
did not touch the walls: it moves two committed masters (`fort_dearborn_commandants_quarters`
and `fort_dearborn_magazine`, the only two attested-brick buildings in the dataset) and it
is a different argument from the one about flues.

This is the same complaint as `docs/RESEARCH/materials.md` §2.3 and R-W2a finding 4 — a
town painted by generators sharing no palette splits visibly — and it is the same shape as
**T-0138**, the placeholders' `#89503F`, which converged onto the sheet on 2026-08-28.
With that one closed this is the LAST brick in the town that is not the sheet's.

**What has to be decided rather than assumed:** whether the fort's 1816 brick SHOULD be
the town's 1833 brick. There is an argument that it should not — different clay, different
decade, a wall rather than a flue — but if it is kept apart that has to be stated on the
record as a claim, not left as an undocumented archetype-local constant. Either answer is
fine; the current state, which is neither, is not.

**Acceptance:** the fort's brick either comes from the sheet, or the sheet carries a second
brick row with the argument for why the fort's is different. Both committed masters
rebaked, `tools/check.sh` and the smoke green, and the before/after values recorded.

**Links:** T-0137 (the stacks, which took the sheet's brick) · T-0138 (the placeholders'
third brick) · `docs/RESEARCH/materials.md` §2.3 · `docs/RESEARCH/chimneys.md` §6.
