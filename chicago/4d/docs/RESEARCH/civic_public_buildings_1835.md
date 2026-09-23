# The public buildings of Chicago on 1 July 1835

ROADMAP **T-I3**, the parcel L93 opened when a block schedule dealt an anonymous civic
roof and the generator refused to mass it. The question the crosswalk asks is *"which
civic and public-service buildings Chicago actually had in July 1835, where they stood,
and what they were built of"*, and the reason it has to be asked before a slot is spent
is L93's: a dwelling nobody named is a count-unit toward a documented aggregate, and a
**public** building nobody named is the assertion that an institution stood on this
ground and left no record at all.

**The answer is three roofs, and all three are already committed named records.**

Everything below is from `andreas_1884_v1` unless another source is named. Page
references are archive.org **scan** pages of `historyofchicago01andr`, the citation form
this project already uses for Andreas; the scan runs at roughly twice the printed page.
No new source record was needed for this parcel — the whole enumeration is in a book
this project has cited since the scaffold.

---

## 1. What stood, with a roof, on the scene date

| record | what | where | fabric |
|---|---|---|---|
| `log_jail` | the first Cook County jail | north-west corner of the public square | log |
| `council_house` | the Indian agency council house | north side of the river | log |
| `chicago_lighthouse_1832` | the second lighthouse tower | at the river mouth | masonry tower, lantern above |

That is the whole list. The physical-roof reconciliation types exactly these three into
family **I3** (`data/reconstruction/1835_existing_roof_reconciliation.json`), and
`tools/measure_institutional_claims.py` prints the census on every run of the gate.

**The jail is the only county building on the square on 1 July 1835.** Andreas's summary
of the city as it stood in 1837 reads *"A court-house, a jail, and an engine-house
adorned the present square"* (scan p. 369). Two of those three are later than this scene
and are dated out below. Reading that sentence as a description of the square is the
single easiest way to put two buildings on this block that were not there, and it is
worth knowing that the project's own data came within one record of doing it.

## 2. What stood on the square and carries no roof

`estray_pen` — Chicago's first public building, and roofless. Andreas: *"The result of
this generosity on the part of the State was seen in March, 1832, when, through the
architectural skill of Samuel Miller, contractor, there arose upon the southwest corner
of the square, the so-called 'estray-pen.' Although sometimes designated and dignified
as 'the first public building ever erected in Chicago,' the 'pen' was a small wooden
enclosure and quite roofless"* (scan p. 365).

**A correction falls out of that sentence.** The committed record dated the pen to March
**1833** and cited Andreas for the year, under a note reading *"MARCH 1833 IS ATTESTED AS
A MONTH AND CONTESTED AS A YEAR ... The dossier notes that some accounts give 1832
instead."* Andreas gives 1832 in both places he treats the pen and 1833 in neither: the
narrative above, and the chronological index, where *"First public building (the 'Estray
Pen') erected"* stands under the heading **1832**, between *"1832 — (January) — First
Methodist quarterly meeting"* and *"(April) — First street leading to the lake laid out"*
(scan p. 1315). The month was read off that index correctly and the year off the wrong
heading. Nothing in the scene moves — the pen stands on 1835-07-01 either way, and is
roofless either way — which is exactly why it is worth saying that the correction is to
a **citation**: a note that cites a source for a value the source does not carry is
wrong in the way this project cares most about, whether or not anything visible depends
on it. Fixed 2026-08-16 in `data/structures/estray_pen.json`.

## 3. The court-house, which this parcel dated out of the scene

The record modelled it as **complete on 1835-07-01**, under a note reading *"NO SOURCE
REACHED FIXES A MONTH"* and reasoning from a flat prior over a twelve-month window. The
window was never twelve months. Three passages, and not one of them is earlier than the
fall:

- **The narrative.** *"During the fall of the year (1835,) a one-story and basement brick
  court-house was erected on the northeast corner of the square, on Clark and Randolph
  streets. The county offices were in the lower story; the court-room, which was above,
  being one oblong apartment, capable of seating two hundred persons"* (scan p. 369).
