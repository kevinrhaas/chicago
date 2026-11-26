# Make your case: the later cases — T-3678

T-3663 built one comparison on *Gossip or Printed Notice?*. T-3678 turns its hard-wired
check into a case table (`renderers/web/js/jaunt-investigation-cases.js`) and adds four
cases on other jaunts. Each case uses only claims its jaunt already compiles and cites;
nothing here adds a source, a witness or a fact. The model refuses a case unless every
named claim is still in the telling, on a stop the visitor reached and committed, with
the grade and source ids below, its citations resolved, a locator if Attested and
reasoning if not. The Gossip case behaves exactly as before; its outputs for all five
tellings were compared byte for byte before and after the refactor.

The later cases are offered in the four student tellings of each jaunt (3–5, 6–8, 9–10,
11–12). The 18+ (`audience: "adults"`) tellings are left out of them. No question,
label or review note of ours uses graphic words; the 1812 cases ask about a distance and
a sale, not about the fighting or the killing.

## 1812 — The Battle of Fort Dearborn: where along the shore did the attack begin?

Case `where-attack`, jaunt `battle-of-fort-dearborn`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| Written by two officers | `heald-journal` | `the-bank` | Attested | `quaife_1913` |
| | `helm-hour` | `the-bank` | Attested | `quaife_1913` |
| Pointed out later | `place-readings` | `cottonwoods` | Attested | `andreas_1884_v1`, `kirkland_1893_chicago_massacre` |
| | `stand-bank` | `the-bank` | Inferred | `andreas_1884_v1`, `kirkland_1893_chicago_massacre`, `quaife_1913` |

Why they conflict: Heald's journal says the column was attacked "two miles from the
Fort"; Helm (1814) says "about one and [a] half mile", which is also the distance in
Heald's official report (claim `attack`, cited at the same stop and left out of the case
because its text describes the killing). Arnold, in 1884, wrote that the Kinzies pointed
out the Eighteenth Street cottonwood "as near the place where the attack began"; Fernando
Jones was shown the spot by others. The stand's own reasoning (T-3469) records that the
mile and a half reaches only the later Roosevelt Road, the two miles reach Seventeenth
Street, and the tree is at Eighteenth. The case keeps that reasoning and its grade.

The jaunt's other inferred tree claim, `cottonwoods`, was not used: one of its sources'
citations (`moses_kirkland_history_of_chicago_v1`) is longer than the notebook keeps for a
source title, and the case refuses to save a trimmed citation.

## 1812 — Chicago's First Murder: who bought Du Sable's trading post?

Case `trading-post`, jaunt `killing-of-jean-lalime`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| The family's version | `family-version` | `du-sable-house` | Attested | `kinzie_waubun_1856`, `currey_1912_story_of_old_fort_dearborn`, `quaife_1913` |
| The land record | `deed` | `du-sable-house` | Attested | `dailing_2018_chicago_reader_lalime` |

Why they conflict: Wau-Bun (1856), Currey (1912) and Quaife (1913) say a Frenchman named
Le Mai held du Sable's improvements and sold them to Kinzie. The Chicago Reader (2018)
reports that the Wayne County deed records show Lalime, not Le Mai, as the buyer in 1800,
with Kinzie signing as witness. The project has not read the deed itself; the review note
says so, and the reading is the Reader's report of it.

## 1835 — A Schoolday Errand: where did Eliza Chappel's school meet?

Case `chappel`, jaunt `schoolday-errand`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| Andreas, 1884 | `chappel-school` | `the-log-house` | Attested | `andreas_1884_v1` |
| An online history, 2018 | `chappel-moved` | `the-log-house` | Attested | `drloih_chappell` |
| Where this outing places it | `chappel-place` | `the-log-house` | Inferred | `andreas_1884_v1`, `drloih_chappell` |

Why they conflict: Andreas gives only "a log house just outside the military
reservation" for 1833–34. The unfootnoted 2018 history says a log house formerly used as a
store, and a move in 1834 into the First Presbyterian Church. The placement's own reasoning
says the lot is undocumented and that other accounts put the first room at Lake and Market
or Lake and Clark. The two histories also spell her name differently (Chappel, Chappell).

## 1904 — The Bronze at Eighteenth Street: does the monument show what happened?

Case `bronze-rescue`, jaunt `bronze-at-eighteenth`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| The monument, 1893 | `battle-statue` | `bronze` | Attested | `wikipedia_fort_dearborn_massacre_monument`, `chicagoandcook_2017_1812_massacre_site` |
| A historian's essay, 2004 | `statue-doubt` | `bronze` | Attested | `karamanski_2004_monuments_lost_nation_p6` |
| | `statue-models` | `bronze` | Attested | `karamanski_2004_monuments_lost_nation_p6` |

Why they conflict: Pullman's 1893 bronze shows Black Partridge saving Margaret Helm.
Karamanski (2004) reports that some historians regard the rescue as "the product of
romantic imagination instead of eyewitness testimony", says Mrs. Helm rode to the lake
shore, and writes that the sculptor's figures "may have owed more to Buffalo Bill Cody's
Wild West Show than to actual research". It is a monument's telling beside a historian's
reading of it; neither is an eyewitness.

