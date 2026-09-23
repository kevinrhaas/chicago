---
id: T-0426
title: A shop addressed on a cross street improves the lot the plat fronts elsewhere, so 24.7 m of board fence lands across the Tremont House's goods
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-04
pr: 675
claimed_by: run 9/2/2026, 11:58:23 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T20:21:32.814Z
claimed_run: null
---

## ★ THE OWNER'S RULING, 2026-09-03 (evening) — RECORDED, because the last one was lost

Asked: *"Does an improved Lake-fronting lot take a fence at its Lake frontage — L160's
engraving read literally — even when the building that improved it faces Dearborn?"*

**His answer, verbatim: "the answer is yes for this".**

So the split this ticket describes is settled, and it settles the way PR #675 already
built it — **the fence follows the LOT, the post follows the DOOR**:

- **The FENCE is right.** An improved Lake-fronting lot takes its fence at its Lake
  frontage, L160 read literally, whatever street the building that improved it faces.
  The 24.7 m on lot 7 stays. This is now a rule across all 359 committed footprints and
  not a special case for the New York Clothing Store.
- **The POST is the bug.** A hitching post belongs at the face its own door is on. Standing
  the clothing store's post on Lake Street, 49 m from its Dearborn door, with the face's
  bearing 180.5 written over the building's own 90, is wrong and is fixed rather than
  admitted.

**Why this ruling is written HERE and not only on the PR.** The owner reported that he had
already answered the triangle-budget fork "from before but it may have been lost" — and it
had been: PR #599 pointed at **T-0441** as the ticket holding that decision, and T-0441 was
never filed (there is a clean id gap between T-0440 and T-0442). A ruling that lives only in
a PR comment is a ruling the queue cannot see. This one goes in the ledger first.

**What it unblocks.** PR #675 implements exactly this reading and needs only a merge from
dev and a re-derive — its gate is red on two STALE-DERIVED failures (`register_1835.json`
not what a rebuild produces, and the resident index's attested count disagreeing with the
records), neither of which is this parcel's logic. Behind it, **PR #562 (T-0385)** parks on
`hold` waiting for this answer and can then be re-gated.


A shop addressed on a cross street improves the lot the plat fronts elsewhere, so 24.7 m of board fence lands across the Tremont House's goods.

**Acceptance:** the town's derived street furniture is no longer laid off a lot tier that
the building standing on it does not front — demonstrated at `blk_south_water_clark`, where
`new_york_clothing_store` fronts east onto Dearborn Street and today lays a hitching post
and 24.7 m of board fence on the LAKE STREET face 49 m away. The demonstration is the
renderer smoke's own check, `the goods reach the screen from the footway`, back at its dev
figure (mean 3.01, worst 58 on `dev` 2026-08-29; mean 0.19, worst 22 with the shop standing).
Whatever the rule becomes, every face it stops improving is REFUSED IN WRITING with the
bearing that refused it, and the blast radius across the other 359 committed footprints is
measured and stated before it lands — not asserted.

## What was measured, and where

Found by **T-0385/#562** while verifying the New York Clothing Store, and it is why that PR
is parked on `hold` rather than merged. `./tools/check.sh` is green on that branch; the
renderer smoke at mobile 390×780, stage 1-2, published, is not, and it is reproducible to
the digit across two runs.

**The geometry.** `blk_south_water_clark` is bounded north by South Water, south by Lake,
west by Clark, east by Dearborn. Its committed lot grid (`data/traces/vectors/thompson_lots.json`)
runs TWO tiers, north and south, and every lot fronts an east-west street — **no lot in this
block fronts Dearborn at all**, which is the same fact `docs/STREET-FACE-ADOPTION.md` reports
as "it refuses the whole of Dearborn Street, which has eighteen roofs showing it a corner side
and not one whose lot fronts it".

Lot 7 is the south (Lake) tier lot at the Dearborn end: local ENU x 661.4–686.3, y −103.1 to
−56.5, and it is **46.6 m deep**. The Chicago American puts the New York Clothing Store three
doors north of the Tremont House in Dearborn Street, which lands it against the mid-block
alley — local (677.14, −56.77), which is **0.27 m inside lot 7's northern edge** and about
34 m back from lot 7's own Lake Street frontage line. It fronts EAST, `rotation_deg: 90`.

**What `tools/generate_frontage_works.py` then does, twice, and both by the same rule:**

1. `_fence_runs` asks only whether a committed building stands inside the lot polygon —
   `_inside(b["at"], lot["polygon"])` — and lot 7 stops being "no committed building stands
   on this platted lot ... open prairie". So the south face's board fence extends from
   73.9 m to **98.6 m** along, +24.7 m, and the layer's `fence_m` goes 1669.0 → 1693.7.
