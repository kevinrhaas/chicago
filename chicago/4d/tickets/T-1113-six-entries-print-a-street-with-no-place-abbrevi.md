---
id: T-1113
title: Six entries print a street with no place-abbreviation before it, so the address never lands: five let the street follow the firm directly and one has Clark st eaten by the business name
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-13
pr: 1278
claimed_by: run 9/13/2026, 4:09:56 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T21:54:36.108Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34782843048
---

Six entries print a street with no place-abbreviation before it, so the address never lands: five let the street follow the firm directly and one has Clark st eaten by the business name.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1022's before/after measurement, which is where these surfaced and which
deliberately did not widen its scope to fix them.

`PLACE` splits a trade from a street on a place-abbreviation (`h`, `res`, `b`,
`house`, `boards`…). Where Norris sets none, there is nothing to cut at and the whole
line stays in `occupation`. Six entries name a street and carry `address: null`:

    n1844_e0062  Ballentine, David, of B. & Sherman, Dearborn street bet Kinzie and Michigan
    n1844_e0817  Hatch, Herman, of H. & Shur, South Water st.
    n1844_e1206  Magie, H. H. of H. H. M. & Co. house
    n1844_e1470  Raymond, Geo. at B. W. Raymond's 122 Lake st
    n1844_e1858  Weber, Ignace, clerk at J. B. Busch's, Clark st
    n1844_e1993  Intelligence Office, Clark st. opposite Saloon, over J; B. F. Rus-sell's Land Office

They are not one fault but three, and the ticket should say which it is repairing:

1. FIVE OF THEM ARE THE FIRM'S OWN ADDRESS, not the man's home — `of B. & Sherman,
   Dearborn street` is where the partnership stands. Reading it into `address` would
   put a business street onto a resident's card as a residence, which is a provenance
   question and not a parsing one. It may be right to leave all five refused and say
   so, or to land them under a distinct field. Decide that before writing a regex.
2. `n1844_e1206` ends at the word `house` with no street after it — the printed line
   is cut. `PLACE` requires `\.?\s` after the abbreviation, so a trailing `house`
   never matches, which is correct. The entry needs a page-image read, not a rule.
3. `n1844_e1993` is a genuine mis-read and the only unambiguous repair here: the
   business name swallowed `Clark`, leaving an occupation of `st. opposite Saloon,
   over J; B. F. Rus sell's Land Office`. The name/trade boundary is what moved, not
   `PLACE`.

**Acceptance:** each of the six is repaired or named as a deliberate refusal with its
reason; `n1844_e1993` reads a business name of `Intelligence Office` and does not
begin its occupation at `st.`; the crosswalk's `could_carry_address` is counted before
and after; `bash tools/check.sh` green with the derived layer re-run. No bake.
