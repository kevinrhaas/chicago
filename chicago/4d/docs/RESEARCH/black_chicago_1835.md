# The free Black town of Chicago, 1835 — what the corpus counts, what it never names, and what was written

**T-1377**, piece 3 of **T-1177**. Stage `underdocumented` / sub-stage `free_black` of the
1835 resident reconstruction programme. Derived record:
`data/reconstruction/1835_free_black.json`. Writer: `tools/reconstruct_free_black.py`.
Cards: `data/residents/underdocumented/hh_fb_*.json`. Firms:
`data/businesses/authored/rcb_fb_*.json`.

---

## The measurement this stage was opened on

T-1375 gave every person in the layer a community and printed the result. One row of that
table read:

> Potawatomi, Ottawa, Ojibwe, **free Black**, German — **0**

That is not a finding about 1835 Chicago. It is a finding about this project. The town had
free Black residents; the corpus says so; and no stage had ever been licensed to write one.

## Every source read, and what each one gave

This page is the whole of it. Two readings in the corpus bear on the question and they are
five years apart.

| reading | date | what it gives | where it is |
|---|---|---|---|
| Caton's fee before the Court of County Commissioners | **August 1833** | a COUNT: "six or seven free coloured men" | `data/residents/households/hh_caton_john_dean.json`, quoting Andreas vol. 1 |
| The 1840 federal census of Chicago | **1840** | 53 free coloured persons of 4,834, 0 slaves; four households enumerated entirely in the free-coloured block; seven names the borderline roster classes R6 on its `community_term_in_the_reading` rule | `data/research/census_1840/composition_1840.json`, `data/research/census_1840/pages/*.json`, `data/reconstruction/1835_borderline_roster.json` |

And the searches that returned **nothing**, which are as much a part of the reading:

- **The newspapers.** Every issue of the *Chicago Democrat* and the *Chicago American*
  this project holds, 1833–1835, swept for `coloured`, `colored`, `negro`, `mulatto`. Every
  hit is a bolt of cloth — "dark and fancy colored Prints", "Bandanna, silk, flag, and
  black, Italian do." Not one advertisement is by, for or about a Black resident.
- **The books and the reprints.** Hurlbut, Moses and Kirkland, Fergus, the Illinois
  Catholic Historical Review, Hubbard's autobiography, the Genealogy Trails transcriptions
  including the 1843 directory and the marriage register: swept the same way. One hit is an
  elderly servant in a Virginia anecdote and the rest are surnames and cloth.
- **The town's own rolls.** The 1833 tax list, the 1834 poll, the 1835 poll: Illinois law
  made none of these open to a Black resident, so their silence is a statement about the
  franchise and not about the town.

**So the corpus counts the free Black town of Chicago twice and names it never** — not
inside the window, not once. Everything below follows from that sentence.

## The bracket

**FLOOR — August 1833.** Andreas, as this layer's own Caton card quotes him: in August 1833
Caton "defended six or seven free coloured men before the Court of County Commissioners and
obtained certificates of freedom for them, his fee a dollar from each." Under the Illinois
black law then in force a free Black person resident in the state had to hold and record
such a certificate. Men before the county court for one are men settling, not passing
through. The count is of **adult men**, and it is the only count of Black people at Chicago
the corpus makes before the scene date.

The tool parses that phrase out of the card rather than carrying the number in its own
source; `--self-test` asserts the parse reads `(6, 7)`. Seven is written — the phrase's
upper reading — because the ticket's ask is the low end of the bracket **at least**, and
seven is the reading under which the cohort stands at or above the floor whichever of the
two the page means.

**CEILING — 1840.** `composition_1840.json`, derived from the committed IPUMS extract:
53 free coloured persons in a town of 4,834, and 0 slaves. Carried back at the same share
onto the town model's point reading for 1 July 1835 (2,536 persons) that is **27 people**,
and 25 to 35 across the model's whole range of 2,353–3,265.

**WHAT WAS WRITTEN: the floor.** Seven men, fifteen people, two firms. The head-room
between the floor and the ceiling — room for a dozen more people — is left standing, and
that is a decision rather than an oversight: filling it would mean inventing people against
a share carried back across five years in which this town grew faster than at any other
time in its history. A later ticket with a reading in hand may take it.

