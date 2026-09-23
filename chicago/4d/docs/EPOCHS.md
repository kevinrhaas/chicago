# The temporal architecture

The mistake this document exists to prevent: building "Chicago 1835" as a thing, then
discovering that "Chicago 1848" means starting over.

## Three layers, three speeds

| layer | changes | modeled as |
|---|---|---|
| **Land** — elevation, shoreline, river channel, sloughs, ponds | slowly, in punctuated jumps (a harbor cut, a lakefront fill, the grade raising) | **terrain epochs** |
| **Structures** — buildings, bridges, piers, palisades | constantly | **records with dated phases** |
| **Living cover** — flora, fauna | seasonally and with settlement | **zones tied to an epoch, with ranges** |

A **scene** (`data/scenes/1835.json`) names a date and a terrain epoch. Everything resolves
against that date. Adding a year is a new scene file plus, if the ground moved, a new epoch.

## Terrain epochs

`data/terrain/epochs.json` is a registry of non-overlapping intervals. Each epoch owns a bundle
of vector layers and a heightfield spec.

```jsonc
{ "id": "e1834_harbor_cut", "from": "1833-07-01", "to": "1848-12-31",
  "note": "The cut through the bar is open; the old southward channel is decaying behind the spit.",
  "status": "active" }
```

Rules:

- Intervals must not overlap, and a scene's date must fall inside its epoch's interval.
- An epoch is a *state of the ground*, not a year. `e1834_harbor_cut` covers well over a decade
  because the ground did not meaningfully move again until the canal era.
- Only one epoch may be `active` at a time until the first milestone ships. Others sit as
  `planned` stubs so the shape is visible without inviting scope creep.

Planned epochs, in the order they matter:

| epoch | what changed |
|---|---|
| `e1830_natural` | pre-cut: the baymouth bar deflects the river south nearly half a mile; natural mouth a half mile below the fort. **Shoreline traced (T-1242); spec, heightfield and meshes are T-1243.** |
| `e1834_harbor_cut` | **active** — piers and the cut through the bar; the old channel silting behind the sand tongue |
| `e1849_canal_era` | the I&M canal, wharfing, early fills |
| `e1856_grade_raise` | the city lifts itself out of the mud; the original ground surface is buried |
| `e1871_postfire` | the burnt district and the fills that followed; **representative date 1 July 1888**, derived in `data/terrain/1880s_scene_date_constraints.json` |

## Shoreline states are addressed through epochs

An epoch's `shoreline_state` resolves in `data/terrain/shoreline_states.json`. The
state id is the durable address; a scene must never find a shoreline by choosing a
convenient GeoJSON file or by reusing the active epoch's line. Three addresses are
reserved now:

| scene time | epoch | shoreline state | present status |
|---|---|---|---|
| 15 August 1812 | `e1830_natural` | `shore_1812_pre_cut` | **traced** (T-1242) — its own derived planform; no ground generated from it yet |
| 1 July 1835 | `e1834_harbor_cut` | `shore_1835_harbor_cut` | active |
| **1 July 1888** | `e1871_postfire` | `shore_1880s_ic_edge` | date settled by T-1249; geometry deliberately null, and T-1250 owns the line |

Three status words, and they are not interchangeable. **`planned`** is `geometry: null`,
which is not permission to fall back: that state cannot render until its owning ticket
supplies its own sourced line. **`traced`** is a state that has its own geometry but no
ground generated from it. **`active`** is the state the scene renders.

### The 1812 state is derived, and says so

No survey of the pre-cut mouth exists, so `shore_1812_pre_cut` could not be traced the way
1835 was. It is **derived in the open** by `tools/derive_shore_1812.py` from exactly two
committed things — `data/terrain/1812_mouth_readings.json` and the Wright 1834 trace — and
every departure from Wright is stated in the tool rather than drawn by hand:

- the drafted pier faces and the shore accreting behind them are **not carried**; the 1834
  line north of the pier root is recorded on the state as an *eastward bound* instead;
- the bar is declared **continuous to the mainland**, because a spit is why the river was
  deflected south at all, and the isthmus itself is emitted as an explicit unmodelled gap —
  the attachment is claimed, its width and lake face are not (`docs/LIBERTIES.md` L240);
- the mouth is set at the **half mile below the fort** that Lt. Swearingen walked and wrote
  down in 1803 (tier 1). The compilation's "near present Madison Street" is 94.9 m further
  south and is kept beside it as the alternative. Nothing is averaged.

