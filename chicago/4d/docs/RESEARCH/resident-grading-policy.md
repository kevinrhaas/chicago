# The resident grading ladder — the ratified policy, its rungs, and what each one accepts

**Status: ratified by the owner on 2026-09-03. Applied as a PROPOSAL by
`tools/consolidate_resident_evidence.py`; applied to records by T-0514 (minting) and
T-0515 (regrading), and by nothing else.** Read this before grading anybody.

## The ruling, verbatim

> "attested = 1835 poll + any second independent source, or a contemporary record naming
> the person in Chicago; inferred = 1835 poll alone, or 1833/1834 lists with another
> source, or baptism parent/godparent 1833–35, or Hubbard/Fergus naming a resident with
> trade or address; projected_resident = a single appearance with nothing else; 1839/1840
> alone is never a 1835 resident (later evidence only)."

And the tier definitions from the ask that provoked it:

> "for ones that you are confident, those will be attested, the ones corroborated, those
> who you have a source or some potential sources that you think you are reasonably sure,
> include all those unasserted as inferred. the balance of people who you have seen in at
> least one source, they are documented, but you have some names of and you dont have much
> else, you can put those in a sub category of inferred as a projected resident, under the
> inferred category so we can filter by attested or inferred."

So there are two grades a visitor can filter on — `attested` and `inferred` — and
`projected_resident` is a subtype *under* inferred, never a third grade.

## The rungs

One rung, one id. Every row of `data/research/residents/grading_proposal.json` names the
rung that fired on it, and `--self-test` refuses a row graded above what its rung allows.
The rungs are tried in the order printed here; the first that fires, wins.

