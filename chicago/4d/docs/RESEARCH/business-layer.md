# The business layer

*T-1310, of T-1180. The place a business is written down.*

Until this layer there was nowhere to write a business. There were three derived files —
the newspaper claims, `gazetteer.json`, `register_1835.json` — and a business existed in the
scene only as a structure whose `function` and `occupants` block happened to name one. A
register row has an action and a trade string; it has no staff, no tier on anything, no
`sources[]`, and no dates beyond the first and last issue a notice ran. A resident's
`works_at` is a bare structure id, which can say *this person worked in that building* and
can never say *for which house of trade*.

The owner's ask — a complete list of the attested and inferred businesses, then reconstructed
ones beside them, with the staff of each carried as part of their proprietors' resident
profiles — had no shape to land in. `data/businesses/` is that shape.

## What is in it

One record per business, one file, `data/businesses/<id>.json`, against
`data/businesses.schema.json`. Today there are **196**, one for every business in the
scene-date register; **179** of them stand in the town on 1 July 1835 and the rest carry the
register's exclusion and its reason.

| | count |
|---|---:|
| records | 196 |
| present at the scene date | 179 |
| named proprietors and partners | 196 |
| …linked to a card the resident layer already holds | 144 |
| …the distinct people those links reach | 110 |
| households whose `works_at` now resolves to a business | 21 of 50 |

By census class — the classes of `trade_class_rulings.json`, which is the one taxonomy, so a
business counts against the December 1835 State census without a second crosswalk:

| class | n | | class | n |
|---|---:|---|---|---:|
| store | 67 | | printing office | 3 |
| other | 79 | | physician | 3 |
| lawyer | 18 | | book store | 2 |
| tavern | 9 | | druggist | 2 |
| storage and forwarding | 8 | | brewery | 1 |
| school | 7 | | iron foundry | 1 |
| not stated | 5 | | silversmith and jeweller | 1 |
| steam saw-mill | 4 | | tin and copper manufactory | 4 |

## Derived, never authored

`tools/compile_businesses.py --build` writes the 196; `--check` re-derives them and refuses a
committed copy a rebuild would not produce; `--self-test` breaks each of its eleven assertions
and requires every one to fire. Both run in `tools/check.sh`. A hand edit to a compiled record
is a red gate, for the same reason it is on the gazetteer and the register: a hand-edited
record is a place to promote a business — or a proprietor, or a premises — into the town
without an argument.

A record a human means to author goes in `data/businesses/authored/`, which the compiler
reads, validates and carries into the index untouched. That directory is where T-1182's
inferred-by-audit firms are written, and where the reconstruction band's `rcb_…` records
already are: **2 today**, both druggists, written by
`tools/reconstruct_businesses_1835.py --build` against the reconstruction order book's own
quota and re-derived by its `--check`. A reconstructed record carries
`provenance: "reconstructed"` and a `reconstruction` block — the order-book bucket that
bought it, the group and ticket that wrote it, the seed that redraws every drawn value on
it, and what retires it — and the compiler refuses one without it, refuses a compiled
record that claims one, and refuses any reconstructed record that cites a source. See
`docs/RESEARCH/business-naming-1835.md` for the style guide and `docs/LIBERTIES.md § L254`
for the invention.

## The id, and why it is not the one T-1180 named

T-1180 asks for `biz_<surname>_<trade>`. Derived over the 196 that scheme **collides 27
times**: five houses land on `biz_montgomery_other`, four on `biz_wentworth_tavern`, two on
`biz_calhoun_printing_office`. Every collision is the same question — *are these two printed
notices one house or two?* — and that is an identity ruling. It is T-1182's to make with the
sources in front of it, and a compiler that settled it by appending `_2` would be publishing
an adjudication nobody made.

So a compiled record takes the register's own id with `business_` replaced by `biz_`. It is
1:1 with the printed notice it comes from, collision-free by construction, reversible, and
`register_id` on the record says so out loud. `biz_<surname>_<trade>` and `rcb_…` stay in the
schema for records a human authors, where the identity question has an author to answer it.

## A name is attested; the link to a person is a second claim