- **The chronology**, under 1835, at the month of **November**: *"court-house erected one
  story and basement, corner Clark and Randolph Streets"* (scan p. 1317).
- **A biography, which corroborates the season through a person rather than a building.**
  R. J. Hamilton, elected Recorder at the August election, *"removed his office toward
  the end of October to the new building recently erected by the county on the public
  square"* (scan p. 305).

**And the dataset had already said so, in a different file, for four days.** The physical-roof
reconciliation gives this record `roof_count: 0`, `inventory_eligible: false`, with the reasoning
*"Production chronology places construction in fall 1835; no courthouse roof should stand on 1
July."* That entry was committed on **2026-08-12**, the day after the structure record was
committed on **2026-08-11** — so from 12 August one document in this dataset held that the
court-house was not built on the scene date while another stood it on the public square, and
nothing compared them. The walkthrough's own release notes carried the reconciliation's reading
out to visitors — *"a courthouse that was not built until the autumn"* — while the walkthrough
drew the building. This is the drift L12 was caught by, in its worst form: not a document
disagreeing with the data, but the data disagreeing with itself in two files that no gate reads
together. Worth noting which of the two was right: the one with **no citation at all**. The
reconciliation's "production chronology" cites nothing and states the fact; the record cites
Andreas and states the opposite, because what it cited was a caption.

**Why the record had not found this: it cited a picture.** Its note pointed at *"a section
headed 'THE FIRST COURT-HOUSE.' at scan p. 373"*. Scan p. 373 is a **plate** — the words
are an engraving's caption, printed under *"Copyright secured by A. T. Andreas, 1884."* —
and the narrative that carries the date is four scan pages earlier. A caption is a
finding aid, not a source, and this is the second time in this project that a citation
has resolved to a heading rather than to a sentence.

**Two of the record's other claims are settled on the way past, and one of them is a
refutation.**

- The position note said *"no source held by this project places this building on the
  square at all, let alone at a corner of it"*, and adopted the north-east corner anyway
  with a stated undercut: *"Andreas's well-known description of the court-house 'on the
  northeast corner of the public square' is the 1837 BUILDING, so the very siting adopted
  here is the one an 1837 description would contaminate an 1835 record with."* That
  undercut is **wrong**. The north-east siting is in the 1835 narrative and in the 1835
  chronology, both of which describe *one story and basement* — not the later building.
  The invented placement turns out to be where the source puts it.
- The construction was graded as invented plank, with the reasoning *"Brick and stone are
  excluded by date rather than by taste: the first brick building in Chicago is 1837."*
  Andreas says **brick**, in the same sentence that gives the corner. The 1837 fact is
  about the first brick *house* (`peck_brick_house`, already excluded); a brick
  court-house in the fall of 1835 precedes it and Andreas records both.

**Neither is applied to the record in this parcel, and the reason is a bake.** The record
now resolves into 1836 and not into 1835, so it draws nothing and its form is not on
screen; changing a graded form value stales the placeholder mesh, and geometry belongs to
the nightly bake. What the record carries today is the corrected date, and notes saying
what the corner and the fabric are now known to be. Applying them is small and is listed
in the ROADMAP box.

## 4. The public functions that had no building of their own

This is the half that matters most for an I3 slot, because the crosswalk's own list of
what the family spans is *"jail/blockhouse; engine/service; adapted offices"* — and in
July 1835 every **adapted office** in Chicago was a room in somebody's private building.

- **The United States Land Office** is the most conspicuous public function in the town
  that summer and never was a public building. The chronology puts its opening at *"May"*
  1835 — *"Opening of Government Land-Office at Chicago; great land craze"* (scan
  p. 1317) — and the Beaubien claim dates the working office to the week: Beaubien
  *"entered at the land office in Chicago, of which Edmund D. Taylor was Receiver, and
  James Whitlock Register, a pre-emption claim"*, and his certificate *"was dated May 28,
  and recorded June 26"*. It is open, staffed and transacting business four weeks before
  the scene date. What it is not is a roof: *"The location of the first United States Land
  Office in Chicago was on the east side of Lake Street, between Clark and Dearborn
  streets"*, and in the same paragraph, *"the office of the Registers and Receivers were
  usually at their private offices"* (scan p. 313).
