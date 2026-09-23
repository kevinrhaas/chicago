# The John-Dean house at the foot of Randolph Street

**T-0895, 2026-09-11.** Opened by T-0718, which found the house while settling the
Beaubien homestead's corner and could not stop to read it.

The question this memo answers is the one the ticket put first: **was it standing on
1835-07-01?** The answer is that nothing reached says so, that the last sight of it is
1818, and that the building is therefore **excluded** — `data/exclusions.json#john_dean_house`,
on the same reasoning and the same disposition as `ouilmette_cabin`. Along the way it
turns out this project has been holding a second, independent witness to the house for
some time, filed under `landscape` and pointed at a clump of pine trees.

## 1. What Andreas says

Andreas, *History of Chicago* vol. 1, scan p. 183, read directly off the scan on T-0718:

> In 1815, a short time before the rebuilding of the fort, an army contractor named
> **Dean**, built a house **on the lake shore, at the mouth of the Chicago River, near
> where is now the foot of Randolph Street**. In 1817, Mr. Beaubien purchased this house,
> which was **a low, gloomy building of five rooms, for $1,000** — a large sum for those
> days. After this purchase he lived in the Dean house for several years, his son
> Alexander being born there. He used the old cabin after this for a barn.

A builder, a year, a price, a room count, a site named by a street, and an occupant with
a child born there. That is more than this project holds for most of what it has built,
which is why the ticket was opened.

Two later mentions, neither of which follows the building forward. Andreas scan p. 191
has Varnum boarding "in the old John Dean house, with J. B. Beaubien, then its owner" —
Jacob Varnum was United States factor at Chicago until the factory closed, so that
sentence sits inside the same 1816–1822 window and adds no year beyond it. Wentworth's
address of 21 May 1881 (`wentworth_1881_fort_dearborn`, reprinted at Andreas scan p. 339)
says Beaubien's later residence was the one he moved to "after he moved from what was
before known as the John-Dean house" — a statement about a **name**, made sixty-six years
after the house was built, and not a statement that anything was standing.

## 2. The second witness, which this project already had

`data/research/books/claims/hubbard_autobiography_1911.json#bk_hub_064` was read and filed
under `kind: "landscape"`, with `entities: ["The Pines"]` and a note entirely about the
old river mouth. Its quote is Gurdon Hubbard describing Chicago as he found it on arriving
in **1818**:

> For a distance of a quarter of a mile from the "Factor House" there was no fence,
> building, or other obstruction between the government-field fence and the river or lake.
> **Another house of hewn logs stood twelve hundred or more feet from the road, and back
> of it flowed the Chicago River**, which, as late as 1827, emptied into Lake Michigan at
> a point known as "The Pines" …

The house in the middle of that sentence was never picked up. It is, on the argument
below, Dean's.

**The identification is forced rather than merely suggested, and the thing that forces it
is Hubbard's own exhaustiveness.** Three claims on, at `bk_hub_066`, he closes the
inventory: the buildings he has just named, "with the addition of a log cabin near the
present Bridgeport, called 'Hardscrabble,' a cabin on the north side occupied by Antoine
Ouilmette, and the house of Mr. Kinzie, **comprised all the buildings within the present
limits of Cook County**." So if the Dean house stood in 1818 — and Andreas has Beaubien
living in it from 1817 for several years — it has to be one of the buildings on Hubbard's
list. Run the list: the fort and its own buildings; the Factor House, east of the road by
the fort (`bk_hub_063`); the American Fur Company's round-log storehouse on the river's
edge, Craft's (`bk_hub_065`); Hardscrabble, four miles up the South Branch; Ouilmette's
cabin, north side; Kinzie's house, north bank. Every one of those is placed somewhere the
Dean house is not. **The hewn-log house is the only candidate left**, and the only
building on the list with no name attached to it.

Three further agreements, none of which was needed to reach that conclusion:

- **"back of it flowed the Chicago River."** `bk_hub_067`, from the same pages, has the
  river's mouth driven south of the fort by the north-east winds along "a narrow strip of
  sand" between river and lake. A house on the lake shore south of the fort therefore has
  the old channel **behind** it, to the west — which is what Andreas means by "on the lake
  shore, at the mouth of the Chicago River" and what Hubbard says in so many words. The
  same landform is the subject of the open T-0886, and nothing here decides that ticket.
- **The distance.** See § 3.
- **The material.** Hubbard gives "hewn logs", which Andreas does not give at all. It is
  the one fabric statement about this building anywhere this project has reached, and it is
  recorded here rather than used, because the building is not being placed.

**Grade it honestly: `inferred`, and it is not going to get better than that.** Hubbard
never names Dean, never names Beaubien in connection with this house, and never dates its
construction. What he gives is an unnamed house in the right place at the right time inside
a list that claims to be complete.

## 3. "The foot of Randolph Street", read against this town's own ground

Done by T-0759's method, which derived the same phrase for the watering place rather than
taking it by eye. `data/streets/1835.json`'s `randolph` runs from local east −320 north
−249.9 to east 900 north −259.8; extended on its own bearing it crosses the z = 0 waterline
of the committed `e1834_harbor_cut` heightfield at **east 1224.1, north −262.43**, and it
crosses the traced 1834 shoreline within 1.1 m of the same point. The street is not drawn
that far east and this memo does not extend it.

`data/structures/fort_dearborn_palisade.json` stands at UTM E 448194.77, N 4637594.25 =
local east 1122.1, north 198.5. So, in this project's own frame:

| | |
|---|---|
| fort palisade → foot of Randolph Street, straight line | **472.0 m = 1,549 ft** |
| …of which, southward | 460.9 m = **1,512 ft** |
| …of which, eastward | 102.0 m = 335 ft |
| Hubbard's "twelve hundred or more feet from the road" | 366 m or more |
| Hubbard's "a quarter of a mile" of clear ground from the Factor House | 402 m = 1,320 ft |

