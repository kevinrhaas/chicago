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

## Checks

`node tools/test_jaunt_investigation.mjs` drives every case in every telling against the
compiled sidecars: the 18+ tellings refuse, each student telling offers its case with the
telling's own text, grade, locator, reasoning and sources (each source a record in
`data/sources/`), and each claim's stop unvisited or uncommitted, claim removed, stop
evidence removed, source added unresolved or removed, grade changed, locator or reasoning
removed, or text emptied refuses the whole case. Saves go to the real notebook store and
export, escaped, with no links.

## Also in T-3678 — Packing for the March (1812, play a part)

The owner asked, in the same ticket, for a play-a-part jaunt of 1812. `packing-for-the-march`
(Stories, grades 6–8; 3–5, 9–10, 11–12 and 18+ tellings from
`docs/RESEARCH/jaunt-grade-versions-3621/words/`) has the visitor play an unnamed
twelve-year-old of a household outside the pickets on 13 and 14 August 1812. Six stops at
existing 1812 anchors (the Kinzie house front, the factory, the main gate, the covered way,
the river mouth, the parade); two choices; four endings, each handing on to *The Battle of
Fort Dearborn*. Only the build-up is told and nothing is staged.

Every attested claim is copied word for word from *Fort Dearborn, Building by Building*
(`order-arrives`, `kinzie`, `march`, `goods`, `agency`, `plan`, `inside`, `destroyed`,
`covered-way`, `secure`) or *The Battle of Fort Dearborn* (`hull-order`, `wells`, `medal`,
`gate-evening`). Three claims are new: `days` and `places` (Inferred: the two-day frame and
the anchors) and `role` (Reconstructed, `L-play-a-part-1812-3678`). No named person speaks
to the visitor, no known child of a named family is given a part, and no unnamed person
besides the visitor is used, so no person card is added. The 18+ telling exists because
the T-3623 gate asks one of every jaunt; it quotes more of the same evidence and still
stages nothing.
