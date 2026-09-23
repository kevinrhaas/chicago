# The Lake House, under construction — research dossier

**Record:** `data/structures/lake_house_construction.json` · **Scene status:** a building site on
1835-07-01, not a building · **Lake Street / north bank parcel**

Chicago's first luxury hotel — brick, three storeys and a basement, nearly $100,000 — opened in
the autumn of **1836**. `data/exclusions.json` carries `lake_house_finished` specifically to keep
the completed hotel out of the 1835 scene and says that on the scene date this is "a partial
three-story brick shell". This record builds that shell. **Everything about the finished building
is documented and nothing at all about its state on 1 July 1835 is**, which is the interesting
part and is why the storey count is the record's central conjecture.

---

## 1. What Andreas actually says

> Chicago did, however, have a really grand hotel as early as 1835; this was the Lake House,
> located on the corners of Kinzie, Rush and Michigan streets, fronting on the latter. This
> hotel, which was built of brick, was three stories and a basement in height, was elegantly
> furnished throughout, and cost its owners nearly $100,000. The men whose enterprise led them
> into building a house which for those days was far in advance of the needs of the town, were
> Gurdon S. Hubbard, General David S. Hunter, John H. Kinzie, Dr. W. B. Egan and Major James B.
> Campbell. **The hotel was completed and thrown open to the public in the autumn of 1836**,
> Jacob Russel, of Middleton, Conn., assuming control of its management.

And, in his account of the First Unitarian Society, whose first Chicago service was held in the
unfinished building in June 1836:

> The services were held in the Lake House, **which stood at the corner of Rush and Michigan
> streets.** … [Harriet Martineau:] "a respectable congregation was assembled in the large room
> of the Lake House, **a new hotel then building.** Our seats were a few chairs, and benches, and
> planks laid on trestles."

**Andreas gives no groundbreaking date and no dimension.**

## 2. The 1835 groundbreaking is NOT Andreas — record the discrepancy

`chicagology_prefire112` prints the Andreas paragraph above and then two **uncredited editorial
paragraphs** with no typographic break. The uncredited one reads:

> The Lake House hotel on the north side of the river, near the bank opposite the fort, at Rush,
> Kinzie, and Michigan streets, facing the latter; **ground was broken in 1835**, and opened in
> the fall of 1836 across the Chicago River from Ft. Dearborn near where the Wrigley Building
> stands today. … It was three stories high and built of brick, the hotel was elegantly furnished
> and **construction cost was $90,000**.

So the single fact that puts this structure in the 1835 scene at all — "ground was broken in
1835" — is in the uncredited paragraph and **must not be cited as Andreas**. The same paragraph
**drops Andreas's basement** and gives **$90,000 against his nearly $100,000**, which is the
proof that it is not a faithful restatement of the text it sits under. `data/exclusions.json`
sources the same claim to `drloih_hotels`, a second unfootnoted compilation. Two compilations
agreeing is not two witnesses.

## 3. The street name is a trap, and the modern gloss moves the site

North-side **Michigan Street** in 1835 is the east-west street one block north of Kinzie —
today's **East Hubbard Street**. It is **not Michigan Avenue**, which did not cross the river
until 1920. The chicagology gloss "near where the Wrigley Building stands today" puts the site on
Michigan **Avenue** at the river, about 150 m south-east of the block Andreas's three streets
describe and on the wrong side of Kinzie Street. `docs/research/03-structures-north.md` §3.8
carries the same gloss and additionally renders the third street as "Michigan (Water)",
equating it with North Water Street — which no source reached supports.

**The record follows Andreas's street names.** What Andreas does not say is which side of Rush
Street the block is on; the two candidate blocks are about 110 m apart, which is why the position
is `conjectural` rather than `inferred`, and the east side is adopted on a neighbourhood argument
that is not evidence.

## 4. How far had it risen? — the record's central conjecture

**No source reached says.** `chicagology_prefire112`'s own *what_it_does_not_supply* list says so
in terms: no storey reached, no walls up, no foundation depth, and no month for the
groundbreaking either.

The best anchor found is **J. D. Bonnell**, in a letter to the *Chicago Times* dated 15 March
1876 and quoted by Andreas, describing walking the town the morning after he arrived:

> Passing east, toward the mouth of the river, was **the Lake House in course of construction**,
> east of which was the residence of Dr. Kimball …

**His date is not clean and the conflict is recorded rather than hidden.** The letter opens "My
first entry into the city of Chicago was forty years ago, **August 25, 1835**" — forty years
before 1876 is 1836 — and Andreas's own lead-in says Bonnell "came to Chicago in 1837". The 1837
reading is ruled out by the letter's own content, since the hotel was open by the autumn of 1836.
Between 1835 and 1836, the letter's explicit date is preferred; under it, an eyewitness saw the
building visibly going up **eight weeks after the scene date**. Martineau's June 1836 "a new
hotel then building" is consistent with either reading and shows the work still unfinished a year
on.

**The schedule argument the record uses:** ground broken somewhere in 1835, opened autumn 1836,
so roughly eighteen months for three storeys and a basement of brick in a town whose only
brickyard was two years old. 1 July 1835 is then somewhere in the first quarter of that — cellar
dug, footings in, first storey of brickwork at most. **One storey is the value; the honest range
is zero to two**, and at three storeys this structure would stand about 12 m and be the tallest
thing in the scene, which is exactly the misreading the exclusion exists to prevent.

## 5. The archetype is off-label, and it is the least-wrong option

`fort_structure`, `kind: "magazine"`, `construction: "brick"`, `roof_type: "none"`.

**`kind: magazine` is an archetype selector and not a claim** — it does not say the Lake House
was a powder magazine. It is the only one of the archetype's eleven builders that produces a
plain masonry rectangle with a single opening and **no windows**; every other kind cuts a regular
window rhythm into both long faces, which would render a building site as a finished hotel.

`fort_structure` is used at all because it is the **only archetype in this project whose
vocabulary admits `brick` AND `roof_type: none`**, and brick is the single documented fact about
this structure's fabric while rooflessness is the single most important fact about its state.
`frame_tavern` would build a windowed, roofed, five-bay hotel; `outbuilding` can build neither
brick nor a roofless structure — the constraint `docs/LIBERTIES.md` L60 records for the estray
pen. The archetype's own docstring already extends it past the fort once, to the 1832 lighthouse,
on the ground that a government structure "has no other archetype it could belong to".

**What the model still cannot show:** a construction site is a hole in the ground before it is
anything else, and nothing here cuts a cellar into the terrain, so the shell sits **on** the
surface rather than in it. The footprint is also a full rectangle walled to one height, where a
real site would be part cellar, part first-course brickwork, part mortar-bed, scaffold and
stacked material.

## 6. What would resolve what

- The **Chicago American** (first issue 8 June 1835) and the **Chicago Democrat** for 1835-36. A
  $100,000 hotel going up in a town of three thousand was news, and the papers carried building
  notices — a dated notice would fix the groundbreaking month and might describe the progress.
- The **Kinzie's Addition conveyances**, which would give the lots and therefore the maximum
  plan, and would settle which side of Rush Street the block is on.
- Anything at all giving the finished building a frontage would replace the record's
  order-of-magnitude arithmetic on its cost.
