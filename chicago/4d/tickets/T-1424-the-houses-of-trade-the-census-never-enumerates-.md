---
id: T-1424
title: The houses of trade the census never enumerates: the livery stables and the lumber yards, built on the trade head as the order, with the river and transport trades adjudicated head by head
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1409
opened: 2026-09-19
closed: 2026-09-20
pr: 1551
claimed_by: run 9/19/2026, 11:45:57 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T05:44:39.690Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35489743452
---

The houses of trade the census never enumerates: the livery stables and the lumber yards, built on the trade head as the order, with the river and transport trades adjudicated head by head.

Piece 1 of 2 of **T-1409 — The river and transport trades: the forwarding and warehouse gap beyond the attested four, the drays and livery, the lumber yards, the pier-works contractor and his gang, and the vessels in port on 1 July with their masters**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

- A THIRD quota form in `tools/reconstruct_businesses_1835.py` beside the count row and
  the standing roof: **the trade head is the order**. A head the resident band drew at a
  trade whose own word names a house of trade — a `livery_stable_keeper` keeps a stable, a
  `lumber_merchant` keeps a yard — is itself the order for one establishment, in a class
  the December 1835 State census never enumerates and therefore can never count short.
  With its schema block, its `--check` refusals and its self-tests, as T-1408's roof form
  carries.
- The four houses that form orders, built: two livery stables and two lumber yards,
  proprietors adopted from the trade heads and never minted, typed `other` so no census
  count is spent, faced off a stated rule, named in the register's own forms.
- **The adjudication printed, head by head.** Every remaining reconstructed head at a
  river or transport trade appears in the ledger with the kind of absence it is: the
  forwarding and commission men (the census's four houses against the register's eight —
  a person short is not an establishment short), the teamsters and boatmen and the sawyer
  and the seaman (employments with no premises to keep), and the master mariner and the
  mail contractor (T-1425's). No head is silently passed over.
- `--check` re-derives; `./tools/check.sh` green; the liberty registered; the naming
  guide's two new worked forms; the changelog entry; published.

**Stop condition:** no reconstructed head at a river or transport trade is unaccounted
for — each either keeps a house this ticket built, or has a printed reason it keeps none.
