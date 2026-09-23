---
id: T-0422
title: The widened counterfactual deals a roof per street, and every roof a widening adds already fronts another street
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-13
pr: 1235
claimed_by: run 9/13/2026, 1:28:33 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T07:07:31.808Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34742685228
---

The widened counterfactual deals a roof per street, and every roof a widening adds already fronts another street.

Found by a second run that took T-0416 from the queue in the same minute as **#568** and
built the costing independently. #568 landed first and its numbers are right; this is the
one thing the two implementations disagreed about, and it is worth keeping.

**What it is.** `tools/adopt_street_faces.py` `allocate()` keeps the one-roof-one-business
ledger PER STREET — `free = [sid for sid in free_under(...) if sid not in
taken.get(street_id, [])]`. Under the policy's own reading (`lot front`) that is free and
needs no ledger at all: **no reconstructed roof in this town has its platted lot on two
streets**, so a face's supply is exclusive by construction.

**Under a widening it is not, and the reason is exact.** *Every* roof a corner-side reading
adds to a face already fronts ANOTHER street by its lot — of Dearborn Street's eighteen,
seven front Randolph, five Washington, five Lake and one South Water; of Wells Street's
fourteen, six front Randolph and four South Water. So the widened supply is not new supply:
it lets two faces deal the same roof. A per-street ledger cannot see that, and the pass can
seat a Dearborn advertisement and the Randolph advertisement whose lot the roof actually is
in one building.

**It does not bite today, and that was measured rather than assumed.** Run against `dev`,
both widenings deal **31 and 32 DISTINCT roofs** for 31 and 32 adoptions — no duplicate. The
free supply on the lot-front faces is large enough (Lake 19 free, Randolph 33) that the
evidence ranking never reaches the contended roofs. **The published +12 / +13 are correct.**

**Why it is still worth closing.** The counterfactual is the thing the owner is being asked
to rule on. If he rules yes, this ledger becomes the LIVE allocation over a supply that is
already tightening — South Water refuses fourteen advertisements today, seven of them purely
on supply — and the day it bites, the number in front of him was measured by the pass that
gets it wrong. `limits()` would catch the shipped table ("two businesses on one roof" is
already a self-test case), so this would surface as a red at commit time rather than a
silent error; it is a wrong counterfactual, not a wrong town.

**Acceptance:** the widened allocation spends each roof once TOWN-WIDE rather than once per
face; a self-test derives both widenings on every commit and fails if any roof is dealt
twice, so the costing cannot rot while the policy refuses it; and the widened figures in
`street_face_adoptions.json` and on T-0416 are re-derived under the corrected ledger and
stated — whether or not they move.

**Links:** T-0416 (the blocked question these numbers are for) · T-0354 / L212 (the policy) ·
`docs/STREET-FACE-ADOPTION.md` · #568 (the costing) · #566 (the duplicate run, closed, whose
comment carries this finding).
