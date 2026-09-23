# The residents layer: the town's people, and what each of them rests on

**Data:** `data/residents/` · **Manifest:** `data/residents/index.json` ·
**Gate:** `check_residents` in `tools/validate.py`, tested in `tools/test_validate.py` ·
**Scene date:** 1835-07-01 ·
**The measured state:** `docs/RESEARCH/residents-households-summary-2026-09.md`

> **This dossier describes the model. It carries no population figures**, because they move
> every week and a number typed into prose goes stale silently. The summary beside it prints
> every figure from a command over the committed layer; run
> `python3 tools/summarize_residents.py` and the answer is current by construction.
>
> **Rewritten for the current model under T-0517 (September 2026).** Everything before that
> described the 2026-08 phase-one parcel of 72 households, a `documented` / `derived` /
> `inferred` grading and a reconstructed population that no longer exists. The old text is
> in the file's history.

---

## 1. What this layer is for

Chicago went from about 350 people in 1833 to 3,265 in the town census of November 1835
(`andreas_1884_v1`, printed p. 180, archive.org scan p. 377), counted in 398 dwellings. The
programme's argument is that the people and the buildings are the same problem seen from
opposite ends: *the population is what justifies the roofs*. A household that needs a
dwelling can become a structure record on the plat, archetyped, baked and confidence-graded.

**No human figures are drawn.** `docs/LIBERTIES.md` L1 and AGENTS.md stand: this ships an
empty, accurate town. This is a dataset layer feeding structures, the register and the
evidence panel.

## 2. The schema, and the one thing about it that is easy to get wrong

`data/residents/index.json` is the manifest — a static host cannot be globbed — and
`data/residents/households/*.json` is one file per household. The shape mirrors
`data/flora/` and `data/fauna/`: denormalised copies in the manifest, the record
authoritative, the validator failing the build on drift.

**There are two orthogonal grading axes and they must not be conflated.**

| axis | key | vocabulary | what it grades |
|---|---|---|---|
| evidence | `confidence` | `attested` / `inferred` / `reconstructed` | an **attribute** — the same contract as a roof pitch |
| resident evidence | `grade` | `attested` / `inferred` / `reconstructed` | a **person** — how strongly the town's records place them here |

The two vocabularies are the same three words on purpose — the project has one accuracy
ladder — but they answer different questions, and a person graded `attested` may carry an
attribute graded `reconstructed` and routinely does. `occupation` is the common case: a
person the poll book names is `attested`; the absence of a trade beside their name is
written as `none_recorded` at `reconstructed`, because "the list did not print a trade" is
not evidence that the man had none.

**Two terms are retired and the validator refuses them by name.** `recommended` was renamed
away from on 2026-08-13 (`RETIRED_GRADE_TERMS` in `tools/validate.py`, with a message
pointing at the rename), because a vocabulary that merely omits a word gets it back the
first time somebody copies an older file. `derived` was the phase-one grade for a real named
person partly reconstructed; it is now `inferred`, and the axis table above is what stops
the old conflation coming back.

## 3. The three grades, the subtype, and the ladder that assigns them

- **`attested`** — the town's own contemporary records name this person here. Requires at
  least one `source_id` that resolves in `data/sources/`.
- **`inferred`** — a real, named person the evidence reasonably places in the 1835
  population, with something about them reconstructed: their presence read across from a
  partnership, their forename from another record, their residence bounded rather than
  dated. Requires a note stating *which* details are reconstructed and from what — a real
  person with invented details and no reasoning is indistinguishable from a fabrication.
- **`reconstructed`** — a hypothesised person filling a demonstrable need of the town.
  **The layer holds none, deliberately.** The 108 the earlier programme had minted were
  retired in the 2026-09-02 synthesis. The grade stays in the vocabulary, gated and tested,
  so a later explicit reconstruction pass can use it without a schema change. If one ever
  returns it carries a `name_basis` block: an invented name can never grade above
  `reconstructed`, because a name *looks* like a fact in a way that "wall height 3.25 m"
  does not.