The ladder is the resident layer's, unchanged — `attested`, `inferred`, `reconstructed`. A
printed name is attested: the paper prints it. Whether that printed name is *the same person*
as a card in `data/residents/` is a different claim, and it is the register's:

- where the register matched the name to a card, `person_id` carries that card's id and the
  basis names the action that made the match — **144 of 196**;
- where it did not, `person_id` is **null** and the basis says the town holds no card for
  them under an id this record can name — **52 of 196**.

Those denominators were 209 until T-1401. Thirteen of the printings were a SECOND STYLE of a
person the same record already named — "J. D. Caton" and "J. Dean Caton" are one partner of
Collins & Caton, and Giles Spring was printed three ways — so the layer was counting the
register's typography as the town's partners. `compile_businesses.fold_printed_styles` folds
them on `person_id`, never on the name, and the styles are kept on `also_printed_as[]`: the
fold removes a second COUNT of one man and no evidence at all. Twelve pairs, thirteen
printings, and the 52 names the resident layer holds no card for are untouched — a printing
that resolves to nobody cannot be folded onto anybody.

A null there is a finding, not a gap to be filled by guessing. It is also the queue for
T-1189, which staffs every business with real persons.

## The community of a house, and where it is read from

`proprietor_community` stood at the literal string `unattested` on all 196 from the day the
layer was compiled. T-1378 ended that by reading it off the PEOPLE a record names — each
keeper's own card in `data/residents/community.json`, which is itself derived off household
origin blocks and reconstruction name pools — and never off a surname, which is exactly the
move the resident layer refuses. The sentence that used to stand here said the field was
still `unattested`; T-1401 found it eighteen days stale and T-1403 rewrites it with the
measurement beside it.

**The distribution, on all 201 records:**

| community | n | community | n |
|---|---:|---|---:|
| *unknown* | 85 | british | 9 |
| yankee | 48 | southern | 5 |
| new_york | 41 | free Black | 2 |
| other | 10 | Métis | 1 |

And the rule that produced each: `proprietors_agree` 116, `no_person_linked` 73,
`proprietors_disagree` 8, `no_community_on_the_people_named` 4. The 73 are the register
naming nobody the town holds a card for, or naming nobody at all — they are the queue for
T-1189, not a gap to be closed by reading letters in a name.

### Black-owned, and Native or Métis-run — the attested floor (T-1403)

The parent's clause 5 asks that every house whose proprietor the sources place in either
community carry the field at the tier the evidence supports, so the Businesses view lists
them on one filter and T-1177 reconstructs **above an attested floor**. This is what the
corpus gives, and the floor is low because the corpus is thin, not because the town was.

- **Métis — one house, and it is attested.** Andreas, of Alexander Robinson
  (Che-che-pin-qua): "During the latter part of his residence in Chicago, he lived at Wolf
  Point, where he had a store or trading-house." Behind it stand his tavern licence of 8
  June 1830 and the county clerk's 1831 permits to sell goods — to Robinson, John B.
  Beaubien and Madore B. Beaubien. His card already read `metis` at `attested` on his own
  origin sentence ("his father a Scots trader, his mother an Ottawa woman"), and the
  register never held the house because he never advertised: the register is a reading of
  newspaper notices, and the country trade at the forks did not take them.
  `data/businesses/authored/biz_robinson_trading_house_wolf_point.json` is that house —
  authored, not reconstructed, and nothing in it is invented. Its premises is `inferred` on
  `robinson_caldwell_cabins`, the only Wolf Point building this dataset attaches to him and
  the same structure the household's own `works_at` names; its dates are unbounded because
  "the latter part of his residence" is a position in a life and not a year; and it carries
  `review_required` for the reason its household and its structure do.
- **Native (all four terms) — none, and the silence is about the register.** No house in the
  layer is kept by anybody the resident layer reads in the Potawatomi, Ottawa, Ojibwe or
  unspecified-Native terms. The one name the clause points at is **the interpreter**: Billy
  Caldwell (Sauganash), `metis` at `attested`, interpreter to the United States Indian
  agency under Col. T. J. V. Owen. An agency post is an employment and not a house he kept,
  so it is not a `proprietor_community` on anything — it belongs to the civic band. T-1188
  split (T-1410, T-1411) and the agency fell to neither half, so it is **T-1412** now: the
  agency is where Caldwell, David McKee the blacksmith and Joseph Porthier the striker are
  seated, and its standing on 1 July 1835 has to be read before any of them is written.
