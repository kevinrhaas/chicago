---
id: T-1026
title: Medard Beaubien is a third card for the man T-1002 folded to two, and a committed note already calls it the same man under two spellings
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-11
pr: 1119
claimed_by: run 9/11/2026, 3:46:22 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T10:27:46.926Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34580576063
---

Medard Beaubien is a third card for the man T-1002 folded to two, and a committed note
already calls it the same man under two spellings.

**FOUND BY T-1002**, which folded `beaubien_medore_b` onto `beaubien_madore` under rule C11
and wrote this out in its own `against` clause rather than reaching for it. The layer still
holds `beaubien_medard`, "Medard Beaubien", a thin civic mint off the poll list of the very
election that ruling turns on — the first election of the board of trustees, 10 August 1833,
where Madore B. Beaubien was returned with 23 votes.

**THE PROJECT HAS ALREADY WRITTEN THE ANSWER DOWN AND DECLINED TO ACT ON IT.**
`data/research/civic/claims/town_findings_andreas_v1.json` claim c003 carries Andreas's
return of the five trustees and its own note ends: *"'Beaubien, Medard' and Andreas's 'Madore
B. Beaubien' are the same man under two spellings; the merge is not made here."* The internal
check that note describes is strong — all five men Andreas names as elected stand on the poll
list of that election, and the list's Beaubien-among-the-five is `Beaubien, Medard`. A man
voting at the election that returned him is the ordinary case, not the suspicious one.

**WHY T-1002 COULD NOT RULE IT, WHICH IS THE WHOLE REASON THIS IS A SEPARATE TICKET.** Medard
is THREE letters from Madore and TWO from Medore, so it is outside the one-letter class that
ticket measured and outside both rules it wrote: C10 wants a title caught setting both
spellings and no title sets these, and C11 wants a spelling variation, which Medard may not
be. Médard is a BAPTISMAL forename and Madore a familiar one, and folding the first onto the
second is a research reading — an argument about what a French-Canadian Catholic family at
Chicago called its son in church and what the town's clerks wrote down — not an argument about
a compositor. That reading wants the parish registers, which this project holds, and a rule of
its own if one is warranted.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The pair RULED in `data/residents/card_merge_rulings.json`, in that file's own shape, under
  a named rule and appended under `also_ruled_on`. Either way is a result: a fold, or a
  written refusal that says what would decide it. `beaubien_medard` and `beaubien_madore` are
  NOT in a derived candidate cluster — `compatible()` cannot see them either — so the cluster
  is written in by hand with its `why_not_derived`, exactly as T-1002's three were.
- The St Cyr and St Mary's registers read for a Médard Beaubien baptism, marriage or sponsor
  entry, because that is where a baptismal name would be printed if it is one. The registers
  are at `data/research/church/`; `st_marys_baptisms_crosswalk.json` already carries "Madore
  Benjamin Beaubien" nine times, so the crosswalk has an opinion the ruling should read.
- The civic claim's note updated to name the ruling instead of saying the merge is not made
  here — the same bookkeeping T-1002 did for its three `does_not_follow` notes.
- If it folds: `tools/consolidate_town_cards.py --apply`, and the derived crosswalks that
  gather by name re-built (`tools/read_land_sales.py --build` at least; check what else drifts).
  If it stands: say so on both cards under the rule, so the next pass reads the answer.
- `bash tools/check.sh` green. No bake: nothing here moves geometry.

**WHAT MUST NOT HAPPEN.** A fold is a card DELETION and the town's resident count moves by it.
This pair must not be folded because two other Beaubien pairs were — three cards standing for
one man is a reason to read the registers, not a licence to assume the third follows the second.
And nothing here may upgrade a confidence: whichever way it goes, the survivor's grade is what
it was.
