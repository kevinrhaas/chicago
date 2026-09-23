# Mansion House — research dossier

**Record:** `data/structures/mansion_house.json` · **Scene status:** standing and in public-house
use on 1835-07-01 · **Lake Street parcel**

Dexter Graves's log tavern of 1831 on the north side of Lake Street near Dearborn, with a frame
block built across its front in 1833 that reached the street line. **The best-attested FABRIC of
any building in this parcel** — four separate facts about the building itself, from two
independent passages of Andreas plus a judge's recollection — and no dimension whatever.

---

## 1. The two Andreas passages

**The hotel chapter, printed p. 635:**

> The Mansion House was built in 1831 by Dexter Graves; it stood on Lake near Dearborn and almost
> opposite the old Tremont House. **As originally built, the Mansion House was situated some
> little distance back from the street, but two years later Mr. Graves erected a frame addition
> in the front, which came out to a line with the street.** About this time he sold it to a Mr.
> Haddock, his son-in-law, who kept it until 1835 when it passed into the hands of Abram A.
> Markle, who, for two years thereafter accommodated and entertained many of Chicago's early
> residents, and travelers coming this way to take an observation of the "town lying in the mud."

**The town inventory for the fall of 1833**, listing the four hotels then standing:

> the Mansion House, **where are now numbers 84 and 86 Lake Street**. It was at that time **an
> unpretentious log tavern kept by Dexter Graves**, and according to some authorities had no
> name, being on the site of the building which was afterwards known by the above-mentioned name.

**Judge J. D. Caton, quoted by Andreas** on the May 1834 term of the Circuit Court:

> we all first met together in the **unfinished loft of the old Mansion House, just north of
> where the Tremont now stands**

## 2. A contemporary witness, from the *Chicago Democrat* of 26 November 1833

Verified on the page image (`data/sources/assets/chicago_democrat_1833_11_26/page1.jpg`):

> **Blacksmithing Business. MATTHIAS MASON & CO.** Carries on the above business in all its
> various branches, **on Main-street, nearly opposite Graves' Tavern**, where they intend to
> keep, ready made, all kinds of Shoes, Chains, &c. … Chicago, Nov. 26, 1833.

A paying advertiser using the house as the landmark his customers would find him by, in the
town's own week. It attests the tavern's existence, its keeper and its standing as a landmark;
it attests nothing about the fabric.

**It also leaves a puzzle this project should not paper over.** No street called **Main** is
platted in the 1830 Thompson plat, drawn on Wright 1834, or named anywhere in Andreas vol. 1 for
Chicago. The likeliest reading is that an advertiser newly arrived called the principal
thoroughfare what every other town called it, and that the street meant is Lake (where Graves's
tavern stood) or South Water. Recorded, not resolved. It is the only *contemporary* statement of
this building's street.

## 3. What the record does with it

