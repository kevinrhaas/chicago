# Tremont House I — evidence correction, T-2385

**Current ruling, 2026-10-26:** the default July 1835 model follows Edwin O. Gale's
retrospective town walk: **30 × 20 ft, two storeys, yellow**, as **inferred** evidence.
The native **gifford-reading** version preserves the earlier picture-led model.
Original T-2385 remains open: the two-storey default does not match the drawing's
real third storey. Neither source establishes a dated enlargement.

## Direct source and date

`gale_1902_tremont_town_walk` records the book text separately from its jail plate.
Actual printed p. 25 (scan n40) dates Gale's arrival to **25 May 1835**; Chapter III
begins his town walk on printed p. 43 (n66). On printed p. 51 (n76), he writes:

> On the northwest corner of Lake and Dearborn streets is Chicago's sixth hotel,
> the original 20x30 yellow two story Tremont House, built in 1833 by Alanson Sweet,
> with Starr Foot as first proprietor.

Published by Fleming H. Revell in **1902**, this is an 1835-framed participant
recollection, not a contemporary survey. Feet are a contextual inference: the text
states neither units nor axes. We adopt 30 ft along the existing long axis and
20 ft along the short axis, a rectangle of **9.144 × 6.096 m**. Exact conversion
implies no survey precision. The claims that no source gives dimensions or supports
Starr Foot as first proprietor are withdrawn. That identification does not displace
the independently documented Ira Couch tenure in 1835; Mallory & Able remains unsupported.

## Real disagreement, preserved

The whole Gifford drawing visibly shows **three** storeys, three short-elevation bays,
five long-elevation bays and four stacks. It supplies no metric scale, dated viewpoint
or recoverable wall colour. It is undated within the first house's 1833–1839 life.
Gale's specifically 1835-framed text is preferred for the default scene. The native
version preserves the undated picture-led form, its reconstructed 50 × 30 ft scale
and unpainted colour, explicitly contrary to the selected text. No dated alteration
or canonical image-gate acceptance is invented.

Gifford use remains the owner's project-specific attributed reference/comparison
approval: **N. Roswell Gifford; reproduced by Chicagology**,
https://chicagology.com/prefire/prefire021/ . This establishes neither public-domain
status nor original publication/collection credit or general redistribution rights.
The separate US-published 1902 book text is out of copyright by age.

## Visible geometry and corner

The default retains the working 3.1 m lower-storey module plus one 2.35 m upper
module, giving **5.45 m** walls. These are reconstructed, not historical measurements.
The raised entry, bays, roof, arched name panel, stacks and flag remain bounded
picture-led inferences or liberties; their exact 1835 fitting dates remain open.
Yellow uses the existing stock palette, with no precise historical pigment asserted.

At bearing 180 degrees the polygon extends west and south from its northeast origin.
Preserve both street-facing planes: **E 447760.52** east and **N 4637295.24** south.
The new origin is **E 447760.52, N 4637301.336**; subtracting the new 6.096 m depth
preserves the south plane exactly. This retains the existing uncertain street control;
it neither moves the platted grid nor creates a survey. The roof-staff flag anchor
is recalculated from the smaller native roof, rather than a whole-building box.

## Existing opening kit limit

The 30 ft default gives 1.8288 m per long-elevation bay. The existing native
open-shutter kit requires a conservative **1.95 m** minimum; the smaller default
therefore omits shutters, which Gale does not describe. The native Gifford version
retains its original pictured shutters. No clearance assertion is weakened and the
text-led rectangle is not enlarged to fit a stock kit. The default omission remains
an explicit pictured-feature difference, not a finding that shutters were absent.

## Earlier research, retained as history

The text below records the earlier text-only investigation. Its rejection of a
three-storey picture and its negative dimensional/proprietor findings are superseded
by the actual Gifford and Gale readings above. Its current-tense model descriptions
refer to that historical investigation.

---

# Tremont House I — research dossier

**Record:** `data/structures/tremont_house_1.json` · **Scene status:** standing and open on
1835-07-01, Ira Couch proprietor · **Lake Street parcel**

The principal house on Lake Street, built 1833 on the north-west corner of Lake and Dearborn,
burned 27 October 1839 with seventeen other buildings. Its corner, its material and its dates
are unusually well attested. **Its height is not, and the three-storey Tremont of 1833 is a
manufactured fact.**

---

## 1. What is attested

| claim | source |
|---|---|
| built 1833 by **Alanson Sweet** | Andreas, printed p. 635 |
| **north-west corner of Lake and Dearborn** | Andreas p. 635; Chicago *Tribune* 2 Feb 1874; *Chicago Illustrated* Jan 1866 — three texts |
| **frame / wood** | the same three texts |
| kept first as a saloon and boarding-house by Sweet and "a man from Canada, named Darwin" | Andreas p. 635 |
| **Ira Couch** proprietor from 1834, "ran it until 1836" | Andreas p. 635; *Tribune* 1874 |
| "a mere shell, **without any sidewalk around it**, and poorly furnished, as none of the rooms were entirely carpeted … very many of the beds were minus one pleasant luxury, a pillow" | *Tribune* 2 Feb 1874, Ira Couch's own account of what he took over |
| the corner impassable to the stage in early spring, passengers walking two blocks | *Tribune* 2 Feb 1874 |
| **burned 27 October 1839** | Andreas p. 635 and again in the 1839 narrative |

