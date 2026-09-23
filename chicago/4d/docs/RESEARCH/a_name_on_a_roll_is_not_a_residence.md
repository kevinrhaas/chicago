# A name on a roll is not a residence — the written ruling on all 718 name-on-a-roll units

**T-1297**, the second piece of **T-1236**. Registers:
`data/research/civic/spend_rulings.json` (496),
`data/research/census_1830/spend_rulings.json` (204) and
`data/research/directories/spend_rulings.json` (18), all derived by
`tools/spend_name_on_a_roll_rulings.py` and re-derived by its `--check` in the gate.

## What was open

Three domains held 718 units that the closed research-spend ledger could not place, and
they were all one question — **a name on a roll**:

| units | corpus | why the ledger could not place it |
| ---: | --- | --- |
| 345 | the 1833 poll list, the 1833 tax list, the 1834 and 1835 poll lists of the Town of Chicago | A roll entry carries a name, a list and a line, and nothing that self-classifies: no `describes_date` the year test can read, no `outside_chicago` flag, no `superseded_by`. |
| 200 | the 1830 heads of family of the enumerator's division headed *Peoria & Putnam Counties & Territory attached* | Same shape. The schedule's date lives in the file header, not in the row. |
| 134 | the Black Hawk War enrollments at Chicago, 1832 | Same shape again, and its crosswalk's target is the voter lists rather than the residents layer. |
| 39 | the town findings of Andreas (1884), the Chicago *Democrat* (1835), Norris (1844), Fergus (1839) and the lists' own readings | Prose claims whose `describes_date` names a year *at or before* 1835 even where the book is decades later, so the ledger's `year > 1835` test never fires. |

So all 718 fell to the one outcome left — `unresolved` — and the epic owned them by
default rather than by argument.

## The rule every unit is ruled under

**A NAME ON A ROLL IS NOT A RESIDENCE ON THE SCENE DATE.** Under the ladder ratified
2026-09-03, an *earlier* source corroborates and dates and never promotes — a man at
Chicago in 1830 or 1832 is not thereby at Chicago on 1 July 1835 — and a *later* source
does not promote either. What a roll can do is **bound** the presence of a person the town
already holds, and drawing an arrival from a bound is the arrival pass's work, not this
file's.

## The twenty-one rulings

### civic — 496

| units | rule | reaches | what it says |
| ---: | --- | --- | --- |
| 202 | `the_poll_book_bounds_a_held_residents_presence` | → **T-1169** | A poll entry the crosswalk joins to a person the town holds. A man who voted was here that day; the date bounds his presence and nothing more. |
| 90 | `the_1833_tax_roll_bounds_property_and_not_presence` | → **T-1169** | The same, on the 1833 *tax* list — which this domain's own reading (`v005`) has already ruled a property roll and not a check on residence. The bound is on his taxable standing, not his body. |
| 83 | `the_enrollment_index_prints_no_surname` | → **T-1159** | The 1832 index prints the name without a surname comma — the French and Potawatomi forms, 83 of 134 rows. A surname-indexed crosswalk cannot reach it; the name is carried exactly as printed and nothing is inferred about who the person was. |
| 38 | `the_enrollment_names_a_man_the_rolls_do_not_carry` | → **T-1159** | Enrolled at Chicago in 1832 under a name the 1833-1835 rolls do not reach. The crosswalk's target is those rolls, so this file may not say the *town* has no such person. |
| 36 | `the_roll_names_a_person_the_town_does_not_hold` | → **T-1159** | A named person on a roll of the Town of Chicago the crosswalk can join to nobody. Read and withheld — the borderline roster's case exactly. |
| 17 | `a_roll_agreeing_on_surname_alone_is_never_a_merge` | refused | The crosswalk declares a candidate, not a match: an initial that fits two men, or no forename at all. A surname-only join is always a refusal here. |
| 8 | `the_1884_history_is_later_evidence_about_the_town` | later_only | Andreas, forty-nine years after the scene. May corroborate and may date; may not assert. |
| 8 | `the_1832_enrollment_may_bound_a_rolled_mans_arrival` | → **T-1169** | The index and one roll reading agree initial for initial. The crosswalk says the same *name* stands on both and does not say it is the same *man*; **if** the identity holds, the presence goes back to 1832. |
| 5 | `an_ambiguous_enrollment_agreement_is_never_a_merge` | refused | More than one reading agrees, and nothing printed separates them. A contested agreement is a candidate, never a merge. |
| 4 | `the_finding_describes_the_roll_and_not_the_town` | refused | A finding about the *list* — what it prints, which election it is not the poll book of, which discrepancy the search failed to resolve. A statement about the evidence names no person to mint. |
| 3 | `the_democrats_date_falls_after_the_scene_date` | later_only | The town's own paper, on the charter election of 10 July and the ordinance code of 5 August 1835. The ledger's year test reads `1835` and not "after 1 July 1835". |
| 2 | `the_towns_charter_is_not_a_person_or_a_place` | refused | The act enlarging the corporation's powers, and the section fixing how its Board is elected. True of the town on the scene date, and still neither a person, a household nor a structure. |