Wright's own 1834 bar tip falls **9.2 m** south of the station Swearingen's half mile lands
on — an 1803 distance paced on foot and an 1834 instrument survey agreeing to within ten
metres, inside that trace's own ±20 m. That convergence is the strongest thing this project
can say about where the natural mouth was, and it is why the tier-1 reading was adoptable.

Because the file is derived, it is also re-derivable: `tools/check_shoreline_states.py`
rebuilds it from the readings and fails on a hand edit, on a pier vertex, on a midpoint
between the two readings, and on any feature claiming `documented`.

**A date is not a line either (T-1249).** The 1880s address date is now 1 July 1888 —
derived from the one Prairie Avenue landmark this project can date from a committed
source, and re-derived on every commit by `tools/check_1880s_scene_date.py`. Settling
it bought `shore_1880s_ic_edge` nothing: the state is still `planned`, its geometry is
still `null`, and the gate fails if a ticket that only fixed a day gives it a coast.
The date it replaced — an undocumented `date(1885, 7, 1)` that lived in
`tools/check_shoreline_states.py` from T-1152 — is recorded in the constraints file
under `adopted.supersedes`, because a plausible-looking number in a gate is read as
settled by the next run that finds it.

A dated observation may bound a shoreline without becoming it. The Rees & Rucker
1849 trace below Twelfth Street is recorded under the 1835 state as a lower bound,
not as an exact 1835 line. Where it overlaps Wright's independently fitted 1834
reading, `data/terrain/shoreline_disagreement_bands.geojson` carries the full
50.0–134.4 m spread as a polygon. It has `resolution: unresolved` and no adopted
line. `tools/check_shoreline_states.py` re-derives that polygon from the committed
station readings and fails if the states alias, a reference stops resolving, or the
band is replaced by a midpoint.

## Why fast-changing works are structures, not terrain

The north pier grew from roughly 700 ft at the end of 1834 to 1,260 ft by the close of the 1835
season. If the pier were terrain, every few months of pier construction would need its own
epoch, and the epoch registry would become a calendar.

So: **terrain is the slow layer; anything that changes on a human project schedule is a
structure with phases.** Piers, bridges, wharves, and the palisade are structures. The sandbar,
the shoreline, and the slough are terrain.

## Structure phases

One identity, several forms over time. The Sauganash is the reference case:

| phase | range | what it is |
|---|---|---|
| `log_1829` | 1829 → 1831 | the one-story log Eagle Exchange, including its documented **move** after the 1830 plat put it in the middle of a platted street |
| `frame_1831` | 1831 → 1851 | the two-story white frame block with blue shutters, built onto the log core at Lake & Market |

Phases carry their own `position`, so a relocated building is native to the model rather than a
special case. Early Chicago moved buildings routinely — the Methodist meeting house was floated
across the river and rolled on logs to Washington & Clark in 1838.

Resolution rule, shared by the validator, the scene compiler, and the renderer: for scene date
`T`, exactly one phase must cover `T`. Zero phases means the structure is not in that scene.
Two means the data is wrong.

## Vertical datum

Internal working datum is **Z = 0.0 at the summer-1835 lake/river water surface**, in feet,
converted to meters at export. Export offset: `ASL = Z + 580.0`.

This is deliberate. The Chicago City Datum was established in 1847 against a low-water mark and
sits on an obsolete "mean tide New York" reference; mixing it with modern NAVD88 figures
introduces a systematic error of most of a foot in a landscape whose *entire* natural relief is
under fifteen feet. Pick one internal datum, convert once, and record the conversion.

Total relief across the whole modeled area is less than 15 ft. Flatness is the story — the
lakeshore sand ridge stands about 9–10 ft above the lake while the plain west of State Street
sits 2–3 ft above the river. A vertical-exaggeration toggle may exist in the renderer for
legibility, but it defaults **off**, and no zone is invented to make the terrain interesting.

## Horizontal datum

Working CRS **EPSG:26916** (UTM 16N, NAD83, meters); scene frame is local East-North-Up meters
from a fixed origin at the Chicago River forks at Wolf Point.

`data/datum.json` carries `verified: false` until the origin has been derived from the
georeferenced 1834 Wright and Hathaway maps, and **the generators and the bake refuse to run
while it is false.** Fixing the origin after geometry exists means regenerating everything, so
the build is designed to make that impossible rather than merely discouraged.
