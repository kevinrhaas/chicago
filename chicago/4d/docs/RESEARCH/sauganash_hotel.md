# Sauganash Hotel — research dossier

**Record:** `data/structures/sauganash_hotel.json` · **Scene status:** standing and operating
on 1835-07-01 · **Milestone 0 subject**

The Sauganash was chosen as the first record on purpose. Two of its attributes are vividly
documented and two are unknowable from present evidence, which is exactly the situation the
per-attribute confidence model exists to handle. If the model can carry this building honestly,
it can carry the other hundred and fifty.

---

## 1. Identity and sequence

| period | name | note |
|---|---|---|
| 1829–1831 | **Eagle Exchange Tavern** | log cabin; Peoria County tavern licence 9 June 1830 |
| 1831–1838 | **Sauganash Hotel** | two-story frame block added; "Chicago's first hotel" |
| 1838– | Chicago Hotel | rename only; from Nov 1837 the dining room housed the Chicago Theatre Company |
| 4 Mar 1851 | — | **destroyed by fire** |
| 1860 | — | the Wigwam was built on the site for the Republican National Convention |

Named for Billy Caldwell, *Sauganash*, the Potawatomi–British interpreter and leader.

## 2. Location — and the move

**South-east corner of Lake Street and Market Street** (today Lake St and N Wacker Dr), on the
south side of the main stem near the forks, facing the confluence to the north-west.

Attested twice independently: chicagology's compilation ("near what is now the south-east
corner of Lake and Market streets") and the City of Chicago landmark designation for the site
(*Site of the Sauganash Hotel/Wigwam*, lanId 1417, now 191 N Wacker).

**The building moved, and this matters for the data model.** Mark Beaubien bought a small log
cabin near the forks from James Kinzie around 1826–27 and opened it as a tavern in 1829. After
the 1830 Thompson plat was laid out, the cabin was found to stand *in the middle of a platted
street*, and Beaubien relocated it to the Lake and Market corner. The 1831 frame block was then
built onto the relocated log core.

So the `log_1829` phase spans two positions. The record carries the post-move site, because the
pre-move position is not attested precisely enough to place — that limitation is stated in the
phase's position note rather than papered over with a guess.

This is also why `phases[]` carry their own `position`: early Chicago moved buildings routinely
(the Methodist meeting house was floated across the river and rolled on logs to Washington &
Clark in 1838), and a data model that treats position as a property of the building rather than
of the building-at-a-time cannot represent that.

## 3. What is documented

One near-contemporary description does nearly all the work. Juliette Kinzie, *Wau-Bun* (1856),
describing 1831:

> "At the Point, on the south side, stood a house just completed by Mark Beaubien. It was a
> pretentious white two-story building, with bright-blue wooden shutters, the admiration of all
> the little circle at Wolf Point. Here a canoe ferry was kept to transport people across the
> south branch of the river."

From this, three attributes are `documented`: **two stories**, **white paint**, **bright-blue
shutters**. "Just completed" independently corroborates the 1831 date.

Worth noticing *why* the description exists: a painted white frame building was remarkable at
Wolf Point in 1831, among log taverns. The building's visual signature is the thing that made
someone write it down.

**Caveat on the source's tier.** *Wau-Bun* was published in 1856 and describes 1831 — recollection
at twenty-five years' distance, hence tier 2 rather than tier 1, and hence the `describes_date`
field in the source record. It is the best evidence available and it is not an eyewitness note
made on the spot.

## 4. The gallery — revised 2026-08-09 after looking at the pictures

**No period source attests a gallery, porch, or veranda either way.** The secondary literature
describes the surviving images as disagreeing about one, so the record initially modelled a
gallery as `conjectural`.

**Then we examined the two images the project actually holds, and they agree — there is no
gallery.**

| image | shows |
|---|---|
| *The Sauganash Hotel*, in Andreas (1884) — **now held as `andreas_1884_sauganash_hotel_plate`, vol. I p. 632** | two-story clapboard block, gabled roof, two chimneys, multi-pane sash, a modest entrance with no veranda — **and a single-story log wing attached at the left front**, log courses and corner notching plainly drawn |
| Kurz & Allison, *Chicago In Early Days*, panel 14 (1893) | the same composition: two-story frame block, attached single-story log wing, red roof, no full-width porch |

**Caveat, and it matters:** the Kurz & Allison panel follows the Andreas composition closely
enough that it is almost certainly derived from it. These are not two independent witnesses;
they are one witness and a copy. Both are also retrospectives made fifty to sixty years after
the building went up.

**Decision:** `gallery: false`, confidence `inferred`, with the reasoning and the derivation
caveat recorded in the attribute note. "No gallery" is better attested than "gallery" without
being documented — which is exactly what `inferred` means.

