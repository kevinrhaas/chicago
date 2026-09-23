---
id: T-0316
title: The 665-roof deal puts a large river warehouse on an inland platted block, and the block generator cannot build one
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 520
claimed_by: run 8/29/2026, 3:10:03 AM CT
blocked_on: null
needs_bake: false
---

The 665-roof deal puts a large river warehouse on an inland platted block, and the block generator cannot build one.

**Acceptance:** `tools/reconcile_665.py` no longer deals F3 — the large river warehouse — to a
platted block bounded by four platted streets, and the three F3 roofs the crosswalk schedules are
either dealt to the wharf and landing ground that can carry them or held with a stated reason. The
demonstration is a re-derive with the deal moved and `tools/measure_family_deal.py` still green,
NOT a new refusal in the block generator: that refusal already exists and is the symptom.

Found by **T-0028** on 2026-08-28 while opening `blk_lake_franklin`, the first platted block this
programme has opened since 2026-08-23.

**What the deal did.** The schedule dealt that block four roofs — A1, D1, D5 and **F3**. F3 is the
"Large river warehouse", `target_roofs` 3, `phase1_instantiated` 0. Its crosswalk entry makes water
access a precondition of the FORM, not a preference: `required_variant` is
`warehouse_river_large`, the variants line reads *"multiple cargo doors; landing apron; sparse
glazing"*, and the assumption note reads *"Landing apron and cargo-door arrangement must follow
site access and cannot extend into water or duplicate a counted pier."*

**What the generator can do about it: nothing.** `tools/generate_block_infill.py` authors no
coordinates. Every metre comes from a committed lot polygon inside a block bounded by four platted
STREETS. The landing and wharf ground of the main stem lies outside that grid, beyond South Water
and Market, and is placed by `tools/generate_river_wharves.py` against the committed bank. Sampled
against the committed heightfield `e1834_harbor_cut`, the nearest water to `blk_lake_franklin`'s
boundary is **134 m** away. An F3 massed there is a river warehouse the river does not reach: its
cargo doors open onto a residential street and its landing apron would have to cross a public one.

**What T-0028 did instead, and why it is a stopgap.** F3 is now in the generator's
`REFUSED_FAMILIES`, so a recipe meeting the slot must DEFER it in `deferred` with a stated reason
rather than reach for a shape — and `blk_lake_franklin` does exactly that, building 3 of its 4
dealt roofs. That keeps the roof on the books instead of dropping it, which is the whole point of
the deferral mechanism. But it treats a fault in the DEAL as a fault at the block: every future
platted block dealt an F3 will now defer it, and the three warehouse roofs will accumulate as
deferrals nobody is scheduled to build. The right fix is upstream — the same shape as **T-0213**,
which weighted the trade families onto the business front rather than teaching each block to
refuse them.

**Note for whoever takes this.** F3 is also absent from the block generator's `FUNCTIONS` table
and from the `block` arm of `tools/measure_family_deal.py`'s report, so the deal was reaching for a
family the parcel shape has never been able to name. Check F1, F2 and F4 for the same question
while you are there: F4 ("Lumber shed") carries the same site logic and F2 ("narrow two-story
warehouse") may not.

Related: **T-0028** (found it), **T-0213** (the deal fix this should be shaped like),
**L203** (the liberty that records the deferral).
