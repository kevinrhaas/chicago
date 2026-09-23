---
id: T-0855
title: A card whose only evidence reads Hubbard, [Henry] G. was folded onto Gurdon Saltonstall Hubbard: one man's record is on the wrong person
state: done
epic: TOWN
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 958
claimed_by: run 9/5/2026, 10:58:09 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T04:12:10.045Z
claimed_run: null
---

A card whose only evidence reads Hubbard, [Henry] G. was folded onto Gurdon Saltonstall Hubbard: one man's record is on the wrong person.

**Acceptance:** `hh_hubbard_g` rests on the man its own evidence names, the ruling
says which and why, and the gate that re-derives the clusters agrees.

## The evidence, and it is the folded card's own

`data/residents/merged/hh_hubbard_g.json`, on `dev` today:

```
.superseded_record.persons[0].name                      = "G Hubbard"
.superseded_record.persons[0].press_evidence[0].as_read = "Hubbard, [Henry] G."
.superseded_record.persons[0].press_evidence[0].record_id = "person_hubbard_henry_g"
.merged_into.person                                     = "hubbard_gurdon"
```

**The card's only press evidence reads `Hubbard, [Henry] G.` and cites a record id
naming Henry. It was folded onto Gurdon Saltonstall Hubbard.**

The bracket is the transcriber's own: five committed source files carry that exact
normalisation — `fergus_1839_crosswalk_1835.json`,
`fergus_1839_election_crosswalk_1835.json`,
`newspapers/extracted/chicago_democrat_1835_08_05.json`, `newspapers/gazetteer.json`
and `newspapers/register_1835.json`. It is a reading somebody made, not an inference
available to a name-matching pass.

**And Henry is a real, separate, attested man on this same tree.**
`data/residents/households/hh_hubbard_henry_g.json` carries `hubbard_henry_g`,
"Henry G Hubbard", `grade: attested`, on the evidence `Henry G. Hubbard`
(`person_henry_g_hubbard`). So the fold did not merge two spellings of one man — it
moved one man's record onto a different man who is also in the town.

## Where it came from

The T-0839 consolidation (#929) ruled the `hubbard` cluster `merge / C0`, survivor
`hubbard_gurdon`, folding five cards including `hubbard_g`. The reasoning recorded in
`card_merge_rulings.json` is about Gurdon being "the one Hubbard the town documents",
which is true of `G. S.`, `G. T.` and `Gordon S.` — and is exactly the argument that
fails on `G.` alone, because that card is the one whose transcription names somebody
else.

**The rival PR #932 caught this and was closed.** Its words: *"the sixth card is not
Gurdon … the transcriber's own bracket names Henry, so it is ruled onto
`hubbard_henry_g` … A pass that merged on the initial would have got it exactly
backwards; the ledger is what caught it."* It ruled 31 clusters against #929's 36 and
lost on coverage; it was right on this one. This ticket is that finding rescued
before the branch closed.

## What to do

1. Re-rule the `hubbard` cluster so `hubbard_g` folds onto **`hubbard_henry_g`**, not
   `hubbard_gurdon`, with the bracket quoted as the reason. The other four
   (`g_s`, `g_t`, `gordon_s`, `gurdon_s`) are not in question.
2. Re-run the cascade the fold feeds — `consolidate_resident_evidence --build`, the
   mints and regrade, `compile_register --build`, `town_census`, `compile_scene --all`
   — because the survivor's evidence block and the town's count both move.
3. Check what the wrong fold carried across: any source `hh_hubbard_g` brought to
   Gurdon's card belongs to Henry, and Gurdon's evidence block should lose it.
4. Ask whether the gate could have caught it. `consolidate_town_cards.py --check`
   verifies every cluster carries a ruling and that folded ids resolve; it does not
   ask whether a ruling AGREES WITH THE CARD'S OWN TRANSCRIPTION. A card whose
   `as_read` names a different person from its survivor is a decidable check, and it
   would have caught this one.

**Item 4 is the durable half.** The mis-fold is one man; a gate that reads the
transcription against the survivor would hold every future fold to it.

## How far it spreads: measured, and it is one

All 42 records under `data/residents/merged/` were scanned for the same shape — a
folded card whose reading carries a **bracketed forename** (the transcriber's own
judgement) that does not appear in the survivor's id:

```
merged records scanned : 42
folded cards whose bracketed forename is absent from the survivor : 1
  hh_hubbard_g    "Hubbard, [Henry] G."    -> survivor hubbard_gurdon
```

**One.** So this is an isolated ruling error and not a systemic fault in the
consolidation — which is worth saying plainly, because "42 cards were folded and one
is wrong" is a very different report from "the fold is unsafe". The other 41 stand.

That also sizes item 4 honestly: the gate it asks for would have caught exactly this
one case today, and its value is prospective — every future fold, not a backlog.
