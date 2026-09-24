# The provenance model

This is the part that makes the project worth doing. It is fixed before there are thirty
buildings in the dataset, not after.

> **The words, and when they changed (2026-08-15, K23a).** The three levels are
> **`attested` · `inferred` · `reconstructed`**, and `tools/validate.py` (`CONFIDENCE`)
> rejects anything else — it is the enforcement, this page is the explanation. Until
> K23a this page still named them `documented` / `inferred` / `conjectural`, the
> vocabulary the v76 merge of 2026-08-13 retired; a record written to this page would
> have failed the build. `documented_range` keeps its name: it is a field, not a level.
> **ROADMAP K16 proposed a different rename and is superseded** — do not follow it.
>
> The rename is not cosmetic, and the middle tier is where it bites. `inferred` used to
> be the BOTTOM tier, so "an inferred building" meant an invented one. It is now the
> MIDDLE tier — *reasoned from evidence about this particular thing* — and the bottom
> tier is `reconstructed`. Prose written under the old sense therefore claims a grade
> better than its own record, which is exactly the fault K23a swept out of 193 structure
> records and the building card.

## Confidence is per attribute, not per building

You will routinely know a building's footprint and location precisely while knowing nothing
about its roof pitch. A single confidence score per building would either lie about the
footprint or lie about the roof. So every attribute carries its own.

```jsonc
"form": {
  "stories":  { "value": 2, "confidence": "attested",
                "sources": ["kinzie_waubun_1856"] },
  "gallery":  { "value": true, "confidence": "reconstructed",
                "note": "All surviving images are retrospective and disagree. Unresolved." }
}
```

| level | meaning | validator requires |
|---|---|---|
| `attested` | a primary or near-primary source directly attests this attribute at the scene date | ≥1 `source_id` resolving in `data/sources/` |
| `inferred` | derived from typology, adjacent evidence, or construction practice of the period and region | a non-empty `note` stating the reasoning |
| `reconstructed` | no evidence about *this thing*; invented to fill a demonstrable need of the town, bounded by a typology | a non-empty `note` stating the reasoning — and it is surfaced in the build report and rendered distinctly |

**A `reconstructed` attribute may cite `sources`, and usually should.** Under the old
vocabulary that combination was a warning — *conjectural but cites sources, so either it is
not conjectural or the citation is decorative.* That rule died with the rename and
`validate.py` no longer raises it. A reconstructed value is invented WITHIN a bound, and the
source that establishes the bound — the reconstruction programme, a trade roster, a census
total — is exactly what makes the invention defensible rather than arbitrary. What it may
never be is silent: the bottom tier owes its reasoning just as the middle tier does, which is
the gate that stops an invention nobody can defend from shipping as a reconstruction.

## The tier of an attribute, and the fourth one (T-1158, 2026-09-18)

The owner, 17 September 2026: *"note for each attribute of each person what is attested,
inferred or reconstructed and reasons why."* `confidence` above already grades an attribute.
What it could not do was tell an ABSENCE from an INVENTION, and on the resident layer that is
most of the layer:

| | blocks | what the card used to show |
|---|---:|---|
| `confidence: "reconstructed"`, `value: null` or `"none_recorded"` | 7,314 | the hatched *reconstructed* chip — "we made this up" |
| `confidence: "reconstructed"`, a real value | 40 | the hatched *reconstructed* chip — correctly |

Written the same way, they read the same way, and the common case is the misleading one: a
household whose origin, party, trade and address are simply not in the record was rendered as
four inventions. It also blocks the reconstruction bands, which need `reconstructed` to mean
the value they are about to supply.

So an attribute carries a **tier**, derived from its confidence and its value, with a fourth
value the confidence vocabulary has no word for:

| tier | meaning | validator requires |
|---|---|---|
| `attested` | a source says it | what `confidence: attested` requires |
| `inferred` | reasoned from evidence about THIS person or thing | what `confidence: inferred` requires |
| `reconstructed` | a value this project supplied, not a source | `basis`, `replaceable_by`, and `seed` when it was drawn |
| `unknown` | **nothing is asserted.** No source records it and nothing has been invented | `value` is null or the layer's own not-asserted sentinel |

`unknown` is not a weaker claim than `reconstructed`. It is the absence of a claim, and it is
69.7 % of the resident layer's 10,499 attributes — the single most honest number this dataset
publishes about itself. The walkthrough gives it an empty dashed chip and the words "not
recorded", so no reader can mistake a gap for a liberty.

```jsonc
"arrival": {
  "value": "1826", "confidence": "reconstructed", "tier": "reconstructed",
  "note": "NOT ATTESTED HERE. …",
  "basis": { "kind": "rule", "id": "arrival_uncited_literature",
             "note": "The year is the figure in general circulation …" },
  "replaceable_by": { "kind": "person",
                      "match": "a dated source that says when this person came to Chicago" }
}
```

**A tier is derived, never granted.** It is read out of the block's own confidence and
value; `validate.py` refuses a `tier` that disagrees with that derivation. Without that rule
the tier would be a second, softer grade that a writer could set to whatever flattered the
record — and the whole value of the fourth tier is that a band cannot quietly reuse `unknown`
for something it invented, or `reconstructed` for something it merely failed to find.

**Where the tier of an EXISTING value lives, and why it is not in the card.** Writing it into
the 1,258 household records was tried first and cannot stand: those bytes are owned by nine
derivations that each rebuild a card from its sources and compare the result to the committed
file — the resident synthesizer, the four mints, the two back-projections, the later-trade
qualifier, the kin survey and the four directory crosswalks. None of them knows the field
exists, so ten of `check.sh`'s steps go red the moment a tier lands in a card and stay red
until every writer emits one. Teaching nine writers is real work and it belongs with T-1144,
which owns that layer's drift. **A field nine writers silently drop is a field that lies.**

So the existing layer's tiers are derived — in `tools/migrate_attribute_tiers.py` for the
gate and the published table, and in `renderers/web/js/attribute-tiers.js` for the one card
a visitor has open, with `tools/check_attribute_tiers.mjs` holding the two to the same
answer. What a RECORD may carry is the full shape above, enforced by `validate.py` wherever
it appears: the reconstruction bands mint their own records and a value invented without a
basis and without a seed has to be refusable at the moment it is written.

**A reconstructed value owes a basis, and there are two kinds.** `kind: "model"` was DRAWN —
from the population, household or occupation model — so it owes the `seed` that redraws it: a
draw nobody can reproduce is not a reconstruction. `kind: "rule"` was ARGUED — the earliest
year the evidence forces, an address carried back from an 1843 directory under
`docs/ADDRESS-BACK-PROJECTION.md` — so it owes the rule's id and the reasoning, and carries
NO seed, because nothing was drawn. Requiring a seed of an argued value would mean inventing
one, which is what this document exists to prevent.

**And it says what would retire it.** The owner: *"so if we get new research … we can replace
the reconstructed person or business with an inferred or attested one later."* Every
reconstructed value carries `replaceable_by: { kind, match }`, where `match` is the
attribute's own definition read back as a search — what retires a reconstructed arrival is a
source that dates the arrival. It is not a prediction about the future, which is why the
migration can write it without inventing anything.

**Two different things are called a tier, and they never meet.** A SOURCE carries a numbered
tier — the 1–6 evidence ladder in the next section, "how good is this document". An ATTRIBUTE
carries a named tier — the four words above, "what kind of thing is this value". One is an
integer on a record in `data/sources/`, the other a string on a claim block; nothing reads
both off the same field.

Counts per attribute per tier, and every reconstructed value with its basis and its
replacement rule, are re-derived and never typed:
`data/research/residents/attribute_tiers.json`, or `python3 tools/summarize_residents.py
tiers`.

## Substitution: what a new source retires, and how it is read before it is done (T-1441, 2026-09-20)