- **Free Black — no attested house at all; the floor is zero.** `black_chicago_1835.md` is
  the whole of the reading, and its finding is that the corpus counts the free Black town of
  Chicago twice — Caton's fee in August 1833, the 1840 census — and **names it never**, not
  one advertisement, not one directory line, not one roll. So the two houses that carry
  `free_black` are both T-1377's reconstructed firms, `rcb_fb_barbers_shop` and
  `rcb_fb_washing_and_ironing`, standing above a floor of nothing. That is the honest state
  and it is not a defect to be corrected upward.

One line the count does not print: a `metis` reading of **1** is a statement about the
register, not about the forks. The French Canadian and Métis families of Wolf Point traded,
kept taverns and held permits; what this layer holds is the one of them a book names keeping
a house. T-1177 reconstructs above these floors, and the floors are what it must not sink
below.

## The civic establishments — a class the census never counts (T-1410)

Three of the best-documented workplaces in the town were not in this layer at all, because
the layer was compiled out of printed trade notices and none of them advertised. They are
authored records now, under `data/businesses/authored/`:

| record | officer, attested | where it stops |
|---|---|---|
| `biz_us_land_office_chicago` | James Whitlock, Register · Edmund D. Taylor, Receiver | `street_only` on Lake Street, east side, between Clark and Dearborn |
| `biz_chicago_post_office` | John S. C. Hogan, Postmaster | `street_only` on South Water Street, at the Franklin end |
| `biz_cook_county_offices` | Richard Jones Hamilton, County Clerk | `unplaceable` — not on the square, and in no building of the county's own |

**They take a new class, `civic`, and it is the one class in the enumeration the December
1835 State census does not enumerate.** That count runs through the trades — stores, book
stores, druggists, taverns, lawyers, physicians — and never reaches a post office. So a
civic establishment counts against no census line, the crosswalk does not compare it, and
the reconstruction order book orders none. It is deliberately not `other`, which means *the
register printed a trade this enumeration has no line for*: these three were never in the
register at all. The four officer roles (`postmaster`, `land_office_register`,
`land_office_receiver`, `county_clerk`) are words `data/residents/index.json`
`.vocabulary.occupations` already carries — one word for the office on the man and on the
seat.

**A civic establishment is not a civic building, and the dossier had already settled that.**
`docs/RESEARCH/civic_public_buildings_1835.md` enumerates the town's public roofs at three —
the log jail, the council house and the lighthouse — and files the land office, the custom
house and a town hall in `data/exclusions.json` as kind guards, because a public FUNCTION in
a private room is not a public building. These records honour that: not one of them names a
structure, and no roof is dealt to any of them.

**One correction the dossier's own summary invites, and which these records carry.** The
post office on 1 July 1835 is *not* at Hogan's store. The committed `hogan_store` record
already says so in its `function` note — the office was there from 31 March 1831 until about
July 1834, when Andreas removes it "to near the corner of Franklin and South Water" — and
the walkthrough's `first_post_office` anchor marks where the mail BEGAN, not where it was
taken at the scene date. The conflicting reading is preserved rather than resolved: eight
printings of Hogan's standing card, through the issue of 1 July 1835 itself, put his South
Water store "one door [… of] the Post Office", and one door is not four blocks (T-0859).
The street is what both readings agree on, so the street is as far as the location goes.

**What is deliberately absent: staff.** Each of the three certainly had clerks, and not one
is written here. Minting them is `T-1189`'s — *staff every business with real persons* — and
a clerk minted in this record would be a person the resident band never drew, ordered twice.

## The churches — four congregations, five counted, and no sexton (T-1421)

The `church` class existed in the enumeration and held **zero records**, for the same
reason `civic` did: this layer was compiled out of printed trade notices and no
congregation advertised. Four are authored records now, each seated on a roof the town
already carries:

