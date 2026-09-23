# data/residents/ — the id, filename and manifest contract

`households/*.json` is one file per household; `index.json` is the manifest
(`households[]` rows of `{id, file, head, division, persons, grades, ...}`,
plus the `vocabulary` block that declares every closed enum a renderer must
implement). This note exists because a household's **filename has looked, at
different times, like it was encoding something it wasn't** — see "On the
`hh_doc_`/`hh_placed_`/`hh_ll_` prefixes" below, which is the direct answer to
that question.

## The rule

A household's id is always `hh_<surname>_<given...>`, lowercase-slugged, surname
first (`hh_morris_b_s`, not `hh_b_s_morris`) — built by `plain_fragment()` in
`tools/mint_documented_residents.py` from the head person's name (`surname()`
finds the surname; `plain_fragment` drops it from the token list and puts it
back in front). `id == the filename stem == the manifest's `id` field for that
row` is enforced by `tools/validate.py check_residents()` — never hand-diverge
one from another.

**Nothing about a person's evidence grade, residency status, or which pass
minted them belongs in this name.** Those are fields:

- `grade` (`attested` / `inferred` / `reconstructed`, on each person) is the
  accuracy ladder. A household is free to be promoted — a `letter_list_only`
  person corroborated by a second source becomes `attested` — **without a
  rename**. 21 households did exactly this under T-0489 while keeping
  whatever id they already had.
- `letter_list_only` (bool, per person) and `resident_subtype:
  "projected_resident"` mark how a person entered the dataset.
- `source_pass` (household-level, optional — see below) records which of the
  three mint tools produced the record, for the tools' own bookkeeping. It is
  provenance about the *tooling*, not a finding about the *person*, so it is
  not part of the public `vocabulary` block in `index.json`.

## On the `hh_doc_` / `hh_placed_` / `hh_ll_` prefixes

