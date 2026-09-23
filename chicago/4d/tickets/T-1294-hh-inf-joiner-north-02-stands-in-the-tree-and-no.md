---
id: T-1294
title: hh_inf_joiner_north_02 stands in the tree and no pass derives it: the register deal seats four roofs where its own docstring says five, and J. W. Reed's household is owned by nobody
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

hh_inf_joiner_north_02 stands in the tree and no pass derives it: the register deal seats four roofs where its own docstring says five, and J. W. Reed's household is owned by nobody.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1228 while settling what the three inferred-household passes still own.

`tools/replace_invented_residents.py` opens by saying five roofs had their invented
name retired in favour of a documented practitioner the newspaper register named. Its
deal seats FOUR today — hh_inf_cooper_north_04, hh_inf_physician_south_01,
hh_inf_tailor_north_02 and hh_inf_tavern_keeper_north_01. The fifth,
`hh_inf_joiner_north_02`, stands in the tree carrying J. W. Reed, graded `attested`
under ladder rule G1a, with the retired-invented-name prose still in his note — and
no pass derives it. It is the one record in T-1228's settlement that nothing owns:
`generate_inferred_households.py` derives a household by that id which the ruling
removed, the deal no longer reaches it, and
`tools/synthesize_resident_research.py` carries the man but not the household's place
in this pipeline.

Two things could be true and this ticket is to find out which:

- The register's joiner candidate began failing one of the deal's refusals (a date, a
  garble, a firm, or T-0367's street test) after the household was already written, in
  which case the household is a leftover of a deal that no longer holds and the
  question is whether J. W. Reed's own evidence still puts him in the town.
- The deal is right and the household is simply the resident layer's now, in which
  case the settlement at
  `data/reconstruction/1835_inferred_household_pass_ownership.json` should name its
  owner instead of recording it as ownerless.

**Acceptance:**

- Which of the two it is, decided from the register and the refusal that fires (or
  does not), with the reading shown.
- `tools/replace_invented_residents.py`'s docstring no longer says five where it deals
  four, or deals five again — whichever the reading supports.
- The settlement record names the household's owner, or states with evidence that the
  record should not stand.
- No confidence is upgraded and J. W. Reed is not removed from the town to tidy a
  pipeline: he is a real named man in the resident layer, and his grade is that
  layer's to argue.
