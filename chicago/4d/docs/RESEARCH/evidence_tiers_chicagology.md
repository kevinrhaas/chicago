# The chicagology pages, read for what they carry

**Date:** 2026-08-10 · **Subject:** `chicagology_prefire127`, `chicagology_prefire273`,
`chicagology_prefire278`, `chicagology_kinzie_bridge` · **Outcome:** three regrades, one
declaration, fifteen of twenty-one ladder warnings cleared without a value being touched.

## 1. The question, and why it is a question about sources

`docs/STATUS.md` § 43 switched on `check_evidence_ladder` and it counted **21 `documented`
values resting on no source at tier 3 or better** — later scholarship alone, with no period
document, no eyewitness recollection and no compilation from pioneer testimony behind them.
The check ends its own warning with the honest ambiguity: *either the values are over-graded
or the sources are under-tiered*, and only reading the page settles which.

`docs/ROADMAP.md` § S5 named the cheaper half first. Regrading a **value** is a mesh input,
so it arrives with a Blender bake attached; regrading a **source** is not, so it can be done
by anyone who can read. And the dataset already contained the precedent: `chicagology_prefire252`
is tier 2, not tier 4, because it prints an 1893 *Chicago Tribune* retrospective — a page
transcribing a period newspaper is worth what the newspaper is worth whatever site hosts it.

Three pages carry fifteen of the twenty-one. This memo is what happened when they were opened.

## 2. Method

Each page was fetched live on 2026-08-10 (`https://chicagology.com/prefire/<id>/`, HTTP 200)
and read in full as text. The transcribed documents were identified from **the page's own
printed attributions** — chicagology sets each transcription under a line naming the
publication and its date — not from the citation this project had already written, which in
two of the three cases turned out to be wrong. Each committed Wayback snapshot was re-checked
and returns 200.

Nothing was promoted on the strength of a page *looking* old. The test applied throughout: can
the document that carries this dataset's claim be named, dated, and placed on the ladder in
`data/source.schema.json` on its own terms?

## 3. `chicagology_prefire127` — Green Tree Tavern · tier 4 → **2**

**What it is.** An anthology of dated transcriptions: about nine Chicago city directories
(Fergus 1839, Norris 1844, Fergus 1846, 1855-6, Cooke 1859-60, Halpin & Bailey 1863-64 and
1871, Lakeside 1881 and 1885), *Chicago Tribune* notices of 1880, 1890, 1900, 1901 and 1902,
*The Inter Ocean* of 22 June 1902, Edwin O. Gale's *Reminiscences of Early Chicago and
Vicinity* (1902), and — the substance — **the Inter Ocean of 1 July 1883**, the old-settlers
hotel feature.

**Why tier 2.** The 1883 feature is not a writer summarising: a sketch of the building was
prepared from W. H. Stow's recollection, and the reporter then carried it to people who had
lived in the house and printed their corrections in their own words. F. H. Taylor (in Chicago
from 1834, lodged in the west one-storey addition) gives the orientation; John Gray (landlord
1838-41) gives the plan, the entrance on the Lake Street front, the divided hall and the
stairway, the low addition on each end, and the attic window in the gable; Gale, who reached
Chicago in 1835, describes the bar-room from inside. That is *near-primary recollection*, the
schema's rung 2, and it is the same kind of evidence as `chicagology_prefire252`.

**What the page says against itself, and it is kept.** The feature prints the disagreements
rather than resolving them — one settler wants a door in the middle of the long side, another
wants attic windows, another moves the door to the end — and closes: *these differences of
opinion will show how difficult it will be to ever write the history of Chicago completely.*
Tier 2 grades the KIND of evidence, not its unanimity. The witnesses are also recalling the
house from the late 1830s and 1840s at fifty years' remove; Gale's "when the house was built"
is what ties the fabric he describes back to 1833.

**Not declared, deliberately.** The city directories are period documents in their own right —
rung 1 material — and no claim in this dataset rests on them. Declaring them in `transcribes`
would drag the record's rung onto evidence nobody here uses. They stay in `note` as apparatus.

## 4. `chicagology_prefire273` — Wolf's Point · tier 4 → **2**, and the citation was wrong