| record | in the pulpit | seated on |
|---|---|---|
| `biz_first_presbyterian_church` | Rev. Jeremiah Porter, `minister`, **attested** | `first_presbyterian_church`, the congregation's own house since its dedication on 4 January 1834 |
| `biz_st_marys_church` | Rev. John Mary Irenaeus St Cyr, `priest`, **attested** | `st_marys_church`, in use since October 1833 |
| `biz_first_baptist_church` | Rev. Allen B. Freeman, `minister`, **inferred** | `temple_building`, the lower storey — the upper is Sproat's school |
| `biz_methodist_episcopal_congregation` | *nobody* | `walker_meeting_house`, the log house at the forks, `inferred` |

Two new role words, `minister` and `priest`, and they are not new words: the resident
layer's `.vocabulary.occupations` already holds both, as what Porter and St Cyr WERE. A
church establishment needs them as what each man DID at a meeting house — the same rule
`civic` followed for `postmaster` a ticket earlier.

**The office is attested; the morning is not, and the two are kept apart.** Porter's card
carries the pastorate on `andreas_1884_v1` and Andreas has him in that pulpit until he left
Chicago in September 1835 — but he was married at Rochester, New York on 15 June 1835,
sixteen days before the scene date, and went on to Massachusetts, so the minister of the
First Presbyterian may have been eight hundred miles from it that morning. The committed
roof says the same thing from the other side: `first_presbyterian_church`'s `occupants`
field refuses to name a person because "NO SOURCE REACHED NAMES THE MINISTER IN CHARGE ON
1835-07-01". Neither record overturns the other. **The establishment carries the office, the
roof carries the room, and neither is asked to carry the other** — which is why
`st_marys_church` can keep its `inferred` occupancy while this layer's priest row stands at
`attested`: the roof is grading a day and the establishment is grading an office.

**The one inference, and why it is not an attestation.** Freeman's arrival (16 August 1833)
and the church's organisation (19 October 1833, nineteen members) are both verbatim in
`baptisthistoryhomepage`. That he was still the minister twenty months later is not, and one
reading points the other way without dating itself: `lathrop_samuel_s`'s card records Samuel
S. Lathrop building the fence around Rev. A. B. Freeman's Chicago **grave**. A death that
might fall on either side of 1 July 1835 cannot be read as falling after it — or before it.
So the row is `inferred` with the reasoning printed, and `person_id` is null, because the
resident layer holds no card for him and a surname agreement is a refusal here as everywhere.

**NO SEXTON IS RECONSTRUCTED, AND THAT IS THE FINDING.** The obvious move — a keeper for each
of four houses of worship — would have invented four town offices. The only sexton any trade
table this project holds ever prints is **one**: `sexton, St. James' Church` in Fergus's 1839
directory, four years and some three thousand people after the scene, in a town that by then
had more congregations than this one. Four against one printed is not a reconstruction, so
the establishments carry no staff but their clergy, the schema is given no word for `sexton`
until a source names the man, and each record's `replaceable_by` says what would create the
office. Documented zeros stand.

**The census counts five and the town holds four, and the fifth is not invented.** The
crosswalk row stays `not_compared` — T-0988's ruling that a church is a structure and not a
trade is untouched — but it now names the four records instead of standing empty. The gap is
the one the whole crosswalk is read with: the State count was taken between 1 September and
December 1835, two to five months after the scene, in the fastest-growing months the town
had, and `1835_town_model.md` says so in its own caution — "A church with five congregations
in December had fewer in July and some of them had no building at all." A fifth congregation
on 1 July 1835 would need a source naming it. None reached does.

## The schools and the press — the staffing overlay, and the third printing office (T-1422)

T-1411 asked for the churches, the schools and the press as establishments with their people,
and it **split over a hole in this layer**. A church needed nothing new: the class held zero
records and every congregation above is authored whole. The schools and the printing offices
are the opposite case — the register COMPILES them, `--check` refuses a hand edit to a
compiled record, and `data/businesses/authored/` holds whole records rather than *additions
to* compiled ones. So a reading about who taught at the Chicago Academy, or about the boy the
Democrat advertised for, had **nowhere in this layer to be written down**.

