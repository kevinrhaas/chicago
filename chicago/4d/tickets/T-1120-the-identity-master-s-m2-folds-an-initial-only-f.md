---
id: T-1120
title: The identity master's M2 folds an initial-only forename onto a full one on the LEADING initial alone, so B. S. Sherman of the 1840 census attaches to Benjamin F. Sherman across a disagreeing middle initial
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-14
pr: 1314
claimed_by: run 9/13/2026, 11:29:57 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T06:30:55.028Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34806090302
---

The identity master's M2 folds an initial-only forename onto a full one on the LEADING initial alone, so B. S. Sherman of the 1840 census attaches to Benjamin F. Sherman across a disagreeing middle initial.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1021, which surfaced it rather than caused it: the fold was there all along,
masked by a phantom identity.

M2 reads: "An initial-only forename attaches to the ONE full forename of that surname
carrying the initial. Two or more rivals is R3, never a choice." It does not say WHICH
initial, and `compile` attaches on the leading one. So on dev today:

    id_sherman_b_s   census_1840  "B. S. Sherman"
      folds onto
    id_sherman_benjamin_f  "Sherman, Benj. F., dry goods and groceries, cor Lake and Clark"

`B. S.` and `Benjamin F.` disagree in the MIDDLE initial, which is the thing M3 exists to
reason about ("a middle initial present on one reading and absent on the other"). Here it
is present on both and different, and M2 folds anyway.

Until T-1021 the fold did not fire, because `Sherman, Ballentine <fc` — a firm read as a
man — was a second "full forename" beginning in B and M2 refused on rivals. Lifting the
scanner's ampersand removed the rival and the fold landed. Nothing is regraded by it
(every identity involved is G0, not_1835_resident), so this is a question about the rule,
not a live error on a card.

- Decide whether M2 must compare the middle initial when BOTH readings carry one, and
  write the ruling into the rule's own text in `identity_master.json` either way.
- Whatever lands, enumerate every fold it changes — before and after — by identity id.
  `B. S. Sherman` is one; the sweep says how many others there are.
- `bash tools/check.sh` green and the derived layer re-run in the same commit.