| rung | grade | fires on |
|---|---|---|
| **G5** | *no proposal* | The town already carries this person and every appearance this consolidation can see describes a date after the scene year. Their card rests on sources outside these seven domains (Andreas, the newspapers' own register). **The ladder abstains** and the row is listed as a conflict. |
| **G0** | `not_1835_resident` | Every appearance describes a date after 1835 and the town does not carry the person. This is the owner's "1839/1840 alone is never a 1835 resident" — later evidence only. |
| **G1a** | `attested` | The 1835 poll list **and** at least one other independent source. |
| **G1b** | `attested` | A contemporary record naming the person in Chicago — the 1833–1835 newspapers, printing the person by name in the town. |
| **G1c** | `attested` | **CONVERGENCE (T-0699).** Two or more independent in-window records from DIFFERENT class families — the town's civic lists · the contemporary press, letter lists included · the parish register. Two bodies that did not copy each other, naming one man inside the scene window. |
| **G2a** | `inferred` | The 1835 poll list alone. |
| **G2b** | `inferred` | An 1833 or 1834 list (poll, tax, the 1832 muster) **with another source**. |
| **G2c** | `inferred` | The St Cyr parish register inside 1833–1835 — a party to a marriage or a burial in the scene window. |
| **G3** | `inferred` + `projected_resident` | A single appearance and nothing else. |
| **G2e** | `inferred` | A Chicago post-office letter list of 1833–1835 **and something else**. |
| **G2d** | `inferred` | Fergus 1843 or Norris 1844 naming a person the town already carries, with a trade or an address. |
| **G4** | `inferred` + `projected_resident` | Two or more appearances, none of a class a rung above accepts. |

### Why G3 sits above G2d and G2e, and it is a ruling not an accident

The owner defined `projected_resident` as "a single appearance with nothing else". The
rungs that outrank it are the ones he named a *lone* source for — the 1835 poll (G2a), the
parish register (G2c), the contemporary press (G1b). A lone directory entry or a lone
letter-list name is not one of those, so it falls to G3. The layer already agrees: the 706
`ll_*` people it carries today are `inferred` + `projected_resident`, which is exactly what
G3 re-derives.

### G1c, and what the owner ruled on 2026-09-04

He opened `hh_allen_edward_richards.json` and asked: *"we have people now who have been
identified in multiple sources, but they are still being marked as inferred? they should be
attested if you have seen them like this in multiple sources."* Then, naming the pair
himself: *"like to me alone these two sources together would be attestation —
`chicago_democrat_1833_1835`, `chicago_voter_lists_1833_1835_irad`."*

**The first review pushed back and was wrong**, and the reasoning is recorded here because
the mistake is instructive. The objection was that the ladder grades by CLASS and not COUNT,
and that a count rule would attest a man on two 1843 directory entries. That conflated the
NUMBER OF APPEARANCES with the CONVERGENCE OF INDEPENDENT CLASSES. Two 1843 directory
entries are one class, one era, possibly one lineage; the town's poll list and the town's
newspaper are two different bodies recording the same man in the same window. G1c takes the
second reading and refuses the first: it asks for two FAMILIES, not two appearances.

**A letter list is still never promoted on its own.** G2e and G3 hold it exactly where they
did — it only COUNTS TOWARD convergence, which is precisely the owner's wording: *"the
letter list places someone as likely there, AND there are voter records."* And **G0
survives untouched**: two later sources with nothing in-window remain `not_1835_resident`,
because G1c requires its records to be inside the window.

### The defect G1c's measurement uncovered — records, not source_ids

`G1a` and `G2b` both read *"and at least one other independent source"* and both counted
`source_id`s. Every Chicago poll, tax and muster list in this project was digitised by IRAD
under the single id `chicago_voter_lists_1833_1835_irad`, so:

| | evidence | graded |
|---|---|---|
| Willard Jones | tax 1833 · poll 1834 · poll 1835 | `G2a` — **"the 1835 poll list ALONE"** |
| Byran Guisin | tax 1833 · poll 1834 | `G4` — **`projected_resident`** |

Both descriptions are false of the records they were applied to. **Independence is a
property of the RECORD** — a distinct list, taken on a distinct occasion, by a distinct
body — not of whoever digitised it. The rungs now count distinct
`(evidence_class, describes_date)` records. Jones reaches `G1a` under the ladder *as
ratified*; no new policy was needed for him.

### The one reading the ladder needed, put back to the owner

**Is a post-office letter list "a contemporary record naming the person in Chicago"?** It
names a person whose *mail* is at Chicago. Reading it as G1b would grade roughly 1,500
letter-list names `attested` in one pass. This tool takes the cautious half — a
letter-list-only name is `inferred`, never `attested` — and says so here rather than
quietly. **If the owner rules the other way, one line of `grade()` changes and the counts
move; nothing else does.**

### The second reading put back to the owner — the parish register, and the man who kept it (T-0841)

**Does G2c's `a party to a marriage or burial in the parish` mean the parish REGISTER, baptisms
included?** T-0724 gave `st_cyr_john_mary` a rung at last and the rung came out **G5**, the ladder
abstaining. T-0841 read that as a question about one man — may the keeper of a register be graded on
his own register — and it is not. Measured on dev 8c260130f, with the register's rows put through
`read_church()` four different ways and nothing committed:

- **He is not only the officiant.** St Mary's baptismal register names him as a PARTY four times in
  his own hand: godfather at 1834 entry 19 and 1835 entry 9, sponsor at 1834 entry 21 — all three at
  Chicago — and sponsor once at 1834 entry 10, which was written in Sangamon County. The premise
  that "he is a party to neither" is true of the marriage and death pages this tool reads and false
  of the register as a whole. **Under G2c as written a baptism is still neither a marriage nor a
  burial**, so the rung does not reach him even so; what changes is the question. It is not
  *may we grade the keeper on his book* — special pleading for one priest — but *does the rung mean
  the register*, which is a reading of five words the owner ratified.
- **It is not one man's rung.** Reading the register's Chicago rows under the existing church class
  moves **137 people onto G2c** (34 → 171), mints 131 identities, lifts 3 to G1c on convergence with
  the press or the civic lists, and takes 5 off G0. Eighty-five of the register's Chicago adults
  reach no surname anywhere else in the layer: the French, Métis, Irish and German Catholic town
  the poll books never recorded.
- **There is no read-it-and-change-nothing option.** Putting the rows under a class of their own that
  no rung accepts still lifts the priest — to G4, on count alone — and moves 135 others with him
  (G3 1,703 → 1,808, G4 1 → 31). The ladder counts appearances; a source it can see is a source that
  grades.
- **A naive read plants twelve entries in the wrong place.** Eleven of them — 1834 entries 1 to 11 —
  were written at Bear Creek, the South Fork of the Sangamon and Springfield, in Sangamon County, on
  the priest's journey back from St Louis, and a twelfth, 1833 entry 7, at Ottawa. The reading marks
  all twelve `at_chicago: false`. Ignoring that flag adds the register's 57 non-Chicago readings and
  38 more people to G2c who were never in this town. **Any read of this register filters on
  `at_chicago` or it is wrong**, and the source record says so itself.
- **And it would mint a second priest before it graded the first.** The register spells the particle
  out — `John Mary Saint Cyr`, `Jean Marie Irénée Saint Cyr` — and T-0724's closed particle list
  carries `St` and not `Saint`. So `Saint Cyr` splits to a surname **`cyr`** with `saint` left
  standing among the forenames, the three Chicago party rows land on a NEW identity
  `id_cyr_john_mary_irenaeus_saint`, that
  identity takes G2c, and the town's own `id_stcyr_john_mary_irenaeus` stays at G5 beside it. This is
  exactly the hazard T-0724's own note names — one rival `Cyr` away from putting the priest on
  another man — recurring on the spelled-out printing. **Whatever the owner rules, `saint` joins the
  particle list first**, and the corpus now prints it, so the closed list's own evidence rule is met.
- **The register's RULINGS already reach this tool; only its ROWS do not.** `declared_rulings()` and
  `person_links()` rglob every `*crosswalk*.json`, so `st_marys_baptisms_crosswalk.json`'s 8 merges,
  18 refusals and 275 rulings are spent here today. The register says who is who and testifies to
  nobody's presence.

**The question, and it is his.** Either (1) G2c means a marriage or a burial and no more — the
register's baptismal pages stay out, the priest stays a G5 conflict, and this is written down as a
ruling rather than an omission; or (2) G2c means the parish register of 1833-1835, its parties
whatever the sacrament, in which case the rung's text changes to say so and 137 people take it. Both
are defensible. Neither is a tool's call, and the tool has not made it: nothing in
`grading_proposal.json` moved for this pass.

**What did land**, because it needs no ruling: every reading in `data/research/church/records/` is now
either read by `read_church()` or declared unread in `CHURCH_RECORDS_NOT_READ` with its reason, and
`--check` fails on a file that is neither. The baptismal register was invisible for as long as the
file list was a two-name tuple, and it was not alone — the Second Presbyterian roll of 1842-1892 sat
beside it in the same silence. `--report` now prints both, under the domain table whose `church` row
counts two readings of four.

## What the tool proposes today

Built 2026-09-03 from seven landed domains; `--report` prints these.

| | |
|---|---|
| identities | **6,558** over 9,644 appearances |
| identities standing in two or more domains | 1,132 |
| identities the town already carries | 840 of 849 person records (7 names this tool cannot split) |
| proposed `attested` | 444 (G1a 42, G1b 402) |
| proposed `inferred` | 1,986, of which 1,717 `projected_resident` |
| proposed `not_1835_resident` | 4,095 — the 1843/1844 directories, the 1840 census and the death notices, none of which stands alone for 1835 |
| ladder abstains (G5) | 33 |
| proposed changes to existing people | 159 — 19 up, 63 down, 77 subtype only |
| conflicts listed rather than resolved | 77 — 44 proposed downgrades, 33 abstentions |

Against the #668 baseline (117 attested / 731 inferred / 706 projected / 848 persons), the
ladder as ratified moves 159 of 849 people. **It is a proposal. No household file was
changed by this pass.**

## How much of the layer the ladder has actually ruled on

**Restated 2026-09-04 against the WHOLE layer rather than the part the ladder reached
(T-0692), because "moves 159 of 849" was only ever true of the people it looked at.**
`--coverage` prints this and `--check` fails if the account is not total; the full list,
one person per line with their sources and their current grade, is
`data/research/residents/ladder_coverage.json`.

| | people |
|---|---|
| person records in `data/residents/` | **1,404** |
| carrying a `ladder_rule` on the card | 531 |
| carrying none | **873** |

And the 873 are not one thing, which is the finding. The ticket was opened on a count of 18
and read as *"the consolidation never reached them"*. It had reached all but nine:

| what the ladder can say | people |
|---|---|
| **a rung already ruled, never written onto the card** | **864** — G3 649, G1b 76, G2e 56, G5 36, G1a 20, G2b 17, G1c 10 |
| the person's row sits on an identity that names ANOTHER card as canonical | 3 |
| the splitter built no identity from the name, and says which guard refused it | 6 — R5 4, R1 2 |

**So the bottleneck is the SPEND, not the reading.** For 864 of 873 people the rung exists
in `grading_proposal.json` and no pass has ever carried it onto the card; 76 of them are
`attested` rungs sitting unspent. That is a different job from reading a new source, and it
is the one that moves the number.

### The spend, made 2026-09-05 (T-0720)

`tools/spend_ladder_rungs.py --build` carried those rungs onto the cards. It writes ONE
scalar — `ladder_rule`, immediately after `grade` — and only where the ladder AGREES with
the grade and the subtype the card already carries. Nothing else on a card moves: not the
grade, not a source, not a note. That is what makes it safe to run across cards four other
passes derive, and it is why the pass cannot close the gap by grading anybody down.

| | before | after |
|---|---|---|
| carrying a `ladder_rule` on the card | 531 | **1,313** |
| carrying none | 873 | **91** |
| a rung ruled and never written | 864 | **0** |

The 782 spent are G3 628, G1b 76, G2e 48, G1a 20, G1c 10 — 106 of them `attested` rungs
that had been sitting in the proposal since 3 September.

**The 82 the ladder disagrees with are the owner's**, listed in
`data/research/residents/ladder_spend.json` with the reason, and left off the cards:

| | people |
|---|---|
| the rung proposes a LOWER grade than the card carries | 45 — T-0515 already ruled on each and declined it, and the refusal is on the card |
| the ladder abstains (G5) | 36 — an abstention is not a rung, so there is none to write |
| the same grade with a different `resident_subtype` | 1 |

Those 82 now report as `ruled_but_disputed` in `ladder_coverage.json` rather than as an
unspent rung, so `proposed_not_written` means what it says and reads nought. The nine
below are unchanged: the ladder still cannot see them.

**The nine the ladder cannot see, each with the reason it abstained.** Two were absorbed:
`canonical_person_id` is `town[0]`, so an identity holding two town cards reported one and
dropped the other in silence — `brown_mrs_rufus` onto `brown_rufus` (a wife whose only
printed name is her husband's, and the honorific strip makes the two indistinguishable) and
`norton_n_r` onto `norton_nelson_r` (where the merge is right and the town simply carries
the man twice). Master rows now carry `town_person_ids`, so an absorbed card is visible
rather than silent. **T-0723 answered both, and they are two different answers**: R6 below
holds Mrs Rufus Brown apart and she has a rung of her own, while the Nortons were one man
and the cards are one card, merged under rule C2 of
`data/residents/card_merge_rulings.json`. **A third joined them on 2026-09-05 and stands** —
`vanderbogart_h`, the town's `H. Vanderbogart`, onto `Dr Henry Van der Bogart`, whom the
compound-surname rule below finally let the splitter read as the same surname. It is
undecided on purpose and T-0842 owns it: merging them to close the coverage gap would be
the old splitter's guess wearing a ruling's clothes. The other six are refusals the master
has recorded all along: `8. G. Abbot`, `A. 8. Perry` and `James I1. Gabbs` are OCR
misreadings of an initial (S. read as 8, H. as I1) rather than names the town used;
`Heacock's wife and children, unnamed` is a description; and `Beckford` and `Mrs Temple`
name no forename at all.

`Rev. John Mary Irenaeus St Cyr` used to be the seventh, turned away by the four-token cap
that his compound surname tripped. **T-0724 fixed the splitter and he now carries a rung —
but the rung is G5, not the G2c the ticket expected, and that difference is the finding.**
G2c is *a party to a marriage or burial in the parish*, and the priest is a party to
neither: he is the officiant, and the reader of `st_cyr_marriages_1834_1839.json` and
`st_cyr_deaths_1834_1837.json` yields the people the register is *about*. So the
consolidation can see exactly one appearance of him — his own town card, citing Andreas —
and G5 is the ladder abstaining and filing him as a conflict for the owner, which is the
honest answer to what these seven domains actually hold. **Whether the keeper of a register
may be graded on it is a change to a ratified rung and therefore the owner's to make; it is
filed as its own ticket rather than decided here.**

**No grade has moved.** The measurement above touched no household file, and the spend
that followed it wrote a rung and nothing else: `grading_proposal.json` is byte-identical
across both, and every grade on every card is still the one the pass that wrote it derived.

## The review half — what each source turned out to be worth

| domain | names read | identities | on a card the town already has |
|---|---|---|---|
| directories (Fergus 1843, Norris 1844) | 4,346 | 2,915 | 179 |
| newspapers (gazetteer) | 2,274 | 2,101 | 867 |
| old settlers (Fergus death notices) | 743 | 735 | 25 |
| church (St Cyr register) | 520 | 480 | 4 |
| census 1840 | 459 | 456 | 14 |
| civic (poll/tax lists, 1832 muster) | 460 | 386 | 116 |
| residents (the town layer itself) | 842 | 840 | — |
| newberry index | 0 | 0 | surname-only finding aid: R1 refuses all 4,646 cards by construction |
| census 1830, genealogytrails, books | 0 | 0 | nothing person-level read yet |

**Which domains disagree with which.** The overlap matrix in `source_coverage.json` is the
whole answer; the shape of it is that the newspapers and the town layer are nearly the same
population (782 shared identities) because the town layer was largely minted from them,
while the directories are the biggest pool of names the town has never met (2,915
identities, 100 of them already on a card). The church register is the loneliest: 480
identities, 4 of which the town carries.

**The gap that remains, and it is the finding of the pass.** 817 of the 840 identities the
town already carries have at least one source this consolidation can offer that their card
does not cite — **1,050 unspent source-links**. Philo Carpenter, the owner's worked
example, is the shape of it: ten appearances across five sources, a card citing three
(`andreas_1884_v1`, `chicago_democrat_1833_11_26`,
`chicago_tribune_1882_05_19_fourth_reception`), and 23 rulings reaching him of which **22
state no source at all** — which is T-0598, and why T-0598 stands beside this ticket in the
queue. Until a ruling can say what it rests on, spending it onto a card is a human
rereading the crosswalk.

## The merge and refusal rules

They are the newspapers' rules, already ratified in
`data/research/newspapers/identity.json`, plus two for the cross-domain case. Every merge
and every refusal in `identity_master.json` names the rule that made it.

| rule | says |
|---|---|
| **M1** | Identical normalised name — same surname, same forename tokens. |
| **M2** | An initial-only forename attaches to the ONE full forename of that surname carrying the initial. Two rivals is R3, never a choice. |
| **M3** | A middle initial on one reading and absent on the other, forename and surname agreeing, no rival middle initial. |
| **D1** | A merge already declared by a domain's crosswalk or by `identity.json`. **A landed adjudication outranks everything derived here** — 74 appearances moved on this rule in this pass, including `W. H. Adams` of the 1833 poll, whom R3 had refused while `civic/voter_crosswalk.json` had matched him a month earlier. |
| **R1** | Surname only — the record genuinely prints no forename. Never merges onto a person. 389 derived refusals, plus the whole Newberry finding aid. |
| **R2** | Same surname, different forename initial. Never merges. 970. |
| **R3** | An initial-only forename with two or more rival full forenames of that surname — refused with the rivals named. 182. |
| **R4** | Same surname and initial, two different full forenames. 79. |
| **D2** | A refusal already declared by a crosswalk or `identity.json`. 1,574. |
| **R5** | **A printed name the splitter cannot read as (surname, forename) at all** — a firm style, an institution, a digit standing where an initial was misread, a description rather than a name, more forename tokens than the four-token cap. 264, each row naming which guard fired. |
| **R6** | **A female honorific standing on a man's own name.** `Mrs Rufus Brown` is not Rufus Brown. Refused only where one SOURCE prints both readings as separate entries; 5 surnames. |

**Why R5 exists, and what it cost to not have it (T-0692).** Until 2026-09-04 every one of
those 266 rows was filed as R1, *"names no forename"* — and that sentence is false of most
of them. `8. G. Abbot` prints a forename initial; `Rev. John Mary Irenaeus St Cyr` prints
three forenames and is turned away by the token cap, not by an absent name. Seven of the
town's own cards carried that refusal, and a refusal whose stated reason is untrue of the
page is barely better than no refusal at all. **The guards did not change and no identity
moved** — `grading_proposal.json` is byte-identical across the split. What changed is that
each refusal now says which guard fired.

R2 and R4 are stated **once per surname**, naming everyone the bucket holds apart, not once
per pair: the cross product of forty Smiths is 780 rows that say what the bucket already
says.

### A wife is not her husband (T-0723)

The honorific strip is right for `John Bates Jr.` — a Bates, not a Jr. — and it is what
folded `Mrs Rufus Brown` onto `Rufus Brown`: what it throws away there is the only thing on
the page saying she is not him. The two readings arrive at the comparison letter for letter
identical, M1 fires, and a woman ends on her husband's card with no rung of her own.

**R6 refuses that merge, and the PAGE has to prove it.** The refusal fires only where one
source prints both readings as separate entries. Fergus 1843 sets `Brown, Rufus B., warehouse
man, John P. Chapin & Co., res 189 Lake` at entry 458 and `Brown, Mrs. Rufus B., dress and
cloak maker, 189 Lake, up stairs` at 459 — two trades, one address, two death notices
eighteen years apart — and a directory does not enter one person twice under two spellings.
That is a fact about the page rather than about the name, and the fact is what the rule
stands on.

**Why it is not a rule about names.** `Mrs. Eliza Haight` and `Mrs. Diana Hamilton` are the
same shape and are one woman each, printed under her own forename. Nothing in the letters of
a name says Rufus is a man and Eliza is not; this splitter holds no lexicon of men's names,
and inventing one would tear a real woman off her own evidence. Two further guards keep the
rule narrow: the title must LEAD the name it qualifies, because the letter lists set
`Gooding, Caroline Miss` with the title trailing her own forename; and the tokens must match
the bare reading exactly, so M3 still joins `Mrs. Sabrina Mason` to `Mason Sabrina A.`

Five surnames meet the test — Anderson, Atkinson, Brown, Gale and Johnson, all of them on
Fergus 1843's own pages. Two printings of the same shape are deliberately **left merged**
because no single source prints both readings: `Hadley, Mrs. T. G.` against Norris 1844's
`Hadley, T. G.`, and `Mrs. Wm. B. Egan` against Norris's `Egan, Wm. B.` T-0903 owns the
reading that would settle them. `data/residents/card_merge_rulings.json` states the same
refusal card-side as **D3**, and the derivation's four cases are asserted in
`--self-test`.

### A compound surname is one surname (T-0724)

`St`, `Van`, `Von`, `De`, `Den`, `Der`, `Du`, `La`, `Le`, `Mc` and `Mac` are printed with a
space in this corpus, and the splitter used to take only the LAST token for the surname.
So `Rev. John Mary Irenaeus St Cyr` read as a **`Cyr`** with five forenames — `Rev · John ·
Mary · Irenaeus · St` — and the token cap turned him away. **The cap was the symptom.** The
fault was that `St Cyr` and `Cyr` are two different surnames, and the old reading was one
rival `Cyr` away from putting the priest on another man; raising the cap would have made
that likelier, not safer.

The particle and everything after it now belong to the surname, and a stack of them
(`Van Den Bogart`, `Van der Bogart`) is absorbed together. Two guards keep it honest:

- **The list is closed, and it is a list of printings rather than of languages.** Every
  particle above is one this corpus actually prints. A first draft carried `Ste`, `Des`,
  `Del`, `Da` and `Di` on the strength of the languages, and `Ste` immediately took the
  forename off `Ste Beadieston` — a man whose single printing in the whole corpus is the
  post office's `Beadieston, Ste`. A particle nobody here has printed can only cost a
  reading; it can never win one.
- **A trade is not a forename.** Norris prints `Peterson. GPO. captain schooner St. Joseph`,
  and the rule would have made `St. Joseph` the man's surname and `captain schooner` two of
  his forenames. The only thing on the page separating that line from the priest's is that
  the word before its particle is `schooner` and the word before his is `Irenaeus`. When
  the token before the particle is not printed as a forename — capitalised, or a bare
  initial — the rule stands down and the reading falls back to the cap that always refused
  it.

**What it moved, reported rather than applied.** Nineteen identities were re-keyed onto
their true surname — `Van Horn`, `Van Acker`, `Van Cleve`, `Van Cortlandt`, `Van Fleet`,
`Van Osdel`, `Van Vatzah`, `Van de Velde`, `Von Schnideau`, `De Roche`, `De Tonty`,
`De Lasalle`, `La Frombois`, `Le Claire`, `Le Framboise`, `Le Grand`, `Mc Kee`,
`Van Den Bogart` and `St Cyr`. Two refusals were lifted (`Rev. John Mary Irenaeus St Cyr`
and `Van de Velde, Rt.-Rev. Jas. Oliver`) and one was gained, correctly: the 1840 census's
`J. M. Van Osdel` now sits in the same surname bucket as Jesse Redifer, John M. and John
Mills Vanosdel, and R3 refuses to guess which `J.` he is — a refusal that could not even be
stated while he was keyed as an `Osdel`. **Three town cards moved and none of them was
touched**: `st_cyr_john_mary` gains a rung (G5), `mckee_david` rises from G5 to **G2b** on
the 1832 Black Hawk war enrolment the surname now reaches, and `vanderbogart_h` is absorbed onto
`Dr Henry Van der Bogart` at G2e. All of it stands in `grading_proposal.json`; the minting and regrade passes
that own the civic-minted cards were re-run in the same commit, because their gate refuses
a layer that no longer re-derives from the ladder.

**And it un-merged one man, on purpose.** `Bogart, Dr. Henry Van der` and `H. Van Den
Bogart` both truncated to `bogart` and were carried as one identity — a merge nobody ruled
on, made by taking the last token. They are now `vanderbogart` and `vandenbogart`, two
surnames, and the consolidation keeps two surnames apart; `hh_vandenbogart_h` was minted and
the town's person count went 1,404 to 1,405. It is very likely the same man. It is also very
likely a ruling somebody has to make on the page rather than an assumption the splitter
makes silently, which is what T-0724's acceptance asked for. **T-0842** holds the reading.

## Running it

    tools/consolidate_resident_evidence.py --build       write the four data files
    tools/consolidate_resident_evidence.py --check       they re-derive; the invariants hold
    tools/consolidate_resident_evidence.py --self-test   the assertions still fire when broken
    tools/consolidate_resident_evidence.py --report      the tables above
    tools/consolidate_resident_evidence.py --coverage    who the ladder has ruled on, and
                                                         who it has not, with the reason

`--check` and `--self-test` run in `tools/check.sh`. The pass is **incremental**: it
consolidates what is closed and runs again after every few sources. A pass that finds
nothing newly closed says so and costs a run nothing.