**The record said** the page compiles A. T. Andreas and the Fergus Historical Series. **It
does not.** The body is the **Chicago Magazine of 15 May 1857**, whose author is writing
twenty-five years after the scene he describes, from George Davis's 1832 drawing of the forks
and from Gurdon S. Hubbard's account given to him directly — the passage ends *This is a
picture of Chicago, and of all that then composed it, as described to us by Gurdon S. Hubbard,
Esq., as seen by him when he first came here, in 1818.* Andreas is on the page, under his own
heading, carrying the town-limits chronology and the 1830 Thompson plat; nothing in this
dataset reaches Andreas through this page (`andreas_1884_v1` is cited directly). Modern gallery
captions and a CBS news item sit at the foot and carry nothing.

**Why tier 2.** A named witness describing what he saw, taken down by a writer who names him,
plus a resident's contemporary drawing. Rung 2.

**A sibling left alone on purpose.** `chicagology_prefire276` transcribes the *same* 1857
magazine and is still graded 4. No record in `data/` cites it, so regrading it would be a
judgement made about a page for no reason and half-read; it is named here so the inconsistency
is on the record rather than silent, and it is the obvious first move the day something cites it.

## 5. `chicagology_prefire278` — Town of Chicago · tier 4 → **2**, and the record described the wrong half

This is the sharpest finding of the three and it is about our own record, not about the page.

**Every value in this dataset that cites `prefire278` is about the WESTERN HOTEL**, and the
source record's citation and note described only the town's incorporation and the town code of
7 November 1833. The material four claims actually rest on was not mentioned at all.

The page is **the Inter Ocean of 22 July 1883** — "Old Chicago: The Town in 1833", the same
old-settlers series as § 3 a fortnight later. Below the incorporation record it runs **"The Old
Western Hotel — First Frame House on the West Side"**: the reporter's description of what was
left of the building in 1883, and interviews with old settlers and with W. H. Stow's son. From
those interviews come the farmers' and teamsters' house, Stow as builder and proprietor, the
original two storeys (*"make it full two stories high, as it had originally been"*), and the
large stable and wagon yard with entrances from both streets.

**The two halves are not the same rung.** The incorporation half is quoted on the page from
*Colbert's Chicago* (1868), a compiled secondary account — rung 3. No value here rests on it,
so it is not declared, and if one ever does it must not inherit the interviews' rung.

**The page is also where the Western Hotel's open question comes from**: *When the Western
Hotel was built is a disputed question, which may never be settled* — Stow said 1834, an old
settler on the same page says "about 1836 or 1837". That is why the dated range stays
`inferred`, and it is now attributable to the page rather than to a summary of it.

## 6. `chicagology_kinzie_bridge` — tier 3 unchanged, judgement declared

Its `note` has always ended *"Tier 3 for the Andreas transcription; the surrounding apparatus
is a finding aid."* True, and unreadable by any check. The Andreas passage is now declared and
the tabulated bridge chronology is explicitly not, which is what the sentence meant.

## 7. What cleared, value by value

The ladder check is per-value and this memo's promotions are per-source, so the fifteen are
walked one at a time rather than counted. Each line names the transcribed document that carries
it.

| value | now rests on | the sentence |
|---|---|---|
| `green_tree_tavern` function, occupants | Inter Ocean 1883-07-01 | the house kept as a tavern, its landlords named in sequence |
| `green_tree_tavern/frame_1833` documented_range | Inter Ocean 1883-07-01 | built 1833, standing to the 1902 collapse the same page reports |
| `green_tree_tavern/frame_1833` form.stories | Inter Ocean 1883-07-01 | Gray: "a stairway in this hall led to the second floor" |
| `green_tree_tavern/frame_1833` form.roof_type | Inter Ocean 1883-07-01 | Gray: "a small attic window in the gable end, for we used the attic, too" |
| `miller_house/log_frame_1827` form.construction | Chicago Magazine 1857-05-15 | "It was a log structure partly sided" |
| `miller_house/log_frame_1827` form.frame_addition | Chicago Magazine 1857-05-15 | "partly sided" — that a frame element existed |
| `miller_house/log_frame_1827` form.frame_addition_side | Chicago Magazine 1857-05-15 | the Davis 1832 view printed on the page, the range between cabin and water |
| `wolf_point_tavern/log_frame_1828` form.construction | Chicago Magazine 1857-05-15 | "This building was partly log and partly frame" |
| `wolf_point_tavern/log_frame_1828` form.frame_addition | Chicago Magazine 1857-05-15 | the same clause |
| `western_hotel` function | Inter Ocean 1883-07-22 | "the stopping place for all the farmers town from the west" |
| `western_hotel` occupants | Inter Ocean 1883-07-22 | Stow built and kept the house; his son interviewed in the bar |
| `western_hotel/frame_1834` form.stories | Inter Ocean 1883-07-22 | "make it full two stories high, as it had originally been" |
| `western_hotel/frame_1834` form.stables | Inter Ocean 1883-07-22 | "the large stable and the yard into which the trains were driven" |
| ground `e1834_harbor_cut` surface_materials.south_division_marsh | Chicago Magazine 1857-05-15 | Hubbard: "a strip of land still more marshy … covered with tall grass, reeds and rushes" |

