---
id: T-0282
title: The ceiling declaration cannot see the shrub stratum, and no card a visitor opens carries it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 455
claimed_by: run 8/28/2026, 6:02:55 AM CT
blocked_on: null
needs_bake: false
---

The declaration T-0019 landed on 2026-08-28 (PR #449) states every FORB layer the lattice
ceiling binds — nine of them. It cannot see the SHRUB stratum, which `flora.js` deals through the
same `shareOf` against the same 0.34602 plants/m² ceiling, and `z06_dense_forest`'s shrub layer is
ON it: 0.4035 /m² recorded against a ceiling of 0.346, drawing 85.8 % of its own record. ROADMAP
K54 named that community as the one whose shrub density reaches the clamp; the gate that exists to
catch a layer joining the clamp in silence is blind to a quarter of the lattice — `shrubShareWet`
and `shrubDensityWet` are not exported from `flora.js` at all.

Second half, and it is the visible one. The debt now lives in `tools/forb_clamp_baseline.json` and
`docs/STATUS.md` — where a reviewer reads, not where a visitor does. A visitor standing in the
dense forest is looking at half a per cent of the flowers the research put there with no way to
find that out. [[T-0281]] proposes the full "What grows here" panel section and is a bigger unit;
this one puts the clamp in the register that already ships to the Evidence panel.

**Acceptance:** the declaration covers every (community, stratum, side) the ceiling binds, with
`--gate` failing on an undeclared shrub layer exactly as it does on a forb one; and
`docs/LIBERTIES.md` carries an entry stating the ceiling, the layers on it and the share of its own
evidence each one draws, compiled into `data/liberties.json` and published.
