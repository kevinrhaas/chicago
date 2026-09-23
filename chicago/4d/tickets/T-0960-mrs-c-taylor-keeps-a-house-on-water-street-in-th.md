---
id: T-0960
title: Mrs C. Taylor keeps a house on Water Street in the Democrat of 19 August 1835 and the town has no card for her
state: done
epic: PAPERS
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-10
pr: 1050
claimed_by: run 9/10/2026, 12:08:13 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T06:12:33.142Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34439481923
---

The Chicago Democrat of **19 August 1835** prints, over the Juvenile Society's notice:

> "The Ladies and Gen[t]lemen of the town of Chicago are respec[t]fully in[v]ited to attend
> a sale of the \"Juvenile Society's\" work, [at] 3 o'clock P.[M.] next Saturday, the 22d
> inst., at the hous[e] of **Mrs. C. Taylor, Water-st.** … Chicago, Aug. 10, 18[35]."

`data/research/newspapers/extracted/chicago_democrat_1835_08_19.json` on `dev` carries that
transcription. **The town has no card for her.** `data/residents/households/` holds
`hh_taylor_anson`, `hh_taylor_augustine`, `hh_taylor_edmund_d`, `hh_taylor_william` and
`hh_taylor_william_h`, and none of them is a Mrs C. Taylor; `taylor_c` appears nowhere in
`data/`.

**`#925` wrote the card and it was never landed.** That branch — parked under `hold`, closed
by T-0930 because its ticket T-0723 merged under `#998` — carries
`data/residents/households/hh_taylor_c.json`: `taylor_c`, "Mrs C Taylor", grade `attested`,
ladder rule G1b, `present_on_scene_date: uncertain` because every source naming her falls
after 1 July 1835. That card is the salvage from a closed branch and it is why this ticket
exists. This is the case T-0930 names outright — *"a family that was nearly deleted as
invented when a verified source states it."*

**And the branch's own card understates the source.** Its `lives_at` reads `null`,
*"Not attested: the lists that name this person give no address."* The notice gives one:
**Water-st.**, and it is her HOUSE, not a business — "at the house of Mrs. C. Taylor,
Water-st." A woman keeping a house on Water Street, hosting the Juvenile Society's sale, is
about as placeable as an 1835 resident gets without a lot number.

**Acceptance**

1. `hh_taylor_c` exists on `dev`, off the Democrat of 1835-08-19, with the transcription as
   its source and `present_on_scene_date` reasoned rather than assumed.
2. `lives_at` states Water Street at the confidence the notice earns — a named street and no
   number is not `null`, and it is not a lot either.
3. Whether "Mrs. C. Taylor" is the wife of one of the five Taylor heads already on `dev` is
   asked and answered in the card's own note, under R6 (`#998`: a wife is not her husband).
   If she cannot be tied to one of them, that is written down as the finding it is.
4. If a placement follows, it obeys T-0514's sequencing — this ticket does not guess a lot.