2. The hitching rule reads the same containment and stands a post for this shop at local
   (678.9, −105.99) on **Lake Street**, with `"street": "lake"` and
   `"facade_bearing_deg": 180.5` — the FACE's outward normal, written over the building's own
   90. The post is 49 m from the door it is supposed to serve.

**The visible damage is the fence, not the post.** The Tremont House's south front carries the
longest group on the goods layer — four casks, an empty on its side and two cases, at
y = −101.11 — and the smoke stands a walker at (684.9, −104.3) 3.2 m off that wall to check
they read from the footway. The new fence stands on lot 7's frontage line at y ≈ −103,
**between the camera and the goods**, and the with-goods/without-goods signature collapses
from mean 3.01 / worst 58 to mean 0.19 / worst 22.

## The part that is NOT this ticket's to decide, and is why it is filed rather than fixed

Two readings are available and they are not the same repair:

- **The post is plainly wrong** and a narrow refusal would fix it: a trade takes its custom
  from a stranger off the street, so a post belongs at the face the shop's DOOR is on. A
  building whose facade bearing disagrees with the face's outward normal should be refused
  here in writing. That is contained.
- **The fence may be right.** An improved lot fronting Lake Street taking a board fence at
  its Lake frontage is exactly the first Cook County jail engraving read literally, which is
  the clause `L160` rests on, and a house at the back of a deep lot does not make the lot
  unimproved. What it collides with is a SECOND thing this dataset already does: the Tremont
  House's goods are laid on ground inside lot 7 while `tremont_house_1`'s own placement point
  (687.8, −91.4) falls 1.5 m EAST of lot 7 and improves nothing. So the pass this check has
  enjoyed on `dev` is an accident of where one origin point fell, and the fence-versus-goods
  collision was always latent.

Deciding between them changes a shared rule that reaches all 359 committed footprints, so it
wants its own run and its own before/after census — not the tail of a placement PR.

**Related:** T-0385 (found it, parked on it) · T-0416 and T-0372 (the same "is a corner side a
face?" question from the adoption side) · T-0194 and L136 (the hitching rule) · L160 (the
street-lining fence) · T-0405 (the other layer that repaints when one record is added).

---

## THE OWNER'S RULING, 2026-08-31 — THE FENCE STAYS, THE POST FOLLOWS THE DOOR

The ticket set out two readings and said the choice was the owner's because it
reaches a shared rule over all 359 committed footprints. It was put to him with
the measurement and he ruled for the first:

> **A lot that fronts a street takes its street-lining board fence at that
> frontage, whatever way the building standing on it faces.** `L160` is read
> literally — the first Cook County jail engraving shows the fence on the lot
> line, and a house at the back of a deep lot does not make the lot unimproved.

**So `_fence_runs` is unchanged and is now correct by ruling rather than by
default.** The 24.7 m the New York Clothing Store adds to lot 7's Lake frontage
is a fence that belongs there.

### The post is the other half, and it is done

A hitching post serves a stranger off the street, so it belongs at the face the
shop's DOOR is on. `EDGE_HITCH_FACE_TOL_DEG` (45 deg) now refuses a post whose
building faces more than that away from the platted face it stands on, in
writing. Measured: `dev` unchanged at 18 posts / 83 refused; PR #562 goes 18/82
to 17/83, removing exactly the post that stood 49 m from its own door.

### WHAT THIS RULING DOES NOT SETTLE, AND IT IS WHY #562 IS STILL RED

The smoke failure that parked PR #562 is **the fence against the goods**, and the
ruling keeps the fence. `the goods reach the screen from the footway` reads mean
3.01 / worst 58 on `dev` and mean 0.19 / worst 22 with the shop standing, because
the fence now stands on lot 7's frontage line at y ≈ −103, between the walker at
(684.9, −104.3) and the Tremont House's goods at y = −101.11.

The ticket already recorded why that collision was always latent and is not the
clothing store's fault: **the Tremont House's goods are laid on ground inside lot
7, while `tremont_house_1`'s own placement point (687.8, −91.4) falls 1.5 m EAST
of lot 7 and improves nothing.** One building's goods are sitting on another
lot's frontage. The pass this check enjoyed on `dev` was an accident of where
that origin point fell.

**So the remaining work is the goods, not the fence**, and it is its own ticket:
either the Tremont House's goods belong on the Tremont House's own lot, or a lot
whose frontage carries a fence may not also carry a neighbour's goods, or the
smoke's stand is measuring across a boundary it should not. None of those is
decided here.