- **The post office** is the same shape and this project already holds it: the mail was
  taken at a store, and the walkthrough's own `first_post_office` anchor stands at Hogan's
  store rather than at a post office.
- **The county's own offices** were private until late October 1835 — that is what the
  Hamilton passage in section 3 is evidence of, read the other way round. Before the
  county building existed, the Recorder, the Clerk of the Circuit Court, the Judge of
  Probate and the notary were one man working out of an office of his own.

A public function in a private building is not a public building, and the dataset already
has the machinery to say so: it is a function on a committed record, not a record of its
own. Three guards are added to `data/exclusions.json` so the next parcel does not have to
find this out again — `us_land_office_1835`, `custom_house_chicago` and
`chicago_town_hall`.

## 5. The buildings that are later, with their dates

- **The engine house.** *"Up to September, 1835, there was nothing like an organized Fire
  Department, or a fire engine in the town. Prior to that time buckets put out any fire
  that occurred, or it burned itself out"* (scan p. 299). The house came after the
  company: the site committee reported that the County Commissioners would give them
  *"leave to erect an engine house on the public square, on LaSalle Street ... without
  paying rent therefor"*, and *"On the 30th of December, 1835, Levi Blake contracted to
  build the engine house for $220"* — still not fairly completed when the chief engineer
  resigned in February 1836 (scan p. 463). Already excluded as
  `first_fire_engine_house`; that entry dated the **engine** and has been amended to date
  the **house**.
- **The custom house.** Chicago was not a port of entry until the act of 16 July 1846;
  before that the district *"was a tributary to the Detroit District, and the revenue was
  collected by Seth Johnson ... with the office at 38 Clark street"* (scan p. 325). A lake
  port with a lighthouse, two piers and a harbour under improvement invites the
  assumption, and there is nothing to it.
- **The market house** at Lake and State is 1837 and was already excluded.
- **A town hall** was never built in the years this project models. The evidence runs the
  other way rather than being merely absent: the town had no ground of its own — its fire
  company had to ask the **county** for leave to build on the county's square — and it
  polled its own elections in taverns, the last town election at the Tremont House in June
  1836 and the first city election of May 1837 at the Eagle Hotel, Lincoln's Coffee House,
  a private house, Cox's Chicago Hotel, the Canal Office and the Franklin House (scan
  pp. 369, 373).

## 6. What follows for the programme, and what does not

**No anonymous I3 may ever stand, and that is now asserted rather than argued.**
`tools/generate_block_infill.py` has refused the three institutional families by name
since L93, but that refusal only ever covered the block generator — the North, West and
phase-one parcels ran before it existed, and nothing had ever asked the committed records
the question. `tools/measure_institutional_claims.py` asks it of every record in
`data/structures/`, runs in `tools/check.sh`, and is **absolute** for I1 and I3: an
anonymous roof of either family is a regression, and zero is enforceable because the
buildings are enumerable. I2 is a ratchet at one, naming `recon_1835_north_i2_015` — the
liberty L93 records rather than deletes. All three halves were broken deliberately before
the gate was trusted.

**The six-roof I3 target is wrong, and correcting it is NOT this parcel.** Three of the
six slots are a count of nothing. But the inventory's arithmetic is closed — every family
target sums into a district-group row, every row into a district target, and every
district into `roof_total: 665`, and `tools/reconcile_665.py` asserts all three sums — so
three slots cannot simply be removed. There are exactly two ways out and they are
different claims about the town:

1. **The town had three fewer roofs than 665.** `roof_total` becomes 662, inside the
   spec's own `defensible_range` of [565, 765]. This says the authored total was over by
   the three phantom civic roofs.
2. **The three roofs existed and were not civic.** They return to the pool the 665
   apportions and are re-typed by weight into the ordinary families. This says the total
   is right and the family split was wrong.

The research settles which buildings were public. It does not settle how many roofs the
town had, and choosing between the two on a parcel about public buildings would be
inventing the very kind of aggregate this parcel just removed. It is written up as
**T-I3(b)** for the owner. Until then the target stays at six and the programme keeps
scheduling I3 slots that every generator refuses — which is visible, gated and honest,
and is a better failure than a number quietly changed.

