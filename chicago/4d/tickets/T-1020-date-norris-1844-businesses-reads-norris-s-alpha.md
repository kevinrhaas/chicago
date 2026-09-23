---
id: T-1020
title: date_norris_1844_businesses reads Norris's alphabetising comma as a partner separator, so 'Jones, B. & Co' loses its initial and the continuity test refuses B. Jones on a surname alone
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-11
pr: 1108
claimed_by: run 9/11/2026, 1:05:42 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T06:33:57.535Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34568181956
---

date_norris_1844_businesses reads Norris's alphabetising comma as a partner separator, so 'Jones, B. & Co' loses its initial and the continuity test refuses B. Jones on a surname alone.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

MEASURED AGAINST DEV AT 0b25c9002 (T-1013 as merged), so this ticket is the fix and not
the survey.

`firm_names()` splits a printed firm style on `&`, on `and`, and on the comma Norris uses
between partners — `Jones, King & Co.` So it reads the ALPHABETISING comma the same way.
For the inverted style `Jones, B. & Co` the parts are `Jones` / `B.` / `Co`; the middle
part is an initial with no surname beside it, `if not longs: continue` drops it, and the
initial `B` never reaches `initials['jones']`.

T-1013 put 24 of these inverted styles into the dating pass for the first time
(`firms_in_the_directory_proper` 65 → 89), and the cost is visible in the committed
`norris_1844_businesses_1835.json` on dev today:

    Jones, B. & Co     meets business_b_jones_grocery_and_provision_store
                       and  business_b_jones_storage_and_forwarding
    Johnson, J. & Co   meets business_lathrop_johnson_co_livery
      "One surname, and no initial printed on both sides agrees.
       Refused — the eleven-Smiths rule."

The 1844 style prints B. and the 1835 businesses are B. Jones's. The refusal is the tool
saying it cannot see an initial it is holding, which is a different thing from the
eleven-Smiths rule refusing on evidence.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- An initial-only part that FOLLOWS a surname part attaches to that surname; one that
  follows nothing is still dropped. `Jones, B. & Co` reads `{jones: {B}}` + `{co}`.
- `Jones, B. & Co` and `Johnson, J. & Co` are re-adjudicated against the 1835 businesses
  they meet, and the outcome is stated whichever way it falls. A one-surname firm still
  REQUIRES an initial agreement, so this makes the rule able to run, not certain to pass —
  and `D. A. & E. M. Jones`, which meets the same two businesses and prints neither
  initial B, must stay refused.
- No firm that matches today stops matching. The continuity counts — `continuity`,
  `continuity_ambiguous`, `continuity_refused_on_a_surname_alone` — are stated before and
  after. `bash tools/check.sh` green. No bake.