`data/businesses/rulings/establishment_staffing.json` is that place. It is laid over the
compiled records by `compile_businesses.apply_staffing_overlay`, it supplies exactly two
fields and no others, and it is derived like everything else here — `--check` re-derives it
and an entry naming a record the register does not compile is refused.

- **`staff`** — people, with citations, at the tier the evidence supports. A compiled record
  otherwise always has none.
- **`staffing`** — what KIND of hand the 1835 business staffing model puts about this kind of
  house. **It names nobody**, `writes_no_person` is held true by the compiler, and a hand
  nobody has written carries `drawn: false` with the reason. It is not a roster and cannot
  become one by itself; T-1189 is the ticket that puts people in `staff`.

### The seven schools' teachers are the seven keepers the register already prints

The staffing model gives a school one role — an assistant, 0–1 with a **typical of nought**,
because "the town's schools of 1835 are one room and one teacher". So the answer to *who
taught here* is a pointer at a row each record already carries, and **not a new row beside
it**: `principal_role: "teacher"` and `principal_is` name the proprietor or partner, and the
assistant stands undrawn on all seven. Counting a man once is the whole of the rule.

| school | the teacher | pupils |
|---|---|---|
| `biz_the_chicago_academy` | G. T. Sproat, signed "Preceptor" | none printed — a four-department fee table instead |
| `biz_john_watkins` | John Watkins | **thirty subscribed for, twelve attending** — and the figure is *1832* |
| `biz_miss_bayne_s_boarding_and_day_school` | [uncertain: Miss Bayne], unlinked | none printed — terms by the quarter, $3 to $8 |
| `biz_j_a_marshall_s_dancing_school` | J. A. Marshall | none printed — addresses left at the Exchange Coffee House |
| `biz_samuel_lewis` | Samuel Lewis | none printed — he was waiting on subscribers in August |
| `biz_hiram_everts_high_school_for_young_gentlemen` | Hiram Everts | none printed — and **not standing on 1 July**, opened 10 August 1835 |
| `biz_charles_hunt_high_school_for_young_ladies` | Charles Hunt | none printed — **not standing on 1 July**, first term 17 August 1835 |

**One pupil figure exists in this whole project and it is not a figure for 1835.** Andreas
quotes Watkins's own later letter on his FIRST quarter: thirty scholars subscribed for but
only twelve attending, "only four of them were white: the others were quarter, half, and
three-quarters Indians". That quarter was taught in the autumn of 1832 in Colonel Hamilton's
horse stable, twelve feet square — three years before the scene date and two moves before the
schoolhouse the record is seated on. It is carried with its own date on it, because a dated
figure can be read with its date where a silence cannot be read at all, and nothing may read
it as the attendance of 1 July 1835.

**And two of the seven schools were not open on 1 July.** The register says so itself —
`present_at_scene_date: false`, `exclusion: opening_announced_after_scene_date` — and both
notices are conditional on "sufficient encouragement", which is what a schoolmaster wrote when
the subscription list was not yet full. The December census counted them because December is
after August. The trade-census crosswalk does **not** yet read the register's judgement here;
see T-1428.

### The Democrat's apprentice — the one advertised hand in the corpus

The Chicago Democrat of **20 May 1835** carries, in its own columns: *"Wanted immediately,
[a]n apprentice at this office to the printing [b]usiness. A good opportunity is offere[d] by
an immediate application."* That is the only hand any notice in this corpus places in either
printing office, six weeks before the scene date — and it is a **vacancy, not a man**. The
staff row stands at `inferred`, names nobody, and says in its basis that a reading where the
place went unfilled through July is open and the row must be able to take it. The journeyman
the model also allows stays undrawn: a shop advertising for the cheaper hand is not evidence
that it already had the dearer one.

The *Chicago American*'s office gets the same block and no rows at all. Its `proprietors` and
`partners` are both **empty** — the one notice it compiles is the shop advertising its plant,
signed by nobody — and that null is the finding.

### The third printing office: two notices, one house

The census prints **two printing offices** and the register raised **three**. The third was
never a third shop; it was the Democrat's own weekly imprint, read twice:

