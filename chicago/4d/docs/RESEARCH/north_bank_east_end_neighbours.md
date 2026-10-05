# The Lake House's neighbours — Bonnell's walk of 26 August 1835, ruled

**Ticket:** T-1717, piece 4 of 4 of T-1204 · **Records:** `kimberly_residence`,
`kelsey_boarding_house` (raised), `newberry_dole_warehouse` (a third reading recorded) ·
**Liberty:** L291 · **Source:** `andreas_1884_v1`, printed pages 136–137

T-1204 asks this district for "the Lake House's neighbours on the north bank east end". This
is the reading that answers it. **The whole of the evidence is one paragraph of one letter**,
and the useful thing to say about it up front is what it is good at and what it is silent on:
it names four buildings, three trades, five people and one paint colour, and it gives **not
one dimension, lot, street, corner or distance**.

## 1. The passage

J. D. Bonnell, from Lake City, Minnesota, to the *Chicago Times*, 15 March 1876, quoted by
Andreas, *History of Chicago* vol. 1, printed pages 136–137 (the folio for 136 sits just above
the paragraph and 137 just below the sentence that carries into Kelsey's house). Bonnell has
arrived on foot from Thorn Grove, slept at the Mansion House, and is walking the town the next
morning looking for a boarding place:

> "Passing east, toward the mouth of the river, was the Lake House in course of construction,
> east of which was the residence of Dr. Kimball, who was a partner of Mr. Pruyne in a drug
> store on South Water Street. Mr. Pruyne was State Senator. Opposite Dr. Kimball's was Hunter
> & Hinsdale's warehouse. Adjoining on the west was Newberry & Dole's warehouse, and on one
> part of the latter building was the hat store of McCormick & Moon, of Detroit, Mr. Moon being
> the partner of the Chicago store. In the back part of the store was Jesse Butler's tailor
> shop. In turning the corner of Dr. Kimball's residence, away to the north-east, among the
> sand-hills, close by the lake shore, stood a small yellow house, occupied by Parnick Kelsey
> as a boarding-house, ostensibly run by Eve, Parnick's wife, for Mr. Kelsey was a
> sub-contractor in removing stumps and grubs, preparatory to the grading of the street on the
> North Side … But as Mrs. Kelsey had all the boarders that she could accommodate, I was
> obliged to seek other quarters."

**The date, and it is the same conflict the project has already ruled on.** The letter opens
"My first entry into the city of Chicago was forty years ago, August 25, 1835"; forty years
before 1876 is 1836, and Andreas's own lead-in says Bonnell "came to Chicago in 1837". The 1837
reading is ruled out by the letter's own content — the Lake House was open by the autumn of
1836 and Bonnell walks past it *in course of construction* — and between 1835 and 1836 this
project prefers the letter's explicit date. That ruling is already committed, on
`data/structures/lake_house_construction.json`, where this same letter is the record's best
anchor; **this reading does not make a new one, it applies the existing one to the rest of the
sentence.** Under it the walk is the morning of 26 August 1835, **eight weeks after the scene
date**, and every carry-back below is graded as the inference it is.

## 2. Dr. Kimball is Dr Kimberly, and the identification is not close to doubtful

Bonnell gives the man three attributes: a doctor, Pruyne's partner, and a drug store on South
Water Street. This project already holds all three on one household —
`data/residents/households/hh_pruyne_kimberly.json`, "The Pruyne and Kimberly partnership
household", head `pruyne_peter`, trade druggist — whose own arrival note quotes Moses and
Kirkland naming **"Dr. E. S. Kimberly … of Vermont"**, which is Dr Edmund Stoughton Kimberly.
Pruyne's senatorship is the fourth check and it is right. Of the eight Kimball and Kimberly
identities in `identity_master.json` not one other is a physician or Pruyne's partner, and
`hh_kimball_walter` — the only Kimball household in the town — is a South Water Street
merchant, which is a different man at a different trade.

**And the fifth check is a building this project already stands.**
`data/structures/pruyne_kimball_drugstore.json` — "Pruyne & Kimball's Drug Store", aka "the drug
store on South Water Street", occupants "Pruyne and Kimball, druggists" — is committed, on the
south bank, and has been since before this reading. So the firm Bonnell names had its shop in the
model and its partner had no house in it. **Note also that this project spells the same man two
ways**, `Kimball` on the store and `Kimberly` on the household, which is the corpus reproducing
the sources' own disagreement rather than a second person; the new record is named for the
household's spelling and carries Bonnell's in its `aka`.

**So `kimberly_residence` is raised**, east of the Lake House, and it is the one thing in this
reading where an attested occupant meets a building the town did not have. Everything a visitor
will see of it is invented and L291 lists every piece.

## 3. Kelsey's small yellow house, and the one number the ground supplied

**`kelsey_boarding_house` is raised** on the sand hills, N 58° E of Dr. Kimberly's corner,
238.5 m out, 61.9 m west of the committed 1835 lake shore and 19.6 m east of Sand Street's
platted corridor. Every one of those numbers is this project's; Bonnell's three phrases are
"away to the north-east", "among the sand-hills" and "close by the lake shore", and none of
them is a distance.

**What is not invented is the sand hills.** The committed `e1834_harbor_cut` heightfield stands
at **+2.59 m** above the summer-1835 water surface under this footprint, against **+1.51 m**
under Dr. Kimberly's house on the Michigan Street frontage and **+1.51 m** at the Lake House
site: a rise of **1.08 m** between the strip Bonnell walked out from and the ground he calls
sand-hills. That heightfield was derived years before this sentence was read and knows nothing
about it. It does not fix the house's place; it does say the described ground is where the model
already has it, and it is the only corroboration in this reading that comes from a measurement
rather than from an argument.

**The yellow is attested and it is not built.** "A small yellow house" is the only statement any
source reached makes about the painted finish of any dwelling in this town. `frame_dwelling`
accepts `unpainted`, `white`, `whitewash` and `red`, and `generators/common/materials.py` holds
no yellow, so the house builds in unpainted clapboard. **White was refused as a substitute** —
it is a different claim, and a wrong one, about the one appearance fact this building has. The
record states no paint rather than the wrong paint and the finish is filed as its own ticket.

**Paid, 2026-10-04 (T-1724).** The finish is built: the record states `paint: yellow`, attested,
and `generators/common/materials.py` carries a `yellow_paint` coating for it alone. The shade is a
reconstruction and L291 says what bounds it.

**It is not the house the directories print, and the range says so.** Fergus 1843 has "Kelsey,
Patrick, boarding-house, Wolcott, bet Kinzie and Michigan" and Norris 1844 has "Kelsey,
Parnick, boarding house, Wolcott st. b Kinzie and Mich." — the same trade on a platted
north-side street about 230 m west of the sand hills. A keeper moving off the beach onto a
street in eight years is the ordinary reading; a range running to 1844 would assert the
sand-hill house and the Wolcott Street house are one building, which no source says, so the
range stops at the end of the attested year.

## 4. The two warehouses, and a finding against a committed position

**Hunter & Hinsdale's warehouse is REFUSED**, and the refusal is about compounding and not
about the evidence. Bonnell attests it and places it "opposite Dr. Kimball's" — but Dr.
Kimberly's own position is a 12.0 m offset from a building whose block this project cannot say
which side of Rush Street it is on. A position whose only content is "opposite" an invented
coordinate is an invention squared, and this project already stands one warehouse for a firm
with Hunter in its name (`kinzie_hunter_warehouse`, "Kinzie, Hunter & Co.", on the north bank
east of the forks, its own note admitting "THE BANK IS NOT ATTESTED"). Whether Bonnell's
Hunter & Hinsdale is that firm re-partnered is an identity question nobody here has evidence
for. Filed, not built.

**Newberry & Dole's warehouse is a finding against a position this project has already
committed, and it is the substantial one.** `newberry_dole_warehouse` stands on the SOUTH bank
near the forks. Its own note has carried two readings since August 2026: reading A, the south
bank, off c. 1835 views reported in `docs/research/03-structures-north.md` §3.10 as a `[DOC]`
tag naming **no source record**; and reading B, the north bank, off Andreas's "whose warehouse
was on the North Side, immediately east of where Rush-street bridge now stands" (scan p. 1139).
**The entire argument for adopting A is that B's citation "is not about 1835"** — the Andreas
sentence locates the warehouse a named 1839 grain shipment was made from.

Bonnell is about 1835. He puts Newberry & Dole's warehouse on the north bank at the east end,
adjoining Hunter & Hinsdale's, eight weeks after the scene date — which is where Andreas's 1839
sentence puts it too. So the north bank now has a **contemporaneous** witness and the south
bank has an untraceable tag, and the balance has moved against the committed position.

**Nothing is moved here, and the reason is scope.** Moving a committed warehouse across the
river moves its dock, the wharf and river-works layers that read it, its signboard, the yard
goods on its frontage and the block it is counted on, and it wants the c. 1835 views identified
rather than merely doubted. The third reading is written onto the record's own
`position.note`, which is where a reader will meet it, and the move is filed as its own ticket.
Two businesses Bonnell puts inside that building — the hat store of McCormick & Moon of
Detroit, and Jesse Butler's tailor shop in the back part of it — are unrecorded by this project
and are filed with the move.

**Ruled 2026-10-05 (T-1723): the south bank stands, on the paper, and nothing moves.** The
paragraph above weighed a contemporaneous witness against an untraceable tag, and the tag was
never the best evidence for the south bank. The project's own *Chicago Democrat* corpus
(`data/research/newspapers/extracted/`) had it all along, unlinked to the record: Newberry &
Dole's premises are the most-cited anchor in the paper's advertising columns, and the
advertisers who hang off them say where they are.

| issue · claim | the words | what it places |
| --- | --- | --- |
| 1834-05-28 · c004 | "on Dearborn street, one door from Newberry & Dole's store" | a Dearborn Street neighbour |
| 1834-11-12 · c002, 1834-12-03 · c002 | "next door below Messrs. Newberry and Dole's store house, on south water street" (copy of 3 Nov 1834) | the store house on South Water Street |
| 1835-05-20 · c020 | "on Dearborn street, a few rods north of Messrs. Newberry & Dole's Store" | a Dearborn Street neighbour, six weeks before the scene |
| 1835-06-17 · c008 | Cohen "at his old stand", copy of 11 June 1835 | the same stand, still held |
| 1835-07-01 · c001 | "[…]low Messrs. Newberry and Dole's" | Cohen's card still standing on the scene date |

South Water and Dearborn were both south-bank streets, and four advertisers who never mention
one another agree. So on 1 July 1835 the firm's store house is on the south bank by a source
dated on the scene, and Bonnell — eight weeks later — walked past a north-bank warehouse of the
same firm. Both can be true, and the firm's own card, "STORAGE, Forwarding & Commission", is the
kind of business that held more than one house. **What the paper does not give** is a date for
the north-bank house, so it is not added to the July scene; "opposite to Fort Dearborn", set
over the firm's card on 14 May 1834 (c007) and over Kinzie's the week before, names a direction
and not a bank, and is not used either way.

**One thing the reading turns up against the record, and it is filed, not done.** Both Dearborn
Street neighbours put the store house at the Dearborn end of South Water Street. The committed
building stands in the Franklin corner the owner chose on 2026-10-04 (T-2097, L378), four blocks
and about half a kilometre west, and `dole_warehouse_south` — Andreas's Lake-and-Dearborn
warehouse — stands one block south of the end the paper names. Whether the store house is that
building, a second one on South Water at Dearborn, or the Franklin house after all is a placement
ruling with a bake, a dock and four jaunts behind it, so it is its own ticket.

## 5. What is filed rather than done, and why each is somebody else's ruling

| finding | why it is not done here |
| --- | --- |
| `hh_pruyne_kimberly` is a PARTNERSHIP household banded to the south division on the store's evidence, and Bonnell puts one partner's residence on the north bank | seating it here would carry Peter Pruyne across the river on a sentence about Kimberly; splitting a partnership household is the resident layer's ruling under its own rules |
| `id_kelsey_patrick` (Fergus 1843) and `id_kelsey_parnick` (Norris 1844) are one man, and Bonnell's sentence spells him **both ways in one sentence** against the same trade | an identity merge is `identity_master`'s ruling under its M-rules, not a structure record's |
| Eve Kelsey is in no identity of this corpus; Bonnell is the only source that names her | naming her on the roof she kept is the whole of what a structure record can do for her |
| ~~`newberry_dole_warehouse` should probably be on the north bank east end~~ | **ruled by T-1723: it should not.** The *Chicago Democrat* places the firm's store house on South Water Street on the scene date (§4); the north-bank house is a later one. The paper points at the Dearborn end, which is filed |
| Hunter & Hinsdale's warehouse, McCormick & Moon's hat store, Jesse Butler's tailor shop | the first has no position but "opposite" an invented one; the other two are businesses inside a building whose bank is in dispute |
| a yellow finish for the one house a source paints | a materials-table change with its own gates, not a line in a structure file |

## 6. What would resolve what

- The **Kinzie's Addition conveyances**, or any sale of the sand ground east of Sand Street.
  These would give both houses a lot and would settle which side of Rush Street the Lake House
  block — and therefore Dr. Kimberly's house — is on.
- The **Chicago American** (first issue 8 June 1835) and the **Chicago Democrat** for 1835–36,
  which carried building notices and advertisements for exactly these firms.
- The **1839–40 North Side grading accounts**, which paid Kelsey as a sub-contractor and would
  date his work and possibly his house.
- **Whatever the c. 1835 views of Newberry & Dole's warehouse actually are.** Identifying them
  is the one thing that would settle §4 either way, and until it is done the south bank rests
  on a dossier tag rather than on a source.
  *(T-1723, 2026-10-05: the bank is settled without them — the paper's advertising columns
  place the store house, §4. They would still help with the block.)*
