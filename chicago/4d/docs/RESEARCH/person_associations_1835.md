# The other places a person was, 1 July 1835

**T-1405.** Piece 5 of T-1182, and clause 7 of T-1147 finally spent on the layer rather
than demonstrated on four records. Generator: `tools/person_associations.py`. Derived
report: `data/research/residents/person_associations.json`. Gated in `tools/check.sh`.

## The numbers, before and after

`tools/associations.py` counts the migration, and its file is the before-and-after:

| | records | rows | undated | tiers |
|---|---|---|---|---|
| before (T-1238) | 4 | 7 | 2 | 5 attested, 2 inferred |
| after (T-1405) | 76 | 81 | 2 | 23 attested, 58 inferred |

By kind, after: 51 `land_purchased`, 19 `church`, 5 `civic_seat`, 2 `school`, and the
four T-1238 rows — `business_premises`, `home`, `lodging`, `workplace` — untouched. By
rung: 51 `tract`, 25 `structure`, 5 `face`.

**74 rows were written and 159 relationships were refused.** The refusals are the more
interesting half and they are the reason this file exists.

## The refusals, by why

| n | what | why |
|---|---|---|
| 83 | land | the purchaser's register rows are not sorted onto any tract — the tract sort's own `refusals` block (town plat lots, ground outside the modelled extent, descriptions not read, rows with neither a ring nor a citation) |
| 20 | civic | the office is real and dated out of the scene — 1837, 1839, 1840, 1843, 1844, 1864 |
| 12 | civic | **the county had no building.** `civic_public_buildings_1835.md` § 4: the county's offices were private until late October 1835, and the Recorder, the Clerk of the Circuit Court, the Judge of Probate and the notary were one man working out of an office of his own |
| 16 | church | the parish act is dated after 1 July 1835 |
| 7 | school | the press printed the trade against the name and never the room |
| 5 | civic | **the town had no hall.** `chicago_town_hall` is one of the three guards § 4 added to `data/exclusions.json` |
| 5 | civic | the council house (below) |
| 5 | land | the crosswalk's identity match is unruled, and that file says of itself "PROPOSALS, not identities" |
| 2 | agency | E. K. Hubbard's fire-insurance agency (below) |
| 2 | civic | a militia commission is not a place |

## The three calls that had to be argued

**The post office is a corner, not a roof.** The obvious answer is `hogan_store`: it held
Chicago's first post office and the walkthrough's `first_post_office` anchor still stands
there. The store's own record refuses it — *"NOT THE POST OFFICE AT THE SCENE DATE, which
is the fact this record exists to get right"* — because Andreas has the office removed
about July 1834 to **near the corner of Franklin and South Water**, where it stayed
through Hogan's term. So Arnold, Galaher and Hogan are placed at
`south_water_and_franklin_corner`, rung `face`. The word *near* is the source's own, and
it is why the rung stops at a face. The date is kept at the year because *about* is the
source's word too.

**The Indian agent is not seated in the council house.** It is the only Indian-department
roof this dataset holds, which is exactly what makes the inference tempting.
`data/structures/council_house.json` refuses it in its own words — *"Both sources name the
building by its function and neither describes what happened inside it in a way this
record repeats"* — and the record is `review_required` under AGENTS.md's standing
constraint. Seating an agent's office inside it would put a man to work in a building
whose record declines to say what happened in it. T-1204 builds the Agency establishment;
a seat waits for it.

**E. K. Hubbard's agency gets no place at all.** `data/reconstruction/1835_agencies.json`
states the limit twice: *"A holding is a relation and nothing more. Nothing here says this
holder dealt in the principal's line, kept a roof for it, or was a partner in any house
that signed for it"*, and of the firm holding, *"a line on its card and nothing else — no
trade, no street, no roof."* Seating the agency at his own house, or at the roof of the
firm the agency passed out of, is precisely the claim those sentences refuse.
`associated_with[]` is defined over claims **with a place**; this claim has none, so it has
no row. It is not lost — the agency file carries it and the town card prints it.

## A fifth rung: `tract`

A man who bought the north-east quarter of section 16 bought ground the town plat does not
describe. It has no street, no face and no division, and calling it one of those would be a
fabricated address rather than a coarse one. `tract` is therefore a fifth rung on
`associated_with[].resolves_to` rather than a coarser fourth, and its vocabulary is the
committed survey layer's own — `data/reconstruction/1835_survey_tracts.json` — so ground
this project has not surveyed cannot be named on a card either.

Of the 51 land rows, 49 name `school_section`, 1 `kinzies_addition` and 1
`canal_section_9_remainder`. Every one is graded `inferred`, and the note says why the two
halves differ: the **purchase** is documented, because the federal register is a public
record and states it, while the tie between that purchaser and **this card** is an identity
ruling. The weaker half sets the tier. `to` is null on every row, because the register
records a sale and not a tenure.

## What this does not claim

- A church row is **not a membership row**. Being a witness, a party or a decedent at a
  Catholic act is what St. Cyr's register states, so `from` and `to` are the act's own day
  and nothing is carried forward to the scene date.
- A civic seat row states where the **office** sat. It inherits neither the dates nor the
  tier of the holder's `roles[]` block, and the holder's own tenure gates it: a register
  of the 1844 land office is not placed at the 1835 one.
- Nothing is written on a **household**. An office, a parish act and a quarter-section are
  held by a man and not by a house, which is also what keeps `singular_drift` out of the
  way — `lives_at`/`works_at` are household fields.
- The four T-1238 demonstration records keep every row they had. The generator appends by
  the `(kind, place, from)` key `associations.py` already dedupes on.

## What is still owed

- **Schools.** Seven teachers have no room. `watkins_school_house` and
  `north_side_school_1833` both carry *"the Watkins school-house"* among their aka, and
  until that overlap is ruled on, one man taught in two records and only one of them is
  attested for the year of the scene.
- **The county's private offices.** § 4 says they existed; no source reached names them.
  A reading that placed Hamilton's office would seat twelve rows at once.
- **The non-Catholic congregations.** St. Mary's is the only church in this dataset whose
  register has been read, so a Presbyterian or Baptist member has no row to gain.
- **83 land rows** wait on the tract sort reaching town plat lots and the ground beyond the
  modelled extent.
