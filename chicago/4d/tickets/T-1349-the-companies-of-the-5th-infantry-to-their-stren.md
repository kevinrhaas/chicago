---
id: T-1349
title: The companies of the 5th Infantry to their strength: the 1835 establishment read from a stated source, the enlisted men, the four laundresses a company, the soldiers' families and the sutler written as programme stage `garrison` and seated in the barracks by company, with the population model's garrison row reconciled
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1176
opened: 2026-09-18
closed: 2026-09-19
pr: 1515
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T12:20:19.313Z
claimed_run: null
---

The companies of the 5th Infantry to their strength: the 1835 establishment read from a stated source, the enlisted men, the four laundresses a company, the soldiers' families and the sutler written as programme stage `garrison` and seated in the barracks by company, with the population model's garrison row reconciled.

Piece 2 of 2 of **T-1176 — Reconstruct the Fort Dearborn garrison of 1 July 1835: the officers the sources name, the companies of the 5th Infantry to their strength, the surgeon, the sutler, the laundresses and soldiers' families, the Indian Agency establishment as attested — seated in the fort's roofs**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance (stated before working, 2026-09-19):** the 1835 establishment of an infantry
company READ from a stated source and printed; the enlisted men of two companies written at
that establishment as programme stage `garrison` and seated in the barracks by company; the
four laundresses a company, their families and the sutler written and seated; the order
book's un-apportioned `persons/garrison/fort` and `households/garrison/fort` rows given the
return they asked for; `tools/check.sh` green and no record's grade moved. Never weakened.

## WHAT THIS RETURNED (2026-09-19)

`tools/reconstruct_garrison_1835.py` is the stage's one writer, with `--build`, `--check`,
`--report` and `--self-test`, wired into `tools/check.sh` beside the other stages.
`data/reconstruction/1835_garrison.json` is the return and `--check` re-derives every
number in it. `docs/RESEARCH/fort_dearborn_garrison_strength_1835.md` is the dossier;
`docs/LIBERTIES.md` L248 is the liberty.

| | |
|---|---|
| establishment | Act of 2 March 1821 § 2, 3 Stat. 615 — 54 all ranks a company, 51 enlisted |
| companies | 2 (Andreas's 1833 reading carried forward; `reconstructed`) |
| officers | 6 at establishment, **0 written** |
| enlisted | 102, at establishment |
| laundresses | 8, four a company |
| soldiers' children | 14 |
| sutler | 1 |
| **written** | **125 persons in 11 households**, all `division: fort`, all seated |

**Three things it refused.** No officer is invented (T-1348 already ruled them, and six
invented commissioned officers would be the worst place in the layer to put an invention).
No reviewed community is drawn (art. 19 enlisted "free white male persons" and no others —
the Army's colour bar, recorded as a fact rather than passed over — and T-1177 owns those
reconstructions in any case). And **no drawn soldier bears a family name any attested or
inferred person of this town bears**, which is § 8 of the dossier and the finding below.

**The quartering check it ran and did not act on.** The 1835 General Regulations art. 31
allows 225 sq ft to every six enlisted men and washerwomen above the 38th parallel. The
barracks' committed footprint quarters 84 on one floor against the 110 this establishment
puts in it — short by 26. Three readings survive (a second floor; a short footprint, which
the record already invites at ±20 %; or companies below establishment, the likeliest) and
the stage picks none. Nothing was reduced to fit.

## FINDINGS THIS RUN RECORDED AND DID NOT ACT ON

**(a) The Indian Agency establishment is in NEITHER half of T-1176.** The parent asks for
"the Agency establishment (the agent, sub-agent, interpreter, blacksmith of the agency) as
the sources name them, its Native and Métis employees and their families reconstructed
where only counted — through T-1177's rules, `review_required`, `touches_removal`". T-1348
took the officers and this ticket took the companies; the Agency falls between them and
would have been lost when the parent closed. Filed as its own ticket rather than bolted on
here, because it is a reviewed-community unit and belongs beside T-1177's rules.

**(b) Every stage below `women_and_children` will meet the name-collision fault.** T-1173's
trade households and T-1175's lodgers draw hundreds more invented names over the same
sixty-five surnames and resolve against the same research passes. Refusal 4 of this stage is
written generally enough to lift. Carried onto T-1179, which owns the band's convergence.

**(c) `reconstruct_sex_age.py` needed to be told about this stage.** Its own rule is "A DRAW
IS NEVER EVIDENCE, WHOEVER DREW IT", and `SELF_DESCRIBING_STAGES` is how it keeps another
stage's drawn sexes out of the male rate it measures off the town's rolls. A company of
infantry is male by the statute that constitutes it, so leaving `garrison` off that list
moved the measured male share of every roll by a hundred men nobody read off a roll. Fixed
in this PR, with the reason beside it.

---

**SALVAGED, 2026-09-19.** The run that did this work pushed four commits to
`steward/t-1349-garrison-companies` at 07:35 UTC and died before it could open a pull
request, so `inflight` filed the branch under RECOVERABLE — work nobody can see, on a
ticket the queue still offers. This run read the branch instead of rebuilding it, merged
four hours of `dev` into it (T-1353, T-1365, T-1376) and re-derived the layer on top.

**What the merge cost, and it is the shape T-1179 predicts.** 124 files conflicted, 110 of
them `data/residents/households/hh_*.json` — the derived cards T-1282 records the lap
cannot resolve. Every one was taken from `dev` and re-derived rather than hand-merged; the
only conflicts settled by hand were the five sources (`check.sh`, `derived_manifest.json`,
`reconstruct_residents_1835.py`, `LIBERTIES.md`, `changelog.js`) and three tickets. Two
things had to move with the town rather than with the branch: the garrison's liberty is
**L251** now, because `dev` minted L248-L250 while this branch was orphaned, and the
release note went back to `v: null` for the stamp tool to assign — the branch had
hand-written v970 and `dev` is at v976.

**One stage below had to redraw, and only one.** Stage `transients` (T-1353) draws its
invented names over the same pools, and it sits AFTER `garrison` in the programme, so the
125 soldiers moved 25 of its cards. Re-running the stage settled it. Nothing above
`garrison` moved — the refusal this stage carries (no drawn soldier bears a family name a
named resident bears) is what keeps `women_and_children` and the civic mint still, and it
held across a four-hour-newer town.