`replaceable_by` states the promise. The owner asked for it in one sentence — *"so if we get
new research we can replace the reconstructed person or business with an inferred or attested
one later"* — and every reconstructed record above carries it. What the field cannot do on its
own is ANSWER it. A reader holding a new directory line would have to open 32 reconstructed
firms and 308 reconstructed trade heads, read 340 sentences of prose, and work out which of
them the line retires; and the expensive parts of a retirement are not written in the record
at all. `tools/substitute_reconstruction.py --dry-run` is the reading, and this is the rule
it implements.

**A candidate is a reading, never another reconstruction.** The tool takes a small JSON
document naming a record the research has just won — its `kind`, `tier`, the trade or census
class it belongs to, and the division if the source narrows one.
`tools/fixtures/substitution_candidate.json` is the shipped example and the fixture the
self-test runs over. A candidate at `tier: reconstructed` is REFUSED: a reconstruction cannot
retire a reconstruction, or the layer would churn without ever being read out of a source. An
`attested` candidate that cites no source is refused for the reason the ladder above gives.

**Three predicates, all of which must hold.**

  1. **The trade or class agrees.** A reconstructed record stands in for a count of its own
     class, so a candidate of another class replaces nothing and is an addition instead.
  2. **The place does not disagree.** Where both the candidate and the record name a
     division they must be the same one; where the record narrows to no division, the match
     stands and the plan says so. Silence is not disagreement — a `street_only` face is not
     a division, and reading one off a street would be making T-1182's ruling in passing.
  3. **The scene date agrees.** A house that arrived in the autumn did not stand in for one
     on 1 July 1835 and retires nothing.

**It never picks between matches, and that is a finding rather than a gap.** Where a class
leaves two reconstructed millineries on the same face, neither is more this candidate's than
the other on any authority — the same limit `docs/STREET-FACE-ADOPTION.md` states about order
within a face. The tool prints every match and names the choice as the operator's. A tool
that chose would be inventing the one fact the evidence does not carry.

**The retirement has three parts a hand-read loses, and the plan prints all three.**

  * **The id is redirected, not deleted.** The town is walked through links; a reader who
    bookmarked a house may not find a hole where it stood.
  * **The roof is carried.** A reconstructed firm seated on a committed structure did not
    invent that structure — the building stood before the firm was dealt onto it. The new
    record takes the roof; nothing is demolished.
  * **The order-book row re-opens by being ANSWERED, not by being filled.** An attested
    house of a class the December 1835 census counts raises that bucket's `known` by one,
    which lowers `to_reconstruct` by one, while the retirement lowers `filled` by one. A
    firm that fills no census row was bought by a trade head instead, and is withdrawn with
    the head — the plan names the head rather than inventing a quota for it.

**And it names the liberty whose count moves.** Every reconstructed firm is covered by an
entry in `docs/LIBERTIES.md`, and each of those entries states in its own prose how many of
the population are its own. `compile_liberties.py` re-derives the POPULATION and fails on
drift; it has never re-derived the SHARE, because a firm carries the ticket that built it
and a liberty carries no ticket, so the two cannot be joined out of the data. The tool holds
that join and re-counts both ends — the records on disk against each entry's own sentence,
required to agree and to sum to the scope — so a group rebuilt one house larger now fails a
gate instead of leaving a word like FIFTEEN standing over sixteen firms.

**THE TOOL WRITES NOTHING, AND THERE IS NO `--build` BESIDE THE DRY RUN.** Every reconstructed
record says the same thing about its own retirement: *the retirement runs through `--build`,
never by hand* — and the `--build` it means is its OWN generator's. Those tools re-derive a
whole population from the order book, and a record that is no longer ordered simply stops
being written; a second tool reaching in to delete one record would put the layer off the
fixed point `check.sh` holds it to. What retires a reconstruction is the SOURCE, entered
where sources are entered. This one reads the cost first.

## The business record, and the limit as a field (T-1310, 2026-09-18)