| record | compiled from | says |
|---|---|---|
| `biz_the_chicago_democrat` | the terms block, 26 November 1833 | "THE DEMOCRAT, Is published every Tuesday, in [t]he village [of] Chicago, … [in the building on the] corner of South Water and Clark stree[ts]" |
| `biz_chicago_democrat_printing_office` | the colophon, 7 January 1834 | "[The Chicago Democrat] is published every Tues[day, in the villa]ge [of] Chicago, Cook co. Ill. in the building on the corner of South Water and Clark streets" |

One sentence, thirteen months apart, one address. Both are class `printing_office`, both give
South Water Street, both name John Calhoun, and no third proprietor, second address or second
press appears anywhere in the corpus. The register split them only because the gazetteer read
the firm STYLE two ways.

`one_house_rulings` in `trade_class_rulings.json` is where that adjudication is now made, and
it is deliberately narrow: `register_cautions` beside it is where a suspected double is NAMED
without being ruled, and that is where a double belongs until somebody has read the pages and
written the argument out. Noble & Wesencraft sits in the cautions and is **not** folded.

**The fold moves the count and nothing else.** Both records stand, both keep their claims, and
`folded_business_ids` on the class row names the pair — exactly as
`compile_businesses.fold_printed_styles` removes the second count of one man without deleting
the second spelling of his name. `printing_office` now reads **2 against 2**, and the office is
the survivor because the office is what the census counted: the Chicago Democrat is the
newspaper printed in one of them.

## The limits are data now

61 of the register's businesses are `street_only` and 62 are `unplaceable`: the paper gives a
street and no house, or no anchor at all. Those are not missing locations. They are locations
whose resolution the evidence stops short of — and they were carried in prose, inside an
`action_note`, where nothing could count them.

Each is now a `locations[]` entry whose `kind` names the limit and whose `limit_reason` quotes
the register's reason:

| kind | n | what it means |
|---|---:|---|
| `premises` | 30 | matched onto a roof the town holds. `attested` where the register matched the structure's occupants line, `inferred` where it matched only its name |
| `anchored` | 26 | the paper anchors the house against a landmark the town holds, and the town holds no roof of the house's own (the register's `new_building`) |
| `street_only` | 61 | a platted street and nothing narrower |
| `unplaceable` | 83 | no anchor the town can resolve — 79 at the scene date, plus the 4 earlier sitings of the houses that moved |

So *how many of the town's businesses can we actually place?* is a query now, not a
re-reading. The four houses that moved keep their earlier siting as a second, dated,
non-primary location rather than losing it to the current one.

### The anchor is an id (T-1401)

`anchored` is the one kind that names something and could not reach it. The landmark lived
only inside `limit_reason`'s sentence — *"The register places this house against
`tremont_house_1`…"* — so the Tremont House's own card could not say which houses stood
against it, and the Businesses view's `anchored` branch rendered a landmark title no record
supplied. Parsing that sentence for an id would have been a reading made by a regular
expression, and the crosswalk rightly refused it.

The register had the id all along, in its own `action_target` field. `compile_businesses.anchor_of`
resolves it there, and every anchored location carries an `anchor` block — `kind`, `id`,
`title`, and the two street ids of a corner. All 26 resolve:

| anchor kind | n | example |
|---|---:|---|
| `structure` | 15 | Andrews & Eells, against `tremont_house_1` |
| `business` | 7 | Collins & Caton, against `business_brewster_hogan_co` |
| `corner` | 4 | Russell E. Heacock, at Franklin and Lake |

A landmark the town does not hold is a REFUSAL in the compiler, not a null carried forward,
and the same is true of a `business_` id the register does not carry.

**The anchor is not a premises, and nothing may read it as one.** `structure_id` stays null
on all 26: the anchor says what the house stood next to, which is exactly as far as the
register went. The gate says so both ways — an anchored location with no resolved anchor is
refused, and one carrying a `structure_id` is refused as well.

## What this layer does NOT do

- **It reconstructs nothing.** Every one of the 196 records is the register's own reading,
  restated with its tier made explicit and its limits made queryable. The reconstruction
  bands are T-1182 and after.
- **`staff` is empty on all 196.** The newspapers name owners and almost never a clerk. That
  is a true reading of the register, not an omission: T-1183 rules the staffing model and
  T-1189 fills it.
