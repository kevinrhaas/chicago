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
