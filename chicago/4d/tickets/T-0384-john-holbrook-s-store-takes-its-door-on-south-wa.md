---
id: T-0384
title: John Holbrook's store takes its door on South Water Street, one door from Dearborn
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: T-0306
opened: 2026-08-29
closed: 2026-08-30
pr: 598
claimed_by: run 8/30/2026, 2:11:39 AM CT
blocked_on: null
needs_bake: true
---

John Holbrook's store takes its door on South Water Street, one door from Dearborn.

Piece 2 of 5 of **T-0306 — The American names six Chicago storefronts with usable placements and none of them is standing in the model yet**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** either John Holbrook stands at the address the paper prints for him, or
the ONE question below is answered and the answer is recorded. Seating him on a roof the
street-face policy has not freed, or raising him a building the policy says a street-only
business does not get, are the two outcomes this ticket refuses.

## The blocker this ticket was written with is STALE. Re-derived on `dev` at c658a7b6, 2026-08-29

This ticket said the piece was held behind *"may a platted business-front lot carry TWO
documented storefronts standing at the street?"* — the question PR #514 asked and is
parked on `hold` carrying. **That question is no longer the one in the way**, and a run
that answers it still cannot place Holbrook. Two things moved under it on the same day:

**1. The register no longer reads this advertisement as a placement.** `business_john_holbrook`
in `data/research/newspapers/register_1835.json` today reads `action: street_only`,
`anchor.kind: street`, over the verbatim *"[on South] Water st., one door from Dearborn
street"*, with the note *"The anchor is a reach of dearborn and names nothing narrower."*
PR #514 read the same words the other way — as an ordinal off the Dearborn corner — and
raised a 30 × 25 ft frame shop 3.048 m east of the American's printing office. **Both
readings are of one printed line and the register's is the committed one.**

**2. The owner ruled on 2026-08-29 what a `street_only` business gets** (T-0354,
`docs/STREET-FACE-ADOPTION.md`, L212): *adopt a reconstructed roof already standing on
that street face and attach the business to it* — **nothing new is built, and every
adoption declares `lot: null` and `claims_lot: false`.** So under the register as
committed, Holbrook never seats on a platted lot at all, and the two-storefronts-on-one-lot
question this ticket names is **moot for him**: `data/research/newspapers/street_face_adoptions.json`
refuses him for a different reason entirely —

> `every roof on the face is spoken for` — *19 roof(s) front this street: 5 are a named
> household's dwelling, 5 are yard buildings the parcels dealt behind a lot, and 9 are
> already adopted by a better-evidenced business.*

He is one of **seven** South Water advertisements short purely on supply, beside A. Filer
& Co., A. Garrett, E. L. Thrall, J. Curtiss, the New Store at Water and Clark, and the
auction and commission merchant at `[uncertain: DATID GAD]`.

**The old question was measured anyway, since a stale blocker is only shown stale by
arithmetic.** Derived from the committed plat and structures through
`tools/plat_occupancy.py`, no figure authored:

| | |
|---|---|
| business-front lots dealt town-wide | **19** |
| — carrying a documented building | **5** |
| — where the 2026-08-27 clause is LIVE (the store stands alone, the run may still take the lot) | **2** |
| — where it is already OFF (the run now stands there too, so the lot is exhausted) | **3** |
| register businesses anchored on any of those five documented buildings | **0** |

The three where it is off are `blk_south_water_dearborn` lot 0
(`chicago_american_office` + `…_a3_06`), `blk_south_water_wells` lot 0 (`h_jones_store` +
`…_a3_08`) and lot 2 (`carpenter_south_water_store` + `…_d1_05`). With the block's own run
excluded — which is how `generate_block_infill.py` asks the question — Dearborn lot 0
holds `chicago_american_office` alone and IS shared, so the run gets its lot today. Adding
a second documented store makes `len(holders) != 1` in
`plat_occupancy.shared_business_fronts`, the clause switches off, the run is refused its
lot and `check.sh`'s platted-parcels step goes red. That is exactly the red PR #514
reported, and it is reproducible — **but nothing in the corpus is waiting on it: zero
register businesses anchor on any of the five.** Widening that clause today would unblock
nothing, Holbrook included.

## The question, and it is one line

> **Does *"one door from Dearborn street"* place a store, or is it a street and nothing
> narrower?**

- **A street and nothing narrower** — the register's committed reading. Then Holbrook is a
  `street_only` business, he is owed a South Water roof and there is not one free, and this
  ticket waits on **T-0375** (South Water's reconstructed roofs are all a labourer's).
  `adopt_street_faces.py` re-derives on every commit, so **the first fronting roof T-0375
  adds seats him automatically, with no further ruling and no work on this ticket.** PR #514
  is then superseded: a street-only business does not get a building raised for it.
- **An ordinal off the corner is a placement** — PR #514's reading. Then the register's
  `anchor.kind` for this advertisement is wrong and must be corrected at the source, the
  side of Dearborn is still unstated and stays `inferred` on the record, and the
  two-storefronts-on-one-lot clause DOES then need widening — for this one store, and for
  nothing else in the corpus today.

The advertisement is `chicago_american_1835_06_13`, *"South Water street, one door from
Dearborn"*, printed 10 June to 12 August 1835.

**Related:** T-0306 (parent) · T-0354 / `docs/STREET-FACE-ADOPTION.md` / L212 (the ruling
that moved this) · T-0375 (the roof that would seat him without any ruling at all) ·
T-0416 (the other three storefronts the same policy refuses) · PR #514 (`hold`, built and
baked against the superseded reading)

---

## THE OWNER'S RULING, 2026-08-30 — READ IT AS AN ORDINAL OFF THE CORNER

Asked whether *"one door from Dearborn street"* places a store or is a street and
nothing narrower, the owner chose:

> **Read it as an ordinal off the corner.**

So *"one door from Dearborn"* is a NARROWER claim than *"on South Water Street"*:
it counts doors from a named corner, which is a position along a face and not
merely the face. **The register's anchor is therefore wrong at the source, and
PR #514's reading is the right one.**

**What follows, and the two things that must not be over-read.**

- Holbrook does **not** fall to the street-face policy. Under it he would have
  taken a standing South Water roof and never a new building — and South Water
  has none free, so he would have waited on T-0375 indefinitely. The ordinal
  reading is what lets him be placed at all.
- An ordinal is **still not a lot.** "One door from the corner" fixes a position
  in a sequence along a face; it does not name a platted lot and may not claim
  one. The same limit the street-face ruling carries applies here.
- **The door count is evidence; the metres are not.** How far one door is from
  the corner is a reconstruction, and the record says so — the source gives an
  ordinal, and turning it into a distance is this project's arithmetic.

**The blast radius is small and was measured before the ruling:** nothing else in
the corpus turns on it — **0 register businesses anchor on any of the 5
documented buildings holding a business-front lot**. So this corrects one anchor
and does not cascade.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The register's anchor for Holbrook is corrected at the source, and the ordinal
  reading is written into the extraction/claim vocabulary so the NEXT "n doors
  from" advertisement is read the same way without re-deciding.
- The placement claims a position on a face, never a lot, and a gate proves it.
- The metres between doors are recorded as this project's reconstruction, with
  the rule that produced them.
- PR #514 is either merged or superseded explicitly — it must not be left open
  as a parked branch whose reading has since been ratified.
- A sweep says how many other corpus claims use an "n doors from" form and are
  now readable; if there are none, that is stated.
