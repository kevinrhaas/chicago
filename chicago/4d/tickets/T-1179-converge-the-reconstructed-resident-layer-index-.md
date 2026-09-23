---
id: T-1179
title: Converge the reconstructed resident layer: index, sidecars, town census, People view and gates agree; every reconstructed person carries basis, seed, liberty and substitution rule; the population profile is re-run and the town reads complete against the model
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-19
pr: null
claimed_by: run 9/19/2026, 8:26:57 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T13:39:47.837Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35445442831
---

The closeout of the resident band, the way T-1144 closes the spend. After it, the owner's
sentence holds: *"All people should have a best profile … note for each attribute of the person
what is attested, inferred or reconstructed."*

**Acceptance:**

1. **Fixed point.** `reconstruct_residents_1835.py --check` (every stage), `rebuild_resident_index.py
   --check`, the three mints' `--check`, `compile_scene.py compile_people`, `town_census.py
   --check`, `export_resident_audit.py --check` all re-derive with zero drift; the audit table
   gains the reconstructed rows with their basis.
2. **Per-attribute completeness.** `profile_population_1835.py` re-run: every person has sex,
   age band, arrival, origin, reason, roles (or `not_employed` reason), presence, division,
   household relationship — each at a tier; the report's "unknown" columns read zero or list the
   attested/inferred rows where the sources conflict (T-1146's `contradicted`).
3. **The model met.** Headcount, sex ratio, age pyramid, household sizes, lodging occupancy,
   division split, trades — every table within the model's bracket; the order book's person and
   household buckets read filled; the town census screen shows residents / transients / garrison
   and the dwellings ratio.
4. **Substitution.** `substitute_reconstruction.py` (T-1190) handles persons: a new
   attested/inferred person retires the reconstructed one its `replaceable_by` matches, redirects
   the id, frees the bucket; self-test on a fixture.
5. **Liberties.** One entry per stage with `Scope:` counts the compiler agrees with; L1 restated
   (no figure drawn — a reconstructed person is a card, not a body in the scene).
6. **Visible.** People view: tier filter, transient/fort/reconstructed pills, per-attribute tier
   on the card; the "Reconstructing the town" card's person bars full; `smoke_renderer.mjs` walks
   a reconstructed card at both viewports.
7. `docs/RESEARCH/1835_resident_reconstruction.md` closes with the final tables and the exact
   counts by tier; `docs/STATUS.md` says what is unverified.

**Stop condition:** the resident layer is complete to the model, reproducible, and every invented
fact says how it will be replaced.

**Links:** every ticket in this band · T-1144 · T-1160 · T-1166 · T-1190.

---

**Finding (T-1314, 2026-09-18): the model a stage draws from is re-derived FROM the layer
that stage writes into.** `data/reconstruction/1835_town_model.json` counts the resident
layer — `people_the_layer_can_name`, the household-per-record ratio, the arrival-year
shares — and the reconstruction programme's `model_inputs.rows` point at that same file.
So every stage that adds a person moves the model the NEXT stage draws from. The first
stage to land measured the size of it: three people moved `share_of_the_layer_arriving_in_1835`
from 0.449 to 0.448 and moved no derived population figure at all, so nothing is wrong
today. It will not stay that size once T-1173–T-1178 add hundreds.

The model's own prose is already careful — "A count of the layer, not of the town" — and
that is exactly why this is convergence's problem rather than any one stage's: the fix is
a rule about WHICH people the model may count (the sources' people, not the programme's),
and it has to be made once, for every stage, with the order book re-derived under it. Three
other gates were narrowed the same way by T-1314 and are the precedent for the shape of it:
`spend_person_sex_age` (a reconstructed person no longer teaches the forename table),
`read_newberry_index` (an invented name is no longer a candidate for an archival lead) and
`profile_population_1835` (the refusal is now "no reconstructed person the programme cannot
re-derive", not "none at all").


---

**Finding (T-1172's closeout read, 2026-09-19): the 1,223-vs-643 gap is a UNIT mismatch, and
this ticket is where it resolves.** Recorded here because the owner asked whether the resident
reconstruction was going to overshoot by design. It is not, and the answer was already written
down in two places that are easy to read past.

`data/reconstruction/1835_readmissions.json` states the tension and then disposes of it in the
same object. `the_tension_this_leaves.what` is the alarming line — the order book models 643
households and ruling 787 more cards present takes the layer to 1,223, "nearly twice the model".
The two fields under it are the answer: the roster "is a licence on WHICH name a filler uses and
never a quota", and **736 of the layer's households are letter-list CONTAINERS holding one
person** — arguing for a person rather than for a dwelling. "A container is not a household in
the model's sense, and the two counts are not yet in the same unit." So the gap is not 787
surplus people; it is households and containers being counted against each other.

Its `whose_it_is` names this ticket: T-1171 draws families into the heads (done) and **T-1179
converges the layer against the model**. Neither could run before the presences were ruled,
which is what T-1172's stage was for.

The measurement on dev at 290cc65d9, for whoever picks this up:

| | |
|---|---|
| cards in the layer (`persons_total`) | 1,588 — attested 410, inferred 875, reconstructed 303 |
| established PRESENT on 1 Jul (`persons_present`) | 457 |
| the model's target (`persons_target`) | 2,535 |
| still to reconstruct | 2,081 |
| households: layer / present / model | 1,258 / 436 / 643 |
| letter-list containers inside that 1,258 | 736 |

Note that `reconstructed: 303` has NOT moved for T-1172's 909 re-admissions, and that is by
design rather than a lag: the stage writes to `data/residents/readmitted/` and declares
`"not_into": "data/residents/households/ and data/residents/index.json"`;
`tools/rebuild_resident_index.py` does not read that directory at all. 726 presence rulings and
183 minted cards are on disk waiting for this convergence. Anyone reading the front screen or
the index for "how far along is the reconstruction" is reading a number that the last stage
deliberately did not touch.

**See also T-1365**, filed the same day: the walk splash fills its bar toward 3,265 (the
NOVEMBER 1835 census) while this programme fills toward 2,535, and counts all 1,588 cards
against it rather than the 457 present. Acceptance 3 here owns the town census screen's final
form, so T-1365 is the interim fix and may be folded into this ticket.

**Finding (T-1174's merge, 2026-09-19): rebuild the MODEL before the stages that draw from
it, and verify the fixed point against `rederive.mjs --run`, not against the stage checks.**
Learned by getting it wrong twice while clearing #1497, and recorded because this ticket has to
do the same convergence for the whole band.

#1497 merged dev with 136 conflicts, 118 of them resident household cards carrying drawn values
the two sides disagreed on (`arrival_year` 1832 against 1835 on the same household). They were
not hand-picked: `reconstruct_residents_1835.py --check` names the remedy itself — "a draw that
cannot be reproduced is not a reconstruction. Run --stage attribute_fill_arrival --build" — so
dev was taken as the base and the programme re-ran its own draws.

**The wrong order cost four passes and was still red.** Rebuilding only the stages —
`attribute_fill_arrival`, then `readmissions`, then `women_and_children`, then the order book —
reached a state where `reconstruct_residents_1835.py --check` exited 0 on every stage. The gate
then failed FIVE steps:

```
* the reconstruction programme answers for every reconstructed resident
* every re-admission re-derives, and no refusal it stands beside has moved
* the 1835 town model re-derives, and every figure is bounded and says what it rests on
* the 1835 population profile re-derives from the resident layer, on every axis
* the 1835 reconstruction order book re-derives, and no bucket is overfilled
```

The cause is the T-1314 finding above, read forwards: the model is re-derived FROM the layer the
stages write into, so a stage rebuild moves the model, and every stage that draws from the model
is then drawing from one that predates its own rebuild. The first pass never rebuilt
`tools/model_town_1835.py` at all. Each stage agreed with itself, which is why the stage checks
were green — a stage's `--check` cannot see that its own input is stale.

**The right order converges in ONE pass:**

```
python3 tools/model_town_1835.py --build
python3 tools/reconstruct_residents_1835.py --stage attribute_fill_arrival  --build
python3 tools/reconstruct_residents_1835.py --stage readmissions            --build
python3 tools/reconstruct_residents_1835.py --stage women_and_children      --build
python3 tools/profile_population_1835.py --build
python3 tools/build_order_book_1835.py --build
```

Then all four of `reconstruct_residents_1835.py --check`, `model_town_1835.py --check`,
`profile_population_1835.py --check` and `build_order_book_1835.py --check` exit 0 — **and still
exit 0 after `node tools/rederive.mjs --run`**, which is the test that matters and the one this
ticket's acceptance 1 is written around. A fixed point that the full derived-layer rebuild undoes
is not a fixed point; the stage checks alone will not tell you which you have.

Acceptance 1 lists the `--check` commands but not an ORDER for the builds, and the order is the
whole difference between one pass and an oscillation. Whoever works this should write it down
where the programme can be run from, not leave it to be rediscovered.

State after that merge, for the next reader: the population profile covers 2,144 persons against
the model's 2,535 target; 900 re-admissions and 124 female-headed households (556 people — 124
women and 432 others) are built and gated, and none of them reaches `index.json` yet.

**Finding (T-1349's merge, 2026-09-19): a new stage's invented NAMES can move the stages
above it and, worse, can move a research pass.** Stage `garrison` drew 125 people over the
sixty-five surnames the pools hold. Two things broke, and both are this ticket's to
generalise:

* `reconstruct_women_children.py` redrew 43 of its own cards, because its `real_names()`
  folds every name in the layer including `rc_` ones — so a stage BELOW it in the programme
  changed what it steps past. A later stage should not be able to move an earlier one.
* `mint_civic_residents.py` minted a 393rd civic person where dev mints 392, because six
  invented Tuttles standing beside the town's one real Tuttle made `id_tuttle_james_b`
  unresolvable. **An invention that changes how a source is READ has become evidence.**

T-1349 fixed both from its own side with one refusal — *a drawn soldier may not bear a
family name any attested or inferred person of this town bears* — and with it in force the
civic mint returns to 392 and `women_and_children` redraws nothing. Forty-nine of the
sixty-five pool surnames are free of the named layer, which is enough for 125 people and
will not be enough forever: **T-1173's trade households and T-1175's lodgers draw hundreds
more over the same pools.** The refusal is written generally enough to lift into the
programme, and the convergence this ticket owns is where that decision belongs.

The rebuild order recorded above still holds, with one insertion — stage `garrison` goes
AFTER `women_and_children`, which is its position in the programme's `stages` array:

```
python3 tools/model_town_1835.py --build
python3 tools/reconstruct_residents_1835.py --stage attribute_fill_arrival  --build
python3 tools/reconstruct_residents_1835.py --stage readmissions            --build
python3 tools/reconstruct_residents_1835.py --stage women_and_children      --build
python3 tools/reconstruct_garrison_1835.py                                  --build
python3 tools/rebuild_resident_index.py --write
python3 tools/profile_population_1835.py --build
python3 tools/build_order_book_1835.py --build
```

**Correction (2026-09-19, same night): the set is SIX tools, and a fixed list is the wrong
shape of answer.** The finding above names four builds in an order and reads as though the
order is the whole of it. It is not, and the list was wrong three times in one evening. Each
time the error had the identical shape: the checks that happened to be run came back green, the
tree was called converged, and the GATE knew about a reader that the list did not.

| attempt | what was rebuilt | what the gate then found |
|---|---|---|
| 1 | the three stages, no model | 5 red — model, profile, order book, re-admissions, programme |
| 2 | only the stale piece (`model --build`, repeatedly) | a 2-cycle: model green, `attribute_fill_arrival` red, three passes running |
| 3 | all four, in order | 2 red — the 1835 transient cohort and the attribute tiers |

The two missing from attempt 3 are `tools/model_transients_1835.py` and
`tools/migrate_attribute_tiers.py`. Both read the resident layer; neither was in anybody's
mental model of the set. With them the whole thing converges and `rederive.mjs --check` reads
clean:

```
python3 tools/model_town_1835.py          --build
python3 tools/reconstruct_residents_1835.py --stage attribute_fill_arrival --build
python3 tools/reconstruct_residents_1835.py --stage readmissions           --build
python3 tools/reconstruct_residents_1835.py --stage women_and_children     --build
python3 tools/reconstruct_garrison_1835.py                                 --build
python3 tools/profile_population_1835.py  --build
python3 tools/build_order_book_1835.py    --build
python3 tools/model_transients_1835.py    --build
python3 tools/migrate_attribute_tiers.py  --build
```

**Take that as a starting point and never as a stopping point.** The set is defined by WHAT
READS THE LAYER, the layer gains readers as this project grows, and the only authority on the
current set is `tools/check.sh`. So the method, rather than the list:

1. Run the sequence you have.
2. Gate. Read the steps it names red.
3. Rebuild those, re-run the WHOLE sequence — not the step the check named. Attempt 2 above is
   why: the check names the stage that is stale, and the cycle runs through a stage it does not
   name. Rebuilding only what the check names never converges.
4. Gate again. Repeat until it names nothing.

Two more traps worth having in writing, both paid for on #1497 and #1502:

- **A stage's `--check` cannot see that its own input is stale.** Every stage agreed with itself
  in attempt 1 while the model underneath them all was out of date. Green stage checks are not
  evidence of a fixed point.
- **`rederive.mjs --run` can UNDO the fixed point** — it re-runs manifest steps that write the
  layer the model counts, which is T-1363. So the fixed point has to be verified against a
  `rederive.mjs --check` that reads clean AFTER the sequence, and a `--run` late in the
  procedure means starting over.

Acceptance 1 of this ticket is a fixed point over exactly this set. It lists the `--check`
commands and, as written, neither the order nor the method. Whoever works it should fix that in
the acceptance itself rather than trusting this finding, which will also be out of date the
moment another reader of the layer is added.

---

**FINDING from T-1364, 2026-09-19 — the arrival table is a circle, and only a rebuild can
open it.**

T-1364 fixed the two `arrival_and_origin` FIGURES, which counted the whole compiled layer
over a denominator that excluded every reconstructed person in it. The share read 1.63 and
its complement read -809. Both figures now divide the named layer by the named layer, which
is the rule `build_population` already applied to the population floor.

**The TABLE under them was deliberately left alone, and this ticket is why.**
`arrival_and_origin.tables.arrival_year_of_the_known_layer` is named for the known layer and
is computed over the WHOLE compiled layer, reconstructed people included — and
`tools/reconstruct_residents_1835.py` (`arrival_fill_plan`, `plan_household`) draws every
filled arrival year out of its `year`/`people` columns. So the distribution the arrival
stage draws from is computed over a layer that same stage has already written into: each
pass re-reads its own last draw, and the more people the reconstruction adds, the more the
table is a picture of the reconstruction rather than of the evidence.

Cutting the table to the named layer is therefore **not a figure change**: it redraws every
arrival ever dealt, on every card the arrival stage owns, and then moves the model those
cards are counted back into. That is a rebuild in this ticket's own sequence, in this
ticket's own order, and it is exactly the class of change the "rebuilding only what the
check names never converges" trap above is about. It is recorded here rather than done on a
figures ticket.

What T-1364 did leave in place for it:

- The table's `unit` now says on its face that it is the whole compiled layer, and a
  `not_the_figures_denominator` line says the figures above do not share its denominator.
  Its `share` column divides by the table's own total, so the column sums to 1 instead of
  dividing a whole-layer count by a named-layer one.
- `model_town_1835.py --self-test` carries a guard that refuses the build if the arrival
  numerator ever outruns its denominator again. A rebuild that re-cuts the table will trip
  nothing; a rebuild that re-crosses the two populations will.

**Links:** T-1364 · `tools/model_town_1835.py` § `build_arrival` ·
`tools/reconstruct_residents_1835.py` § `arrival_fill_plan`.