`resident_subtype` is the second axis on a person and has one value, **`projected_resident`**
— the weakest evidence-based subset of `inferred`, a person whose whole claim on the town is
one appearance, or several of a class no stronger rung accepts.

**The ladder** is written into `index.json`'s `vocabulary.ladder_rules` and is the machine-
readable form of the grading policy in `docs/RESEARCH/resident-grading-policy.md`. Its rungs,
in order: **G0** refuses outright — every appearance describes a date after the scene year,
and 1839 or 1840 alone is never an 1835 resident. **G1a/G1b/G1c** grade `attested`: the 1835
poll list plus an independent source; a contemporary record naming the person in the town;
or convergence — two in-window records from *different* class families that did not copy each
other. **G2a–G2e** grade `inferred`: the poll list alone, an 1833/1834 list with another
source, the St Cyr register, a later directory naming someone the town already carries, and
— G2e — a post-office letter list and nothing stronger. **G3** and **G4** grade `inferred`
with `projected_resident`. **G5 abstains**: the town already carries the person and every
appearance the consolidation can see is later, so the row goes to the owner as a conflict
rather than demoting a resident on evidence the ladder has not read.

A `ladder_rule` on a person names the rung that graded them. Only the civic mint writes one;
the earlier mints graded before the ladder existed and their reasoning is in the notes.
**That is an audit-trail gap, not an evidence gap**, and the summary counts it.

## 4. The four mints, and the precedence between them

Every household is `hh_<surname>_<forename>` — the prefix families `hh_doc_`, `hh_placed_`,
`hh_ll_` and `hh_civic_` are **gone**, collapsed by the T-0638 rename
(`data/residents/rename_map_t0638.json`, applied by `tools/rename_household_ids.py`). What
minted a household is now recorded in its **`source_pass`** field, which
`RESIDENT_SOURCE_PASSES` closes to four values. A hand-authored household omits the key.

| `source_pass` | tool | what it mints from |
|---|---|---|
| `documented` | `tools/mint_documented_residents.py` | the newspaper register's `new_resident` people whose **trade** the papers print |
| `placed` | `tools/mint_placed_residents.py` | the register's people who pass the residency test — named in the town, doing something in it |
| `letter_list` | `tools/mint_letter_list_residents.py` | the Chicago post office's letter lists of 1833-1835 |
| `civic` | `tools/mint_civic_residents.py` | the town's own lists — poll books, tax rolls, the 1832 muster |

`documented` here is a **pass name and not a grade**; it is the one place the retired word
survives, kept because renaming a gated enum value is a migration and not a documentation
fix. Everything the word once graded is now `attested`.

**The precedence is `civic` above the other three** (T-0514). Each mint refuses to write a
person the town already carries, and the sharpest of those refusals is by family name — *the
town already names a Smith* — because a bare surname on a list is probably the Smith the town
already holds. That refusal is a proxy for identity and the better-evidenced pass gets to
spend it: the civic lists say a man voted or paid tax **in the town**, which is a stronger
claim than that his mail was waiting for him at its post office. Each mint also excludes its
own output when it reads the town, so the refusal is about what stood before the pass ran.

## 5. The evidence blocks

Beyond the flat `sources` array, a person may carry a typed block per body of record:
`press_evidence`, `civic_evidence`, `book_evidence`, `church_evidence`, `census_evidence`
and `biographical_evidence`. Each holds the reading itself — what the record says, where it
says it, and the locator — so that the *kind* of record standing behind a person is
machine-readable rather than inferable from a source id.

That is what makes convergence checkable. `tools/export_resident_audit.py` categorises every
cited source id — newspaper, civic, census, church, book, directory, secondary — and reports
`corroborated_across_categories` only where two different kinds of record agree. Two
newspaper notices of the same name are `two_or_more_sources_one_category` and no stronger.
**The category table is the audit's one judgement**, written record by record in that tool
rather than heuristically, and a source id no rule reaches stops the build.

`resident_research` is the parallel block: which research ticket looked at this person, on
what date, what it concluded (`corroborated`, `corroborated_enrichment`, `candidate`,
`candidate_identity`, `no_corroboration`, `no_corroboration_yet`) and whether an identity was
asserted. `no_corroboration_yet` and `no_corroboration` are different claims — the corpus not
yet searched to exhaustion, against searched and found nothing — and neither is evidence that
the person did not exist.

