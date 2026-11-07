# The people of Chicago on 14 August 1812 (T-3461)

Kevin, 2026-11-07: *"maybe you should do a multi agent research sweep to identify and place and
fill in any possible people, and do reconstructions for the balance in 1812 since we dont have many"*.

Four researchers read the sources in parallel on 2026-11-07. Each fact in their files carries a
source id, a locator (Gutenberg text line numbers, chapter, appendix, page) and a quote of 25
words or fewer that a script matched against the text it names.

| file | what it reads | count |
|---|---|---|
| `garrison.json` | Heald's muster-roll to 31 May 1812 (Quaife 1913 App. VIII), Quaife's fates (App. IX), Heald's journal and report, Helm's narrative and lists, Wau-Bun, Kirkland, Simmons 1896 | 83 people: 55 regulars, 12 militia (6 named), 9 women, 18 children (11 identifiable) |
| `civilians.json` | Wau-Bun, Quaife, Kirkland, Currey, Andreas, Hurlbut | 41 people, 12 excluded (gone or dead before 14 August) |
| `native.json` | Heald, Helm, the Missouri Gazette (via Quaife), Wau-Bun, Andreas, Keating, Matson | 31 entries; Helm counts 500 warriors and 179 women and children on 12 August |
| `dress.json` | period pictures and garments for every role but Native dress (in native.json) | 8 roles, 26 proposed source records, for T-3462..T-3467 |

`build.py` arranges the readings into `data/residents_1812/households/` (27 households, 120
people). It composes no fact; its header says what it decides (households, grades, presence) and
liberty `L-1812-people-3461` records the reconstructed homes and the counted-unnamed cards. Rerun
it after editing a reading, then `python3 tools/compile_scene.py --scene 1812` and
`python3 tools/compile_source_use.py`; `build.py --check` says whether the cards are current.

Not carded, because the readings put them dead or gone before 14 August: Jean Lalime (killed in
June), Liberty White and Jean Baptiste Cardin (killed 6 April at Lee's Place), the Mirandeau
family (back at Milwaukee), Matthew Irwin (left 5 July), Charles Jouett (resigned 1811), Billy
Caldwell (arrived after the battle), Shabbona (arrived hours after it), Main Poc (near Malden),
and the Healds' stillborn son (4 May). People the readings could not place on 14 August (Russell,
Fettle's household, Le Mai, the Coursolles, Clark and the discharged soldier at the forks,
Noke-no-qua and her son, Alexander Robinson, the interpreter François) are left for a source that
does; Fettle and Le Clerc appear only as Quaife's guesses at the militia.

Wells's Miami escort and the camp's families are carded by T-3467 when it places them.
