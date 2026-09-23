---
id: T-1515
title: Read Fergus 1839 as a dated directory role like its 1843 and 1844 siblings, so a printing is carried as evidence whether or not the 1835 field is empty
state: open
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Read Fergus 1839 as a dated directory role like its 1843 and 1844 siblings, so a
printing is carried as evidence whether or not the 1835 field is empty.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1299 (PR #1617), which fixed the SYMPTOM narrowly and filed this for the
cause. The owner's call on 2026-09-21: narrow now, this sized separately.

WHAT T-1299 HIT. Filling ten cards' 1835 occupation field out of their own `roles[]`
made `crosswalk_fergus_1839`'s carry test read those cards as no longer needing a
trade, so `could_carry: ["occupation"]` dropped to `[]` (91 -> 84),
`spend_directories` wrote no `occupation_later`, and `derive_resident_roles.
later_role()` — which reads that pointer and nothing else — dropped the 1839 printing
from `roles[]` for six people: Hubbard, Jones, King, Mulford, Sherman, Taylor. The
printing never stopped existing; it stopped being POINTED AT.

THE NARROW FIX, ALREADY LANDED, is that a trade T-1299 PROMOTED out of a card's own
roles is not the directory's gap being filled, so the pointer survives. It restores
exactly those cards and offers nothing new. It does not touch the asymmetry underneath.

THE ASYMMETRY. `crosswalk_fergus_1843` and `crosswalk_norris_1844` are read as DATED
ROLES straight from their crosswalks by `directory_roles()`. Fergus 1839 is the only
one of the four routed through `could_carry` / `occupation_later`, a pointer whose own
semantics are about filling a gap. So one directory's evidence is conditional on the
1835 field being empty and three others' is not, for no reason anybody stated.

**Acceptance:**

- Fergus 1839 is read by `directory_roles()` on the same footing as 1843 and 1844: the
  printing is carried as 1839 evidence with `describes_date` 1839, whatever the 1835
  field holds, and no grade moves.
- `later_occupation` becomes a CONVENIENCE rather than the sole origin of a role row.
  Removing it must not remove a row; the self-test holds that in both directions.
- SIZE THE BLAST RADIUS BEFORE CHANGING ANYTHING AND WRITE IT DOWN. This offers rows
  for every 1839 match, not only the six T-1299 disturbed — 91 carry occupation today.
  The count of role rows this adds, and the cards that gain one, are stated in the PR
  body before the change is argued for.
- The narrow rule T-1299 added to `crosswalk_fergus_1839` is REMOVED in the same
  commit if this makes it dead, and kept with its reason if it does not. Two rules
  answering one question is the fault T-0867 already fixed in this file once.
- `tools/check.sh` green, and no card LOSES a role row — the same clause that stopped
  T-1299, applied to the larger change.
