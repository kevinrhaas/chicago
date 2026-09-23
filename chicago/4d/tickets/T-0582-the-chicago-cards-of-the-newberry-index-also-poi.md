---
id: T-0582
title: The Chicago cards of the Newberry index also point at Moses's Illinois, historical and statistical (1888-92), the La Salle Book Co. Cook County volumes (1900, 1909), Wood's Chicago 1881 and Hurlbut's Chicago antiquities (1881), and none of the four is in this project's sources
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 851
claimed_by: run 9/5/2026, 12:01:30 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T05:53:19.153Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33945824435
---

The Chicago cards of the Newberry index also point at Moses's Illinois, historical and statistical (1888-92), the La Salle Book Co. Cook County volumes (1900, 1909), Wood's Chicago 1881 and Hurlbut's Chicago antiquities (1881), and none of the four is in this project's sources

**Found by T-0570** (the Newberry genealogical index, volume 1). Four works its Chicago
and Cook County cards cite are absent from `data/sources/`:

| work | Chicago/Cook cards in vol. 1 | on a lead surname |
|---|---|---|
| Moses, *Illinois, historical and statistical* (1888-92) | 57 | 11 |
| La Salle Book Co., Cook County biographical volumes (1900, 1909) | 19 | 5 |
| Wood, D. W., Chicago (1881) | seen in the sample; not yet clustered | — |
| Hurlbut, *Chicago antiquities* (1881) | 2 | 0 |

This is the SECOND rank of the reading order — T-0581 has the largest one. The work here
is to locate each, decide whether it is reachable, and write the source record; the
reading of each is its own ticket after that.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Each of the four either has a source record with a locator that can be re-read, or a
  written finding that it could not be located and where the search went. An
  unreachable work recorded as inaccessible is a result; silence is not.
- `WORKS` in `tools/read_newberry_index.py` gains a pattern for Wood 1881 if one can be
  written, and the re-parse counts are reported.
