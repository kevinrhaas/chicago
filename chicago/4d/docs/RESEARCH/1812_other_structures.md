# 1812: the other structures the record may place at Chicago before the evacuation

T-2489, 2026-10-15. The owner asked for every known structure of 1812 (project thread
"1812 structures", 2026-10-13). T-2484..T-2488 build the houses the histories agree on;
this page rules on the ones the record names on weaker evidence, and lists what else the
corpus places at the post in 1803-1812. Every ruling is IN (a build ticket filed under
T-2489), OUT (an entry in `data/exclusions.json` scoped to the 1812 scene with
`scenes: ["1812"]`, so the scene's "not here" list shows it), or CARRIED (another
ticket already builds it).

## What was read

| source | how | id |
|---|---|---|
| Andreas, *History of Chicago* v1 (1884) | archive.org full text, `historyofchicago01andr_djvu.txt`, scan pp. 89-92 | `andreas_1884_v1` |
| Quaife, *Chicago and the Old Northwest* (1913) | Gutenberg 69274, ch. VI-VIII and the index | `quaife_1913` |
| Moses and Kirkland, *History of Chicago* v1 (1895) | the committed text, lines 5600-6000, 6590-6800, 9790-9915 | `moses_kirkland_history_of_chicago_v1` |
| Hubbard, *Autobiography* (1911) | the committed text and claims (`bk_hub_066`, the River Guarie passage) | `hubbard_autobiography_1911` |
| Kinzie, *Wau-Bun* (1856) | the Gutenberg epub in `chicago/reference/Wau-bun/`, ch. XVIII and its footnote 30 | `kinzie_waubun_1856` |
| Currey, *The Story of Old Fort Dearborn* (1912) | Gutenberg 52346, ch. II | `currey_1912_old_fort_dearborn` (new) |
| Kirkland, *The Chicago Massacre of 1812* (1893) | Gutenberg 59624 full text | read, not cited: no source record yet, and nothing ruled here rests on it alone |

Lossing's *Pictorial Field-Book of the War of 1812* (1869) was not reached and nothing
here cites it.

## The rulings

### Guarie's trading house on the North Branch — OUT

`data/exclusions.json` `guarie_trading_house`. The whole of the evidence is one tradition
Hubbard took from two old voyageurs: a picketed trading house on the west bank about
where Fulton Street is, "prior to 1778" (Andreas p. 92); in his own book Guarie is "the
first trader that followed La Salle" and the trace is "the field he cultivated". By 1818
there were corn-hills grown over with grass. Quaife (p. 138): Hubbard's story is "our
only knowledge". Currey alone has Kinzie find Guarie a "permanent resident" in 1804, and
cites nothing; Cooper's count of the houses in 1808 and Whistler's draught of the same
winter name no house there. Out.

### Cobweb Castle's build date — OUT for 1812; Mrs. Callis's house is the Burns house

`data/exclusions.json` `cobweb_castle_1812`. Mrs. Callis (Andreas p. 89) says the house
her father lived in from 1816 was built before 1812. Andreas (p. 90) and Moses and
Kirkland (pp. 70-71) say Cobweb Castle was BEGUN under Jouett's second agency (1816-18)
and finished by Wolcott in 1820. They are two houses: Moses and Kirkland say Jouett
occupied the Burns house in 1817, "near where the agency house, called Cobweb Castle, was
subsequently erected", and the house Callis describes — two large rooms, twenty steps
from the river bank, west of Kinzie's — is the Burns house as Hurlbut placed it. Wau-Bun's
footnote 30 agrees. So the pre-1812 house is T-2487's, and `cobweb_castle.log_1820`
stands as it is.

### Lalime's dwelling — IN, filed as a build

Jean (John) La Lime, the post's interpreter, came with the troops: he and Dr. Smith
wintered 1803-04 in a vacant cabin on the north side (Quaife p. 142). Surgeon Cooper,
at the post from 1808, counted four houses on the north side, "occupied by Kinzie,
Ouilmette, La Lime, and Le Mai", and says La Lime "was living in one of the four houses
on the north side of the river and acting as government Indian interpreter" (Quaife
pp. 148-50, 166). Whistler's draught of the same winter draws three houses west of
Kinzie's, numeral 31 on each, "Oather Dwelling Houses on opisite side River", with no
names; Quaife pairs them with Cooper's. So the source says WHERE he lived to within one of
three drawn houses, and the build ticket (below) carries the choice. He was killed in the
spring of 1812, four months before the evacuation; nothing read says what became of
the house, so its standing on the scene date is inferred from continuity and the build
says so. Whistler also draws an "Interpreters House"
(no. 19) west-south-west of the fort, which T-2062 left unbuilt; whether La Lime ever
lived in the government's house rather than his own is not stated.

### Russell — CARRIED by T-2488, no separate house

Heald's letter names "Messrs. Russell and Lee's cabin, in a field on the Portage branch"
(Moses and Kirkland v1, line 6883 of the committed text; Quaife pp. 212-13). Quaife: "Russell was evidently the
partner of Lee, but aside from this fact nothing is known about him." No source gives
Russell a house of his own, at the fort or anywhere else; his one building is the
partners' cabin T-2488 builds. Nothing to exclude and nothing to file.