- `archetype: log_dwelling` with `frame_addition_side: "front"`, which is the archetype's
  Miller-house case: a log core with a frame block against the facade. The side is **documented
  in as many words** — the only frame addition in this dataset whose side is (the Wolf Point
  Tavern's is conjectural, `docs/LIBERTIES.md` L24).
- `loft: true`, `documented` — Caton sat in it.
- The **south face is set on the Lake Street building line**, which is the one dimension-like
  statement any source makes about this building: the 1833 addition "came out to a line with the
  street".
- Everything dimensional is invented: 12 × 9 m overall, a 12 m wide and 4 m deep frame front, one
  storey each. The 4 m stands in for "some little distance back from the street", which is an
  unmeasured setback.

## 4. Position — how the side of Lake Street was decided

Two statements agree and neither is explicit. Andreas p. 635 puts it "on Lake near Dearborn and
almost opposite the old Tremont House"; Caton puts it "just north of where the Tremont now
stands". The Tremont standing when Caton spoke is the post-1850 brick house, which
`chicagology_prefire021`'s header places at the **south-east** corner of Lake and Dearborn — the
one thing that header is probably right about, since it describes the later Tremonts. North of
that is the **north-east** corner of the crossing: north side of Lake, immediately east of
Dearborn. That is also consistent with "almost opposite the old Tremont House", the first Tremont
standing on the north-west corner, with the two houses facing each other across Dearborn.

"Near Dearborn" is not "at the corner", so the along-street uncertainty is at least a lot's
width — South Water lots were 55 ft — on top of the georeference's ±20 m.

## 5. Conflicts recorded and not resolved

1. **One building or two.** Andreas's own "according to some authorities had no name, **being on
   the site of** the building which was afterwards known by the above-mentioned name" admits a
   reading in which the 1833 log tavern was replaced rather than extended. His hotel chapter
   contradicts it by carrying one building from 1831 to 1850, and the record follows the hotel
   chapter. The parcel brief's instruction — treat Graves' boarding house and the Mansion House
   as one structure — is Andreas's own reading.
2. **Who kept it on 1835-07-01.** Haddock "until 1835", then Markle "in 1835". No month. The
   record names both and chooses neither.
3. **Markle in two houses at once.** Andreas has Markle at the Mansion House from 1835 for two
   years, and separately quotes a *Chicago American* advertisement of 6 August 1836 for seats at
   "Markle's Exchange Coffee House". Either he held both or one dating is loose.
4. **"Cook's Coffee House".** `docs/research/04-structures-south.md` line 156 says the house was
   advertised in 1835 under that name, citing Andreas and `drloih_hotels`. **The phrase is not in
   Andreas vol. 1** — a full-text search returns nothing, and the volume's Coffee House index
   entries are the Exchange, Lincoln's, the Eagle and the Lake Street. It may be drloih's alone.
   Not asserted in the record.

## 6. What would resolve what

- **Chicago Democrat and Chicago American advertisements** of the house under Haddock or Markle,
  which would carry a room count and might settle the "Cook's Coffee House" name and the 1835
  handover month. *Partly answered — see §7. The Democrat under Haddock is now read, and it dates
  the 1834 handover rather than the 1835 one; the room count and the coffee-house name are still
  wanted.*
- **Cook County deeds** on the lots that became Nos. 84 and 86 Lake Street — the frontage, and
  therefore the footprint's width, from a document rather than from a street-number inference.
- Andreas at page-image level around the fall-1833 inventory, for the sentence about "some
  authorities" and what it is citing.

---

## 7. What the newspaper corpus added, 2026-08-29 (T-0324)

§6 asked for *Chicago Democrat* advertisements of the house under Haddock. There are several, and
they close three things this dossier had left open. The full argument, with every printing, is in
`docs/RESEARCH/botsford_graves_1834.md`.

**(a) The house is named as Haddock's, by both names, in the summer of 1834.** "H. Haddock's
Mansio[n House]" (1834-06-25 c002); "at the Mansion House, **E. H. Haddock's**" (1834-07-30
c003); "Haddock's Man[s]ion-House" (1834-08-13 c007). Andreas's Graves → Haddock succession is
confirmed by the town's own paper.

**(b) The Graves → Haddock handover is bracketed, where Andreas gives only "about this time".**
The Board of Trustees adopts ordinances "at the house of Dexter Graves" on 1833-12-04 and
1834-03-05; an employment notice of **1834-04-01** (c017) reads "enquire of Mr. Graves, at his
tavern"; the ordinances of **1834-06-06** are adopted "at the house of E. Haddock" (1834-06-18
c002). **Graves's on 1 April 1834, Haddock's by 25 June 1834.** Dexter Graves commences the
Baking Business on South Water Street over a copy date of 1834-03-25 — the same spring. The
trustees' venue is not by itself a tenancy (the board also sat at Starr Foot's house, the
Presbyterian church, the Tremont House and "the Exchange" later that year), so the bracket rests
on Graves's own advertisement and on the naming, with the venue agreeing rather than proving.

**(c) §5.1's "some authorities had no name" is answered.** The *Democrat* calls this building the
Mansion House **by that name** from 1834-09-03 (c010, a militia election "held at the
Mansion-House in Chicago"), ten months before the scene date. Whatever the 1833 house was called,
the 1834-35 one had this name contemporaneously.

**(d) A lot and block number — the only one in the corpus for any building here, and unusable.**
G. Spring's For-Sale notice, six printings from 1834-06-18 to 1834-11-19: "LOT No. 7, in block No.
16, **one lot east of Haddock's Tavern, on Lake street** … a large Dwelling-House and fine well."
Nothing committed carries the Thompson plat's block numbering, so "block No. 16" resolves to
nothing on the plat this model is built on (`T-0358`). What *is* usable is the neighbour: the lot
east of this house held a **dwelling**, not a shop — which is what makes J. K. Botsford's "next
door to Graves' Tavern" and "corner of Dearborn and Lake-sts." readable as one frontage on this
house's **west** side, and puts this house on the second lot from Dearborn rather than the corner
lot. **The stored coordinate is not moved on it**: one lot is about 24 m, inside the along-street
allowance §4 already carries.

**(e) Not renamed the Tremont House.** Matthias Mason & Co.'s standing advertisement — one
unchanged dateline of 26 November 1833 — is anchored on Graves' Tavern to 1834-06-11 and on the
Tremont House from 1834-09-10. The forge did not move and neither did this house; the landlord's
name went stale, in exactly the weeks the paper stopped being able to call the house Graves's.
The two houses stood diagonally across Dearborn throughout, which is Andreas's "almost opposite"
(§4).

**(f) And a warning about §5's Main-street.** The same standing advertisement sets the street word
as "Main-street" in four settings and "on Mar[k]et street" in the setting of 1834-10-15 (c007).
The word is unstable across settings of one advertisement, so it is a weaker witness than this
dossier had treated it as. Main Street is still not identified with any platted street.