**No persistence draw, and this is the one place this stage departs from the sub-stage
beside it.** T-1376 priced each of its men against the persistence model because its
subject was a NAME, and a man named once in 1832 may have left. Here the subject is a
COUNT, and a count does not leave town. Between the 1833 reading and the 1840 one the free
Black population of Chicago went from six or seven men to fifty-three persons; no monotone
path between those two readings passes below six on 1 July 1835.

## What is on the 1840 sheets, and the leaf that nearly doubled the town

Eight households on the enumerated leaves carry a free-coloured cell. Four stand **entirely**
in that block — no free-white cell at all — and four are a free coloured person inside an
otherwise white household.

| household, as the sheet reads it | free coloured | free white |
|---|---:|---:|
| Joseph L. Williams (97P, line 10) | 3 | 0 |
| Sam[l] Anderson (97P, line 11) | 3 | 0 |
| Mrs. Nan[?]y H. Jackson (LV, line 19) | 2 | 0 |
| [?]. [K]. Bul[l] (RY, line 13) | 1 | 0 |
| Ira Couch (97P, line 3) | 1 | 16 |
| E. C. Stowell (BP, line 1) | 1 | 5 |
| T. M. Monta[?]on (CK, line 24) | 1 | 1 |
| W[m]. [?] Sh[e]n[e]r (RK, line 2) | 2 | 6 |

**A fifteen-line trap, avoided by name.** Leaf `33SQ-GYYJ-PW` carries free-coloured cells on
fifteen of its thirty lines and **not one of them is a household**: it is the enumerator's
own recapitulation, and T-0966 read it as such. A pass that counted those lines would read
this town as holding five times the free Black households it does. The writer excludes it on
the leaf's own description of itself and `--self-test` asserts both that exactly one leaf is
excluded and that excluding it is not cosmetic.

**The shapes, and only the shapes.** `composition_1840.json`'s own rule is that 1840 gives
this project shapes to be tested against and never a population to be filled from. What is
read off these four lines is how many adults and children stood under a free Black roof —
never who they were. Three of the four are headed by a man and are the shapes this stage
deals; every card holds exactly as many people as its shape counts, which `--self-test`
asserts card by card.

**The woman-headed household is set aside, not discarded.** Mrs. Nan[?]y H. Jackson's line
is a free Black household with no adult man in it. The floor this stage carries is a count
of **men**, so every household written here is headed by one, and dealing her shape to a
male head would invent the man the page does not show. The record says so in
`shapes_set_aside_because_no_adult_man_stands_in_them`. The woman-headed free Black
household of this town is real, it is not written here, and it wants a stage whose unit is
a household rather than a count of men.

## The name pool — the thinnest in the file, and its thinness is the finding

`data/reconstruction/1835_invented_name_pools.json` gains a `free_black` community. Every
other pool in that file extends a naming stock this project has attested many times over.
For the free Black town of 1835 the corpus holds **one** set of names, anywhere, and it is
dated five years after the scene.

**The surnames are the reading.** Five: **Anderson, Askie, Johnson, White, Williams** — one
from each roster row whose printed surname is whole. Two rows are refused: `T. M. Monta[?]on`
and `[?]. [K]. Bul[l]` each leave an unread position inside the surname, so neither is a name
the page actually makes.

**Read off `name_as_read`, never off `normalised`.** The roster normalises for its own
matching and the normalisation breaks names: `Eliza Askie` normalises to `eliza as ie`, whose
last word is `ie`, which is not a surname and is not anything. The printed string is the
evidence here as it is everywhere else in this project, and `--self-test` holds that
`Askie` is in the pool and that the row it came from really does normalise to `eliza as ie`.

**The given names are the town's own stock, and that is a reading rather than a shortcut.**
Every given name the schedule prints *whole* in that block — Eliza, George, John, Joseph —
is already borne by a real person of this town. `--self-test` asserts it against the
committed layer. A fifth, `Sam[l] Anderson`, is a supplied forename and is not carried,
though his surname is. So this pool does not invent a second naming tradition; it
contributes the surnames no other pool can and takes its forenames from the same stock the
rest of the town draws on.

**Two rules keep the pool from being a back-projection of five real people.** The roster
dates all seven readings `later_only` and this stage mints none of them:

1. **No draw may reproduce a printed reading.**
2. **No draw may share a reading's `surname | first initial` key** — the discriminator this
   project's directory crosswalks match on. `Samuel Anderson` and the schedule's `Sam[l]
   Anderson` are one key, and a reader who met the first would take it for the second.

And the programme's own standing rule, enforced here and again in
`reconstruct_residents_1835.py`: no invented name may be one a real person of this layer
bears.

`drawn_by` on the pool says `tools/reconstruct_free_black.py` ONLY. No trade weight names
it, so no other stage can draw from it: the free Black town of 1835 is written by the one
stage licensed to write it and is not sprinkled through the reconstruction by a weighting.

## The trades are a liberty and say so

**The corpus records no occupation for any Black person at Chicago before 1840** — not an
advertisement, not a directory line, not a roll. The seven trades dealt here (barber, cook,
waiter, drayman, labourer, whitewasher, sawyer) and the one woman's trade (laundress) are
the service, carrying and labouring trades of a northern lake town, and dealing from them
rather than from the merchant and professional classes **is an assumption about the 1835
labour market and not a reading of anything**.

Nothing here says a free Black man at Chicago could not keep a store or read law. It says
this project has no reading either way and has written down which way it guessed. The
liberty is in `docs/LIBERTIES.md`, it is on the face of every card it touched — which
`--self-test` asserts — and any source naming a free Black resident of Chicago at a trade
retires it.

## What was written

| | |
|---|---:|
| households | **7** |
| persons | **15** |
| — adult men (the floor) | 7 |
| — adult women | 6, of whom 4 are wives |
| — children under ten | 2 |
| Black-owned firms | **2** |
| surnames the pool holds | 5 |

The two firms are `rcb_fb_barbers_shop` and `rcb_fb_washing_and_ironing`, both in
`data/businesses/authored/`, both `provenance: reconstructed`, both unplaceable — no reading
puts a free Black household or business on any street of this town — and each reads its
`proprietor_community` off the one keeper it names, which is how T-1378's filter finds them.

**Nobody here is a person a source names.** Every person is `grade: reconstructed`, wears the
`rc_fb_` prefix a grep finds, and is retired by the first source that names a real free Black
resident of this town. The 1833 certificates of freedom themselves would retire the whole
cohort and name the men it stands for; they are the single most valuable unread document
this ticket could point the next researcher at.

## Every card is `review_required`, and `touches_removal` is false

Both deliberate. This is not the removal, and writing that flag true would borrow the weight
of a subject this stage is not about. The review is owed for the reason each card states in
its own prose, as AGENTS.md requires of any flagged record: these are reconstructions of
Black residents of a town inside a state whose black laws made a certificate of freedom the
condition of their residence, written from five surnames and no biography at all. No human
figure is drawn, for anyone (L1).

## What this stage does not write, and who owns it

- **The free Black residents who lived under somebody else's roof.** Four of the 1840 leaves
  enumerate free coloured people inside otherwise white households — the live-in cook, the
  driver, the servant, the child. That person belongs inside a card
  `data/residents/households/` owns and the mint writers re-derive, so seating them is the
  convergence's (T-1179) and not this stage's.
- **The woman-headed household**, for the reason given above.
- **A nation, a birthplace or a route.** The `origin` block of every card is null, and its
  note says why: the corpus says where this town's white residents came from and says
  nothing at all about where any Black resident came from. Free, freed, born in Illinois or
  come up out of a slave state — the record does not say, and an origin written here would
  be this project answering the one question its sources most conspicuously do not.
- **Any person the 1840 census names.** All seven readings are `later_only` and not one is
  back-projected.
- **The head-room between the floor and the ceiling** — about a dozen people.

## The gate

`tools/check.sh` runs both:

```
python3 tools/reconstruct_free_black.py --check       # everything re-derives, byte for byte
python3 tools/reconstruct_free_black.py --self-test   # 26 rules, each refusing its own case
```

The gate holds what the record cannot vouch for itself: that the floor is parsed out of the
Caton card rather than typed into the tool; that the cohort stands at or above it and below
the ceiling the 1840 share carries back; that the pool's surnames are still exactly the ones
the roster's rows print; that no drawn name reproduces a printed reading or its key; that
every card holds as many people as its shape counts; and that every card carries
`review_required` with its own sentence.