## 6. The 1840 bridge, and the rule that keeps it from leaking

The project holds a substantial 1840 census layer under `data/census/1840/` — named
household heads on the printed pages, with resolved IPUMS serials and household demographic
fields. **1840 is later evidence, not the 1835 household**, and the rule is absolute:

- A bridge is an explicit, graded assertion on a person — a `later_census` block naming the
  year, the serial and the bridge's confidence. It is never minted in bulk from a name match.
- **Nothing crosses the bridge backwards.** Household totals, children, sex structure,
  industry, foreigner and literacy fields stay under the census dataset. They do not mint a
  spouse, a child, a partner, a servant or a boarder into the 1835 layer, and they never
  raise an 1835 grade.
- 1839 or 1840 evidence *alone* is rung G0 — not an 1835 resident at all.

The bridge's value is the reverse direction: an 1840 row is how a person the 1835 lists name
once acquires a household, a trade and sometimes an address, all correctly dated as five
years later. `docs/RESEARCH/resident-household-synthesis-2026-09-02.md` records the first
validated bridges and the reasoning; the same rule governs the directories of 1839 and 1843,
whose addresses may be carried back only as `inferred`, with the date of the printing on the
note.

## 7. A street name nobody else uses

Matthias Mason's own 1833 advertisement puts his smithy on **"Main-street"**, which appears
nowhere in `data/traces/street_control.json`, the Thompson plat module or either 1834 sheet.
The cross-reference is usable: Graves' Tavern is the log tavern at what became 84-86 Lake
Street, so "Main-street" in November 1833 is very probably Lake Street under a colloquial
name. **Recorded as a finding for the streets layer, not acted on** — and cited as this
section by `data/structures/mason_blacksmith_shop.json`, its sidecar and
`data/signage/town_business_signboards.json`, which is why this dossier keeps a § 7. The
signboard takes the firm and the trade word and refuses the address.

## 8. The scene-date gate, and the removal

An arrival after 1835-07-01 is the population layer's version of the Saloon Building problem,
and it fails **silently**: a household record for a man who reached Chicago in September 1835
looks exactly like one for a man who reached it in 1832, and this layer licenses buildings.

Arrival values carry a **`precision`** — `day`, `either_of_two_days`, `month`, `season`,
`year`, `not_later_than` — because the sources give years far more often than days, and the
rule is **asymmetric on purpose**: the *earliest* day a value permits must not be after the
scene date → **error**; a value whose *latest* day is after it → **warning**, because "1835"
with no month is a real state of the evidence and not a mistake. `not_later_than` exists
because the commonest evidence of residence in this corpus is *an act performed at Chicago on
a date* — an advertisement placed, an office taken, a tavern licensed. That bounds an arrival
from above and not at all from below, and calling it a month precision would be a claim nobody
made.

`either_of_two_days` exists for the opposite reason, and for one record: a source that is
exact to within a day and *will not pick between two of them*. Hurlbut has Gurdon Hubbard
first reaching Chicago "on the last day of October or first day of November" of 1818, and
every other precision here misreports that sentence — `day` chooses one of the two on the
reader's behalf, and `month`, `season` or `year` widen a nearly-exact reading in order to
contain both. The value is the **earlier** day and the bound runs to the day after it, so the
gate sees the two days the source offered and no others. (`hh_hubbard_gurdon`, T-0594.)

`review_required` and `touches_removal` mark the households that touch the removal of 1835-36
— the Indian agency's establishment, the families with Native kin, and the households the
sources name at Wolf Point — and the validator makes the second imply the first. Two datings
are held side by side and **not** averaged: Andreas puts the last assembly and the march to
the Missouri in 1836; `chicagology_lastwardance` puts the last great war dance at Chicago on
18 August 1835; AGENTS.md takes the 1835 dating as the project's standing constraint. Under
either, 1 July 1835 is before it. Nothing in this layer improvises Native presence,
representation or depiction; it states what named sources say about named people and stops.