- **It does not change a resident record.** `works_at` on a household still names a
  structure. The crosswalk in `index.json` says which businesses stood in that structure —
  two entries where two houses share a roof, because the evidence does not choose between
  them and the compiler must not either.
- **It is not on screen yet.** T-1181 is the Businesses view and T-1180's building card. A
  card that reads a layer no gate had ever re-derived would show a reader a number nobody had
  checked; the layer and its gate come first.

## Where the pointers go, and who refuses them

| pointer | refused by |
|---|---|
| register row → `business_record_id` | `compile_register.py --check`: a row whose record the layer lacks |
| record → `register_id` | `compile_businesses.py --check`: a record a rebuild does not produce |
| record location → `structure_id` | `tools/validate.py`: a structure id `data/structures/` does not hold |
| index → its own record files | `tools/validate.py` |
| `works_at` crosswalk → a business | `tools/validate.py`: a dangling business id |

## The mechanics' shops of 1835 — three counts, three units, one that binds

**T-1185.** The ticket asks for the mechanic trades set against the *Chicago American*'s
twenty-five mechanics' shops and against the workshop roofs of the building programme, with
the bound that wins each row named. Here they are, and the first thing the table shows is
that the three numbers **do not count the same thing**.

### 1 · What the December 1835 State census enumerates

The census counts establishments by class, and of the eighteen classes it names only four are
mechanics' shops in the ordinary sense. Those four are the whole of T-1185's quota:

| census class | census counts | the register holds | ordered | what was done |
|---|---:|---:|---:|---|
| two breweries | 2 | 1 | 1 | *M. Quinn, brewery*, North Water bank |
| two silversmiths and jewellers | 2 | 1 | 1 | *L. Chevalier, watches, jewelry, engravings and fancy goods*, Canal Street |
| one iron foundry | 1 | 1 | 0 | nothing — Dart & Co.'s castings stands at the target |
| two tin and copper manufactories | 2 | 4 | 0 | nothing — the register is **two over** the census |

The tin and copper row is the one to read twice. The register prints four houses in that trade
— J. K. Botsford twice, W. Keeney, and a fourth whose proprietor was never recovered — against
a census that counts two. **The reading wins over the count**, and nothing is retired to make
the two agree: a printed advertisement is a house somebody saw, and a census class is a tally
taken five months later by an enumerator who may have merged Botsford's two signs into one
establishment or counted the shop and not the factory. The over-count is recorded here and in
**L257**, not corrected.

### 2 · What the *Chicago American* counts, and the one row where it bites

> "There are now upward of fifty business houses, four large forwarding-houses, eight taverns,
> two printing offices, two book-stores, one steam saw-mill, **one brewery**, one furnace (just
> going up), and twenty-five mechanics' shops of all kinds."
> — *Chicago American*, 15 August 1835, quoted by Andreas; see
> `data/sidecars/1835/tremont_house_1.json` and **T-0406**.

Two things in that sentence matter to this band. **The twenty-five** is an aggregate with no
trades named, so it can bound a total and can never bound a row. **The one brewery** is a row,
and it disagrees with the census: the American counts one brewery six weeks *after* the scene
date where December counts two. That is the tighter bound and the nearer one, and this band
does **not** apply it — re-cutting an order-book bucket on a run's own reading of a newspaper
is a ruling made in the wrong place, and the Sept–Dec 1835 crosswalk (**T-1404**) is the right
one; the bucket reads `compared_by_the_crosswalk: true` with `crosswalk_note: null`. So
*M. Quinn, brewery* stands on the book's quota **with the American printed in its own
`reconstruction.basis.note`**, and a crosswalk that rules the American in re-cuts the bucket
and `--build` withdraws the record. See **L258** — the liberty that authorises this brewery and
the jeweller's shop beside it, and which carries the American on its own face. (It read L257
until T-1442 checked the citation: L257 is the four boarding houses, and the liberties were
renumbered after this paragraph was written.)

The same sentence corroborates the rest of the band where it can be checked: "one steam
saw-mill" against the register's two and the book's one, "two book-stores" and "two printing
offices" exactly, "one furnace (just going up)" against the census's one iron foundry.

### 3 · What the roof programme counts

