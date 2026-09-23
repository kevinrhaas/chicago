---
id: T-1372
title: Crews, the works gang and the guest lists: the vessels in port and the pier-works hands seated, and every lodging card printing who lived there
state: split
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1175
opened: 2026-09-19
closed: 2026-09-19
pr: null
claimed_by: run 9/19/2026, 7:35:20 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T12:42:53.191Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35443021089
---

Crews, the works gang and the guest lists: the vessels in port and the pier-works hands seated, and every lodging card printing who lived there.

Piece 3 of 3 of **T-1175 — Fill the beds: boarders, lodgers, hotel guests, boarding-house keepers' households, the crews of the vessels in port and the hands at the works, seated in the named and reconstructed lodging places to the lodging model's capacities**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

---

**FINDING from T-1353, 2026-09-19 — what the crews are waiting for, and it is not this
ticket's to invent.**

T-1353 minted the transient cohort and **refused the crews outright**. T-1352 records 4 to
6 hulls lying at Chicago on the scene date, from the Marine Journal of the Chicago American
of 4 July 1835, and names three of them — the *Llewelling*, the *Hiram* and the *Whig*,
plus an unnamed steamboat; the *Jesse Smith* and the *Philips* cleared on 1 July itself.
Its composition table prices that row `bounded: hulls only`. **No committed source in this
corpus gives a crew complement for an 1830s lake schooner**, and the same is true of a
strength for the pier-works gang (`bounded: no`). A crew written without one is a number
invented whole, which is the one thing this project's provenance rule refuses, so
`data/reconstruction/1835_transient_persons.json` carries both as written refusals with the
tickets they are owed to.

**So seating the crews needs a reading first, not a draw.** Until a committed source gives
a complement, this ticket cannot do the first half of its own title without inventing the
number it is seating. The third part — *every lodging card printing who lived there* —
is unaffected and is also downstream of T-1371, which deals the lodging model's surge beds.

Two things T-1353 did leave in place for it:

- `data/residents/transients/hh_*.json` carry a plural `lodged_at[]` with `kind`,
  `place_id`, `resolves_to`, tier, basis and `replaceable_by` — the shape a vessel seat
  would use (`kind: vessel`), already gated and already read by the People view.
- The four ROOFED sleeping classes deliberately name **no house**: they resolve to the
  class of place, with `replaceable_by` naming T-1371 and T-1372. Those rows are what the
  guest lists resolve when the beds are dealt, so the crowd and the beds cannot double-book
  each other.