**One of those is thinner than the rest and it is said here rather than left to be found.**
`miller_house.form.frame_addition` is graded `documented` and what this page attests is *partly
sided* — that part of the building was frame-clad. The words the record's note quotes, *"a
two-story house added to the cabin, fronting the river"*, are **drloih_hotels'**, not the 1857
magazine's. The split in the record turns out to be exactly right: that a frame element existed
is carried by the 1857 text, and that it stood two storeys is `form.frame_addition_stories`,
which is one of the four values below and did **not** clear.

## 8. What did not clear, and why

Six warnings remain. Four are the ones § 43 called sharper than the count:

| value | rests on | the problem |
|---|---|---|
| `sauganash_hotel/log_1829` form.stories | `drloih_hotels` alone | the source record's own words: *use only to generate leads and to corroborate; never as sole evidence* |
| `sauganash_hotel/log_1829` form.construction | `drloih_hotels` alone | same |
| `miller_house/log_frame_1827` form.frame_addition_stories | `drloih_hotels` alone | same, and it is the storey count § 7 above declines to launder |
| `wolf_point_tavern/log_frame_1828` form.sign | `drloih_wolf_point` alone | same — and this is the `documented` chip that justified modelling a signboard |

Plus two outside this memo's scope: ground `surface_materials.south_division`
(`chicago_architecture_history_115`) and ground `water` (`wikipedia_chicago_river`).

These are **not** solvable by re-tiering. Both `drloih` pages are unfootnoted blog
compilations, they disagree with each other about the Wolf Point Tavern's build date, and
neither has a web archive. The fix is either better evidence or a regrade of the value — which
is a mesh input, so it lands with a bake, and it stays queued in `docs/ROADMAP.md` § S5.

## 9. What this does not settle

- **A rung is still a judgement, and this is one.** The declaration makes it re-derivable —
  the document is named, dated and placed — it does not make it right. Anyone who thinks an
  1883 interview at fifty years' remove is rung 3 rather than rung 2 now has something specific
  to argue with, which is the whole gain.
- **The ladder gate is per-value; the declaration is per-record.** A source cited for
  corroboration on one attribute lends its rung to every attribute that lists it. § 7 exists
  because a cleared warning is not by itself an improvement in the evidence for the value that
  carried it, and no check can tell the difference.
- **Nine pages remain undeclared** at tier 4 or weaker — counted in the validator's own note
  every run. `chicagology_prefire062` ("Quoting the Chicago American, 9 July 1835"),
  `chicagology_prefire276` (Chicago Magazine 1857) and `wikipedia_chicago_river` (quoting
  Swearingen's 1803 account) all *look* like the same case, and none of them was opened here.
  Looking like the case is what this memo exists to stop being sufficient.
  **Opened 2026-08-11 — `docs/RESEARCH/evidence_tiers_round_two.md`.** Two were the case and
  one was not: `prefire062` reprints Andreas (who quotes the newspaper) and is tier 3,
  `prefire276` reprints the 1857 *Chicago Magazine* and is tier 2, and Wikipedia reprints
  nothing at all — it paraphrases Swearingen and footnotes Quaife 1913, pp. 373-377, which
  needed a third state in the schema to record. Six pages left, and the date above is wrong:
  the American item is 9 July **1836**.
- **No value moved and no mesh is stale.** A confidence is a mesh input and a source tier is
  not; the whole of this slice is sources, sidecars and prose.
