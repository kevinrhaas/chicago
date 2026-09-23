---
id: T-0626
title: Spend the Sauganash reading: retire the 12x8 placeholder for the two-mass plan, site the log annex where the views put it, and bake the door, sash, shutters and roof the reading resolved
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0616
opened: 2026-09-03
closed: 2026-09-04
pr: 770
claimed_by: run 9/4/2026, 2:01:09 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T08:13:52.429Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33846627075
---

Spend the Sauganash reading: retire the 12x8 placeholder for the two-mass plan, site the log annex where the views put it, and bake the door, sash, shutters and roof the reading resolved.

Piece 2 of 2 of **T-0616 — "The Sauganash is one 12x8 box: its two-storey rear wing is missing, its log annex stands in front, and four attested views resolve the massing, the door, the windows and the roof"**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. `data/structures/sauganash_hotel.json` phase `frame_1831` carries the two-mass
   plan T-0617 measured, in place of the 12 × 8 m placeholder, with the placeholder
   note replaced by the derivation and every new attribute carrying its own
   confidence and sources.
2. The log annex is sited where the four views put it — at the END of the
   composition, beside the tall wing. **Nothing log-built stands in front of the
   main block's street face.**
3. **The 1835 tenancy is told correctly, and this is the owner's explicit
   instruction of 2026-09-03.** The annex is Beaubien's own original cabin, let to
   tenants: Carpenter from late summer 1832, "soon" out, then John S. Wright, then
   a school under Eliza Chappell from September 1833 — **which moved into the First
   Presbyterian Church in 1834**. Sources: drloihjournal 2018-06 "The History of
   Chicagoan Mark Beaubien" and 2018-01 "Eliza Chappell…"; file both as source
   records first (`drloih_hotels` is a different page), tier 4, secondary.
   **So on 1 July 1835 it is neither a drug store nor a school, and the record must
   not name a fourth use it cannot source.** So:
   - `philo_carpenter_log_shop.json` stops being "Philo Carpenter's Log Drug Store"
     at the scene date. `name`, `function` and `occupants` agree: three documented
     FORMER uses, none current, the chain in the note, each field graded on its own.
     The record's `occupants` block already says "NO SOURCE REACHED NAMES ANYONE IN
     THIS BUILDING IN 1835" — make `name` and `function` say the same thing.
   - Whichever of the two `PHILO CARPENTER / Druggist` boards in
     `data/signage/town_business_signboards.json` stands on the LAKE STREET log
     shop is retired or re-lettered; the South Water Street board is correct for
     1835 and stays. A board in July 1835 must not letter a man who left in 1832.
   - Link the school to `hh_chappel_eliza_mir`, which the residents layer already
     holds.
   - Reconcile against the Sauganash's own `log_1829` phase, which ends 1831-12-31
     and may be this same building recorded twice — either merge them or state why
     they are two.
4. The preview at the Lake & South Water stand reads as the three-part building the
   views show: two masses of near-equal ridge height, the annex at the end. A
   before/after pair from the same pose goes on the PR.
5. `bash tools/check.sh` green, the smoke's Sauganash assertions updated to the new
   massing rather than deleted, and the bake re-run (`needs_bake`).