A business is the third thing in this dataset with an identity of its own — after a structure
and a person — and until T-1310 it was the only one with nowhere to carry a tier. It has a
record now: `data/businesses/<id>.json`, one file each, against `data/businesses.schema.json`.
`docs/RESEARCH/business-layer.md` is the page; two rules on it belong here.

**A printed name is attested. The link from it to a person is a separate claim.** The paper
prints *A. Clybourn* and that is attested at the printing. Whether that name is the same man as
the card `clybourn_archibald` in `data/residents/` is a second assertion with its own evidence
— the register's match — and the record keeps them apart:

```jsonc
"proprietors": [{
  "name": "A. Clybourn",                  // attested: the notice prints it
  "person_id": "clybourn_archibald",      // the LINK, with its own basis below
  "register_person_id": "person_a_clybourn",
  "role": "proprietor", "tier": "attested",
  "basis": "The register matches the printed name to the town card clybourn_archibald
            (action: enrich) … Dated by the printing window, which bounds the reading
            and does not date the partnership."
}]
```

Where the register made no match, `person_id` is `null` and the basis says the town holds no
card for them. **That null is a finding, not a gap to be filled by guessing** — the same
reading `unknown` gets in the table above. 157 of 209 named people link today; the other 52
are the queue for T-1189, and none of them will be resolved by matching a surname.

**A limit on a location is a location, not a missing one.** 61 of the register's businesses
give a street and no house; 62 give no anchor at all. Written as absence, those read as work
nobody had done. They are `locations[]` entries whose `kind` names the limit — `street_only`,
`unplaceable`, and `anchored` for a house placed against a landmark but holding no roof of its
own — and whose `limit_reason` quotes why the evidence stops there. The schema requires the
reason: a limit that does not say what it is is refused, exactly as an `inferred` attribute
with no note is.

This generalises the rule two sections up. `unknown` says *nothing is asserted about this
attribute*; a limit kind says *something is asserted about this location and it stops here*.
Both are claims about the evidence, both are counted, and neither may be written as a blank.

## Evidence tiers

Not all sources are equal, and the dataset should not pretend otherwise.

| tier | kind | examples |
|---|---|---|
| 1 | period document, eyewitness at or near the date | period surveys, the 1834 Wright and Hathaway maps, newspaper advertisements |
| 2 | near-primary recollection | *Wau-Bun* (1856, describing 1831) — the load-bearing text for the Sauganash |
| 3 | compiled secondary from pioneer testimony | Andreas, *History of Chicago* (1884) — cite the page for every claim |
| 4 | later scholarly synthesis | Encyclopedia of Chicago, academic ecology and geology |
| 5 | modern retrospective illustration or reconstruction | the Conley/Stelzer 1933 pictorial map, Kurz & Allison chromolithographs |
| 6 | decorative or popular cartography | the 1940 Nelson/Winters pictorial map — **orientation and toponyms only; no geometry** |

Tier 5 and 6 sources may inform *inventory* (what existed, roughly where) and *cross-checks*.
They must never be the sole evidence for an `attested` attribute, and no geometry is traced
from them.

### The ladder is enforced, and the enforced copy is the schema (2026-08-10)

Until now this table was prose. The word `tier` did not appear in `tools/validate.py`: every
other rung of the confidence model had a gate — `attested` owes a resolving source,
`inferred` owes stated reasoning, an invention owes an admission in `docs/LIBERTIES.md` —
while the question all of those assume an answer to, *how good is the source*, was checked by
nobody. `check_evidence_ladder` is that check, and `tools/tiers.py` reads the ladder out of
`data/source.schema.json`'s own `tier` description so that the rung a value is held to and the
rung a visitor is shown on the provenance card are one list. **The table above is the
reasoning; the schema is the copy the gate reads.** A rung spelled out in one and not the
other is a hard failure rather than a silent gap.