### The first fort's riverside works — the Wau-Bun root-houses do not count

The root-houses and company gardens in Wau-Bun ch. XVII are the SECOND fort's, in 1831.
For the first fort the authority is Whistler's draught and his description of it: the
index names a wharf (no. 27), a covered way to procure water (no. 33, "Omited in their
places") and gutters (no. 34); his description, through Quaife, has a field of eight or
nine acres "close to the forks on the south side of the main river" serving as the
company gardens and public cornfield, and a meadow along the timber that gave the
garrison its hay. The gardens on the sheet already stand (`first_fort_outer_officers_garden`,
`first_fort_outer_sutlers_garden`). The wharf and the covered way go into the build ticket
for the draught's unbuilt outer works; the cornfield goes with the forks.

### Anything else the corpus places at Chicago, 1803-1812

| what | evidence | ruling |
|---|---|---|
| Le Mai's house, a second no. 31 house | Cooper names Le Mai among the four north-side occupants in 1808 (Quaife p. 166) — after he had sold the du Sable house to Kinzie | IN, with La Lime's |
| The interpreter's house, armourer's shop, merchant's shop, bake house, house in the factor's department (Whistler nos. 19-23) | the draught's index; T-2062 built 17, 18 and the stables and left these | IN, one build |
| The wharf (no. 27) and covered way (no. 33) | the draught's index; Quaife's text for the covered way | IN, with nos. 19-23 |
| Clark's house near the forks | Cooper: "one near the forks of the river occupied by a man named Clark who was a cattle dealer" (Quaife p. 167) | IN, the forks build |
| Two houses at the forks, one a discharged soldier's | Whistler, through Quaife p. 167; not on the committed trace's 34-item index, so the build must find them on the sheet or say it cannot | IN, the forks build |
| Coursoll's house and inclosed field north of the river | Whistler, through Quaife p. 167; the Courselles otherwise appear only in Kinzie's account books | IN, the forks build |
| The company garden and public cornfield, 8-9 acres by the forks | Whistler's description, through Quaife | IN, the forks build (ground, not a building) |
| A farmer's house a mile south-east of the fort | Cooper; Quaife takes it to be Lee's | CARRIED by T-2487 |
| Bridges' house, between Kinzie's and Jouett's | Mrs. Callis: "occupied in 1816 by a Mr. Bridges" (Andreas p. 89) | HELD: dated only to 1816; it may be one of the no. 31 houses, which the La Lime build weighs |
| The horse mill (Whistler no. 32) | the draught; du Sable's bill of sale as T-2484 reported it | IN at T-2485: `kinzie_horse_mill_1812`, 1808-1816 (below) |
| The 1812 agency house on the south bank | Wau-Bun; Whistler no. 17 | STANDS: `first_fort_outer_agents_house` |

### The Kinzie establishment and du Sable's bill of sale — T-2485

**Read:** Wau-Bun ch. XVII (the establishment in 1831: "dairy, bake-house, lodging-house for the
Frenchmen, and stables", and the garden north of the dwelling) and ch. VI (the dairy), from the
local Gutenberg epub; Currey 1912 and Kirkland 1893 on the Kinzie house (neither names an
outbuilding); Eastman's view of 1820, Sarony's lithograph, the Cram plate, the Teich painting and
Gemmell's plate, through the house's solved cameras; Whistler's index (no. 32, through Quaife 1913
note 413) and T-2504's box for no. 32 as recorded in the ticket.

**Not reachable:** Quaife, "Property of Jean Baptiste Point Sable", *Mississippi Valley Historical
Review* 15:1 (1928), which prints the bill of sale of 1800 — JSTOR (behind a script wall) and
HathiTrust (blocked) both refused the run's container, and archive.org was blocked. The bill's list
(two barns, a horse mill, a bakehouse, a poultry house, a dairy, a smokehouse) is T-2484's report of
it; no dimension from it is used and it is not cited. The Whistler sheet image could not be fetched
either (the Gutenberg image host was blocked), so no. 32's box was not re-read.

| bill of sale item | ruling for 1812 | record |
|---|---|---|
| horse mill | STANDS: Whistler's "Old Grist Mill Worked by Horses", 1808; closes 1816, Sarony draws nothing at its place about 1831 | `kinzie_horse_mill_1812` |
| bakehouse | STANDS, inferred: the bill (1800, as reported) and Wau-Bun (1831) | `kinzie_bake_house_1812` |
| dairy | STANDS, inferred: the bill and Wau-Bun | `kinzie_dairy_1812` |
| barn (one) | STANDS as the stable: Wau-Bun's "stables", Eastman's one log barn | `kinzie_stable_1812` |
| barn (second) | NOT BUILT: no source after 1800 names two | exclusion `kinzie_second_barn_1812` |
| poultry house | NOT BUILT: named nowhere after 1800 | exclusion `kinzie_poultry_house_1812` |
| smokehouse | NOT BUILT: named nowhere after 1800 | exclusion `kinzie_smokehouse_1812` |

Not on the bill but Wau-Bun's: the lodging house for the Frenchmen (`kinzie_lodging_house_1812`)
and the garden (`kinzie_garden_1812`). Which pictured building is which, and every place and size,
is L420.
