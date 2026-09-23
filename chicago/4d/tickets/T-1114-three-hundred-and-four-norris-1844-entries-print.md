---
id: T-1114
title: Three hundred and four Norris 1844 entries print a business street inside the trade line with no place-abbreviation, and 'b' for between is being read as the start of an address rather than a qualifier on the street before it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-13
pr: 1290
claimed_by: run 9/13/2026, 5:44:03 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T00:08:31.437Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34787535409
---

Three hundred and four Norris 1844 entries print a business street inside the trade line with no place-abbreviation, and 'b' for between is being read as the start of an address rather than a qualifier on the street before it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1113, which repaired the six entries it was filed on and deliberately did
not widen to this. Two findings, measured on dev at the time T-1113 landed:

1. **304 of the 2,073 entries carry a street inside `occupation` and `address: null`,**
   because a shop's address IS its trade line and Norris prints no `h`/`res`/`b` in
   front of it: `Ottaway, Charles, grocer, 175 Lake st`; `Newberry & Burch, bankers, 97
   Lake street`. T-1113's ruling was that a street with no dwelling mark is NOT a
   residence and must not land in `address` — five entries carry that refusal on the
   claim now (`normalized.address_refused`). The same ruling says these 304 are not
   residences either, so the question is not "should `address` take them" but whether
   this reading should hold a SECOND, distinct field for the place a trade is carried
   on — and if so, whether a firm's street belongs on the partners' cards at all.
   Decide the field before writing a regex; the provenance question outranks the parse.

2. **`b` is a qualifier, not a place.** `PLACE` treats `b` (between) as a starter, so
   an entry whose tail begins at a street is cut in the middle of its own address:
   `Brown, S. B. Ohio st. b Cass and Rush sts` reads a trade of `Ohio st` and an
   address of `b Cass and Rush sts`, when the two are one location. Where a `h`/`res`
   stands earlier in the line the first match wins and the reading is right, so this
   only bites entries with no dwelling mark — the same population as (1). Any rule
   here must be priced by re-reading the whole volume against the superseded one, the
   way `CASE_RULE_MOVES` and `STREET_IN_FORENAME` already are in
   `tools/read_norris_1844.py`, and every entry that moves must move for the stated
   defect and no other reason.

**Acceptance:** the field question in (1) is decided and written down in the reader's
own band (a new field, or a refusal that says why the 304 stay in `occupation`); (2)
is either repaired with a priced re-read or refused with its reason; `could_carry_
address` in `data/research/directories/norris_1844_crosswalk_1835.json` counted before
and after; `bash tools/check.sh` green with the derived layer re-run. No bake.
