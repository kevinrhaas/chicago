# The Native and Métis people of Chicago, 1835 — what the corpus names, and what it does not count

**T-1376**, piece 2 of **T-1177**. Stage `underdocumented` / sub-stage `native_and_metis` of
the 1835 resident reconstruction programme — the only stage licensed to write a Native or
Métis person, under the owner's ruling of 2026-09-17 recorded in `AGENTS.md § Standing
constraint`. Derived record: `data/reconstruction/1835_native_and_metis.json`. Writer:
`tools/reconstruct_underdocumented.py`. Cards: `data/residents/underdocumented/`.

---

## The count this stage was opened on

The Illinois State Archives index of Black Hawk War enrollments prints **134 men enrolled
at Chicago in 1832**, in two companies:

| company, as the roll prints it | rows | cards in the town before this stage |
|---|---:|---:|
| `G KERCHEVAL` | 40 | **20** |
| `INDIAN` | 94 | **0** |

One roll. One year. One page. The rank column is empty on both sides of it.

What separated them was not the evidence. The borderline roster (`1835_borderline_roster.json`)
sorts every reading in the corpus into re-admission classes, and its rule
`community_term_in_the_reading` puts any reading carrying a Native, Métis or Black community
term into **R6**, whatever else is true of it. R3 — *"a name on the 1 April 1834 post-office
return or the 1832 Black Hawk muster enrolled at Chicago, with no 1835 corroboration and no
card; mint reconstructed, presence bounded by the persistence rate"* — took the rest.
T-1172 was licensed to spend R3 and not R6; R6's owner, T-1177, was not split into workable
tickets until 2026-09-19. So the town re-admitted twenty of Kercheval's men and none of the
other company's, and no rule anywhere said it should.

This stage spends the Native and Métis part of R6 under **R3's own licence**, unchanged:
the same persistence model, the same lag, the same seeded draw. A card written here is
worth neither more nor less than one of Kercheval's men.

## What was written

| | |
|---|---:|
| R6 `native_or_metis` rows offered by the roster | 131 |
| already on a card the town holds | 15 |
| **cards written** | **87** |
| — present on 1 July 1835 (seeded persistence draw) | 69 |
| — absent | 18 |
| withheld, each with a stated reason | 29 |

Every card carries `review_required: true` **and** `touches_removal: true`, and says in its
own prose which subject it is held for — `AGENTS.md` refuses a bare boolean, and
`tools/reconstruct_underdocumented.py --check` asserts the sentence is there.

The 29 withheld rows, by reason:

| reason | n |
|---|---:|
| `a_card_of_that_name_already_stands` | 9 |
| `earlier_than_the_window_and_nothing_follows_the_person_forward` | 7 |
| `later_only_and_this_stage_does_not_back_project` | 6 |
| `a_one_word_european_surname_gives_no_person` | 3 |
| `the_term_is_prose_and_not_a_statement` | 2 |
| `the_roll_prints_this_name_twice` | 1 |
| `the_reading_carries_no_date_this_tool_can_read` | 1 |

## The three rules this stage does not take from T-1172, and why

**1. A one-word name is still a name.** T-1172 withholds a reading that gives no surname
*and* forename (`not_a_whole_name`). That is the right rule for a land index that clipped
`CHIPMAN` off `CHIPMAN ANSEL`. Applied to this company it is not a rule about evidence at
all — it is a rule about European naming, and it would refuse `Cau Be Nah`, `Mas Go` and
`Ke O Quaw`, every one of them printed whole, and call the refusal rigour. So the test here
is on the reading and not on its shape. What is still refused is a **one-word European
surname** — `Beaubien`, `Morgan`, `Chamblee`, `Francois` — because there the roll clipped a
name this town carries several of.

Two further places the same convention had to come out:

* `title_case` turns a one-letter word into an English initial with a full stop, which
  printed `Ke O. Quaw` and `Mex E. Man`. `display_name` capitalises and does nothing else.
* the collision key is `surname | first initial`, which reads the **last word as a family
  name**. `MES KEE SUCK` and `MAU KAI TAI O SUCK` key alike and are two men. Inside this
  stage the duplicate test is equality of the whole reading; three men were nearly refused
  as duplicates of each other before that was fixed.

And one place the same convention was hiding a real duplicate in the other direction: the
layer writes a person's own Indigenous name in a parenthesis after the English one, so
`Alexander Robinson (Che-che-pin-qua)` keys as `qua|a` and **not** as `robinson|a` — which
would have let `ROBINSON, A` of the 1832 roll be minted a second time. The key is now taken
with the parenthesis off as well.

**2. A community term must be a statement, not a word in the prose.** The roster's R6 rule
is a text match, and a text match over-catches: the biography of an Indian agent, a treaty
commissioner or a trader who dealt with Native customers carries the word `Indian` too.
Charles Jouett, John Tipton and Daniel W. Beckwith reach R6 that way. This stage mints only
where the **source's own structure** says it — here, a company column a clerk filled in with
the word `INDIAN`.

**3. No nation is written.** The roll heads the company `INDIAN` and says no more. The
Potawatomi, the Ottawa and the Ojibwe of this country were three peoples and a united band
of them lived at the forks; the roll distinguishes none of them, so neither does this stage.
`community` is `native`, a term added to `data/residents/community_rules.json` for exactly
this — *the source says Indian and says nothing further*. Writing `potawatomi` on eighty-seven
men because most of the country's people were Potawatomi would invent the one fact the record
withholds. Every card's `origin` is `null` and says so in its note.

## The counted-but-unnamed remainder — REFUSED, and the refusal is the reading

T-1376 asked for the counted-but-unnamed remainder reconstructed within a stated bracket.
**A bracket needs a count, and this corpus does not hold one.**

* The roll spent above is a roll of enrolled **men**. No woman and no child appears on it.
* The 1840 federal schedule, five years after the scene, counts no Native person in any
  column.
* The transient bracket (T-1352) prices the summer crowd off the newspapers and carries
  **no Native row at all** — the American's *"strangers, to the amount of some hundreds
  more"* are the emigrants off the lake vessels and the land-sale parties, and reading them
  as anything else would be putting a number into a sentence that does not hold one.
  (T-1177's own text says T-1178 carries a separate Native-visitor row with its own basis.
  It does not. That is recorded here rather than quietly supplied.)
* The great gathering and the last war dance at Chicago are **August 1835** — six and a half
  weeks *after* the scene date, and the event the standing constraint is written about. A
  crowd that assembled in August is not evidence of a population on 1 July, and this project
  does not stage it.

Drawing a remainder against no count would not be a bounded reconstruction. It would be a
population invented whole, on the one subject `AGENTS.md` says is *"not a research gap to be
filled by inference"*. The refusal is written into the record with what would retire it:

1. an 1835 annuity payment roll or schedule for the Chicago agency;
2. a count of the families at the Agency, at Wolf Point or on the reservations in any month
   of 1834 or 1835;
3. a contemporary estimate of the Native population in or about the town before 1 July 1835,
   in a source this project can commit.

What the layer carries instead: eight households already flagged `touches_removal` — the
Beaubiens, Robinson, Caldwell, McKee, Porthier, Kercheval and the Agency — and inside
`hh_robinson_alexander` a collective row, *"the rest of the Robinson household, unnamed"*,
which its own note calls **an admission and not a person** and refuses to count. That
refusal is right and is not overturned here.

## Every source read

| source | what it gave | spent |
|---|---|---|
| `blackhawk_war_chicago_enrollments_isa` — the Illinois State Archives index, read at `data/research/civic/records/blackhawk_war_1832_chicago.json` | 94 men enrolled at Chicago in 1832 in the company the roll heads `INDIAN`; 93 of them reached the roster's R6 | **yes** — 87 cards |
| `st_marys_baptismal_register_1833_1835` — the reading at `data/research/church/records/st_marys_baptisms_1833_1835.json` | Four entries of 1833 in which the priest states an Indigenous identity **in his own hand**: entry 7 (Josette Ashkam, *of Ottaway*), entries 14 and 17 (*Marianne (sauvage)*, wife of Antoine Aspam), entry 18 (*Jaespquaa (sauvage de Green Bay)*, wife of Paul Vieaux) | no — see below |
| `1835_borderline_roster.json` (class R6, 131 `native_or_metis` rows) | the adjudication list itself | **yes** |
| `1835_readmissions.json` | the 20 Kercheval cards this stage is measured against | read, not written |
| `chicagology_lastwardance`, `encyclopedia_chicago_potawatomis`, `cpn_beaubien_family`, `fcp_treaty_chicago_1833_payments`, `okstate_treaty_chicago_1833`, `treaty_chicago_1833_statutes` | read for a count of people at Chicago before 1 July 1835. **None gives one.** The treaty records are payment schedules naming individuals already carded or already refused; the gathering they bear on is August 1835 | no |

### The finding this stage files rather than spends

The St Mary's register is the only source in the corpus in which a contemporary states an
Indigenous identity for a named person at Chicago, and **the two women it so identifies are
the only adults on their own entries that the borderline roster ruled ineligible**. The
roster carries Antoine Aspam, Josette Aspam, Paul Vieaux, Jean Baptiste, Magdelene and
Susanne; T-1172 minted four of them. It does not carry *Marianne (sauvage)* or *Jaespquaa
(sauvage de Green Bay)*, whose readings sit in the roster's `ineligible` list normalised to
`marianne` and `jaespquaa`. So the town holds these two families' husbands and their
children and not the women the priest wrote down as Indigenous.

It is not spent here, and the reason matters: a baptism is not a residence, and the
ineligibility ruling is the research layer's, not this stage's to overturn from outside with
a one-line patch. It is a reading, and a reading is a ticket. Filed as **T-1383**, with the four
entries and what it should answer — see also `data/reconstruction/1835_native_and_metis.json`
§ `sources_read`, which carries the same sentence in machine-readable form.

## The review still owed

`AGENTS.md` commits this project to review by Native scholars or community organisations
before any depiction ships, and the ruling of 2026-09-17 that permits these cards did not
retire it — it put the promise on every record instead. **All 87 cards carry
`review_required: true`, which blocks a scene from being marked `released`.** The flag is the
promise held open, not a formality, and nothing here is a depiction: no human figure is drawn
for anybody (L1), the August gathering is not staged, and no dialogue, ceremony or portrait
is invented. A card, a name as the roll printed it, and the sentence that says what is still
owed.
