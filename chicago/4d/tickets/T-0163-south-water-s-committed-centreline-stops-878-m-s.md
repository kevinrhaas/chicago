---
id: T-0163
title: South Water's committed centreline stops 878 m short, and it is the only thing left blocking a new platted block
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-24
pr: 358
claimed_by: null
blocked_on: null
needs_bake: false
---

South Water's committed centreline stops 878 m short, and it is the only thing left blocking a new platted block.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by **T-0028**, whose own premise turned out to be exhausted: there is **no next anonymous
block to open**. Re-deriving `data/reconstruction/1835_665_roof_programme.json` with
`tools/reconcile_665.py` on 2026-08-23 produced no diff, so the committed schedule is current, and
it says every platted block under committed street control is now `at_capacity`, `open` (headroom
on lots that already stand — T-0143's densification parcel, not T-0028's) or `reserved` (the public
square, T-A16).

**Two platted blocks are left and both are `gated` on the same thing:**

| block | lots | capacity | headroom | `waiting_on` |
|---|---|---|---|---|
| `blk_south_water_clinton` | 8 | 31 | 27 | South Water's committed centreline stops **878 m short** |
| `blk_south_water_market` | 8 | 31 | 27 | the same |

Bounded north by South Water, south by Lake, west by Clinton, east by Canal — the West Side pair
opposite the forks. Their `lots_note` says the eight lots are *assumed from the emitted blocks' own
subdivision; the block itself is not generated, so it has no measured geometry* — so this is not a
recipe problem and no adoption rule is waiting on a decision. **The block generator has nothing to
stand on.**

The programme's own coverage statement says the same in one line: *"32 of the 331 remaining roofs
stand on ground this project has already surveyed, platted and modelled. The other 299 have nowhere
to go until street control, terrain and hydrology reach them. The binding constraint on the
665-roof programme is coverage, not recipes."* Those 32 are the `open` blocks' headroom. **Extend
the control and 54 roofs of platted, schedulable ground open at once** — the largest single unlock
left in the programme.

**Acceptance:** South Water's committed centreline reaches the Clinton–Canal blocks from control
this project will accept — traced, sourced and re-derivable by `tools/check.sh` like every other
street — or the reason it cannot be is recorded and the two blocks are marked with it. Either way
`reconcile_665.py` re-derives and the two blocks stop reading `gated` on a blocker nobody owns.
ROADMAP **S9** records the street control as owed; this names what it is now costing.