### census_1830 — 204

| units | rule | reaches | what it says |
| ---: | --- | --- | --- |
| 121 | `the_1830_surname_stands_in_no_town_household` | refused | No person in the town carries the surname at all. The crosswalk states the three readings that stay open — gone by 1835, living in the part of the division that was never Chicago, or never found — and settles none. On all three the answer to what the unit spends into the town is **nothing**, which is a complete answer here. |
| 63 | `the_1830_surname_only_match_was_refused_in_the_crosswalk` | refused | Already refused by name: shares only a surname with a town person. The refusal was written down so the next sweep would not make the same match; the ledger now carries it. |
| 14 | `the_1830_line_bounds_a_held_residents_presence` | → **T-1169** | Surname *and* given name agree with a person the town holds. Carried by the crosswalk as earlier evidence that grades nothing on its own; a bound five years before the scene. |
| 2 | `the_1830_town_finding_is_earlier_evidence` | refused | The garrison enumerated as one household, and the two LaFramboise households at the forks. The town it describes is the town of 1830. |
| 2 | `the_1830_schedule_describes_its_own_making` | refused | A heavy rule the enumerator drew, and the fact that Chicago had no county of its own and the schedule never writes the word. Readings of the document, not of the town. |
| 1 | `the_1830_line_names_the_garrison_and_not_a_person` | refused | *U S Garrison Fort Dearborn — Maj John Fowle Commr*. Not a person and it may never reach one. |
| 1 | `the_1830_surname_variant_is_a_candidate_and_not_a_merge` | → **T-1169** | *Archibald Clybourn* against the town's *Archibald Clybourne*: the given names agree and the surnames differ by a silent terminal e. A candidate, never a merge — carried forward with the identity still open. |

### directories — 18

| units | rule | reaches | what it says |
| ---: | --- | --- | --- |
| 16 | `the_1844_sketch_is_later_evidence_about_an_earlier_year` | later_only | Norris's historical sketch of 1844 on 1673, 1795, 1812, 1832-1836 — including his 1835 population figures of 5,500 and "not much less than 3,000". A later man's estimate and a later man's summary. |
| 2 | `the_1839_register_is_later_evidence_about_an_earlier_year` | later_only | Fergus's 1839 register: Cook County organised 1831, and its retrospective population column giving 3,265 for 1835. |

Two orderings are decided in those tables and held by the tool's self-test. **The outcome
outranks the roll**: an *unmatched* entry on the tax list is ruled by its outcome, because
the property-roll limit only bites where there is a held person for it to bite on. And
**the crosswalk outranks the name**: a variant spelling, an ambiguity or a contested
agreement stays a candidate, and no ruling here promotes one.

## What the residue does to the 1835 town

**Nothing, directly.** Not one unit adds a person to 1 July 1835, changes a grade, moves a
household or reopens an identity a crosswalk adjudicated. What the corpus leaves behind is
two hand-offs, both narrower than the bodies they came from:

* **315 units to T-1169.** 292 roll entries and 14 census lines that name a day on which a
  person this town holds was in Chicago or its district, plus 8 enrollments that push a
  presence back to 1832 if their identity holds, and the one Clybourn(e) variant. Ceilings
  on arrival and nothing else; T-1169 owns arrival and will read them there.
* **157 units to T-1159.** Names on the town's own rolls and in the 1832 enrollment index
  that the residents layer does not carry — 36 from the poll and tax lists, 38 enrollments
  the rolls do not reach, and the 83 printed without a surname. They are not residents and
  this file does not make them any; they are candidates for the borderline roster, each
  with its source and its reason.

The other 246 units are closed decisions, not missing work. The largest of them is the
one the parent ticket predicted: 121 of the 1830 heads of family stand in no town
household, and **"nothing" is the true and complete answer** for every one.

## What is derived, and why

Every note is built from the unit's own fields — its list and the list's date, its leaf
and entry, its company and rank, its `describes_date` and its own normalized sentence, and
the crosswalk's verbatim rule — so a reader can set the note beside the row and see it says
what the row says. Nothing is typed, because 718 typed notes would be a *worse* register:
they would drift, and no one could prove a note still matched its row.
`tools/spend_name_on_a_roll_rulings.py --check` is that proof, and it runs in
`tools/check.sh` beside `--self-test`, which holds all fourteen derived rules over a row
built to fall under each and fails on a rule that never fires over the committed corpus.
