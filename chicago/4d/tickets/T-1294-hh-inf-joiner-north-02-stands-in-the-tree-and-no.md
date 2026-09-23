---
id: T-1294
title: hh_inf_joiner_north_02 stands in the tree and no pass derives it: the register deal seats four roofs where its own docstring says five, and J. W. Reed's household is owned by nobody
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-21
pr: 1616
claimed_by: run 9/21/2026, 3:24:04 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T09:14:19.649Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35577446868
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

## THE READING, 2026-09-21 — it is BOTH, and the two options were not exclusive

The ticket offers two possibilities. The measurement says the first one's PREMISE is
true and the second one's REMEDY is what follows from it, which is why neither could be
picked as written.

**Which refusal fires, and the reading.** Refusal 5 — `already named in the town` — and
nothing else. No date, garble, firm or T-0367 street test is involved. Measured by
withholding, from `town_surnames()` only, the six committed cards outside the `hh_inf_`
layer that now speak the surname Reed, and re-running the deal against the same
pipeline input (`generate_inferred_households` → `generate_inferred_names`):

| name pool | seats | the joiner |
|---|---|---|
| as committed | 4 | `joiner  J. W. Reed  already named in the town (reed)` |
| minus T-0514's three documented Reeds | 4 | refused — three other cards still say the name |
| minus all six | **5** | **`hh_inf_joiner_north_02 -> J. W. Reed`**, and no joiner refusal |

So the household IS this deal's own former answer, byte for byte, and the only thing
standing between the deal and the roof today is refusal 5. It is not the guard poisoning
itself: `town_surnames()` deliberately does not read the `hh_inf_` layer back, and all
six cards are outside it.

**It began firing under a household that was already standing.** The roof was dealt
2026-08-13 (T-0366, #518). Every one of the six cards is later — the earliest on
2026-08-30 (T-0379's letter-list mint, #600, which is where `hh_reid_j_chester` and the
two Squire cards come from) and the three documented Reed households on 2026-09-04
(T-0514, #785). And the refusal is RIGHT to fire: `hh_reid_j_chester` carries a
Reid/Reed identity ruling whose own prose reasons about "James W. Reed, joiner, on the
1834 and 1835 polls", and two of the three documented Reeds — S. W. Reed and W. Reed —
are printed as joiners themselves. A reconstructed roof inside an open identity question
is exactly what refusal 5 exists to prevent.

**J. W. Reed's own evidence still puts him in the town, and it never came from this
deal.** `identity_master.json#id_reed_james_w` carries civic `poll_1834_092`
("Reed, James W."), civic `poll_1835_062` ("Reed, J.W.") and the Democrat of
31 December 1833; the grading ladder raised him to `attested` under G1a on that.
`census_1830`'s resident crosswalk has already ruled under D2 that J. W. Reed,
S. W. Reed, Thomas Reed and William Reed are four cards this project will not merge.
Nothing is removed and no confidence is moved.

**Therefore the owner.** The record stands, so the settlement must name whose it is, and
the answer was already written one block up in the same file: under
`tools/generate_inferred_households.py`, the household files went "to T-0489 for the 96
retired; **tools/synthesize_resident_research.py** for the five that survived". Exactly
five `hh_inf_` households survive in the tree and this is the fifth. The synthesizer
already gates it — the unplaced assertion its `--check` makes over every surviving
`hh_inf_` household, and the index grade counts that include this head.

**Shipped.**
- `1835_inferred_household_pass_ownership.json`: the `no_longer_owns` entry stops saying
  "nobody" and names the synthesizer; a new gated `refused_and_standing` block carries
  the refusal, the six cards that fire it, the measurement and the evidence that keeps
  the man.
- `tools/inferred_household_ownership.py`: `check_refused_and_standing` asserts the roof
  still stands with that head, that the deal does NOT seat it again, and that the cards
  firing the refusal have not all left — with five new `--self-test` cases, plus one that
  fails the settlement if any record is ever recorded as ownerless again.
- `tools/replace_invented_residents.py`: the docstring says four, says the fifth was once
  dealt, and says why it is refused and where it went. (The docstring did not in fact
  still say "five" — T-1228 had already taken that out; the only "five" left was a
  correct historical note about five FILES differing. What was missing was the fifth
  roof's story, which is what left the record reading as an orphan.)