Two sentences in this document state the tier-5 rule and they are not the same rule — the
table says such a source may not be the *sole* evidence, and the revision below says it "never
reaches it, alone or in company". The table's reading is the one enforced, because the
revision exists precisely to stop over-caution making the dataset less accurate: refusing an
`attested` value that *cites* a retrospective alongside a period survey would punish
corroboration. A value carried by Wright 1834 and cross-checked against Conley/Stelzer is
better evidenced than the same value with the map struck out, not worse.

What is enforced, exactly:

| rule | state |
|---|---|
| an `attested` value needs at least one source at tier 4 or better | error |
| a `footprint` graded better than `reconstructed` may not cite tier 5-6 | error |
| a source at tier 5-6 may not declare `asset_use: geometry` | error |
| an `attested` value with no source at tier 3 or better | **warning, counted** |

The last one is a warning on purpose and 21 committed values are in it. `attested` "still
requires a period source", and the ladder puts first-hand and testimony-derived evidence at
tiers 1-3; a value resting on nothing but later synthesis is either over-graded or its source
is under-tiered, and which of those it is can only be settled by reading the page. A page
transcribing an 1833 newspaper is tier 2 whatever site hosts it, and this dataset already
grades one chicagology page that way. Regrading a confidence is also a mesh input, so the
decision arrives with a bake attached. Priced and queued in `docs/STATUS.md` § 43.

### They may, however, carry a position to `inferred` (revised 2026-08-10)

The first reading of the rule above was too strict, and the strictness made the dataset
*less* accurate rather than more. A researched retrospective — Conley/Stelzer 1933 is the
case in point — is real evidence about where a building or a bridge stood. Refusing to use
it left those things tagged `reconstructed`, which asserts *no evidence exists*. That is not
caution; it is a false statement in the modest direction, and this project already holds
that under-claiming is as wrong as over-claiming (see `generators/archetypes/frame_tavern.py`,
where the same mistake dithered a well-attested building into a ghost).

So, precisely:

- **`attested`** still requires a period source. A tier-5 map never reaches it, alone or
  in company.
- **`inferred` is available** to a tier-5 source, and is the right tag when a researched
  reconstruction places something. The `note` must name the map, say that it is a
  reconstruction, and say what it shows.
- **Geometry is still not traced from them.** A pictorial elevation is not a survey: it
  gives you *that a thing was here*, not its outline, its footprint or a shoreline. Outlines
  come from tier-1 sheets or stay reconstructed.

Judge a tier-5 source by how it was made, not only by its date. Conley worked about two
years in libraries and archives, and Caroline McIlvaine had thirty years earlier collected
testimony directly from the last surviving pioneers. That is a real evidentiary chain with
one weak link, not a decoration. It still gets things wrong — it labels the du Sable/Kinzie
house "built 1832" against every documentary source (`data/exclusions.json`) — which is
exactly why it informs `inferred` and never `attested`.

`asset_use` on the source record is the operative switch, and the vocabulary already had the
right rung: **`orientation` — "toponyms and rough placement only"**. That, not `cross_check`,
is what a map like this should carry.

## Rights are part of provenance

Each source carries `rights_status`:

- `public_domain` / `no_known_restrictions` — usable, cite the holding institution.
- `check_required` — **may be cited in text, but no asset may be derived from it** until the
  check is done and recorded.
- `cleared` — a `check_required` source that has been resolved; record what was checked and when.

**This sentence said "the validator enforces this" until 2026-08-16 and it was not true in the
way it reads** (ROADMAP K41). Two things enforce it now, and they answer different questions:

- `tools/validate.py` refuses a `check_required` or `restricted` source whose own `asset_use`
  says `geometry`. That is a comparison between two fields of the same source record, so it
  fires when an author has already written the violation down. **No source in this dataset has
  ever carried that combination** — the 38 unresolved sources all declare `cross_check` or
  `text_only`, and the three that declare `geometry` are a survey and two maps, all clear.
