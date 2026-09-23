---
id: T-1046
title: The two out-of-town readings themselves: Carver's Michigan City agent gets the place his own notice gives him, and the shoemaking notice's four impressions read L. W. Montgomery instead of the auctioneer
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1040
opened: 2026-09-11
closed: 2026-09-11
pr: 1166
claimed_by: run 9/11/2026, 8:59:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T03:23:39.840Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34665784850
---

The two out-of-town readings themselves: Carver's Michigan City agent gets the place his own notice gives him, and the shoemaking notice's four impressions read L. W. Montgomery instead of the auctioneer.

Piece 1 of 2 of **T-1040 — Two readings the newspapers gazetteer gives a Chicago person belong to somebody else**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns the READINGS. Piece 2 is T-1047 and owns the card.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- **Miller.** `person_col_samuel_miller` and `person_samuel_miller` are ONE advertisement printed twice — David Carver's storage, commission and lumber notice, whose closing sentence is "Calvin Britain esq. at St. Joseph, and Col. Samuel Miller, Michigan City, are his Agents". The 25 February impression (chicago_democrat_1834_02_25 c003) recorded both agents' towns in a prose `role` and gave neither an `occupations` nor an `associated_places`, so the entities read as placeless names beside a Chicago lumber merchant — T-0694's finding at the person level. Put the place on the entity, as T-0694 did for the firm. The 4 March impression (c006) had already done it, and had additionally dropped the printed title from its normalized name, which is what minted one man as two persons.
- **Montgomery.** `person_w_montgomery` carries `boot and shoe maker` among its occupations beside `auctioneer`, `commission merchant`, `land agent` and `newspaper agent`. The shoemaker is Loton W. Montgomery. Split the readings.
- the gazetteer and the register recompile, the derived resident files re-run in the same pass, and `bash tools/check.sh` is green.

## WHAT THIS PIECE DOES NOT DO

It does not make `hh_miller_samuel` stop citing the Michigan City reading. That needs a place test in `tools/consolidate_resident_evidence.py`, which has none, and it reaches 132 households — T-1047.
