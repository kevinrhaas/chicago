---
id: T-0633
title: Position a business from its later documented address: the back-projection rule, the grade it earns, and the businesses it places
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 784
claimed_by: run 9/4/2026, 8:57:02 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T14:04:19.441Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33875882469
---

Position a business from its later documented address: the back-projection rule, the grade
it earns, and the businesses it places.

**Filed on the owner's instruction of 2026-09-04, and this is his mechanism in his own
words**: *"so locations matter so capture those too of course, like there are business
references that have addresses later and while we don't have that in 1835, you might use
a documented address from later to position the business where you have limited other
information or it could contribute, stuff like that."*

## Why there is something to position

20 of 825 households carry a real `lives_at`; 50 carry a real `works_at`. The 1835 record
prints trades far more often than it prints addresses — a newspaper notice names a firm
and a street, rarely a door. The later directories print doors:

- `norris_1844_advertiser_crosswalk_1835.json` — 14 matched proprietors, and every card
  carries `trade_1844` **and** `address_1844` (e.g. *B. S. Morris, attorney and counselor
  at law, office Clark street, opposite City Hotel*).
- `norris_1844_crosswalk_1835.json` — 39 matches that could carry an address.
- `fergus_1843_crosswalk_1835.json` — 46 matches that could carry an address.

That is **99 adjudicated matches with a documented later address** against a town where
20 households have any address at all.

T-0632 writes those addresses onto the cards. This ticket is the half that puts them on
the ground, and it is the harder half, because 1844 is not 1835 and the town moved.

## The rule this ticket has to write down before it places anything

A later address may position an 1835 business **only** when all of these hold, and the
record says which clause it used:

1. The 1835 record attests the business existed in 1835 (this ticket never mints a
   business out of a later directory).
2. Nothing better places it. An attested 1835 placement always wins; a newspaper's *"three
   doors north of the Tremont House"* always wins over a directory's 1844 door.
3. The address resolves onto the **1835** street grid — the street existed under that name,
   in that place, on the scene date. Streets renamed or platted after 1835 disqualify the
   reading outright, and the refusal is recorded rather than dropped.
4. The placement is graded `reconstructed` at best and its note says, in plain words, that
   it is a later address read backwards and by how many years.

`data/liberties.json` is where a standing back-projection liberty belongs if this becomes a
standing rule — T-0404 already records that 33 documented businesses stand on a backdating
liberty that LIBERTIES.md carries none of, so this ticket and that one meet.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The rule above is written into the repo where a later run will find it — the liberties
   record and the placement layer's own docs — before any business is moved.
2. Every one of the 99 address-bearing matches is put through the rule and gets one of
   three outcomes, all recorded: **placed** (with the clause and the grade), **refused**
   (with the reason — usually 2 or 3 above), or **already better placed**.
3. Counts stated: how many businesses gained a position, how many were refused, and the
   `lives_at`/`works_at` real-value counts before and after.
4. No attested placement is overwritten by a later address. Assert it, do not claim it.
5. Anything this places renders — the scene shows it, and the card says how it got there.