This replaces the earlier reading. It is recorded as a revision rather than an edit because the
first reading came from the literature's characterization of the images and the second came from
the images themselves, and that distinction is worth keeping visible.

**The Andreas plate has a page now (T-0136, 2026-09-13).** This section read it as an Andreas
1884 plate from the start and cited no page, because nobody had opened the volume. It is
**volume I, printed page 632**, captioned *"THE SAUGANASH HOTEL."*, with a copyright line
lettered inside the plate border at the lower left reading `A. T. Andreas` — held as
`andreas_1884_sauganash_hotel_plate`, `public_domain` on the 1884 imprint. Read at the page
image, the plate carries the clapboard block, the two ridge chimneys, the wide entrance surround
with **no veranda**, and the log wing with its door direct to grade under a shed roof — so § 4's
and § 4a's readings both stand, on a citable page instead of an unlocated picture.

**One thing this section attributes and the plate does not.** The heading above named
F. Braunhold as the engraver; **no signature is legible** at the resolution archive.org
publishes, so the attribution is the owner's brief's and stays there rather than becoming the
record's. The table row is worded accordingly.

## 4a. The log wing — a second finding from the same images

Both depictions show the **1829 log cabin surviving as an attached single-story wing** rather
than being absorbed into or replaced by the frame block. That fits the documentary sequence
exactly: the frame block was "built onto" the log cabin after the cabin was moved to the Lake
and Market corner.

The record now carries `log_wing: true` (`inferred`, same sources, same derivation caveat), and
the `frame_tavern` archetype needs to support an attached log wing to build this structure
correctly. That is a real change to the Milestone 0 geometry requirement, discovered by looking
at the evidence rather than by reading about it.

## 5. What is unknown — the dimensions

**No dimensions for either the log cabin or the frame block are attested in any source reached.**
The cabin is described only as "small". The frame block is not measured anywhere.

The footprints in the record are placeholders and are tagged `conjectural` accordingly. Two
leads remain open:

1. **Andreas vol. 1, p. 106** — the index entry "Eagle Exchange (tavern)". Not yet read at
   page-image level. The archive.org OCR search index for this scan is demonstrably lossy, so
   the absence of a hit is not evidence of absence; this needs the page image.
2. **The Hathaway 1834 building rectangle.** Hathaway drew individual structures as small
   rectangles. Once the datum is verified and the raster warped, the Sauganash's rectangle
   gives a measured footprint — at map precision, but measured. This is blocked on the datum
   work and is the single strongest reason the datum is the project's critical path.

Until one of those lands, the building renders as conjectural massing at a plausible two-story
tavern size, and says so.

## 6. Construction — a flagged inference

The record currently carries `construction: balloon_frame`, `inferred` — **and the note flags it
as probably wrong.**

Balloon framing was developed in Chicago in 1832–33 and rapidly became the dominant local
method. The Sauganash frame block predates that by a year. A braced frame built onto a log core
is the more likely reading for 1831, and the value should probably become `braced_frame` once
someone researches the framing question properly.

It is left in place, visibly flagged, rather than silently corrected, because changing it
without evidence would just substitute one guess for another. This is recorded here so the next
agent picks it up as a research task rather than a typo.

## 7. Immediate surroundings (for the Milestone 1 cluster)

- **Philo Carpenter's drug store** — Chicago's first, in a log building on Lake Street
  *immediately adjacent to the Sauganash's public bar*. Carpenter arrived 18 July 1832.
- Chicago's **first billiard table** in a public house stood in the Sauganash.
- **Beaubien's canoe ferry** across the south branch, worked by rope, ran from the Point. By
  July 1835 it was probably superseded by the log raft bridge near Lake Street — an inference,
  not an attestation.

## 8. Occupancy at the scene date

The Beaubiens owned it until 1834. The hotel chronology gives "Davis (1835)" as operator,
possibly the John Davis who ran the Steamboat Hotel on North Water Street — a lead, not a
settled fact, and tagged `inferred`.

Mark Beaubien himself had moved on before the scene date: he built the **Exchange Coffee House**
at Lake and Wells in 1834. The Sauganash in July 1835 is a well-known house under new management,
in an old part of town that is quietly losing its primacy to the Lake Street axis to the east.

## 9. Open questions

| question | where to look |
|---|---|
| Dimensions of the frame block | Andreas vol. 1 p. 106, page image; then the Hathaway rectangle after datum verification |
| Gallery: real or illustrator's invention? | Any pre-1860 depiction, or a description in the Fergus Historical Series / pioneer reminiscences at the Newberry |
| Braced frame vs balloon frame | Period building practice at Wolf Point 1831; Andreas on early construction |
| Whether the log core survived visibly into the 1831 building | Unattested; currently modelled as absorbed |
| The 1835 proprietor "Mr. Davis" | Chicago Democrat advertisements, 1835 |
