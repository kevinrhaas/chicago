# Jaunt library acceptance — 1835, October 2026

T-2042 (piece 4 of 4 of T-1271, *Reconcile and time the complete 25-jaunt library*).
Written 2026-10-03 against `dev` at 17756b47 plus this branch. Every number below is
read from a file or measured by a command named beside it. None is estimated.

The parent's other three pieces are separate PRs. T-2039 (`play_jaunt --all`, the
library-shape audit `tools/audit_jaunts.py`, the six featured titles) merged as #363 while
this piece was in flight. T-2040 (the content refusals) and T-2041 (routed timing of all 25
on the published mirror) are their own PRs. Their tables belong to them and their numbers
are the gate's; this report does not restate them.

**The audit on this branch** (`python3 tools/audit_jaunts.py`): `JAUNT AUDIT PASS — the 25
named premises and 1 more named in the brief, six featured, every shape bound met`. That
covers 26 jaunts, 6 quiet outings, families 5/6/5/5/5, and ranks reached in 5, 10 and 15
distinct completions. `--self-test`: all 13 breakages fire.

## 1. The growth path — a 26th jaunt by JSON and `compile_jaunts.py` alone

**Acceptance (T-1271 #5):** the 26th-jaunt demonstration needs no JS or CSS diff.

**Kept, not removed.** The 26th is a real jaunt, *Over the Draw to the North Side*
(`over-the-draw`). It is not a fixture deleted after the demonstration. It crosses the
Dearborn Street draw to Blodgett's brickyard, the North Side school-house and the Lake
House site. It is a quiet outing (no variable, no inventory, no strip), and its keepsake,
*North of the River*, goes to Wayfinding. Every building claim is reused word for word
from a published jaunt, and the invention is recorded as liberty `L-jaunt-over-the-draw`.

**What the change touched**, and nothing else:

| File | How |
|---|---|
| `data/jaunts/over-the-draw.json` | authored: the one new content file |
| `data/sidecars/1835/jaunts/over-the-draw.json`, `catalog.json` | written by `python3 tools/compile_jaunts.py` (`JAUNTS PASS — 26 jaunts; 22391 catalog bytes`) |
| `docs/LIBERTIES.md`, `data/liberties.json` and the other derived registers | the liberty, plus whatever the repo's own compilers re-derive from it |
| `docs/JAUNTS-INITIAL-LIBRARY.md`, this report, `renderers/web/js/changelog.js` | documentation and the release note |

No file under `renderers/web/` other than the changelog changed. No `.js` module and no
`.css` file was edited. The menu, the card, its estimate, the route and the walker all
picked the jaunt up from the compiled catalog.

**Walked:** `node tools/play_jaunt.mjs over-the-draw --all-paths`: 2 paths, both endings
reached, 1 keepsake awarded on each, 0 failures.

**On the published mirror** (`./tools/publish.sh`, then the menu opened in Chromium with
the scene's own `#welcome-jaunts` button and searched for "drawbridge"):

| Viewport | Card | Walk | Wagon | Horse (recommended) | Fly | Instantly | Start | Page errors |
|---|---|---|---|---|---|---|---|---|
| 390×780 | shown: "Town growth · 4 stops · Wayfinding" | 13.5 min | 6.5 min | **4.5 min** | 3 min | 2.5 min | `atStop` | 0 |
| 1280×800 | shown: the same | 12.5 min | 6.5 min | **4.5 min** | 3 min | 2.5 min | `atStop` | 0 |

These are the card's displayed estimates, the same formula as every other card. The
recommended mode reads inside the 3–6 minute band, and Fly and Instantly read faster. A
routed ride of the primary path is T-2041's measurement for the whole library. This report
does not stand in for it.

## 2. The library as compiled (read from `data/sidecars/1835/jaunts/catalog.json`)

26 jaunts in the 1835 catalog, every one `available`. 6 declare no
variable and no inventory (quiet outings; T-1271 asks for at least 5). Words per stop are
the stop texts' counts; T-1271 bounds them at 25–60.

| Title | id | Category | Stops | Words/stop | Recommended | Family | Quiet | Featured | Catalog |
|---|---|---|---:|---|---|---|---|---|---|
| A Bed for the Night | `bed-for-the-night` | Lodging | 4 | 43–44 | Horse | Neighbors |  |  | available |
| A Decent Coat | `a-decent-coat` | Shopping | 4 | 46–49 | Horse | Provisions | yes |  | available |
| A Letter Home | `letter-home` | Mail | 4 | 38–46 | Horse | News & Knowledge |  |  | available |
| A Schoolday Errand | `schoolday-errand` | Education | 4 | 50–53 | Horse | News & Knowledge |  |  | available |
| A Sunday Circuit | `sunday-circuit` | Social life | 4 | 49–54 | Horse | Neighbors | yes |  | available |
| Across Wolf Point | `across-wolf-point` | River and routes | 4 | 35–46 | Walk | Wayfinding | yes | ★ | available |
| Along the Working Harbor | `along-the-harbor` | River transportation | 4 | 51–53 | Horse | Wayfinding |  |  | available |
| An Evening Stroll | `an-evening-stroll` | Leisure | 4 | 45–50 | Horse | Neighbors | yes |  | available |
| Boots, Leather and the Road | `boots-and-leather` | Trades | 4 | 48–52 | Horse | Livelihood |  |  | available |
| Calling on Neighbors | `calling-on-neighbors` | Social life | 4 | 46–52 | Horse | Neighbors |  |  | available |
| Fort Dearborn Errand | `fort-dearborn-errand` | Fort Dearborn | 5 | 35–43 | Walk | Livelihood |  | ★ | available |
| Freight for the Store | `freight-for-the-store` | River commerce | 4 | 43–50 | Wagon | Livelihood |  |  | available |
| From Prairie to Town | `from-prairie-to-town` | Migration and routes | 4 | 51–56 | Horse | Wayfinding | yes |  | available |
| Gossip or Printed Notice? | `gossip-or-notice` | News and social life | 4 | 44–53 | Horse | News & Knowledge |  |  | available |
| Look Before You Buy a Lot | `inspect-a-lot` | Land | 4 | 41–51 | Walk | News & Knowledge |  |  | available |
| Materials for a Roof | `materials-for-a-roof` | Building trades | 4 | 47–52 | Horse | Livelihood |  |  | available |
| Mend the Harness | `mend-the-harness` | Trades and repairs | 4 | 47–50 | Wagon | Livelihood |  |  | available |
| New in Chicago | `new-in-chicago` | Orientation | 5 | 16–40 | Walk | Wayfinding |  | ★ | available |
| News Before Breakfast | `news-before-breakfast` | Newspapers | 4 | 45–51 | Walk | News & Knowledge |  |  | available |
| Outfit for the West | `outfit-for-the-west` | Migration | 5 | 24–35 | Wagon | Provisions |  | ★ | available |
| Over the Draw to the North Side | `over-the-draw` | Town growth | 4 | 49–55 | Horse | Wayfinding | yes |  | available |
| Shopping South Water Street | `shopping-south-water` | Commerce | 4 | 37–46 | Walk | Provisions |  | ★ | available |
| Soap and Candles | `soap-and-candles` | Household and trades | 4 | 39–47 | Horse | Provisions |  |  | available |
| Stock the Household | `household-provisions` | Household | 4 | 45–48 | Walk | Provisions |  |  | available |
| Taverns of Chicago | `taverns-of-chicago` | Taverns | 4 | 31–39 | Horse | Neighbors |  |  | available |
| Work on the Waterfront | `work-on-waterfront` | Employment | 4 | 44–52 | Horse | Livelihood |  |  | available |

| Family | Jaunts |
|---|---:|
| Livelihood | 6 |
| Neighbors | 5 |
| News & Knowledge | 5 |
| Provisions | 5 |
| Wayfinding | 5 |

Every family has at least 3 jaunts (T-1271 #4). The 26th takes Wayfinding from 4 to 5.

## 3. Corrections and exceptions made in this piece

- None to the initial 25. This piece adds one jaunt and changes no existing one.
- The brief's menu table gains row 26, and its catalogue gains § 26 with the route note.
- **T-2039's audit roster.** As merged, it required the brief to name exactly 25 jaunts,
  so any growth at all would have read as a finding. It now reads the brief's numbered
  sections. §§ 1–25 must all be present, every one of them a jaunt in the scene. Every
  further jaunt must be named in its own section from § 26 on. No id may appear twice, and
  no 1835 jaunt may go unnamed. The initial 25 are still checked one by one, so the bound
  is no looser. Two self-test cases were added: an initial section dropped, and an id
  named twice.
- **T-2039's quiet self-test** broke one quiet outing and expected the floor of five to
  fire. That only works while there are exactly five. With six it was silent, so it now
  breaks every quiet outing at once.