**Hubbard's two figures do not quite reconcile with each other**, and the disagreement is
stated here rather than smoothed away: a house at 1,200 ft would stand *inside* the quarter
mile of ground he has just called clear. Neither number is a survey — they are an old man's
distances in a memoir published in 1911 about a shore he saw in 1818 — and "from the road"
cannot be a perpendicular measure, because the sand strip was nowhere near 1,200 ft wide.
Read as distance along the shore, which is the only reading the sentence supports, the pair
of them put a house **somewhere around a quarter of a mile south of the fort on the shore
strip**, and this project's own geometry puts the foot of Randolph Street 1,512 ft south of
the palisade. That is the same stretch of shore at the precision the sentences carry, and
it is corroboration of the identification rather than a position for the building.

## 4. Survival to the scene date, which is what the ticket turns on

Every sighting of this house falls in a seven-year window:

| | |
|---|---|
| 1815 | built by the contractor Dean (Andreas p. 183) |
| 1817 | bought by Jean Baptiste Beaubien for $1,000, and lived in (Andreas p. 183) |
| 1816–1822 | Varnum boards in it with Beaubien its owner (Andreas p. 191) |
| **1818** | **a house of hewn logs on the shore strip — the last sight of it (Hubbard, `bk_hub_064`)** |
| 1822/1823 | Beaubien is elsewhere: the factory building (Andreas p. 205) or the Craft storehouse after Craft's death (`bk_hub_065`, `bk_afc_008`), which is the open T-0894 and is not settled here |
| 1835-07-01 | **the scene — thirteen years of silence** |
| 1881 | Wentworth, naming it in the past tense as a name |

Nothing reached records its demolition, and this memo does not invent one. What it records
is that **no source places it after 1818**, and that a building is not put into a scene on
its construction date. The site itself is no help either way: the 1828 cut through the spit
and the 1833–34 harbour piers rebuilt the mouth a quarter mile north of here, but neither
touched the ground at the foot of Randolph, so "the shore changed" is not a demolition
argument and is not used as one.

Two sources that look like they should settle it and cannot. `andreas_1884_chicago_1830_map`
is a **land-entry** map whose own printed note says the names on it are patentees "entered
or patented between the years 1828 and 1836" — its own source record spells out that it can
never license a dwelling, and by the same token its silence cannot refuse one. And the
Thompson plat covers the **platted town**, which stops well west of east 1224: the foot of
Randolph Street is on unplatted lakefront inside the Fort Dearborn Reservation, so absence
from the plat means nothing at all.

## 5. Disposition, and why exclusion rather than the watch list

**Excluded**, at `data/exclusions.json#john_dean_house`.

The register already holds this exact shape of finding. `ouilmette_cabin`: "Almost
certainly gone — Ouilmette left for Gross Pointe in the later 1820s and no source attests
the cabin's survival past that decade." Read the Dean house against it — occupant gone by
1822/23, no attestation past 1818 — and it is the same sentence with different names in
it. Following this project's own precedent is the argument; inventing a new grade for a
building that matches an existing entry is not.

The watch list was considered and is the wrong shelf. Its two survival entries are
`cobweb_castle`, which is `in_dataset: true` and stands in the scene, and
`billy_caldwell_house`, whose uncertainty is about existence rather than survival. The
Dean house is neither: it is a building that certainly existed, is not in the dataset, and
has thirteen unwitnessed years between it and the scene. That is `ouilmette_cabin`'s shelf.

**And a second reason, which would hold even if survival were granted.** Nothing
dimensions this building. "A low, gloomy building of five rooms" is a **room count, not a
dimension** — it gives no length, no depth, no storey height and no bearing, and five rooms
will fit a great many footprints. Hubbard adds hewn logs and nothing more. Andreas's
locator is "*near* where is now the foot of Randolph Street", and this project's own
derivation of that phrase lands on the **waterline**, so a house placed there would have to
be set back from the water by an invented distance, on an invented bearing, at an invented
size. That is four inventions stacked on one retrospective sentence, for a building whose
presence in the scene is itself unattested.

## 6. What would change this

- **Any sighting between 1818 and 1835.** The likeliest are the old-settler reminiscences
  (T-0554), which date arrivals and openings by year as a matter of course, and the
  Wilcox v. Jackson record: Beaubien's pre-emption claim of 28 May 1835 covered the whole
  75.69-acre reservation, and a contest over a claim is the kind of proceeding in which
  buildings get enumerated.
- **The Wright 1834 sheet read at reservation scale**, east of the plat. The same reading
  is what `beaubien_barn` names as its own upgrade path.
- **A demolition or a removal.** It would move this entry from "no source attests its
  survival" to `kinzie_house`'s stronger "documented absence", which is a better entry than
  this one.

## 7. What this memo deliberately does not do

It does not touch `jb_beaubien_homestead` or `beaubien_barn`; it does not decide which
building Beaubien moved to in 1822 or 1823 (**T-0894**); it does not adjust the homestead's
phase id or start date (**T-0893**); and it does not rule on whether the water at the foot
of Randolph Street is the old channel or the lake (**T-0886**). It also does not join
Andreas's contractor Dean to Hubbard's United States factor John Dean — T-0718 said that
identity is not established, and nothing read here establishes it.

**Links:** T-0718 · T-0759 · T-0886 · T-0893 · T-0894 · `data/exclusions.json#john_dean_house` ·
`bk_hub_063`–`bk_hub_067` · `docs/RESEARCH/jb_beaubien_homestead.md` § 6