## T-3765 — one more case in each year (26 November 2026)

Owner request, 26 November 2026: "Mysteries and play-a-part: more cases and more roles."
Four more rows, one per year, under the same rules: only claims the jaunt already compiles
and cites, every student telling, the 18+ tellings left out. The notebook now keeps a source's
full citation up to 1,500 characters (it kept 500). Two of these cases cite sources whose
citations run to 586 and 959 characters (the Whistler draught, Moses and Kirkland), and a case
refuses to save a trimmed citation rather than trim it.

### 1812 — Fort Dearborn, Building by Building: where did the blockhouses stand?

Case `blockhouses`, jaunt `first-fort-dearborn-tour`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| The builders' drawing | `plan` | `the-fort` | Attested | `quaife_1913`, `whistler_1808_fort_dearborn_draught` |
| Remembered later | `blockhouses` | `merchants` | Attested | `whistler_1808_fort_dearborn_draught`, `quaife_1913`, `kinzie_waubun_1856` |
| | `covered-way` | `covered-way` | Attested | `quaife_1913`, `whistler_1808_fort_dearborn_draught`, `kinzie_waubun_1856` |

Why they conflict: Whistler's 1808 draught, as Quaife reads it, puts the two blockhouses at
the north-west and south-east corners. Wau-Bun (1856) says "two block-houses on the southern
side, and on the northern a sally-port". The draught's index has a "Covered Way to procure
Water"; Wau-Bun remembers "a sally-port, or subterranean passage from the parade-ground to the
river". Juliette Kinzie was not at Chicago in 1812 and wrote down family memory more than forty
years on. The town builds the blockhouses where the draught puts them. Nothing in the case
speaks of the fighting.

### 1835 — Across Wolf Point: floating logs, or a bridge on bents?

Case `raft-bridge`, jaunt `across-wolf-point`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| Four old settlers | `bridge-build` | `the-crossing` | Attested | `old_settlers_bridges_1883` |
| A later history | `mk-sb-bridge` | `the-crossing` | Attested | `moses_kirkland_history_of_chicago_v1` |
| How this town builds it | `bridge-raft` | `the-crossing` | Inferred | `old_settlers_bridges_1883` |

Why they conflict: Caton, Bates, Cleaver and Noble (printed by Andreas) describe both first
branch bridges on log abutments and two bents, about six feet above the water, so teams passed
under on the ice. Moses and Kirkland (1895) say the South Branch bridge near Randolph Street "at
first consisted of floating logs tied together". The structure record keeps the conflict open
and builds the fixed bridge, keeping the "raft" name; its reasoning is the case's inferred
reading. The review note says the later history may describe an earlier crossing; that is a
possibility the question asks the visitor to weigh, not a finding.

### 1871 — The Great Chicago Fire: which South Side building burned first?

Case `south-side`, jaunt `the-great-fire`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| Andreas, 1885 | `parmelee` | `parmelee` | Attested | `andreas_1885_v2` |
| Colbert, as Andreas quotes him | `gasworks` | `parmelee` | Attested | `andreas_1885_v2` |

Why they conflict: Andreas names the Parmelee Omnibus and Stage Company's new stable at Jackson
and Franklin as "The first building to ignite on the South Side", and the two men there give
half past eleven. Colbert, writing in 1871 and quoted on the same pages, puts the first South
Side fire "in a building of the South Division gas works on Adams Street"; Holden's timetable
has the gas works afire "At about twelve o'clock". Both readings come through Andreas's one
volume, so the case says so in the reading titles. Nobody is shown hurt.

### 1904 — Ghosts of Prairie Avenue: what can a ghost story show?

Case `architect-ghost`, jaunt `prairie-ghosts-at-night`.

| Reading | Evidence id | Stop | Grade | Source ids |
|---|---|---|---|---|
| A ghost story | `richardson-legend` | `glessner` | Attested | `ghost_city_tours_prairie_avenue`, `horror_obsessive_2023_glessner_ghosts` |
| The records | `richardson-dates` | `glessner` | Attested | `habs_glessner_house_il_1015_data_pages`, `glessner_house_richardson_page` |

Why they conflict: the ghost tours say Richardson, "who died before the house was finished", is
felt in the house and seen on its staircase. HABS dates the building from 1 June 1886, and the
house museum gives his death as 26 April 1886: he died before any of it was built, not before it
was finished. The case asks which parts of a modern legend a record can check. The "Attested"
grade on the legend means the tour says it, not that anything was seen.

## Checks

`node tools/test_jaunt_investigation.mjs` drives every case in every telling against the
compiled sidecars: the 18+ tellings refuse, each student telling offers its case with the
telling's own text, grade, locator, reasoning and sources (each source a record in
`data/sources/`), and each claim's stop unvisited or uncommitted, claim removed, stop
evidence removed, source added unresolved or removed, grade changed, locator or reasoning
removed, or text emptied refuses the whole case. Saves go to the real notebook store and
export, escaped, with no links.
