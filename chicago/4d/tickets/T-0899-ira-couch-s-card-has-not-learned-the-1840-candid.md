---
id: T-0899
title: Ira Couch's card has not learned the 1840 candidate ruled onto him: spend it, and drop the write-hop ceiling back to zero
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-10
pr: 1052
claimed_by: run 9/10/2026, 1:20:28 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T06:24:19.991Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34444578081
---

Ira Couch's card has not learned the 1840 candidate ruled onto him: spend it, and drop the write-hop ceiling back to zero.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Left by T-0714, 2026-09-06, deliberately and with the ceiling raised by exactly one.**
Re-deriving `crosswalk_census_1840_heads.py` put 290 previously unadjudicated named heads
through the ladder. One of the rulings reaches a town person whose card cites no 1840
source at all: **Ira Couch**, printed page 211 line 3 of image `33SQ-GYYJ-97P`, read
`Ira Couch` at `high` name confidence, ruled **L7 candidate** — full forename and surname
agree, the name is unique on both sides, and nothing independent of the name was found to
hold the pair together.

`measure_research_spend.py --gate`'s second hop caught it: *1 ruled onto a person whose
card has not learned it*. T-0714 raised `unwritten_ceiling.census_1840` from 0 to 1 with
that reason recorded, rather than writing the card itself, because
`crosswalk_census_1840_heads.py` mints nobody and writes no household file by design —
proposing is its job and applying is `apply_census_1840_bridges.py`'s, under T-0515.

**A candidate must stay a candidate.** Ira Couch is `attested` in 1835 and the 1840 line
carries no discriminator independent of the name, so nothing here promotes anything: what
his card should learn is that a named 1840 head of this name stands at that locator and
has not been joined to him, with the rule that says why. The other ten candidate rulings
in this crosswalk already reach cards that cite the source; this is the one that does not.

**Acceptance:** Ira Couch's card carries the 1840 candidate as a candidate, with the
reading as printed, the locator (image, printed page, line) and the rule that fired; no
grade moves; `measure_research_spend.py --gate` green with
`unwritten_ceiling.census_1840` back at **0**, dropped in the same commit; `bash tools/check.sh` green.

---

**Closed 2026-09-10, and the ticket's own premise had moved under it.** Both halves were
checked against `measure_research_spend.py` itself rather than against the paragraph
above, because the fault this ticket describes is exactly the kind an instrument reports
green while it is true.

1. **The card has learned it.** T-0698 (PR #992) wrote the crosswalk's rulings onto the
   cards they name, `hh_couch_ira` among them, and `tools/spend_census_1840_heads.py
   --check` holds it there. The card carries the reading as printed (`Ira Couch`), the
   locator (`33SQ-GYYJ-97P`, printed page 211, line 3), the rule that fired and the
   crosswalk it came from. Traced through `count_written`'s own code path, the ruling is
   one of census_1840's 30 reached, 30 judgeable and 30 on a card — the person key that
   carries it is `household_id`, which is how it can be present and still read as absent
   if you look for `person_id`.

2. **It is no longer a candidate.** The head is now `outcome: matched`, rule `L6 matched`,
   on a discriminator independent of the 1840 name: the same person separately adjudicated
   into Norris's 1844 directory at a stated address, which is evidence about the PERSON and
   not about the spelling. So "a candidate must stay a candidate" is satisfied by not
   applying — the candidate became a match on evidence, and the card says so in those
   words. The ruling `rests_on` `norris_directory_1844` and the card cites it, which is
   what makes the write hop count it. (The reading of that 1844 entry — the printed token
   `Couch, Iia` — is T-0900's question and is untouched here; the crosswalk records
   `forename_written_out_in_the_entry: false` and rests the link on surname plus first
   given initial, so nothing here depends on resolving it.)

3. **The ceiling is back at zero.** `unwritten_ceiling.census_1840` 1 → 0 in
   `tools/research_spend_baseline.json`, with the reason in the `lowered` ledger. It may
   not drift back up: a later 1840 ruling that reaches a person and not their card raises
   it again and `check.sh` says so.

**No grade moved and no data changed.** Ira Couch is `attested` in 1835 on the 1834-1836
Tremont House tenure, as he was before this pass, and nothing on an 1840 line touches that.