- `tools/measure_rights_derivation.py` asks what the town is built from, using the read-sets
  the generators already declare (`CONSUMED` in each `*_params.py` and in `terrain_inputs.py`).
  **49 geometry-bearing attributes on 21 records cite an unresolved source, 35 of them with no
  other support and 16 of those graded `attested`.** The population is banked in
  `tools/rights_derivation_baseline.json`; it may shrink and may not grow.

Whether those 49 are a rights problem at all depends on a reading this document and
`docs/PLAN.md` do not share — facts read out of a work, or expression derived from it — and
that is the owner's to settle, not a gate's. See ROADMAP K41 for the three routes.

Web sources require an `archived_url`. Several of the best online references for this project
return 503s and 403s intermittently; a citation that cannot be re-read is not a citation.

## Date enforcement

Chicago between 1833 and 1837 changed faster than almost any settlement in American history.
A building correct for 1837 is wrong for 1835.

Every structure phase carries `documented_range`. For a given scene, a structure appears iff
**exactly one** phase's range covers the scene date. Overlapping phases are a hard error. No
covering phase means the structure is excluded from that scene, and the exclusion is reported.

**Do not widen a range to make the build pass.** Narrow it to what is attested and mark the
phase `reconstructed` if that is what it is. A `documented_range` spanning more than about a
dozen years in this period earns a warning on principle.

`data/exclusions.json` records structures that were researched and deliberately left out, with
the date evidence and citation. It exists so that the next agent — or the next you — does not
helpfully re-add the Saloon Building.

## The confidence view is a deliverable

Every renderer implements a toggle that recolors the scene by evidence quality:

- `attested` — renders normally
- `inferred` — renders tinted
- `reconstructed` — renders as translucent massing

Implementation is centralized (the generator paints a per-vertex confidence channel; the
renderer reads it through one shared material patch) so it cannot be forgotten per-building.
The visual claim and the citable claim come from the same record and cannot drift apart.

For a museum, a classroom, or a civic audience this is the single most valuable thing the
project offers.

## Confidence grades the evidence, not the view

A confidence chip answers *how sure are we of this value*. It cannot answer *are you looking at
it*, and the two come apart in the direction that does the most damage: an `attested` attribute
the generator never reads renders nothing and still shows the strongest claim the project makes.
Wolf Point Tavern's painted wolf sign was exactly that for as long as nobody checked.

So the two questions are recorded separately. Each archetype's `*_params.py` declares `CONSUMED`
— the form attributes its `from_phase` actually reads — and any attribute outside that set
carries a `geometry:` field saying what the mesh does instead:

- `absent` — the record attests it and nothing of it is built
- `simplified` — something stands in its place, but this value does not drive it
- `record_only` — never a build instruction: a rejected reading, a negative finding

`absent` and `simplified` are admissions, so `tools/validate.py` requires a matching `Covers:`
token in `docs/LIBERTIES.md` and the provenance popup marks the row. A missing declaration is a
gate failure, which means adding a generator parameter without adding it to `CONSUMED` fails
loudly rather than quietly excusing an omission.

The absence of the field asserts nothing on its own. An attribute inside `CONSUMED` is built
from its value by construction, which is the only reason it needs no declaration.

## When sources disagree

Record the disagreement in `docs/RESEARCH/<structure_id>.md`, state both readings and their
sources, pick the best-attested one, and **write down why**. Then reflect the uncertainty in
the data: a disputed attribute is `reconstructed` or `inferred`, never `attested`.

A dispute that cannot be resolved is not a failure. It is the honest state of the evidence, and
the confidence view is built to show it.

## A fact the dataset has no field for goes in a prose note, not a new shape

Sources hand this project facts it has no field to hold. The rule is that such a fact is written
into the **prose note of a field the record already has**, at that field's grade and under that
field's citation — not into a new field, and not into an existing structure with its checked
parts blanked out.

