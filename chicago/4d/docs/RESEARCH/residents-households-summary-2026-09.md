# What the residents and households look like — September 2026

**The owner's ask, 2026-09-03:** *"then i would like a summary of what the residents and
households look like, since you have good census data now on many you should be able to
improve that."* Delivered under **T-0517**.

**Scene date:** 1835-07-01 · **Layer:** `data/residents/` · **Dossier:**
`docs/RESEARCH/residents_1835.md` · **Audit:**
`chicago/reference/resident-research/final/audit/`

---

## How to re-derive this document

Every figure below is printed by one command, and the command is named above the table it
prints. Nothing here is typed from memory, and a later run that finds a different number
has found a change in the layer rather than a mistake in the prose.

```
cd chicago/4d
python3 tools/summarize_residents.py            # every section, in this order
python3 tools/summarize_residents.py grades     # one section
python3 tools/summarize_residents.py --list     # the section names
```

The tool reads `data/residents/index.json` and the household records it manifests,
`data/town_census.json`, `data/research/residents/identity_master.json` and the gated audit
table. It writes nothing. The one judgement in the programme — which category a source id
belongs to — is made once, in `tools/export_resident_audit.py`, and imported rather than
repeated.

---

## 1. The size of the layer, and how far it has moved

`python3 tools/summarize_residents.py overview`

| measure            |  now | #668 baseline | change |
|--------------------|-----:|--------------:|-------:|
| households         | 1380 |           824 |   +556 |
| person entries     | 1404 |           848 |   +556 |
| attested           |  526 |           117 |   +409 |
| inferred           |  878 |           731 |   +147 |
| reconstructed      |    0 |             0 |     +0 |
| projected_resident |  719 |           706 |    +13 |

