---
id: T-1048
title: Resolve the newspapers' place vocabulary against the committed town before anything refuses on it: 193 persons carry a place that fails in_town_places(), and Fort Dearborn, the Mansion House and 'the corner of Water and Franklin streets, Chicago' are among them
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1047
opened: 2026-09-11
closed: 2026-09-11
pr: 1169
claimed_by: run 9/11/2026, 10:56:31 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T04:25:12.829Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34671588034
---

Resolve the newspapers' place vocabulary against the committed town before anything refuses on it.

Piece 1 of 2 of **T-1047**, itself piece 2 of **T-1040**. T-1046 repaired the readings; T-1049 applies the guard; this ticket makes the guard possible by settling what the corpus's place strings MEAN.

## THE FINDING

`in_town_places()` (tools/mint_letter_list_residents.py, shared by the placed and documented mints) resolves a place string against the bare town, every committed 1835 street name and every committed structure name and aka. Run the gazetteer's `associated_places` through it and 193 of 2,665 persons carry NOTHING that resolves — but the list is not 193 out-of-town men. It contains, measured on dev 2026-09-11:

- places plainly INSIDE the town the function simply cannot spell: `Fort Dearborn`, `Water Street`, `the Mansion House`, `the Point`;
- places that name the town and fail anyway on their own punctuation or qualifier: `Chicago, Illinois`, `the market square, Chicago`, `the corner of Water and Franklin streets, Chicago`, `a farm two miles from Chicago`;
- places genuinely outside it: `Michigan City`, `Green Bay`, `Detroit`, `St. Joseph`, `Hennepin`, `Juliet`, `Cook County`, `Naper's Settlement`, `Buffalo, N.Y.`.

Only the third group may ever refuse anybody. Until the three are told apart, any guard built on the test refuses residents of the town it is modelling.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- every distinct `associated_places` string in the gazetteer is resolved to one of: inside the town, outside it, or UNDECIDED — and undecided is a real answer that is counted, not a silent third state;
- the resolution is DERIVED against the committed dataset wherever it can be (a qualifier stripped, a structure matched, a street matched), and where it cannot be, the ruling is declared with its reasoning in the corpus rather than hard-coded in a tool;
- the counts are stated: how many strings, how many persons, in each of the three buckets;
- nothing refuses anybody yet — this ticket resolves the vocabulary and changes no card. T-1049 spends it;
- `bash tools/check.sh` is green.