## 6a. Route 1 was taken — the target is three, and the town's total is 662

**Settled 2026-08-27, ticket T-0032.** The owner ruled on 17 August: *"close it at 665 or
662 — either is close."* The pick was delegated and **662** is the one taken, for the
reason section 6 gives against route 2: T-I3(a) established the three slots were a count of
nothing rather than miscategorised real roofs, so re-typing them into ordinary families
would have invented three buildings on the strength of an arithmetic artifact. 662 sits
inside the spec's own `defensible_range`.

**Every candidate a slot could have been spent on is settled, and the ledger is re-derived
on every run of the gate rather than remembered from this page.**
`tools/measure_institutional_claims.py` now carries the roster, and prints it:

| candidate | on 1835-07-01 | how the dataset settles it |
|---|---|---|
| `log_jail` | **stood** | reconciliation credits one I3 roof |
| `council_house` | **stood** | reconciliation credits one I3 roof |
| `chicago_lighthouse_1832` | **stood** | reconciliation credits one I3 roof |
| `cook_county_courthouse_1835` | later — fall 1835 | committed record; reconciliation credits no roof |
| `first_fire_engine_house` | later — contracted 30 Dec 1835 | exclusion, `earliest_scene: 1836` |
| `market_house_lake_state` | later — 1837 | exclusion, `earliest_scene: 1837` |
| `custom_house_chicago` | later — 1846 | exclusion, `earliest_scene: 1847` |
| `chicago_town_hall` | never built | exclusion with NO date: a kind guard |
| `us_land_office_1835` | a function, not a building | exclusion with NO date: a kind guard |
| `estray_pen` | stood, and roofless | committed record; reconciliation credits no roof |

Three stood. The target is three, and the tool fails the gate if it is anything else —
above the ledger is a slot that counts nothing, below it is a documented roof with nothing
to count against.

**What else moved, because a closed arithmetic has no free variables.**

- `roof_total` **665 → 662**, and `principal_functional` **511 → 508**. All three phantom
  roofs were principal; `ancillary` stays at 154, so the programme's own ancillary ratio
  becomes 154:508. The block ceiling is unchanged — an eight-lot block rounds to seven yard
  buildings at either ratio — which was checked rather than assumed, because a ceiling that
  HAD moved would have re-dealt blocks this correction never touched.
- **The institutional district row was wrong in a second way, and it is corrected from the
  same enumeration.** The inventory apportioned twelve institutional roofs as south 10 /
  west 1 / north 1, while the named records stand **south 5 / west 1 / north 3**. So the
  schedule kept finding institutional headroom in the South Division that no evidence
  supports, and none in the North where three of these buildings actually are. The row is
  now the census. That is what carries the **south district target 370 → 365** and the
  **north 150 → 152**; no other row in the matrix changed, and the district columns still
  sum to their own targets.
- **Every I3 slot has left the schedule.** `blk_lake_franklin` and
  `blk_south_water_market` each held one, and the South balance held three; the block deals
  now name buildable families instead, so a block that was going to be short a roof for
  arithmetic reasons is not. The remainder falls **327 → 324** and the coverage-gated
  balance **299 → 296**.
- **The gate screen shows it.** `data/town_census.json` is derived, and the first panel a
  visitor meets now reads *338 buildings standing, of the 662 the town held*.

**What did NOT move.** No building was added, removed or re-typed; no record's confidence,
date, position or fabric changed; the standing count is 338 exactly as before. The
correction is to a target, and the only thing a target can be wrong about is what is still
owed.

## 7. What is still owed

- The court-house's **corner** and **fabric**, now attested, applied to the record. Needs
  a bake, because a changed form value stales the mesh.
- Nothing else. The enumeration is closed on the sources this project holds; a new source
  could add a building, and if one does it arrives as a named record and not as a slot —
  and it will move the target, the district row and the town total with it, because the
  gate now refuses a row that does not equal the census. That is the intended cost: an
  institutional roof cannot be added quietly.