The idiom is older than the ruling. No person record has a birthplace field, so every birthplace
here rides in the `birth_year` note: `hh_harmon_elijah_d` reads "20 August 1782 at Bennington,
Vermont", `hh_porter_jeremiah` "5 November 1807 at Geneseo, New York". The fact is on the card,
it is graded, and it cites the page it came from — which is everything a field would have bought
except a query.

**T-0849 is the ruling that made this general** (2026-09-10). Hurlbut names Gurdon Hubbard's
parents, Elizur and Abigail (Sage) Hubbard, and they were living in Montreal, were never in this
scene, and have no household here. The proposal was an external `kin[]` row — `household: null`,
the source's own string in its place. It was refused, because every rule `kin[]` enforces is a
rule about the **far end**: the inverse must be legal, and the mirror row must exist. A row with
no far end is not a weaker kin row; it is a kin row with the entire checked part removed, and
what is left is a graded name — which is a note. It would also make every genealogical name in
the corpus eligible for the residents layer, and this dataset reconstructs a town on one day: a
person who was never in it is not a resident of it.

So kin stays inside the town, a relative outside it is evidence rather than structure, and
Hubbard's parents are named in his `origin` note at `inferred` on Hurlbut's rung-4 prose — the
same footing a kin row could have claimed and no more. `tools/validate.py` refuses a
null-household kin row **in the ruling's own words**, so a run that meets it is told where the
name belongs instead of being sent off to mint a Montreal household.

## A label may outlive a tenancy; a sign may not

Two of this dataset's fields carry a trade's name, and they are not the same kind of object.
A record's **`name`** — "The Chicago Democrat Office", "Philo Carpenter's Log Drug Store",
"The Old Bank Building" — is *this project's caption for a structure*. It is written so a
modern reader knows which building is meant; it is what the search box matches and what the
card heads itself with. It is not, and has never been, an assertion that the named business
was inside those walls on 1 July 1835. A **signboard** is exactly that assertion. It is
painted or hung in the scene, a walker reads it standing in front of the wall, and it says
*this is what is behind this door, today*.

So when the corpus follows a trade **out** of a building before the scene date, the two
fields part company, and the rule is:

* **the name stays.** A town goes on calling a corner by the shop that used to be on it,
  and a record that drops the trade it was known by becomes unfindable — that is a real
  loss, paid to tidy something that was never a claim. Say in the record's own notes that
  the tenancy ended, and say when. Do not rename the building.
* **the board comes down**, because a present-tense statement the register contradicts is
  simply wrong, whatever the wall used to say.
* **and nothing is lettered in its place unless the corpus names who traded there on the
  scene date.** This is where the mistake lives. A frontage that has just lost its board
  invites a replacement built out of whatever else is in the file — an advertisement from
  two years earlier, a for-sale notice, an occupant the record lists without a date. None
  of those attest who kept the counter on the day. An empty wall is a reading; a plausible
  wall is an invention. Leave it blank and write the refusal down.
* **fields the scene is furnished FROM are boards, not names.** `function` is the clearest
  case: the sign rule, the yard goods, the street edge and the register all read it in the
  present tense, so a `function` naming a departed tenancy is the same defect as the board
  and narrows the same way. Narrowing it is not an upgrade and must not move a confidence.

**T-1064 is the worked example** (2026-09-12). `chicago_democrat_office` is documented at
the corner of South Water and Clark by the Chicago Democrat's own imprint of 26 November
1833, and T-0403 then read the paper's later colophons and found the press printing from
over Jones & King's hardware store by 1835-05-20. The building kept its name and its `aka`;
its `function` narrowed from `printing_office_and_store` to `store`, the half the corpus
does not follow out of the door; and the board reading CHICAGO DEMOCRAT / Printing Office
came off the facade with nothing painted in its place, because the one name available for
the successor — W. Kimball's — comes from a notice *offering* the store for sale in 1834.
The refusal is machine-enforced: `tools/generate_business_signboards.py` clause 8
(`VACATED_NAMES`) carries the reason per frontage into the record's `refused` block, where
the next such building will read it.
