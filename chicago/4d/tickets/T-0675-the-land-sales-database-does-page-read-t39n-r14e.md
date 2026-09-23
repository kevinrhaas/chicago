---
id: T-0675
title: The land sales database DOES page: read T39N R14E sections 16, 21 and 29 whole
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0610
opened: 2026-09-04
closed: 2026-09-04
pr: 798
claimed_by: run 9/4/2026, 11:58:54 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T18:12:11.612Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33897548587
---

The land sales database DOES page: read T39N R14E sections 16, 21 and 29 whole.

Piece 1 of 2 of **T-0610 — Three sections of T39N R14E were truncated at the land-sales database's 150-row ceiling, and the ring townships are unread: finish the Illinois land tract sales around Chicago**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

The database's results page carries a **More** button — a keyset cursor
(`hiddenPurchaseNo` + `hiddenPurchaser` + `hiddenSectionNo`) that walks past the
150-row ceiling. The README's "offers no paging" is wrong, and that error is the
only reason these three sections were declared unread.

Done when:

1. `tools/harvest_land_sales.py` follows that cursor, so a section query returns the
   whole section rather than its first page, and says how many pages it walked.
2. T39N R14E sections 16, 21 and 29 are read whole and their sales through
   31 December 1836 are in the committed deposit — 345 rows against the 154 the
   ceiling gave (337 in section 16, 4 in 21, 4 in 29).
3. `coverage.json` declares all three as read, the `TRUNCATED` refusal in
   `tools/read_land_sales.py` is gone, and no file still tells a reader the source
   cannot be paged.
4. `tools/read_land_sales.py --check` re-derives every generated file from the new
   deposit, `./tools/check.sh` is green, and the `--for-diff` smoke legs pass.

Out of scope, and it is T-0676: the ring townships.