## 2. The storey count — how one modern sentence became a fact

`chicagology_prefire021` prints three things with no typographic break between them: an
uncredited editorial "Building Summary", a passage of *Chicago Illustrated* (January 1866), and
a reader's letter to the Chicago *Tribune* of 2 February 1874.

- The **1874 letter** says "an unpretending frame structure". No storeys.
- ***Chicago Illustrated* (1866)** says "a wooden structure". No storeys.
- The **uncredited summary** says "a three-story wooden building". That is the only storey count
  on the page, and it is modern, unsigned and unsourced.

**Andreas gives this building a builder, a corner, a material, four proprietors and a death date
and never counts its storeys.** So there is exactly one witness to three storeys and it is not a
witness.

`docs/research/04-structures-south.md` line 155 records the height as contested and adopts three
on the ground that "chicagology and Wikipedia say three-story wooden" — which is one sentence
counted twice, since Wikipedia's figure has no independent basis.

**Three arguments against three storeys**, none of them evidence and all of them better than the
sentence they are set against:

1. Chicago in 1833 held about 350 people. *Wau-Bun* has the Sauganash's **two** storeys and white
   paint as "the admiration of all the little circle at Wolf Point" two years earlier.
2. The *Chicago American*'s own "Improvements in 1836" list, quoted by Andreas, counts "about
   twenty large **two to three-story wooden buildings**" among that year's **new** work. The
   three-storey wooden building is a phenomenon of 1836 in this town.
3. `data/exclusions.json` excludes the Saloon Building of 1836 partly on the understanding that
   it was Chicago's **first three-storey structure**, which a three-storey Tremont of 1833 would
   contradict. (Note that this claim is `drloih_hotels`' rather than Andreas's — Andreas calls
   the Saloon Building the finest hall in Chicago and does not count its storeys either.)

**The record carries two storeys, tagged `conjectural`**, with the three-storey reading argued
against on the attribute rather than dropped. If three is right the building stands about 2.6 m
taller.

## 3. The header trap on the same page

`chicagology_prefire021`'s metadata block gives "Address: SE corner of Lake and Dearborn Streets"
and "Architect: John M. Van Osdel". **Both belong to the later Tremonts** and contradict all
three body texts on the same page. Andreas confirms the move independently: the house begun in
December 1839 was raised "on the corner where the present Tremont stands", i.e. not where the
first one burned.

## 4. Claims in circulation that this project does not hold

- **"First proprietor Starr Foot"** and **"sold to Mallory & Able 1835"**
  (`docs/research/04-structures-south.md` line 155). Neither name attaches to this building
  anywhere in Andreas vol. 1 — Starr Foot appears once, in an unrelated list of names — and
  neither is on the chicagology page. Not carried.

## 5. What would resolve what

- The **Daily American**'s account of the 27 October 1839 fire, which Andreas quotes for the
  merchants' stock losses and which itemised insurance building by building — the likeliest
  place to find a description or a valuation of the fabric.
- Any **Chicago American or Chicago Democrat advertisement** of the house, 1834–39. Hotel
  advertisements of the period habitually counted rooms and often storeys.
- Both would settle the storey count, and the first might settle the footprint.

## 6. A scene-level corroboration for the whole parcel

The *Chicago American* of **15 August 1835**, quoted by Andreas, counts the town six weeks after
the scene date: "There are now upward of fifty business houses, four large forwarding-houses,
**eight taverns**, two printing offices, two book-stores, one steam saw-mill, one brewery, one
furnace (just going up), and twenty-five mechanics' shops of all kinds." With this record, the
Mansion House and the Exchange Coffee House added, `data/structures/` holds exactly **eight**
public houses for 1835 — Sauganash, Green Tree, Western, Wolf Point, Steamboat, Tremont, Mansion
House, Exchange. That is a check on the parcel, not on any building in it, and it is the closest
thing to a completeness test this dataset has.


T-2385 native capacity correction, 2026-10-26: the first full1070-step gate
retained four lodging-related failures. Its61-step tail had not run the direct
native lodging owners. The unnecessary new Gale lifetime-range citation was
removed while retaining Gale on the dimensions, storeys and paint; all phase
dates and eligibility stay exact. Native build_lodging_model_1835 and
seat_lodgers_1835 now report111.48m² over two storeys and six ordinary-night beds
for Tremont, down from17. Eight other inns' ordinary estimates rebalance under
the existing fixed class total. The actual12 residents, every person identity/name/seat,
source grade, minted ID, quota and carried allocation remain exact. The existing
crowded limit35 is the1840 town model's proxy, not an attested Tremont room count;
it is unchanged. The keeper home's tie is inferred, and the lodger seats remain
reconstructed even where a person's identity is attested. These native owners
change current-capacity reporting, not who lives in the house. No geometry,
crowding rule, new ratio, dated availability or population allocation is changed.
The earlier fullFAIL remains preserved; final downstream/gate results are
reported separately when actually closed.