Three tools independently derive households from the 1835 register
(`data/research/newspapers/register_1835.json`) and the gazetteer, in a fixed
precedence order (best-evidenced first): `mint_documented_residents.py`
(a person with a printed trade), `mint_placed_residents.py` (no trade, but the
corpus places them inside the town and nowhere else), `mint_letter_list_residents.py`
(known only from the post office's letter lists). Until T-0599 each pass
stamped its own prefix onto the id it minted — `hh_doc_`, `hh_placed_`,
`hh_ll_` — so a tool could recognize "a household I minted" by filename alone,
for its own stale-file cleanup and precedence-skip logic.

**`hh_placed_` was never a location.** Every household from that pass carries
`"division": "unplaced"` — "placed" names the pass's own residency EVIDENCE
test (PART ONE of its docstring: does the corpus put this person inside the
town, as opposed to outside it), not a lot or plat position. See the note in
`tools/mint_placed_residents.py` right above `PART ONE — PLACEMENT`.

**As of T-0599, no new household is minted with a legacy prefix.** A
household minted by any of the three tools from here on gets the same plain
`hh_<surname>_<given>` id the ~73 hand-authored households already use, and
records which pass minted it in `source_pass` (`"documented"` / `"placed"` /
`"letter_list"`) instead. The tools still recognize their own prior output —
`minted_by()` checks the legacy prefix OR the `source_pass` field — so a
second run stays idempotent across the migration boundary and a household
never needs two ids for the same identity.

The **747 households already minted under a legacy prefix before T-0599** were
not renamed by that change alone — filenames are load-bearing (cross-referenced
by hardcoded ids in several frozen, gated selector scripts and by the
resident-research findings ledgers) and a rename touching all of them is its
own, separately tracked migration. Until that migration lands, a legacy-prefixed
filename on disk is not a signal of anything about the person it names — check
`source_pass` (once migrated) or just the household's own `grade`/`letter_list_only`
fields, never the filename, for what a household actually is.

`hh_inf_*` (5 files) is `tools/generate_inferred_households.py`'s own, unrelated
pipeline and is not part of any of the above.

## `kin` — a relationship that crosses two records (T-0597)

`persons[].relationship` is a person's place **inside** one household and stops
at that household's edge. A family tie between two households had nowhere to go
but a free-text note, which is to say nowhere a query can reach it — and the
households this dataset most needs to keep apart are exactly the ones a shared
surname makes mergeable. Four household cards here are Kinzies — six until
T-0839 folded two duplicate initials cards on 2026-09-05, and T-0732 ruled on
what the family's remaining prose claims are worth
(`data/research/residents/kinzie_kinship_ruling.json`).

`kin` is an optional household-level list. Each row is an ordinary graded claim
block — `value` names the **other person**, so `walk_attested()` checks its
`confidence`, `sources` and `note` exactly as it checks an `arrival` — plus
three fields that make it a link:

| field | means |
|---|---|
| `person` | whose relative this is; must be a person in **this** household |
| `relation` | the term, from `index.json`'s `vocabulary.kin_relations` |
| `household` | the other household's id; must resolve, and must not be this one |
| `value` | the other person's id; must be a person in that household |

Two rules, and both exist because **half** is the point. Hurlbut says James
Kinzie was the *half* brother of John H. Kinzie — same father, different
mothers — and that is the first thing a summary flattens:

- **A relation is legal only against its declared inverses.** For a sibling tie
  the mirror must be a sibling tie *of the same degree*; a `half_brother` whose
  mirror row says `brother` fails. The vocabulary is therefore exactly the set
  whose inverse `tools/validate.py` knows (`RESIDENT_KIN_INVERSES`).
- **Every row is reciprocal.** Write it on both records or on neither: the
  record that omits it still reads as no relationship at all, which is the
  defect the ticket was opened about.

A relation is refused outright unless its inverse is declared, and the rule is
satisfied rather than relaxed when the set grows: **T-0734 added the asymmetric
pairs together** — `husband`/`wife`, and the parent terms against the child
terms — so `father` is legal only against `son` or `daughter`, and a `father`
whose mirror row also says `father` is the one-way claim the rule exists to
catch. `uncle`/`nephew` and `cousin` are still undeclared, because nothing in
the corpus has needed them.

## `associated_with` — the places a person was, plural and dated (T-1238)

`lives_at` and `works_at` are **singular** and **undated**, and the sources are
frequently neither. Jeremiah Porter's record says so in its own note: Andreas has
P. F. W. Peck invite him "to make his **temporary** lodging place and study in the
unfinished loft of his two-story store", the word is the source's, the link is
dated 1833 — and "whether he was still in the loft in 1835 ... is unknown". A bare
`lives_at: peck_store` states none of that; it reads as the household's residence
on 1 July 1835, which is the one thing Andreas refuses to say. T-1237's
reconciliation row inherits the flattening and dates the same claim `1835-07-01`,
because that is all a singular field can mean.

So a relationship between a record and a place is a **list**. `associated_with` is
optional, may sit on a household **or** on a person, and each row is:

| field | means |
|---|---|
| `kind` | from `index.json`'s `vocabulary.association_kinds` |
| `place_or_structure_id` | a structure id, or the street / face / division the evidence reached |
| `resolves_to` | which of those it is — `structure`, `street`, `face`, `division` |
| `from` / `to` | a year, a month (`1833-06`) or an ISO day; either may be null |
| `tier` | `attested` / `inferred` / `reconstructed` |
| `source_id` | required above `reconstructed`, refused at it |
| `note` | the reasoning that dated it and the clause that limited its place |

T-1147 clause 7 names the six-field shape and says it is written on the person;
`resolves_to` and `note` are added to it for two reasons the rest of this layer
already insists on — a place that is a street is not a place that is a roof and a
consumer may not guess which it holds, and a claim here carries its reasoning.

Three rules, and each exists because of a specific way this goes wrong:

- **`place_or_structure_id` is never null. An absent relationship is an absent
  row.** The four rungs are the four a source can reach; "no place at all" is not
  one of them, because a relationship with no place is not a finding about where
  somebody was. John Bates jr has a workplace row and no home row — his `lives_at`
  says "Not attested." and that is an absence, not a claim. (T-1237's *seating
  class* axis is a different question and does need a `none` class: it is defined
  over the whole household layer, this list is defined over claims.)
- **A row that dates neither end must say `"undated": true`.** An undated
  relationship is an admission this project counts, not a gap a later reader
  mistakes for an oversight.
- **The singular link may not drift from the plural rows.** Both shapes stand
  until the migration lands, so a record carrying `associated_with` and a non-null
  `lives_at`/`works_at` must carry that structure among its rows —
  `lives_at` against a `home`/`lodging` row, `works_at` against one of
  `agency_held`/`business_premises`/`church`/`civic_seat`/`school`/`workplace`.
  Otherwise the half-way point of the migration is a record that says two
  different things about the same man and a reader gets whichever field they
  happened to load. `tools/validate.py` refuses it.

`land_purchased` is in neither family on purpose: a holding is not a place a man
was.

**What this buys, in one record.** The Porter household's single `works_at` names
the First Presbyterian Church for the minister's charge and says nothing whatever
about his wife. Eliza Chappel Porter kept Chicago's first infant school; her own
rows carry it at `chappel_infant_school` from 1833 **to 1834** — a relationship
that was over before the scene date, which no singular field in this layer can
express — and her founding membership of that same church from June 1833. Two
kinds, one roof, two people, three dates.

**What is not yet written.** Four records carry rows; the other 1,253 do not, and
`tools/associations.py --check` prints the distance every run. The `street`,
`face` and `division` rungs are declared and unused here because the corpus
already needs them and this ticket does not spend them: T-1237 committed 61
street-only and 62 unplaceable business locations and 52 households whose evidence
reaches a division and no further. Those are T-1239's and T-1198's to write, and
the migration of the singular fields themselves is its own ticket — nothing in
this layer reads the plural rows yet, so no renderer changes with them.

## The kinship the corpus states, surveyed and ruled on (T-0734)

The audit that opened T-0734 found **14 of 1,404** people related to anybody at
all, and the cause was never that the sources are silent: the St Cyr register
marries six couples this town holds both halves of, and nothing had read it.

Two files, and they are two on purpose:

| file | |
|---|---|
| `kin_survey.json` | **DERIVED** by `tools/survey_stated_kin.py`. Every stated kinship in the committed corpus, with both ends resolved against this layer. Re-derived by `--check`; hand-edits lose. |
| `kin_rulings.json` | **AUTHORED**. One verdict per landable proposal — `landed`, `refused` or `deferred` — each with its reason. No pass may rewrite it. |

`tools/check.sh` runs `survey_stated_kin.py --check`, which fails while a
proposal whose two people this dataset holds is unanswered, while a `landed`
ruling has no reciprocal `kin` rows on the two records, or while a `refused` one
has them anyway. A newly stated kinship is therefore a red build rather than
something to notice one day.

How a name becomes a person differs by source, and the line is drawn at
identity, never at the tie:

- **A register entry** resolves through the `..._evidence[].record_id`
  back-links the cards already carry. Most of these people exist *because of*
  the entry that names them, so nothing is matched by name at all. Where a
  back-link is missing but a townsperson shares the name, the row is
  `identity_not_asserted` and is **not** proposed — the town's John Murphy is
  attested from three sources that are not the register and no one has ever
  established that he is the register's groom.
- **Prose already quoted onto a card** takes that card's head as the subject and
  resolves the other party by the st_cyr crosswalk's own rule: surname folds
  equal, forenames agree initial for initial, and **exactly one** townsperson
  may match. Two is `ambiguous` and is reported rather than guessed. A bare
  forename inside a card (`brother of Samuel`) is read with the subject's
  surname and then has to resolve like any other name.

The 1840 census households are the densest kinship the corpus holds and are
deliberately **not** read: the crosswalk is stale against both the pages
(T-0714) and the town (T-0698), and kin read off it would land on the wrong
people.

## One person, several cards — and a surname the printer spelled two ways (T-1001)

`card_merge_rulings.json` is the written ruling on every cluster of cards that the
candidate test joins, and `tools/consolidate_town_cards.py` lands it. That test buckets
by surname and folds the surname **exactly**, so two spellings of one name never meet in
it. T-1001 is the first cluster written into the file for a surname rather than a
forename, and what moved is itemised here because the next pass should not have to
re-derive it from a diff:

| | |
|---|---|
| `data/residents/card_merge_rulings.json` | rule **C9** added — one surname, two spellings of its ending, ruled at the page; cluster `kimberley` (`derived_candidate: false`) added with its merge ruling; T-1001 added to `also_ruled_on`. |
| `data/residents/households/hh_kimberley_ed.json` | **gone** — the household held one person and that person folded. |
| `data/residents/merged/hh_kimberley_ed.json` | the record, kept whole, with its `merged_into` block. Nothing is deleted. |
| `data/residents/households/hh_pruyne_kimberly.json` | `kimberly_edmund_s` gains the folded card's sources (`census_1840_chicago_familysearch_images`, `chicago_democrat_1833_1835`, `isa_public_domain_land_tract_sales` were already his by the register) and a `merged_from` block. **His grade is untouched: attested, G1a, exactly as before.** |
| `data/residents/index.json` | one more row in the `merged` redirect table; the household count falls by one. |
| `data/research/residents/card_merge_crosswalk.json` | the landed adjudication the consolidation reads, one merge longer. |
| `data/research/land_sales/resident_rulings.json` | `KIMBERLEY EDMUND S` re-pointed from `kimberley_ed` to `kimberly_edmund_s`, with an `amended` block naming what changed and what did not. |
| `tools/read_land_sales.py` | `merged_card_surnames()` — the surname a folded card printed still gathers the person it was ruled to be, so the register's KIMBERLEY reaches Dr Kimberly. Matches that arrive this way carry `via_card_merge`. |
| `tools/measure_surname_fold.py` | new. The count the ticket asked for. |
| `data/research/census_1840/resident_crosswalk.json` | the head `Ed. Kimberley` falls from L7 `candidate` to L2 `no_surname_in_the_1835_pools` — **a loss, and the one cost of this merge**. That crosswalk gathers its 1835 bearers by surname and folds the surname exactly, which is the same fault, and it is deliberately not repaired here: teaching it the merge would hand its ladder the independent discriminator L6 wants (Fergus 1843 prints him) and the head would return `matched` rather than the candidate it was. A merge must not promote an identity as a side effect, so that is its own ticket. |

**Why the merge, in one line:** the Chicago Democrat of 1 July 1835 sets both spellings in
one column of one page — `E. S. Kimberly` in the dinner committee's signature block and
`E. S. Kimberley` in the next article's committee of fourteen, with `Dr. Kimberly` four
sentences after it — and T-0839 had already folded the first of those two readings onto
Dr Edmund Stoughton Kimberly on the owner's own instruction. The full reasoning, and what
would say two men, is in the ruling.

**Why the fold itself is NOT widened**, which is the other half of the ticket and is
answered with a count rather than an opinion. `tools/measure_surname_fold.py` puts a
one-letter fold over the land register's 427 named purchaser spellings:

    gain at least one rival        200 of 427   (47%)
    proposals that change shape     42          24 named matches LOST, 18 refusals named
    hand rulings touched            39 of 72    18 of them sitting on a proposal that moves

and the losses are not noise. `PEARSONS HIRAM` is refused against *Hiram Pearson*,
`CLYBOURNE ARCHIBALD` against *Archibald Clybourn*, `LLOYD ALEXANDER` against *Alexander
Loyd*, `PRUYNE PETER` against *Peter Pryne* — in each the rival the loose fold gathers is
the same man under a variant spelling, and a correct match is refused for having made him
his own rival. T-0993's `BLANCHARD GURTREY` is worse: its hand `named` ruling is
re-pointed onto the garbled card `blanshard_g`, so a written judgement silently changes
who it names. So the mechanical fold stays exact, and a surname the sources spell two ways
is **ruled**, one cluster at a time, on a page that demonstrates the variation.

## One card, several men — the ruling that takes a reading OFF a person (T-1004)

`card_merge_rulings.json` above asks whether a cluster of cards is one man.
`card_conflation_rulings.json` asks the opposite question of a SINGLE card: is this
card one man? Until T-1004 nothing could answer no. `tools/consolidate_resident_evidence.py`
had `declared_anchors()`, which forces a reading ONTO a person a crosswalk has matched,
and no opposite — so where the town held one man of a name and the sources held two, the
second man's documents folded onto the first man's card and nothing said so.

`declared_splits()` is that opposite and reads this file. A ruling is one of two states,
and they are gated in **opposite directions**:

| state | what it does | what the gate proves |
|---|---|---|
| `split` | names readings that come off the card, each with its rule and its reasoning | the reading is OFF that person, on an identity held apart by the ruling's own rule, standing on no card where the ruling says the second man is not in the layer |
| `recorded` | nothing moves — the card is written down as gathering two men, with the question it leaves open | the readings named in `still_on_the_card` are STILL on that person, so something else moving them makes the ruling stale and red |

The rules a split may stand on are `SPLIT_RULES` in that tool, echoed into the master:
**X1** one volume prints both men · **X2** the entry's own qualifier names the other man ·
**X3** the arithmetic refuses it · **X0** recorded, not split.

Two things worth knowing before adding a ruling:

- **A conflation ruling outranks the anchor it contradicts**, and it is the only place
  this tool sets a declared adjudication aside. Norris 1844's `King, N. clerk, at T.
  King's` was crossed onto Nehemiah King by the directories' own crosswalk, on a count of
  who holds a card; the ruling that takes it off him rests on Fergus 1839 printing `King,
  Nathaniel, clerk, Tuthill King`. Both are declared, the later one was made with the page
  in hand, and the override is written into the master's `declared_refusals` naming the
  anchor it displaced. Never silent.
- **A name may have to move with the reading.** `hh_bowen_erastus_selden` was minted under
  the name of the man being ruled off it, so the split alone would have left two identities
  sharing one id. `name_as_ruled` moves the card's name and the gate holds it there. The
  **id does not move**: `bowen_erastus_selden` is a key quoted in twenty-seven committed
  files, and renaming it is a mechanical change with nothing to do with which man is which.
  The disagreement between the id and the name is recorded on the card rather than hidden.

## The merge rulings are guarded against a lost judgement (T-1125)

`card_merge_rulings.json` carries the owner's 64 written rulings on which town cards are
one person, nested one level inside the 50 clusters the surname test proposed.
`consolidate_town_cards.py` reads them and WRITES
`data/research/residents/card_merge_crosswalk.json` from them — so the crosswalk is the
mirror and this is the original. A ruling that vanishes from here does not break the
consolidation; it lands one fewer merge, and a resident silently re-splits into the several
cards T-0839 joined.

Since T-1125 `tools/check_rulings_not_lost.py` (run by `check.sh`) holds this file to the
MERGE BASE. A judgement is `(the cluster it is about, the rule it applied)` — the cluster
and not the ruling alone, because eleven clusters carry more than one ruling and a
cluster-level count would not see one of them leave.

**Left out**: `rules` is the rule text C0–C22 the rulings cite; `derived_candidate` and
`why_not_derived` describe how a cluster was proposed rather than how it was decided; and
`also_ruled_on` is a LOG OF PASSES — a date, a ticket and a sentence about what that pass
decided — whose decisions are themselves in `clusters[].rulings`, so counting it would
count the same judgement twice under a key that is a date.

The two files the guard REFUSED entry, with the reason on record in the tool's `REFUSED`
table: `card_merge_crosswalk.json` and `town_card_candidates.json`, both written by
`consolidate_town_cards.py --apply`. The candidates file is a worklist that gets *smaller*
as clusters are ruled on, so a floor under its count would be a gate against the work
getting done.

**To remove a ruling**, move it into a top-level `withdrawn[]` carrying the cluster `id`,
the `rule`, a `reason` and the `ticket` that decided it.

## `roles[]` is the trade record; `occupation` is a view of it (T-1229, of T-1145)

A person's trades, professions and offices live in `persons[].roles[]`, and
`persons[].occupation` is a **generated compatibility view** of the roles that
actually cover the scene date. `tools/derive_resident_roles.py` writes both;
`tools/check.sh` re-derives them every commit and `tools/validate.py` holds the
shape. Never hand-write either.

The singular field was the defect. It holds one word, one confidence and one
implied date — 1 July 1835 — so a man printed as a candle manufacturer in 1833, a
brickmaker in 1839 and a school inspector in the 1839 civic register could only be
one of them on his own card, and the surviving one was dated to a year no source
cited for it describes. That is exactly what Daniel Elston's card did.

A role row says:

| field | what it is |
|---|---|
| `role` | a controlled word from `index.json`'s `vocabulary.occupations`, or **null** where the source's own wording has not been adjudicated into it — null is honest, a near word is not |
| `as_printed` | the source's own wording, where the card carries it |
| `kind` | `vocabulary.role_kinds` — a trade, a profession, an office, an employment or a business interest |
| `from` / `to` | the bound the evidence permits, **both ends or neither** |
| `precision` | `vocabulary.role_date_precision`; `source_span` is the honest answer when the bound is the span a volume is ABOUT |
| `dated_by` | `vocabulary.role_dated_by` — a date with no account of where it came from cannot be argued with |
| `covers_scene_date` | whether the evidence reaches 1 July 1835, on `audit_scene_window_trades.covers_scene`'s rule and deliberately no other |
| `confidence`, `sources`, `claim`, `note` | as everywhere else in this dataset |

Two rules are load-bearing:

- **An unknown date stays unknown.** It is never widened to the scene date, and a
  role with no bound may not claim a precision.
- **A role that does not reach 1835 cannot fill the 1835 field.** Where one used
  to, `occupation.withdrawn_from_scene_date` carries the trade, the grade it was
  held at and `tools/audit_scene_window_trades.py`'s verdict for taking it off, so
  the withdrawal states its reason on the card and not only in a ledger. That is
  T-0991's repair, and it is why the audit's standing population is now zero.

Two roles covering the scene date are **two roles**: both stand in `roles[]` and
`occupation.roles_at_scene_date` names both, so the singular field can no longer
decide which of a man's two trades the town is told about. A person with no role
evidence carries no `roles[]` and no view keys — and, the assertion that absence
makes, no trade in the 1835 field either.

What this does not yet read: the newspaper gazetteer's `persons[].occupations[]`,
the 1839 directory and civic-register crosswalks and the 1843/1844 identity-master
appearances, together with each role's stated place and employer (T-1254); and the
People view's dated timeline (T-1255).

## `profile_facts` — what the matched research actually said (T-1232)

94 of this layer's `resident_research` blocks carry `asserted_identity: true` — the
project's own verdict that the person traced through a county history, a family
genealogy or a church roll is the person on the card. The facts inside those blocks
lived in their `summary` and `evidence_for` PROSE, beside structured fields on the
same record that read `"Not attested."` `hh_andrus_thomas` is the defect in one file:
a DuPage history gives "arrival in Chicago Dec. 1, 1833" and the card's `origin`,
`reason_for_coming` and every dated life event said nothing.

`tools/spend_person_facts.py` reads
`data/research/residents/person_fact_readings.json` — the hand reading of those 94
blocks — turns EVERY candidate in EVERY research block into a row of
`person_facts.json`, adjudicates it, and writes the asserted ones here.

`persons[].profile_facts` is an optional list. Each row is an ordinary graded claim
block — `value`, `confidence`, `sources`, `note` — plus five fields that make it a
dated reading rather than a 1835 claim:

| field | means |
|---|---|
| `field` | the fact class: `arrival_at_chicago`, `origin`, `sex`, `name_as_printed`, `birth_year_bound`, `death`, `marriage`, `life_event`, `departure_from_chicago`, … |
| `describes_date` | the date the reading SPEAKS ABOUT, which is not the date it was printed |
| `place_class` | `chicago`, `outside_chicago` or `not_a_place` — a fact set somewhere else is why a presence could not be lifted |
| `record_id` | the research block and the row within it, `resident_research:T-0485#01` |
| `as_read` | the sentence it was read from, so the verdict can be disagreed with |

**It never displaces anything.** A household's `arrival` is a separate claim and a
postal bound and a stated arrival are different things; both stand. The only fields
this tool may fill are a household's NULL `origin` or `reason_for_coming`, and only
where the household holds one person — a household field speaks for everybody under
the roof, so one person's origin may not be dealt to a second.

**It mints nobody.** A marriage names a spouse and a chronology names a travelling
companion; neither becomes a household member. T-1170 fills families from exactly
these rows, under the household model, where every such person carries a basis and a
seed.

**The withheld rows are the product.** Most candidates are refused and each refusal is
written down: `later_only` (T-0513's ladder — a volume printed after the scene may date
and corroborate and may never promote), `outside_chicago`, `contradicted`,
`insufficient_identity`, `duplicate`, `no_candidate`, or `unresolved:T-NNNN` where the
fact belongs to a field another ticket is building (a trade is T-1145's plural roles, a
premises is T-1147's location spend). T-1159's borderline roster is a FILTER over
`person_facts.json`, not a second reading of the same corpus.
