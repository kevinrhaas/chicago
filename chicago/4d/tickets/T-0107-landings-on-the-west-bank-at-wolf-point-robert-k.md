---
id: T-0107
title: Landings on the west bank at Wolf Point: Robert Kinzie's store
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-24
pr: 365
claimed_by: run 8/24/2026, 9:52:37 AM CT
blocked_on: null
needs_bake: false
---

Landings on the west bank at Wolf Point: Robert Kinzie's store.

**Salvaged from PR #258** — the T-0062 branch that was superseded by #259. The owner
read the two side by side and said not to reverse work that is functional, and he was
right that something was in the closed one: **a landing on the WEST bank at Wolf Point,
serving Robert A. Kinzie's store.** #259's rule stated a reconstructed `dock` on five
*South Water* merchant records only, so the west bank was out of its scope by
construction. Dev today draws four landings — Jones's, J. H. Kinzie's, Kinzie & Hunter's
warehouse, Newberry & Dole's — and refuses three east of the traced bank's end (T-0106).
**Neither fork's west bank is considered at all.**

The candidate is strong, and the record argues the case itself
(`data/structures/robert_kinzie_store.json`): Robert A. Kinzie, Indian trader, a
storehouse at Wolf Point "dealing in groceries and Indian goods", placed on the west bank
south of Wentworth's tavern, **facing due east onto the water** — and its own position
note gives the reason in as many words: *"a storehouse trading goods off canoes has a
positive reason to face the landing."* A store that faces the water to take goods off
canoes is exactly what T-0062's trade rule claims a landing for.

Extend the wharf rule's candidate set to the west bank and the North Division shore
rather than hand-placing a deck — same shape as T-0062: a rule about trades, not four
edits. Two things the closed branch learned there, worth not rediscovering:

- **The bank bends at Wolf Point**, and a standard rectangular deck outline run against
  the bend can end on dry ground — #258 measured `hogan_store`'s face at **−0.34 m** and
  refused it rather than invent a bespoke outline. Carry that refusal clause across: a
  deck whose face is not afloat is refused with its reason on the record, the way the
  trace-reach refusals already are.
- The dock attribute is safe to state on records now: #259 stopped `frame_storefront`'s
  mesh-input hash from sweeping `dock`, so stating it no longer stales committed GLBs.
  **Check the same is true of `log_dwelling`** — Robert Kinzie's archetype — before
  stating it there, or the bake goes stale on a runner that cannot bake.

**Acceptance:** the wharf rule considers the west bank, Robert Kinzie's store carries a
drawn landing at the reconstructed tier with its liberty recorded, any west-bank
candidate it refuses carries its measured reason in `river_landings.json § refused`, and
the smoke's wharf count moves with the record. Gates green.

**Links:** PR #258 (closed, the source of this) · PR #259 (T-0062 as shipped) · T-0106
(the traced bank stopping short at local e ≈ 390) · `tools/generate_river_wharves.py` ·
`data/structures/robert_kinzie_store.json` · `data/structures/hogan_store.json`.