The building programme carries **30 workshop roofs** in five families — W1 six forges, W2 eight
joiners, W3 six cooper and wheelwright shops, W4 six artisan shop-houses, W5 four riverside
heavy — of which four stand today (one each of W1–W4) and 26 remain. See
`docs/RESEARCH/1835_family_archetype_crosswalk.md`.

### 4 · What the resident layer already holds

The mechanic trades of the ticket's title are **occupations** in this data, not census classes,
and the resident band's `trade_households` stage has already drawn heads at them — **73** of
them:

| trade | heads | trade | heads | trade | heads |
|---|---:|---|---:|---|---:|
| blacksmith | 8 | tailor | 7 | brickmaker | 1 |
| carpenter | 21 | shoemaker | 4 | sawyer | 1 |
| builder | 9 | harness maker | 1 | soap and candle maker | 1 |
| cooper | 2 | tinsmith | 1 | hatter | 1 |
| carriage maker | 2 | mason | 2 | watchmaker | 1 |
| painter | 2 | plasterer | 1 | brewer | 1 |
| baker | 2 | butcher | 3 | miller | 1 |
| confectioner | 1 | | | | |

Seven trades the ticket names have **no head at all** because the resident vocabulary carries
no such word: tanner, saddler, wheelwright, wagon maker, joiner, gunsmith, cabinetmaker. Three
of them nonetheless have a standing roof (`inf_wheelwright_shop_west`, `inf_gunsmith_shop`,
`inf_harness_shop`), which is a gap for **T-1196** and **T-1199** to close, not for this band.

### 5 · So which bound wins

| the question | the bound that wins | why |
|---|---|---|
| how many reconstructed business **records** a mechanic class gets | the order book's per-class row | it is the only one of the three that is per-class, and it is derived from a count of establishments |
| how many mechanics' **shops** the town has in total | the American's twenty-five | it is a reading, it is six weeks from the scene, and it counts shops |
| how many workshop **roofs** get built | the programme's thirty, until **T-1196** re-cuts it | a roof is not a shop: W4 is a shop-house the American would more likely count among its "fifty business houses", and a forge and its shed are two roofs and one shop |
| how many mechanic **people** the town has | the occupation model's 73 heads | a person is not a premises — most of the 73 are journeymen in somebody else's shop, or carpenters and masons who work where the wall is |

The three numbers are **not** in conflict once the units are kept apart: 73 mechanics, working
out of on the order of 25 shops, standing under something like 30 roofs, of which the December
census enumerated 7 as establishments of a named class. Where two bounds genuinely collide on
one row — the brewery — the collision is written onto the record and handed to the ticket that
owns it.

### 6 · The standing `inf_*` workshops, and why none of them is adopted here

The ticket asks that every inferred workshop structure be adopted as one of this group's
premises or listed for retirement. Thirteen stand, and **none is of a class this group writes**:

`inf_blacksmith_shop_west` (W1) · `inf_cooperage_south` (W3) · `inf_cooperage_south_branch`
(W3) · `inf_wheelwright_shop_west` (W3) · `inf_gunsmith_shop` (W4) · `inf_harness_shop` (W4) ·
`inf_shoemaker_shop` (W4) · `inf_tailor_shop` (W4) · `inf_barber_shop` (W4) ·
`inf_butcher_market` (C1) · `inf_artisan_dwelling_west_a` (D3, blacksmith) ·
`inf_artisan_dwelling_west_b` (D3, wheelwright) · `inf_teamster_stable_west` (A2)

There is no brewery, no foundry, no tin shop and no jeweller's among them, so there is nothing
for *M. Quinn* or *L. Chevalier* to move into and nothing that this group's existence makes
redundant. The list is not idle: every one of these thirteen is a roof whose trade the census
does **not** enumerate as an establishment, which is exactly the population **T-1197** re-audits
against the re-derived programme and **T-1199** seats. It is recorded here so that re-audit
starts from a written list rather than a grep.

## Links

`data/businesses.schema.json` · `tools/compile_businesses.py` ·
`data/research/newspapers/README.md` · `data/research/newspapers/trade_class_rulings.json` ·
`docs/PROVENANCE.md` § the business record · T-1180 · T-1310 · T-1311