`index.json`'s **`researched_not_resident`** is the exclusions-style half of the dataset and
is as load-bearing as the households. Three kinds of finding live there: a person whose
arrival is after the scene date; a person the sources place at Chicago but not as a resident
of the town; and a person this project believes was here and cannot cite. **Adding to that
list is preferred to deleting from it**, exactly as `data/exclusions.json` requires for
structures.

## 9. The gates this layer must pass

| gate | what it refuses |
|---|---|
| `check_residents` (`tools/validate.py`) | the schema, the closed vocabularies, manifest/record drift, duplicate person ids, a household with no persons, an unresolvable `source_id`, the scene-date rule, and the retired grade terms by name |
| `check_resident_grade` | an `attested` person with no source; an `inferred` person with no note; a `reconstructed` person with no `name_basis` |
| `tools/town_census.py --check` | the town census re-derives from the roofs and the residents; it is DERIVED and hand-edits are refused |
| `tools/export_resident_audit.py --check` | the committed audit table matches the layer, row for row |
| `tools/consolidate_resident_evidence.py --check` | `identity_master.json` re-derives from the landed domains |
| the mints' own `--check` / `--self-test` | each pass re-derives its own output from its source, and its refusal ranking is tested |
| `node tools/check_published_residents.mjs` | the published mirror carries its source's values |

## 10. The liberties this layer stands on

`docs/LIBERTIES.md` is the register of what this project invented, and the population layer
is the largest single entry in it. **L205** — five men the papers name, given reconstructed
roofs. **L206** — sixteen tradespeople the papers name, written as households of one, where
the *household* is the invention and the man is not. **L207** — twelve letter-list names
written the same way, on the thinnest evidence this project accepts for a resident.
**L211/L212** — businesses standing because nothing says they closed, and nineteen of them
seated on reconstructed roofs. **L213** — four people the papers name with no trade, on a residency
test. **L214** — the ruling that scaled L207 up, and the reason three quarters of this town's
people are a name on a post-office list and nothing else. **L220** — the newest, and the
civic mint's: 531 people join the town on the town's own lists, and a household is written
round each of them.

Read together they say one thing, and it is the honest reading of this layer: **the names are
real and the households are ours.** Every person here comes from a record that names them. The
claim that each of them constituted a household — rather than boarding, lodging, or living in
somebody else's — is the project's, is stated, and is why the layer's mean household size sits
just above one while the town census counts 8.20 people to a dwelling.

## 11. What this layer still cannot say

- **Almost nobody has an address.** The overwhelming majority of households are `unplaced`,
  and the summary measures how few resolve a `lives_at` or a `works_at`. The route in is the
  later directories under the § 6 rule, businesses before residences.
- **Sex is recorded for a small minority**, and the split among those is a property of the
  lists — which print an initial and a surname — and not of the town. It must never be read
  as a sex ratio.
- **The enlisted garrison is absent.** Fort Dearborn was an occupied post; the officers are
  written and no private soldier is, because no source in `data/sources/` names one. That
  needs a muster roll, not a guess.
- **The 1835 town election's date.** Andreas says only "in July, 1835"; the 1833 and 1834
  elections were held on the 10th or 11th of August. This project cannot say whether the
  board sitting on 1 July 1835 was Kinzie's or Hugunin's, so no office-holding claim rests
  on it.
- **The gap itself.** The town census counts 3,265 people four months after the scene date
  and this layer names a fraction of them. That difference is the correct, stated size of
  what the sources do not say, and closing it by reasoning about family sizes would replace
  a dataset whose every row cites a record with one whose rows cite an average.

**Related:** `docs/RESEARCH/residents-households-summary-2026-09.md` (the measured state) ·
`docs/RESEARCH/resident-grading-policy.md` (the ladder, argued) ·
`docs/RESEARCH/resident-household-synthesis-2026-09-02.md` (the synthesis that emptied the
reconstructed grade) · `docs/RESEARCH/residents_1835_inferred.md` (**stale in the same way
this file was** — it still describes the retired reconstructed population; rewriting it is a
separate slice) · `chicago/reference/resident-research/final/audit/` (one row per person).