The baseline is the state of the layer after the 2026-09-02 synthesis (PR #668), as printed
in `docs/RESEARCH/resident-household-synthesis-2026-09-02.md`. **The layer has grown by two
thirds and its centre of gravity has moved.** The +409 on `attested` is the consolidation
and the resident-research cohorts spending evidence that was already adjudicated, not new
reading: a person the town already carried, corroborated by a second body of record, moves
up a rung without anybody being minted.

`reconstructed` is 0 and is meant to be. The 108 hypothesised people the reconstructed
programme had minted were retired in the synthesis; the grade stays in the vocabulary so a
later explicit reconstruction pass can use it without a schema change.

## 2. Grade, subtype and the rung that decided it

`python3 tools/summarize_residents.py grades`

| grade         | persons | share | subtype                            |
|---------------|--------:|------:|------------------------------------|
| attested      |     526 | 37.5% | (none) 526                         |
| inferred      |     878 | 62.5% | (none) 159, projected_resident 719 |
| reconstructed |       0 |  0.0% | -                                  |

| ladder rung      | persons | share |
|------------------|--------:|------:|
| G1a              |      29 |  2.1% |
| G1b              |     315 | 22.4% |
| G1c              |      11 |  0.8% |
| G2a              |      35 |  2.5% |
| G2b              |      25 |  1.8% |
| G2c              |      35 |  2.5% |
| G3               |      81 |  5.8% |
| (no ladder_rule) |     873 | 62.2% |

531 of 1404 persons carry a rung — the civic mint writes one and the earlier mints did not.
**873 do not, and that is a real gap in the audit trail rather than a gap in the evidence**:
those people were graded before the ladder existed, by passes whose reasoning is in their
notes and not in a machine-readable field. T-0692 is the ticket for the 18 of them that are
graded `inferred` on two or more sources; the rest are the letter-list mint, whose rung is
G2e by construction and unwritten.

## 3. Where they are, and whether they were here

`python3 tools/summarize_residents.py division`

| division     | households | present | absent | uncertain |
|--------------|-----------:|--------:|-------:|----------:|
| south        |         52 |      33 |      0 |        19 |
| north        |         11 |       8 |      1 |         2 |
| west         |          6 |       4 |      0 |         2 |
| fort         |          2 |       2 |      0 |         0 |
| outside_town |          1 |       1 |      0 |         0 |
| unplaced     |       1308 |     438 |      0 |       870 |
| TOTAL        |       1380 |     486 |      1 |       893 |

**94.8% of households are `unplaced`.** That is the single largest fact about this layer.
The town has 72 households in a named division and 1,308 that the sources put in Chicago
without putting them anywhere in it — a post-office letter list gives a name and no street.

Presence is the other axis and it is honest in the same way: 486 households are `present` on
1 July 1835, one is `absent`, and 893 are `uncertain`. `uncertain` is not a failure of the
record-keeping; it is what a letter list of 1834 licenses you to say about a man on 1 July
1835.

## 4. Sex

`python3 tools/summarize_residents.py sex`

| sex            | persons | share |
|----------------|--------:|------:|
| female         |      14 |  1.0% |
| male           |      84 |  6.0% |
| (not recorded) |    1306 | 93.0% |

The schema takes `sex` only where a source states or unambiguously implies it, and 93% of
the layer's people come from lists — poll books, letter lists, tax rolls — that print an
initial and a surname. **The 84:14 split is a property of those lists, not of the town**, and
must never be read as a sex ratio. The 1840 census sheets carry sex by age band for the
households they enumerate, which is the route to a real figure and is the 1840 bridge's job,
not this layer's.

## 5. Trades

`python3 tools/summarize_residents.py occupation`

**135 of 1404 persons (9.6%) carry a trade** that is not `none_recorded`; 1,269 read
`none_recorded`. Of the 135, 127 are graded `attested` and 8 `inferred`.

| the trade is printed by | persons |
|-------------------------|--------:|
| book                    |      78 |
| newspaper               |      59 |
| secondary               |       8 |
| church                  |       2 |
| directory               |       1 |
| civic                   |       1 |

61 distinct trades stand in the town. The top of the list is the eleven attorneys, eight
tavern keepers, seven merchants, six schoolteachers and the five each of blacksmiths,
carpenters and physicians; the full distribution is in the command's output.

**The interesting number is the `directory` row: one.** The 1839 and 1843 Chicago
directories print a trade beside almost every name, and this layer reads a trade off them
once. That is the largest cheap gain available to the occupation coverage, and it is what
T-0669's rule — a later printing may carry a person's trade and address forward, dated and
graded as later evidence — exists to unlock.

## 6. Household size

`python3 tools/summarize_residents.py sizes`

| persons in the household | households | share |
|-------------------------:|-----------:|------:|
|                        1 |       1360 | 98.6% |
|                        2 |         17 |  1.2% |
|                        3 |          2 |  0.1% |
|                        4 |          1 |  0.1% |

Mean household size **1.02**. 20 households (1.4%) hold more than one person.

**This is the layer's most misleading figure if read as demography.** The town census of
November 1835 counts 3,265 people in 398 dwellings — 8.20 to a *dwelling* — and T-0507
measured a mean *household* of 5.02 in the 1840 enumeration, from which it followed that a
dwelling held more than one household. A mean of 1.02 here says only that a source that
names one man licenses one person, and the mints refuse to invent his wife. Every household
of one is an honest floor, not an estimate.

## 7. Evidence, by domain and by overlap

`python3 tools/summarize_residents.py evidence`

| domain    | persons citing at least one | share |
|-----------|----------------------------:|------:|
| newspaper |                        1160 | 82.6% |
| civic     |                         288 | 20.5% |
| census    |                          30 |  2.1% |
| church    |                          47 |  3.3% |
| book      |                         192 | 13.7% |
| directory |                         208 | 14.8% |
| secondary |                          69 |  4.9% |

| domains on the card | persons | share |
|--------------------:|--------:|------:|
|                   0 |       3 |  0.2% |
|                   1 |     973 | 69.3% |
|                   2 |     304 | 21.7% |
|                   3 |      88 |  6.3% |
|                   4 |      31 |  2.2% |
|                   5 |       5 |  0.4% |

| what the person rests on         | persons | share |
|----------------------------------|--------:|------:|
| the_letter_lists_alone           |     562 | 40.0% |
| corroborated_across_categories   |     428 | 30.5% |
| one_source                       |     392 | 27.9% |
| two_or_more_sources_one_category |      19 |  1.4% |
| no_source                        |       3 |  0.2% |

**Letter-list-only 727 (51.8%) · bridged to a named 1840 census row 3 (0.2%).**

Two of these numbers should be read together. 727 people carry the `letter_list_only` flag
but only 562 have `the_letter_lists_alone` as their audit result — the difference, 165, is
people who came in from a letter list and have since been corroborated by another body of
record. That difference is what the consolidation and the research cohorts have actually
bought.

The three people with no source at all are the source-counted placeholders — an unnamed
wife, "and family" — that the schema keeps precisely so they are not counted as individuals.

## 8. What the research programme concluded

`python3 tools/summarize_residents.py research`

| research outcome        | persons | share |
|-------------------------|--------:|------:|
| (no research row)       |     555 | 39.5% |
| no_corroboration_yet    |     540 | 38.5% |
| no_corroboration        |     176 | 12.5% |
| candidate_identity      |      72 |  5.1% |
| corroborated_enrichment |      29 |  2.1% |
| corroborated            |      20 |  1.4% |
| (no outcome)            |       7 |  0.5% |
| candidate               |       5 |  0.4% |

14 research tickets are cited on a card; 49 persons carry an asserted identity.
`no_corroboration_yet` and `no_corroboration` are different claims and the distinction is
load-bearing: the first says the corpus has not been searched to exhaustion, the second that
it has and found nothing. Neither is evidence that the person did not exist.

## 9. What is consolidated, and what is unspent

`python3 tools/summarize_residents.py consolidation`

| identity_master                            | count |
|--------------------------------------------|------:|
| identities                                 |  6742 |
| appearances                                | 10448 |
| identities on a card                       |  1395 |
| identities in two or more domains          |  1600 |
| derived refusals                           |  1888 |
| declared merges                            |   304 |
| appearances moved by a landed adjudication |    82 |
| declared refusals                          |  1617 |

| domain       | identities appearing in it |
|--------------|---------------------------:|
| directories  |                       2921 |
| newspapers   |                       2101 |
| residents    |                       1395 |
| old_settlers |                        735 |
| census_1840  |                        697 |
| church       |                        480 |
| civic        |                        386 |

**1,395 of 6,742 consolidated identities are on a household card. 5,347 are not** — and most
of them should not be, because they are 1839 directory entries and 1840 census heads whose
only dated appearance is after the scene year, which rung G0 refuses outright. The number to
watch is not 5,347 but the 1,600 identities that appear in two or more domains: convergence
across bodies of record that did not copy each other is what rung G1c promotes on.

## 10. Where the people meet the buildings

`python3 tools/summarize_residents.py town`

| measure                                                       | value |
|---------------------------------------------------------------|------:|
| persons in a household whose lives_at resolves into the scene |    29 |
| households so housed                                          |    20 |
| households without a dwelling                                 |  1360 |
| roofs standing in the scene                                   |   359 |
| roofs the programme targets                                   |   662 |
| the town census of November 1835 — people                     |  3265 |
| the town census of November 1835 — dwellings                  |   398 |

20 of 1380 households name a `lives_at`; 50 name a `works_at`. **359 roofs stand and 20 of
them hold a named household.** The population layer and the building layer are, at this
date, almost disjoint — the town has people and it has houses and it very rarely knows which
people are in which house.

## 11. What remains unresearched or unresolved

`python3 tools/summarize_residents.py gaps`

| unresolved              | persons | share | what it means                                            |
|-------------------------|--------:|------:|----------------------------------------------------------|
| no_research_row         |     562 | 40.0% | no research row has ever looked at them                  |
| candidate_identity_open |      77 |  5.5% | a candidate identity is open and unasserted              |
| conflicting_evidence    |      97 |  6.9% | the evidence on the card conflicts                       |
| single_source           |     954 | 67.9% | one source id and no second category to check it against |
| no_source               |       3 |  0.2% | no source id at all                                      |
| unplaced                |    1308 | 93.2% | no division                                              |
| no_address              |    1328 | 94.6% | neither a lives_at nor a works_at                        |

- 8 households carry `review_required`, 8 `touches_removal` — the Indian agency's
  establishment, the families with Native kin and the two Native households the sources name
  at Wolf Point. Nothing in this layer improvises Native presence or depiction.
- 1,306 of 1,404 persons have no recorded sex.
- 10 names sit in `researched_not_resident`: researched, and deliberately **not** in the
  town. Adding to that list is preferred to deleting from it.

## 12. The audit, re-run

T-0512 built `chicago/reference/resident-research/final/audit/` as a baseline and asked
T-0517 to re-run it once the update tickets landed, so that two audits bracket the
programme. Re-run under this ticket:

```
python3 tools/export_resident_audit.py --build
python3 tools/export_resident_audit.py --check
```

**1,404 rows re-derive, and the committed table is already identical to them** — the CSV and
the README come back byte-for-byte unchanged, so the audit on `dev` is current rather than
stale, and the closing bracket is a confirmation rather than a rewrite. (The XLSX differs on
every build in its zip timestamps alone and is not re-committed for that.) The audit's own
coverage table and this document's § 7 are two readings of the same rows and agree; where
they are phrased differently, the audit counts *people carrying a record of a kind* and this
document also counts what those records overlap.

---

## The report for the owner

**The town's people are now a large, honest and very thin dataset.** 1,380 households and
1,404 person entries stand where 824 and 848 stood after the September synthesis — a two-
thirds gain bought almost entirely by *spending* evidence that had already been adjudicated
rather than by reading anything new. 526 people are `attested`, up from 117; the
`reconstructed` grade is empty and stays that way until an explicit reconstruction pass wants
it. Every person is a real name from a real record. Not one was invented.

**The thinness is in the attributes, not the names.** 9.6% carry a trade; 7.0% have a
recorded sex; 1.4% live in a household of more than one person; 5.4% resolve an address of
any kind. 67.9% rest on a single source id with no second *kind* of record to check it
against, and 51.8% arrived from a post-office letter list. The mean household of 1.02 against
the town census's 8.20 people per dwelling is the whole shape of the problem in one
comparison: the sources this project holds name individuals, and a town is made of families.

**The three cheapest gains are all locations, and all of them are already adjudicated.** The
directories print a trade beside nearly every name and this layer has read one off them.
99 later addresses stand adjudicated — the figure the queue's own measurement of
2026-09-04 puts against the 20 households that carry any address at all. And
1,600 consolidated identities appear in two or more domains — convergence that rung G1c
promotes on — against 531 people who carry a rung at all. None of those three needs a new
source fetched, an image read or a page turned.

**The recommendation for the placement sweep is to run it off the later directories, in the
order the evidence licenses.** First the businesses, because a printed street address on a
firm is a stronger claim than one on a man and the corner-ordinal machinery already exists to
seat it. Then residences, under T-0669's rule, which is exactly the distinction that matters:
a shop's address is where the trade was carried on, a `res` or `bds` line is where a man
slept, and only the second is a `lives_at`. Then the households those two leave standing on
the same block, seated by division rather than by lot — moving a household from `unplaced`
to `south` is a real gain even when no roof is named, because it is the field the scene
actually reads. The gate that keeps this honest is already written: a later printing may
carry a position backward only as `inferred` with the date of the printing on the note, and
never as `attested`.

**What this layer must not be asked to do is estimate.** The temptation, with 3,265 people
recorded in the town four months after the scene date and 1,404 on the cards, is to close the
gap by reasoning about family sizes. That would replace a dataset whose every row cites a
record with one whose rows cite an average, and it would be undetectable six months from now.
The 1,861-person difference is the correct and stated size of what the sources do not say.
The route to closing it is the 1840 census bridge, the parish register and the directories —
records that name people — and the honest interim answer is the one this document gives:
here is who we can name, here is what we know about them, and here is exactly how thin that
is.
