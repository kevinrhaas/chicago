---
id: T-1304
title: Reconstruct the sex and age no evidence can settle: the population model's sex × age band per bucket seeded by person id, the letter lists at their measured adult-male rate, the known-profile report showing three tiers, and the person card printing sex and age with its tier and reason
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1168
opened: 2026-09-18
closed: 2026-09-18
pr: 1450
claimed_by: run 9/18/2026, 4:20:24 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T10:29:08.974Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35328745449
---

Reconstruct the sex and age no evidence can settle: the population model's sex × age band per bucket seeded by person id, the letter lists at their measured adult-male rate, the known-profile report showing three tiers, and the person card printing sex and age with its tier and reason.

Piece 2 of 2 of **T-1168 — Fill sex and age for every attested and inferred person: recorded where a source says, inferred from forename, office or register role where the evidence about that person allows, reconstructed from the population model otherwise — each value with its tier and reason**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Every person T-1303 left without a sex carries one, drawn from the population model's
  sex share for that person's bucket and seeded by person id, graded `reconstructed` with
  its basis, seed and `replaceable_by` per T-1158.
- The 205 people known only as an initial off a letter list are sexed at the measured
  adult-male rate of a letter list, and the measurement is stated rather than assumed.
- Every person carries a birth year or an age band at some tier; a reconstructed band is
  the model's band and never a fake exact year.
- The known-profile report (T-1160) re-runs and its sex and age tables show three tiers.
- The person card prints a reconstructed sex and age the way it already prints a read one
  — with the tier, the reason, the seed and what would retire it.

**What T-1303 left, measured:** 593 people without a sex (205 initial-only, 379 bearing a
forename this project holds no evidence about, 3 on a named ambiguity, 6 a collective
description) and 1,218 without a birth year.

**Inherited from T-1303, and it is the first thing to settle:** no age may be derived from
an adult status until the rule is in a source record. A poll list, a civic office or a
trade says a person was an adult and says nothing about when they were born; the
franchise's own age rule is not in any source this project holds. 244 people carry civic
evidence and 241 a role, and that is the largest single block of age the model has to
draw for — either find the statute and cite it, or draw the band from the model and say so.

**Done (PR to follow).** 593 people carried no sex and 1,218 no age; 587 sexes and 1,212
age bands are now drawn, and every one of them says on the card that it was drawn, from
what, with which seed, and what would retire it.

  sex        689 -> 1,276 of 1,282   (587 drawn: 552 male, 35 female)
  age band     0 -> 1,276 of 1,282   (1,212 drawn, 64 read off a birth year)

**The rate is measured, and the measurement is this layer's own.** Roll by roll, over the
people whose sex T-1303 settled: letter lists 351/372 male (94.4%), civic rolls 197/208
(94.7%), unclaimed 83/92 (90.2%). A roll settling fewer than 50 names is not measured on
its own and draws at the pooled rate, 93.9% — `documented` and `placed` do that, for 27
people. `data/reconstruction/1835_sex_age_model.json` holds it and `--check` re-derives it.

**AND THE MEASUREMENT'S BIAS RUNS ONE WAY, stated rather than smoothed.** The forename
table those rates are measured through was derived mostly on this layer's men, so a
woman's forename is likelier to be missing from it and to fall into the group being drawn
for. Every rate is a CEILING on its roll's male share, not a point reading, and the 552/35
split leans male by an amount this pass cannot bound (liberty `L-rc-sex-rate`).

**THE INHERITED FINDING IS SETTLED THE SECOND WAY T-1303 OFFERED.** There is no statute in
this corpus, so no age is derived from an adult status. The conditioning is DECLARED as a
liberty (`L-rc-age-conditioning`) and printed on every card that rests on it: 20-and-over
for a poll, tax or muster list (192 people); 15-and-over for any other roll naming a person
in their own right (1,019); under-15 where the record calls them a child (1).

**A BAND, NEVER A YEAR.** The bands are the 1840 Chicago schedule's own columns, used
exactly as its `what_this_may_calibrate` allows and never to name or supply anybody. No
`birth_year` is written by this pass, and the self-test holds that.

**ONE ACCEPTANCE BULLET IS MET WITH A REFUSAL, and it is deliberate.** "Every person
carries one" is met for 1,276 of 1,282. The six collective descriptions — "The four Temple
children" — are rows about more than one person, and a single sex or a single band would
turn a group into a person. Each now carries an explicit `unknown` block saying that, which
is a stated refusal rather than a silent gap; T-1303's refusal is kept word for word.

**Also fixed, because the report was reading its own fills as evidence.** The known-profile
report (T-1160) called any sex on a card `recorded` and so printed `recorded 689` over a
layer where 99 people have a source. It reads the rule off the `sex_basis` block now, and
its sex and age tables each show the three tiers.

**And two gates had to learn the boundary.** `spend_person_sex_age.py` stripped any
`sex_basis` as its own when re-deriving, which would have failed all 587 drawn people; and
its forename table was derived from every person carrying a sex, which would have read the
draws back in as evidence and widened the table off a coin toss. Both now turn on the tier.
`migrate_attribute_tiers.py` overwrote a block's basis from its own table, which would have
filed a draw under an argued rule and lost its seed; a writer that states its own basis now
keeps it, and its drawn values are published as one row per model row rather than 1,799
rows of prose.
