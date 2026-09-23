# The material sheet — what the town's surfaces are made of

**Parcel R-W2a** (ROADMAP · RENDERING §4 W2) · written 2026-08-16 · **a document, not a change**

This is the input `R-W2b` wires in and the bake half draws its atlases from. It commits no
code, no parameter and no record. Its job is to answer four questions for every surface in
the town, in one place, so that a builder and a critic read the same sheet:

1. **which surfaces exist** — not which ones we imagine, the ones actually in the shipped GLBs;
2. **what each one is**, with the evidence this repository holds and the confidence that
   evidence supports;
3. **its roughness**, and — the part §4 W2 asks for explicitly and R-G1 scored worst — *why*;
4. **its tiling rate**, derived from a dimension the generators already commit rather than
   chosen to look right.

Everything in §1 is **measured out of `assets/gltf/**/*.glb`**, not read off the source. The
source and the shipped bytes have disagreed in this project before (B-BUG2), and a sheet that
inventories intentions is worth nothing to a bake.

---

## 0. Headline

`assets/gltf/` holds **334 assets carrying 1,353 material slots**, and they resolve to **32
distinct material names, 41 distinct base colours and 18 distinct roughness values**. Nothing
in the town carries a texture of any kind (§1 item 9). Two independent generators paint it:
the nine Blender **archetypes** (244 assets) and the pure-Python **inferred placeholder**
(90 assets), and their palettes were written separately and have never been reconciled.

**CORRECTION 2026-08-16 (K36(a)) — this sheet measures `assets/gltf/`, which is what this
project BAKES, and the site serves `assets/web/`, which is not the same file.** The sentence
above — *nothing in the town carries a texture of any kind* — is true of the masters and **false
of what a browser downloads**: `gltf-transform optimize`'s palette pass folds the named materials
of **38 of the 334 assets** into a single `PaletteMaterial001` carrying **75 generated PNGs that
exist in no master**, and deletes their material names on the way. The split is exactly at the
count: every asset with five or six materials is affected, every asset with four or fewer is
not, and **275 assets sit one material short of the threshold**. §1 and §2 below are unchanged
and correct **about the generators' output**, which is what an atlas is authored against — but a
sheet whose own preamble warns that *"the source and the shipped bytes have disagreed in this
project before"* should say which of the two it counted, so: the masters. **R-W2b must read
ROADMAP K36(a) before wiring anything to a material NAME**, because on those 38 assets the name
is not what ships. K36(b) owns the repair, and `tools/measure_web_derivatives.py` is the gate
that will now say so out loud.

**The five findings are worth more than the sheet.** They are in §4, and two of them —
**the chimney is not a material in this project**, and **no record anywhere states a roof
covering** — are the reason the town's roofs and stacks cannot be textured today even with a
finished atlas. They are recorded as findings and **not patched here**: this parcel ships a
document.

---

## 1. The surface census, measured from the baked masters (`assets/gltf/`)

Counts are material slots, across all 334 assets. Base colours are the `baseColorFactor`
actually in the file. Every material in the town is `metallicFactor: 0`, unlit by any map,
double-sided and opaque (R-W5a proved this exhaustively when it merged 47 batches into 16).

| material | slots | shipped base colour (as written) | roughness | emitted by |
|---|---|---|---|---|
| `roof` | 234 | `0.34, 0.30, 0.27` | **0.90** (156) / **0.93** (76) / 0.88 (2) | every archetype |
| `wall` | 114 | `0.52, 0.44, 0.34` unpainted (94) · `0.88, 0.87, 0.83` whitewash (11) · `0.55, 0.16, 0.13` red (8) · `0.90, 0.89, 0.85` white (1) | 0.75 (79) / 0.85 (35) | `frame_dwelling`, `frame_storefront`, `frame_tavern` |
| `dark` | 114 | `0.07, 0.08, 0.09` | 0.35 (69) / 0.40 (45) | frame + log + fort + palisade |
| `trim` | 104 | derived from the wall paint | 0.85 (69) / 0.80 (35) | `frame_dwelling`, `frame_storefront` |
| `placeholder_opening_dark` | 90 | `0.176, 0.239, 0.200` | 0.70 | `inferred_placeholder` |
| `placeholder_chimney_brick` | 90 | `0.537, 0.314, 0.247` | 0.88 | `inferred_placeholder` |
| `board` | 76 | `0.335, 0.310, 0.268` (69) + painted variants | 0.94 | `outbuilding` |
| `interior` | 76 | `0.072, 0.068, 0.060` | 0.60 | `outbuilding` |
| `timber` | 76 | `0.208, 0.172, 0.128` | 0.90 | `outbuilding` |
| `log` | 53 | `0.340, 0.266, 0.188` (52) · `0.42, 0.33, 0.24` (**1**) | 0.92 (44) / 0.93 (8) / 0.90 (1) | log + fort + palisade + bridge + crib + tavern |
| `chinking` | 50 | `0.700, 0.670, 0.590` | 0.95 | log + fort + outbuilding |
| `glass` | 45 | `0.09, 0.11, 0.13` | 0.25 | `frame_storefront`, `frame_tavern` |
| `placeholder_wall_*` | 90 | six finishes, §1.1 | **0.86**, all six | `inferred_placeholder` |
| `placeholder_roof_*` | 90 | four conditions, §1.1 | **0.90**, all four | `inferred_placeholder` |
| `frame` | 31 | `0.52, 0.44, 0.34` | 0.75 | `log_dwelling` (frame addition) |
| `fill` | 6 | `0.300, 0.295, 0.270` | 0.98 | `bridge_timber`, `pier_crib` |
| `deck` | 4 | `0.47, 0.41, 0.32` | 0.95 | `bridge_timber` |
| `brick` | 3 | `0.47, 0.26, 0.20` | 0.92 | `fort_structure` |
| `earth` | 2 | `0.34, 0.30, 0.22` | 0.92 | `fort_structure` |
| `stone` | 1 | `0.58, 0.56, 0.51` | 0.92 | `fort_structure` |
| `shutter` | 1 | `0.14, 0.32, 0.62` | 0.75 | `frame_dwelling`, `frame_tavern` |
| `sign` | 1 | `0.60, 0.54, 0.44` | 0.85 | `log_dwelling`, `frame_storefront` |
| `terrain_ground` | 1 | `0.36, 0.35, 0.22` | 1.00 | terrain GLB |
| `terrain_water` | 1 | `0.18, 0.24, 0.24` | 0.15 | terrain GLB |

Three readings that fall straight out of the table and are not obvious from the source:

- **`shutter` ships once.** Exactly one record in the dataset states shutters — the
  Sauganash's documented bright blue (`Wau-Bun`) — and the archetypes build shutters only
  where a record attests them. The `green` and `black` entries in `SHUTTER_RGBA` have never
  been used, and the unreferenced slot is dropped at export rather than shipped. The palette
  is not carrying dead weight into the scene.
- **`timber` has two definitions in the source and one in the town.** `outbuilding.py` and
  `frame_storefront.py` each define a `TIMBER_RGBA`, and they are **3.2× apart in linear
  red** — `0.208, 0.172, 0.128` against `0.66, 0.56, 0.40`. Only the outbuilding's ships:
  no storefront in the dataset turns `framing_exposed` on, so the storefront's paler value
  has never been rendered. Two different materials are sharing one name (§4, finding 3).
- **One log wall in Chicago is a different timber from the other 52.** `frame_tavern` alone
  imports `LOG_RGBA` (`0.42, 0.33, 0.24`, roughness 0.90); every other log surface uses
  `logwork.HEWN_RGBA` (`0.340, 0.266, 0.188`, roughness 0.92–0.93). `logwork.py`'s own
  comment says the darker value was chosen deliberately *against* `LOG_RGBA`. The one asset
  affected is the Sauganash's log wing (§4, finding 2).

### 1.1 The placeholder palette — 90 buildings, its own vocabulary

`generators/inferred_placeholder.py` paints the anonymous inferred-infill town. It is **27 %
of the assets** and it shares no colour and no roughness with the archetypes.

| finish (`finish_key`) | hex in source | shipped `baseColorFactor` |
|---|---|---|
| `fresh_timber` (37) | `#C3A478` | `0.765, 0.643, 0.471` |
| `weathered_timber` (19) | `#817D72` | `0.506, 0.490, 0.447` |
| `whitewash` (16) | `#D8D1BC` | `0.847, 0.820, 0.737` |
| `ochre` (7) | `#A98B52` | `0.663, 0.545, 0.322` |
| `mixed_patch` (6) | `#BFAE8E` | `0.749, 0.682, 0.557` |
| `red_oxide` (5) | `#7A4437` | `0.478, 0.267, 0.216` |

| condition (`roof_condition`) | hex | shipped |
|---|---|---|
| `darkened` (26) | `#4B4037` | `0.294, 0.251, 0.216` |
| `patched` (24) | `#3C3732` | `0.235, 0.216, 0.196` |
| `weathered` (22) | `#6C6258` | `0.424, 0.384, 0.345` |
| `fresh` (18) | `#5E4938` | `0.369, 0.286, 0.220` |

**These are the only per-building finish and roof-condition vocabularies the project has**,
they are driven by real record attributes (`finish_key`, `roof_condition` — the latter stated
on 218 records), and **no archetype reads either of them.** A weathered roof and a fresh one
are the same colour on all 244 archetype buildings and different colours on all 90
placeholders. Whichever way W2 goes, this vocabulary is the one to converge on, because it is
the one the *data* already speaks (§4, finding 4).

### 1.2 What is deliberately not in this sheet

The ground, the roads and the water are the only textured surfaces in the scene and they are
**runtime canvases**, not assets: `terrain.js` builds the prairie tile and one more, `streets.js`
builds the street wear, and the water normal drifts. They belong to the terrain program and to
W5, they carry no license question, and W2's atlas must not absorb them — three parcels have
already been burned by treating the ground as a building surface.

---

## 2. The sheet

One row per surface the atlas has to carry. **`selected by`** is the parameter R-W2b makes
name it. **Confidence follows `docs/PROVENANCE.md`'s function, not its spelling**: *attested*
= a source record says so; *inferred* = reasoned from specific committed evidence, with the
reasoning stated; *conjectural* = invented to fill a need, and owed a `docs/LIBERTIES.md` line.

### 2.1 Wall surfaces

| surface | what it is | evidence | confidence | roughness | tile | selected by |
|---|---|---|---|---|---|---|
| **`clapboard`** | riven or sawn horizontal siding, 0.14 m exposed face, butt joints landing on stud lines and staggered course to course | the commonest wall in the town: the Sauganash is "a two-story clapboard block" in the Braunhold engraving and the Kurz & Allison panel (`kurz_allison_1893`); `andreas_1884_v1` has the agency house "clapboarded part way up"; the Green Tree plate in the owner's 2026-08-11 reference set is "two full storeys of pale clapboard" | **attested** for the form, **inferred** for the 0.14 m (a period exposure, already committed as `CLAPBOARD_COURSE_M` in three archetypes) | **0.86 ± variation** — riven oak weathering silver; the variation matters more than the constant (§3) | **4.48 m square, 1024² → 228.6 px/m**; 32 courses of 0.14 m exactly | `cladding: clapboard` (`frame_storefront`; today read by that archetype only) |
| **`board_and_batten`** | vertical boards with a batten over each joint, 0.356 m set-out | `BATTEN_SPACING_M`, already committed as "14 in, the usual set-out" — a typological value, not a reading of any Chicago building | **conjectural** — no source in this repository puts board-and-batten on any named Chicago building in 1835 | 0.88 ± variation | **4.272 m square, 1024² → 239.7 px/m**; 12 battens of 0.356 m | `cladding: board_and_batten` |
| **`vertical_board`** | plain vertical sawn boards, no batten | one record: `recon_1835_south_h2_039`, and its own note says **"INVENTED, NOT DERIVED"**, bounded by `owner_chicago_1835_reconstruction_spec_2026` | **conjectural**, and the record says so | 0.90 ± variation | **4.58 m square, 1024² → 223.6 px/m**; 20 boards of 0.229 m (`SHEATHING_BOARD_M`) | `cladding: vertical_board` |
| **`hewn_log`** | squared log courses, 0.34 m on the course, chinking 0.055 m proud between them | the log town is the best-attested fabric here: `cobweb_castle`, `blacksmith_shop_state_st`, `fort_dearborn_*`, and `docs/research/03-structures-north.md`'s survey | **attested** for the fabric; **inferred** for `COURSE_M = 0.34` (`logwork.py` argues it from a squared log, and states the reasoning) | 0.92 ± variation — weathered oak, coarse | **4.08 m square, 1024² → 251.0 px/m**; 12 courses of 0.34 m exactly | `construction: log` / `hewn_log` |
| **`chinking`** | clay-and-lime between the log courses; **stands proud** and is separate geometry | `logwork.py`'s note; the fabric is universal in the sources | **inferred** — the material is ordinary and unremarked, which is why nothing says it | 0.95, near-uniform — dried lime scatters and does not vary the way timber does | **2.04 m square, 512² → 251.0 px/m** — matches the log's texel density exactly, which is what keeps a wall from reading as two resolutions | emitted with `hewn_log`; not separately selectable |
| **`sawn_board`** | plain sawn stock, random widths 0.18–0.40 m, gappy | `outbuilding.py`'s `BOARD_W_M`; the archetype's docstring argues the gaps | **inferred** | 0.94 ± variation | **4.00 m square, 1024² → 256.0 px/m** — widths are geometry, so the sheet carries grain only | `outbuilding`, board kinds |
| **`whitewash`** | lime wash over any of the above; **it does not replace the substrate, it coats it** | the Green Tree dossier settles the hard case: Gale's "walls, ceilings, and board partitions had evidently received a coat of whitewash" is **interior**, and the record carries `paint: unpainted` and says why | **attested** where a record attests it (9 `wall` slots + 16 placeholders); never a default | 0.90 — chalky, flat, and **the least glossy surface in the town** | **overlay, not a tile** — a whitewash sheet is a value/roughness modifier over the substrate's own rhythm, so the clapboard courses stay visible through it, which is what a limewashed wall actually looks like | `paint: whitewash` |
| **`white_paint`** | lead paint, a remarkable expense here | the Sauganash: "a pretentious white two-story building" (`Wau-Bun`), and the dossier's own reading — *a painted white frame building was remarkable precisely because its neighbours were not* | **attested**, for exactly one building | 0.60 — the only smooth wall in Chicago, and that is the point | overlay, as whitewash | `paint: white` |
| **`red_paint` / `red_oxide`** | iron-oxide paint | 6 archetype slots + 5 placeholders; no named Chicago building in this repository is attested red | **conjectural** at the building level, **inferred** as a period finish | 0.85 ± variation | overlay | `paint: red` / `finish_key: red_oxide` |
| **`brick`** | fired brick, laid in courses | `fort_dearborn_commandants_quarters` (`construction: brick`, inferred bare) and `lake_house_construction` | **attested** that these two are brick; **no source in this repository gives a brick or a course dimension** | 0.90 | **rate unresolvable — see §3.2.** The tile cannot be set until a source gives a brick size | `construction: brick`, and every chimney (§4, finding 1) |
| **`stone`** | rubble or dressed masonry | `chicago_lighthouse_1832`; its own note says bare masonry is **unattested** and whitewash is the commoner Great Lakes finish | **conjectural**, and the record says so | 0.93 | rate unresolvable, as brick | `construction: stone` |
| **`earth`** | trodden ground and turf | `fort_dearborn_parade`, `fort_dearborn_root_house`; both notes say plainly *"No source describes it"* | **inferred**, minimally | 0.95 | 4.00 m noise tile — no rhythm to be integral with | `construction: earth` |

### 2.2 Roof surfaces

> **WIRED IN — see §11 (T-1487, 2026-09-20).** Both rows below are on the sheet now, the
> exposure is **L263**, the dealing rule is `materials.roof_substrate()` and the part of it
> this section does not grade is **L266**. The framing in the next paragraph is what the code
> obeyed for a year and it overstated this section's own gradings; §11.1 is that story.

**This is the sheet's weakest section and the weakness is in the data, not here.** See §4,
finding 1: no record in the dataset states a roof covering, so nothing below can be *selected*
until an attribute exists to select it.

| surface | what it is | evidence | confidence | roughness | tile |
|---|---|---|---|---|---|
| **`shingle`** | riven shingles over board sheeting | **the one direct attestation in the repository**: the North Side school of 1833 is "a frame building twenty-six by thirty-eight feet; twelve-foot posts; **sheeted and shingled roof**" (`docs/RESEARCH/north_side_school_1833.md`) | **attested** for that one building; **inferred** as the ordinary covering of a framed building here | 0.90 ± strong variation — a shingle field is the most legible weathering surface on a building | **exposure is unattested.** At 1024²: tile = 32 × exposure, which holds 228.6 px/m at a 0.14 m exposure. Pick the exposure from a source or record a liberty — do not pick it to make the arithmetic land |
| **`roof_board`** | plain boards weighted or nailed, no shingle field | `outbuilding.py` argues it explicitly: *"a shingle field on an outbuilding would be claiming a finish"* | **inferred**, and well argued | 0.93 (corrected in §11.2 — 0.94 was `sawn_board`'s; 0.93 is what all 130 outbuilding roofs have always shipped) | as `sawn_board`, 4.00 m |
| **`bark` / `puncheon`** | — | **not modelled and not evidenced.** Named here only so the next reader knows it was looked for and not found | — | — | — |

~~Today all three are one material at one colour: `roof`, `0.34, 0.30, 0.27`. The board roof is
separated from the shingle roof by **0.03 of roughness and nothing else** — same colour, same
name, in the shipped bytes.~~ **No longer true of the name, T-1487**: the 0.03 of roughness is
unchanged and deliberately so (§11.2), but the two are now separate rows dealt by a written
rule, and the material slots are named `roof_shingle` and `roof_board`. Still true of the
COLOUR, which is the weathering condition's and not the covering's.

### 2.3 Everything else

| surface | roughness | notes |
|---|---|---|
| `glass` | 0.25 | the only sub-0.5 surface on a building. Muntins, sash and reveal are geometry and belong to **R-W3c**, not to this atlas |
| `dark` (openings, interiors seen through) | 0.35 / 0.40 / 0.60 / 0.70 | **four different values for one idea across four generators.** Not a texture; a convergence job for R-W2b |

**CORRECTED 2026-08-24 (T-0126) — the row above says four and three ship.** The fourth,
`placeholder_opening_dark` at 0.70, belongs to a generator that now paints no committed asset,
so it was never a surface anyone could see. Both rows are converged and wired in **§7**, which
re-measures the whole family before choosing: one `dark` row at `0.072, 0.068, 0.060` / 0.60,
and `glass` brought onto the sheet at exactly the value it already shipped.
| `trim`, `sign` | 0.80–0.85 | trim is derived from the wall paint and needs no sheet of its own; `sign` is one board and L25 governs what may be on it |
| `deck`, `fill` | 0.95 / 0.98 | bridge and crib; `fill` is river stone and gravel and is the roughest surface in the town |
| `terrain_ground`, `terrain_water` | 1.00 / 0.15 | out of scope, §1.2 |

---

## 3. Roughness, texel density, and where the pixels come from

### 3.1 The roughness reading, corrected

**R-G1's scored note — "there is no roughness variation anywhere" — is right about the thing
that matters and wrong as literally written, and the difference decides what W2 builds.**

Between surfaces there is already a great deal of variation: **18 distinct roughness values**
ship, spanning 0.15 to 1.00, and they are argued in the source rather than guessed. What does
not exist anywhere in the town is variation **within** a surface — every square metre of every
wall has exactly one roughness. That is what makes nothing read as painted, weathered or wet,
because weathering is by definition uneven.

**So the deliverable is a roughness *map*, not a better roughness constant**, and R-W2b should
not spend a round re-tuning the 18 numbers. The `± variation` in §2 is the map's job: the
constant is the mean, and the sheet's per-surface amplitude is what the atlas paints.

Every roughness number in §2 is **reasoned, not sourced**. No source this project holds
measures the gloss of anything, and none ever will. They are `conjectural` in the strict sense
and the sheet says so here once rather than repeating it in every row — but the *substrate*
each one belongs to is often attested, and that is the part provenance is protecting.

### 3.2 Texel density

§4 W2 sets **128–256 px/m**, inspection distance arm's length. Every tile in §2 is sized so
that it (a) lands inside that band and (b) is a **whole number of the surface's own committed
module** — 32 clapboard courses, 12 log courses, 20 sheathing boards. That second condition is
what stops the seam being visible, and it is why the tile sizes are odd numbers of metres
rather than round ones.

Two surfaces cannot be sized: **brick and stone**. Their rhythm is a brick dimension, this
repository holds no source that gives one for Chicago in 1835, and choosing one to make the
arithmetic land would be exactly the invention `docs/LIBERTIES.md` exists to catch. Leave them
untiled or record the liberty; do not quietly pick a modern brick.

### 3.3 Where the pixels come from — the licensing answer, decided here

**Generate them; do not photograph them.** AGENTS rule 6 and `assets/LICENSES.md` gate this
hard, and the arithmetic is not close:

- **38 of this project's 65 sources are `rights_status: check_required`** and may be cited in
  text but must not have an asset derived from them. Every `chicagology_*` record is in that
  set, and that is most of the visual material.
- The one photograph committed at full resolution — `saari_2018_dupage_tallgrass` — is CC
  BY-SA 4.0, cleared for **verbatim redistribution and measurement and explicitly not for any
  derived asset**. `assets/LICENSES.md` spells out that a tile built from it is an adaptation
  carrying ShareAlike. It is also a prairie, not a wall.
- **The one set that could inform materials is rights-gated for exactly this.**
  `data/sources/assets/prefire_views_kevin_2026_08/` — twelve retrospective views supplied by
  the owner as the accuracy bar — states in its own README that it "may drive massing, roof
  form, fenestration rhythm, **materials** and setting as `inferred`". It is also mostly
  `chicagology_*`, which `assets/LICENSES.md` gates `check_required`: **cite it, read it, do
  not derive a tile from it.** That is not a loophole to route around; it is the distinction
  between evidence and pixels, and this sheet is on the evidence side of it.
- No source in `data/sources/` is a photograph of an 1830s Chicago building surface. There is
  no such photograph; the town burned in 1871 and photography arrived after these buildings.

So the atlas should be **procedurally generated from the dimensional constants in §2**, which
the generators already commit and which are themselves sourced or argued. That route needs no
new `assets/LICENSES.md` clearance beyond a row saying the tiles are generated output covered
by the project's own license — and it has the property this project actually cares about: a
visitor can be told exactly which numbers the wall was drawn from.

### 3.4 State the colour space on every value — this sheet's one process rule

The two generator paths express colour differently and **neither module states which space it
is in**. `logwork.py` says its values are linear; `inferred_placeholder.py` writes hex strings
straight into `baseColorFactor`, which glTF defines as linear, and hex notation conventionally
means sRGB.

**This sheet does not claim a bug, because the evidence points the other way.** The one finish
both paths name is whitewash: the archetype's linear `0.88, 0.87, 0.83` against the
placeholder's shipped `0.847, 0.820, 0.737` — a 12.6 % gap in blue. Read the placeholder hexes
as sRGB instead and they would ship at `0.687, 0.638, 0.503`, a 40 % gap. The hexes were
evidently chosen as linear values, and the town is consistent.

But it is consistent by luck of authorship and not by anything written down, and an atlas is
where that stops being survivable: a PNG *is* sRGB-encoded by convention, so the sheet and the
factor it multiplies will be in two different spaces unless someone says so. **Every colour
value W2 produces states its space, in the file that holds it.**

---

## 4. Findings

Five things found while inventorying, none of them patched here.

**1 — The chimney is not a material in this project.** `frame_dwelling`, `frame_storefront`
and `log_dwelling` all build their stacks with `M_ROOF`: **219 chimney stacks on 199
buildings are painted with the roof's colour**, `0.34, 0.30, 0.27` at roughness 0.90. The 90
placeholder buildings, meanwhile, ship a real `placeholder_chimney_brick` at `0.537, 0.314,
0.247`. So the town has a brick chimney material, and the 199 buildings built from archetypes
do not use it. It is worse than a palette slip: `log_dwelling`'s own docstring argues at
length that a frontier stack is *stick-and-clay or fieldstone* built outside the gable so it
can be pulled down when it catches fire — a materially different object from a framed house's
brick stack — and the two render identically, as roof. Opened as **R-W2c**.

**2 — One log wall in Chicago is a different timber from the other 52.** `frame_tavern` alone
imports `LOG_RGBA` (`0.42, 0.33, 0.24`, roughness 0.90); everything else uses `HEWN_RGBA`
(`0.340, 0.266, 0.188`, roughness 0.92–0.93), which `logwork.py` says it made ~20 % darker on
purpose, having measured that a first pass at 0.295 "put the log dwellings visibly in a
different town from the Sauganash's wing". The reconciliation went one way and the Sauganash
did not follow. One asset is affected — the Sauganash's log wing, the single most-looked-at
building in the scene, and the station `sauganash` stands in front of it.

**3 — `timber` is one name over two materials 3.2× apart.** `outbuilding.py`'s
`0.208, 0.172, 0.128` ("heavy timber holds moisture, weathers darker") and
`frame_storefront.py`'s `0.66, 0.56, 0.40` ("fresh sawn lumber, paler than a wall") are both
defensible and are not the same thing. Only the outbuilding's ships — no record turns
`framing_exposed` on — so this is latent rather than visible, and it will surface the first
time a storefront exposes its framing beside a shed. R-W2b should give them two names.
**DISCHARGED 2026-08-24 by T-0126 — §7.4.** Two rows, `heavy_timber` and `sawn_framing`, and
both material slots renamed so the name in the shipped GLB says which one it is. No value moved.

**4 — The data speaks a finish vocabulary that no archetype reads.**
`roof_condition` is stated on **218 records** and `finish_key` drives six wall finishes, and
both are read only by `inferred_placeholder`. On all 244 archetype buildings a weathered roof
and a fresh one are the same pixel. Separately, `cladding` is stated on **27** records and
read on **22** — `frame_storefront`'s. The three taverns and two log dwellings that state a
cladding state it into nothing, and one of those five is the sharpest material attestation in
the dataset: `cobweb_castle` carries `cladding: clapboard_part_way_up`, **`attested`**, sourced
to `andreas_1884_v1` — *"the agency-house being afterward clapboarded part way up"*, David
McKee's recollection. **A documented fact about a real building's surface is committed, correct,
and rendered by nothing**, and the value is not even in `CLADDINGS`. That single record is the
best argument in the repository for why W2 is worth doing.

**5 — 27 % of the town is painted by a generator with no shared palette.** The 90 inferred
placeholders share not one colour and not one roughness with the 244 archetype assets: their
walls are all roughness 0.86, a value that appears nowhere else; their roofs are 0.90 at four
colours the archetypes do not have. Any atlas that textures the archetypes and not the
placeholders will split the town visibly in half, and the placeholders are the anonymous
background buildings — the ones that *make* the town read as a town. Whatever W2 builds must
cover both paths, and §1.1's vocabulary is the one to converge on because the records already
carry it.

---

## 5. What this sheet does not settle

- **The shingle exposure**, and therefore the roof tile — §2.2. It needs a source or a liberty.
- **Brick and stone course dimensions** — §3.2. Same.
- **Which way finding 1 should go**: give the archetypes the placeholder's brick, or model the
  stick-and-clay stack `log_dwelling` argues for. That is a research question about frontier
  chimneys, not a palette question, and R-W2c should open with it.
- **Whether `roof_covering` is a new attribute or a widening of `cladding`.** It is a schema
  change either way and it touches 315 records, so it is a parcel, not a footnote.

Nothing above was derived from a source this repository does not hold, and no confidence was
raised to make a row look finished.

---

## 6. WIRED IN — T-0007, 2026-08-21

**Everything above §6 is R-W2a's document and is left exactly as it was written.** This
section is the record of the parcel that made it reach the town: `generators/common/materials.py`
is this sheet as code, and every wall, roof, log, chinking and heavy-timber surface in the
shipped GLBs now takes its colour and its roughness from a row of it.

### 6.1 The mechanism

A surface is **a substrate times a finish**, which is the shape §2.1 already argued when it
called whitewash, lead paint and iron oxide "overlay, not a tile":

- a **substrate** owns the roughness, the tile and the module the tile is a whole number of —
  clapboard 0.86 / 4.48 m / 32 courses, hewn log 0.92 / 4.08 m / 12 courses, sawn board 0.94 /
  4.00 m, brick and stone with `tile_m = None` because §3.2 says the rate cannot be set;
- a **finish** owns the colour, and the three coatings own a roughness too and override the
  substrate's — limewash 0.90, lead paint 0.60, iron oxide 0.85.

`resolve(substrate, finish)` returns the pair the exporter needs, and the tile rates sit beside
it unused for now, waiting for the bake half to draw an atlas against the same numbers rather
than against a second set.

### 6.2 What now selects a surface — the "selected by" column, answered

| what the record says | where it lives | what it now drives | how many records |
|---|---|---|---|
| `reconstruction.finish_key` | the 665-roof programme's block | the wall colour on every archetype building | **222** |
| `reconstruction.roof_condition` | the same | the roof colour on every archetype building | **218** |
| `form.paint` | the phase | a stated coating, which outranks the dealt finish | 44 + the Sauganash |
| `form.cladding` | the phase | the wall substrate, so its roughness | 27 stated, 22 read |
| `form.construction` | the phase | the substrate where no cladding is stated | every record |

`from_phase` takes the **record** as well as the phase from this parcel on, because
`finish_key` and `roof_condition` are not form attributes — they sit one level up, in
`reconstruction`, which is why no archetype could read them. `generators/mesh_inputs.py` passes
the same pair, so the staleness hash still sees exactly what the builder sees.

### 6.3 Which findings this discharges, and which it does not

- **Finding 4 — the data spoke a vocabulary no archetype read: DISCHARGED.** On the 244
  archetype buildings a weathered roof and a fresh one were the same pixel and every unpainted
  wall in Chicago was one tone. 222 records were carrying a finish into nothing; they now paint
  the building.
- **Finding 5 — two palettes with nothing in common: DISCHARGED.** Both generators read one
  table. The convergence went the way this sheet said it should — onto §1.1's vocabulary,
  because it is the one the records speak — so the placeholder GLBs are byte-identical and it
  is the archetypes that moved. Three whitewashes became one (the frame archetypes' 0.88/0.87/
  0.83, `fort_structure`'s undocumented 0.86/0.85/0.80 and the placeholder's 0.847/0.820/0.737);
  two reds became one.
- **Finding 2 — one log wall in Chicago was a different timber: DISCHARGED.** `frame_tavern`
  was the last importer of the paler hewn-log value; `LOG_RGBA` is deleted and the Sauganash's
  wing is built from the town's log, in front of the station named after it.
- **Finding 1 — the chimney is not a material here: NOT TOUCHED.** It is its own ticket
  (T-0008) and it opens with a research question about frontier chimneys, not a palette.
- **Finding 3 — `timber` is one name over two materials: NOT TOUCHED**, and now recorded on the
  sheet's `heavy_timber` row so the next reader meets it. Split out as **T-0126** with the §2.3
  convergence below.
- **§3.1's roughness MAP: NOT BUILT, and deliberately.** The sheet says the deliverable is a
  map and not better constants, and a map is a texture: it belongs to the bake half. What this
  parcel could honestly ship is the *between-surface* variation the sheet already argued,
  applied per record — which is why a limewashed wall, a lead-painted one, a log wall and a
  weathered board wall are now four different roughnesses instead of two.
- **§2.3's four values for one dark opening: NOT TOUCHED.** It is the openings-and-glazing
  family, not the wall-and-roof family this parcel wired, and it is **T-0126** rather than
  half-done here.

### 6.4 The covering half is still honest

**R-W2a finding 2 stands and nothing here contradicts it.** No source in this repository states
what any Chicago roof of 1835 was covered with, so `generators/common/materials.py` has no
`shingle` row and no `roof_board` row. What it has is one `roof_plane` substrate whose own note
says the covering is unstated, and four **weathering conditions** — the vocabulary 218 records
actually carry. A roof that is `darkened` is a claim about weather, not about material. The
roughness of every roof in the town is still each archetype's own committed literal, left alone
on purpose: §2.2 separates a board roof from a shingle field by 0.03 of roughness, and moving
that number either way would be choosing a covering nobody wrote down.

The shingle exposure, the brick course and the stone course are all still open, all still §5's,
and all still unresolvable from what this project holds.

---

## 7. WIRED IN — T-0126, 2026-08-24: the openings-and-glazing half

**§§1–5 are R-W2a's document and stay as written; §6 is T-0007's.** This section is the
parcel that closed the family T-0007 deliberately left — §2.3's dark openings and the
glazing beside them — and **finding 3**, the one name over two timbers.

### 7.1 THE COUNT WAS RE-MEASURED FIRST, AND §2.3'S "FOUR VALUES" IS NOW THREE

§2.3 was written on 2026-08-16 against four values on four generators. Re-measured over
`assets/gltf/**/*.glb` on 2026-08-24, before anything was chosen, **three** ship:

| shipped material | base colour | roughness | slots | emitted by |
|---|---|---|---|---|
| `dark` | `0.070, 0.080, 0.090` | **0.35** | 112 | `frame_dwelling` |
| `dark` | `0.070, 0.080, 0.090` | **0.40** | 58 | `log_dwelling`, `fort_structure`, `palisade` |
| `interior` | `0.072, 0.068, 0.060` | **0.60** | 117 | `outbuilding` |
| `glass` | `0.09, 0.11, 0.13` | 0.25 | 48 | `frame_storefront`, `frame_tavern` |

**The fourth value ships on nothing.** `placeholder_opening_dark` (`#2D3D33` at 0.70) belongs
to `generators/inferred_placeholder.py`, and that generator now paints no committed asset:
`--check` reports *"verified 0 flagged placeholder GLBs; 226 superseded by a canonical bake"*.
The 90 pure-Python massings §1.1 and finding 5 are written about have been replaced by real
archetype bakes, so the greenish opening colour — the one value of the four that nothing in
this repository argues for, and the only one that is not a near-black — was **dead code, not a
surface a visitor could see.** §1's whole census is stale in the same direction and by the same
cause: **334 assets have become 344 and 1,353 material slots have become 1,628**, `roof`'s 234
slots have become **334**, the 32 distinct material names have become **22**, and there is no
`placeholder_*` material left in the tree at all. **§1 is not rewritten** — it is a dated
measurement and this project does not restate history — but no parcel should quote its counts
again without re-measuring, which is the correction R-W2a's own preamble asks for.

Two further readings fell out of the same measurement and both are recorded rather than acted
on, because acting on either adds a material and the count is the constraint (§7.4):

- **`dark` is not only openings.** It also paints the fort's sun-dial plate and the 1832
  lighthouse's lantern drum, `log_dwelling`'s iron sign-hinge straps, and the stockade gate's
  two shut leaves. All are dark and small; none is an opening. They ride on the row and its
  note says so.
- **A glazed sash and an open bay are the same material on 112 buildings.** Every window
  `frame_dwelling` builds is sized off the Green Tree's attested 6 × 8 in lights, so those
  panels stand for glazing — but the archetype paints its doors from the same slot, and
  `frame_storefront` meanwhile paints its windows from `glass`. Splitting a dwelling's windows
  onto `glass` is a real parcel and it costs one material on 112 assets. It is not this one.

### 7.2 WHAT THE SOURCES SAY ABOUT GLASS, MEASURED

**The word "glass" appears in no source this repository holds.** Two records reach the glazing
at all, and both are `inferred`:

- **`green_tree_tavern.form.fenestration = small_paned_sash`**, sourced to
  `chicagology_prefire127` — Edwin O. Gale on a guest chamber *"about 12x12, with two windows
  6x8"*. That is the **one attested pane size in the dataset**, and it is the number
  `frame_dwelling` sizes every window in the town from (`WIN_W_M`, four lights across and three
  high per sash).
- **`sauganash_hotel`**, `trowbridge_sauganash_hotel` — the plate carries *louvred shutters
  flanking every window of the clapboard block*, i.e. shutters **on the sash**.

So *that* the town was glazed in small lights is inferred and reasonably held. **What colour a
pane reads at fifty metres is stated nowhere**, and `glass` is graded `reconstructed` on the
sheet accordingly. The value itself is untouched: both its generators already agreed on
`0.09, 0.11, 0.13` at 0.25 across all 48 slots, so this parcel **brings it onto the sheet
rather than re-arguing it** — §2.3 asked for it to be carried across, not rewritten.

### 7.3 ONE `DARK` — the colour read, and the roughness bounded

**Colour: the warm near-black wins, and the reason is that the cool one is a claim about sky.**
The two shipped colours are 0.030 apart at their widest (blue) and 0.002 at their narrowest
(red), so this is a convergence and not a repaint. The sheet takes `0.072, 0.068, 0.060` — the
117 slots that already carried it — and retires `0.070, 0.080, 0.090` from the other 170.
Light that reaches an unlit room in this town has bounced off timber and lime, so it comes back
warm; a cool cast in an opening is **sky reflected in a pane**, and sky in an opening is what
`glass` is for. Keeping both hues on one idea kept the only real distinction in the family
pointing at nothing. Near-black rather than black, as the row has always said: an interior in
daylight is dark, not a hole in the world.

**Roughness: 0.60, and it is BOUNDED between two values this project already ships.** This is
the half a visitor sees, because roughness decides whether a surface catches the sun — and a
doorway on a frame dwelling glinted while the identical doorway on the shed beside it did not.

- It **cannot sit at `glass`'s 0.25**, because **every one of the 287 slots** carries surfaces
  that are certainly not glazed — doorways, gaps between boards, open bays, loopholes, gable
  vents, the stockade's two shut gate leaves. At a glazing gloss an open bay takes the same sun
  glint a shop window does, which is the defect, not the fix.
- It **cannot sit at the bare fabrics behind it** — `heavy_timber` 0.90, `hewn_log` 0.92,
  `sawn_board` 0.94 — because **156 of the 287 also carry windows** (112 frame dwellings, 44 log
  cabins), and on the frame dwellings every window is sized off the Green Tree's attested 6 × 8
  in lights, so those panels stand for glazed sash. A sash with no specular at all reads as a
  hole knocked in the wall.

- **Nothing states where between the two it sits**, so it sits at **the midpoint, 0.575**, taken
  to **0.60** — the value the town already speaks, on 117 slots — rather than to a newly invented
  0.575 that would mean the same thing 0.025 away. `renderers/web/js/buildings.js` records that
  nothing in this dataset uses two roughness values closer than 0.01, and adding a second number
  for one idea is the fault this parcel exists to remove.

The bounds are stated by SLOT and by what the slot actually paints, rather than as a clean
percentage, because **no slot in this family is purely one or the other**: `frame_dwelling`
paints its doors and its windows from one slot, and `log_dwelling` paints a door, its windows
and a gable vent from one. The exact census, by archetype — `outbuilding` 117, `frame_dwelling`
112, `log_dwelling` 44, `fort_structure` 13, `palisade` 1, and no other asset carries the slot
(the garrison garden's fence is a `palisade` build with no gate, so it has none). The slots
carrying nothing that could be glazed are the outbuildings' 117, the stockade's 1, and 12 of the
fort's 13 — the thirteenth is the 1832 lighthouse, whose lantern drum is a glazed surface riding
on this row. What the two bounds establish is that the value belongs strictly between them.

Graded **`reconstructed`**, which is a DOWNGRADE from the `inferred` the old `interior_dark` row
carried, and deliberate: no source states any of it, and a row that is reasoned from physics
rather than from evidence about these particular buildings is not an inference about them.
`docs/LIBERTIES.md` **L182** owns it.

### 7.4 FINDING 3 DISCHARGED — `timber` becomes two names

`outbuilding.py`'s `0.208, 0.172, 0.128` (weathered heavy squared stock, roughness 0.90) and
`frame_storefront.py`'s `0.66, 0.56, 0.40` (fresh sawn mill framing, roughness 0.92) are two
materials **3.2× apart in linear red** that shared one name. Re-measured: the outbuilding's
ships on **117** slots and the storefront's on **zero**, exactly as the finding said — no record
in this dataset turns `framing_exposed` on, so the collision was latent and would have surfaced
the first time a storefront exposed its frame beside a shed.

Two rows, `HEAVY_TIMBER` and `SAWN_FRAMING`, and **the material slots are renamed to match** so
the name in the shipped GLB says which of the two it is: `outbuilding`'s `timber` → `heavy_timber`,
`frame_storefront`'s `timber` → `sawn_framing`, and `outbuilding`'s `interior` → `dark`. **No
value moves in either row.** `SAWN_FRAMING` is regraded `reconstructed` from the shared row's
`inferred`, because a value that has never been rendered has no building it is an inference about.

### 7.5 THE COUNT DID NOT MOVE, AND THAT WAS THE CONSTRAINT

ROADMAP K36(a) is why every choice above is a rename or a value and never an addition: a palette
pass folds an asset at five materials and leaves four alone, and the town sits on that line.
Measured before and after over all 344 masters, each file against its own committed blob:

| | before | after |
|---|---|---|
| material-count histogram | 1×2, 2×3, 3×6, 4×125, 5×148, 6×59, 8×1 | **identical** |
| material slots | 1,628 | **1,628** |
| triangles | 484,903 | **484,903** |
| assets whose material count moved | — | **0** |
| assets whose triangle count moved | — | **0** |

### 7.6 WHICH ASSETS MOVED, AND WHY EACH ONE DID

**287 of the 344 masters changed and 57 re-derived BYTE FOR BYTE**, and the split is not a
guess — every changed file was diffed against its own committed blob and its difference named:

| assets | what actually differs | |
|---|---|---|
| **117** | material RENAMED `interior` → `dark` and `timber` → `heavy_timber` | `outbuilding` — **no value moves at all** |
| **112** | `dark`: `0.07, 0.08, 0.09` → `0.072, 0.068, 0.060`, roughness **0.35 → 0.60** | `frame_dwelling` |
| **58** | `dark`: `0.07, 0.08, 0.09` → `0.072, 0.068, 0.060`, roughness **0.40 → 0.60** | `log_dwelling` 44, `fort_structure` 13, `palisade` 1 |
| **0** | *bytes moved with no nameable material difference* | — |
| **0** | *triangle count moved* | — |

**287 is exactly the number of assets carrying the `dark` slot**, measured before anything was
chosen (§7.1), so the blast radius is the family and not a hash wave. The determinism promise is
what proves it: **the 57 that re-derive byte for byte** are `frame_storefront` 38 (its
`timber` → `sawn_framing` rename touches a slot that is UNREFERENCED and dropped at export, so
the shipped bytes cannot move), `frame_tavern` 10 (its `glass` came onto the sheet at exactly
the value it already had), `bridge_timber` 4, `pier_crib` 2, the 2 terrain meshes, and **1
`palisade`** — the garrison garden fence, a palisade build with no gate and therefore no `dark`
slot at all. That last one is the control: a windowless, doorless, gateless object in the family's
own archetype, and its bytes did not move.

Stated the other way, for the reader checking for a leak: **no asset without a `dark` slot
changed, and no asset with one failed to.**

And the family itself, by slot: `dark` 0.070/0.080/0.090 at 0.35 (112) and at 0.40 (58) and
`interior` 0.072/0.068/0.060 at 0.60 (117) → **one `dark` at 0.072/0.068/0.060 / 0.60, 287
slots**; `timber` (117) → `heavy_timber` (117) with `sawn_framing` still at 0; `glass` 48,
untouched. Renaming a slot is free. Adding one tips the whole town at once, and nothing here
adds one.

**What the town DOES lose is two roughness values, and the gate that watches for that is named
here rather than left to be discovered.** `tools/smoke_renderer.mjs` holds the merged building
batch to `ROUGHNESS_VALUES_MIN = 12` distinct per-vertex roughness values — the assertion that
catches a merge which buys draw calls by throwing the town's finishes away. Converging 0.35 and
0.40 onto 0.60 takes the batch from **17 distinct values to 15**. The measured run reports
`batches: 1 · roughness 15 values 0.25–0.98`, so the margin over the floor narrows from five to
three. **The floor was not touched** — it is a real assertion about a real risk and weakening it
to make room would be the exact move this project refuses. It is recorded because the next parcel
that converges two roughnesses should know the margin it is spending.

---

## 8. WIRED IN — T-0138, 2026-08-28: the chimney, and the last local literal

**§§1–5 are R-W2a's document and stay as written; §6 is T-0007's and §7 is T-0126's.** This
section closes the last row `inferred_placeholder.py` still painted from a number of its own.

### 8.1 THE SPLIT, IN ONE LINE

`placeholder_chimney_brick` shipped at `#89503F` — `0.537, 0.314, 0.247` linear, roughness
0.88 — written in `generators/inferred_placeholder.py` and read nowhere else. T-0008 gave the
112 brick stacks on the archetype buildings the sheet's `CHIMNEY_BRICK` at `0.45, 0.23, 0.17`,
roughness 0.85. **About 20 % apart in linear red, on buildings standing on the same streets.**
That is finding 5's complaint — a generator with no shared palette — surviving the parcel that
was supposed to end it, and `docs/RESEARCH/chimneys.md` §4 named it as deliberately left alone.

### 8.2 WHICH VALUE SURVIVES, ARGUED RATHER THAN PICKED

The two are not symmetrical and the convergence is not a midpoint.

| | `#89503F` | `CHIMNEY_BRICK` |
|---|---|---|
| linear rgb | `0.537, 0.314, 0.247` | `0.45, 0.23, 0.17` |
| roughness | 0.88 | 0.85 |
| tier | none stated | `inferred` |
| what argues for it | **nothing in this repository** | `frame_tavern`'s committed `BRICK_RGBA`, read off the Petford watercolour of the Sauganash (T-0092, **L154**) — the one coloured witness to any Chicago chimney — generalised to the town's other framed stacks on the town's own warrant, Blodgett's North Side brick-yard, spring 1833 |

**An `inferred` value carrying a source beats an undocumented literal**, so the literal goes and
nothing about the brick itself is re-argued here. No new number enters the sheet; one leaves the
generator. `CHIMNEY_BRICK`'s own reasoning is `chimneys.md` §2 and is untouched.

### 8.3 THE SELECTOR, NOT THE ROW

The generator now asks `materials.chimney_finish("interior")` rather than naming
`CHIMNEY_BRICK`. The sheet owns the CHOICE as well as the colour (§6.2), and `interior` is what
this generator actually builds: a box inside the footprint depth, rising through the roof — the
framed house's masonry flue. Asked the question rather than told the answer, a placeholder
cannot drift from the archetypes again by pointing at a row that has since moved.

**What it does not do.** A log dwelling's placeholder keeps a brick stack. §3's stick-and-clay
daub belongs to a stack standing OUTSIDE the gable, and the placeholder's massing puts every
stack inside the roof — so claiming the daub would put the right fabric on the wrong silhouette.
That is the placeholder's geometry, not its palette, and it is left alone with the reason said.

### 8.4 THE BYTE CHANGE THE TICKET ASKED FOR DOES NOT EXIST ANY MORE

T-0138 was written on 2026-08-22 against "90 committed masters", and asked for them, their
compressed derivatives and the banked passthrough set to be regenerated in the same commit
(K38, `--write-baseline`). **Re-measured before anything was edited, there are none:**

| measurement, 2026-08-28, on `dev` | reading |
|---|---|
| `python3 generators/inferred_placeholder.py --check` | `0 flagged placeholder GLBs; 230 superseded by a canonical bake` |
| manifest entries with `kind: placeholder` | **0** of 349 |
| committed GLBs under `assets/` containing `placeholder_chimney_brick` | **0** |

So no master moved, no derivative moved, the passthrough baseline did not need re-banking, and
**no building repaints.** This is T-0126's shape exactly (§7): the divergence is closed at the
source so it cannot walk back in the day a record outruns the bake and a placeholder is emitted
again. §1.1's table and finding 5's "27 % of the town" are R-W2a's 2026-08-16 census and stay as
written; the town they measured has since been baked out from under them.

The roughness reading of §3.1 and the batch count §7 closes on are unaffected for the same reason —
0.88 → 0.85 moves no shipped slot, because no shipped slot is this generator's.

---

## 9. WIRED IN — T-0267, 2026-08-29: the fort's wall brick, and the last split brick in the town

**§8 closed the last brick a *generator* painted from a number of its own. This closes the last
one an *archetype* did** — and it is the one a visitor could actually see, because unlike §8's
placeholder it painted three committed masters.

### 9.1 THE SPLIT, IN ONE LINE

`generators/archetypes/fort_structure.py::WALL_RGBA["brick"]` shipped at **0.47 / 0.26 / 0.20**
linear. The sheet's one brick — `common/materials.py::CHIMNEY_BRICK`, read off the Petford
watercolour and moved into the sheet by T-0008 so that there would be exactly one — is
**0.45 / 0.23 / 0.17**. **About 13 % apart in linear green and 18 % in blue.** That is §1's
finding 5 again, one archetype further in: a town painted by generators sharing no palette.

Nothing in this repository argued the 0.47/0.26/0.20. It has no tier, no source and no note; it
is the shape of constant §8.2 refused, and it is refused here for the same reason.

### 9.2 WHAT WAS ACTUALLY IN QUESTION, AND IT IS NOT THE NUMBER

T-0267 asked the real question rather than the arithmetic one: **should the fort's 1816 brick be
the town's 1833 brick at all?** There is a case that it should not — different clay, a different
decade, a wall rather than a flue — and §4 of `chimneys.md` had once excluded the garrison on
exactly that ground, because 1816 is seventeen years before Blodgett's brick-yard.

**`chimneys.md` §6 answered it for the stacks and the answer carries here unchanged.** Brick is
attested *inside* the fort, twice and independently — Hubbard in 1827 on "the brick building,
just within the north stockade" and "the magazine, of brick", and the 1855 key on the same
quarters — so the fort needed no yard in town and nothing about its masonry has to be invented.
What the fort has never had is a **colour**: nothing in this repository shows the tone of any
fort surface. The only coloured witness to any Chicago brick is the Petford watercolour, and the
sheet already holds it.

So the choice was between one brick with a witness and two bricks where the second one's colour
would be invented to express a difference no source states. **The town takes one brick.**

The sheet's §2.1 row had already said so: it names its selectors as `construction: brick` **and
every chimney**. A wall reading that row is the row doing the job it was written for.

### 9.3 WHAT IS NOT CLAIMED

- **Not that the two bricks matched.** This is convergence onto the one witnessed value, not a
  finding about 1816 clay. If a coloured witness to the fort's own brick is ever read, the sheet
  grows a second row and this section is what it argues against.
- **Not a new number.** Nothing enters the sheet; one leaves an archetype. `CHIMNEY_BRICK`'s own
  reasoning is `chimneys.md` §2 and is untouched.
- **Not a roughness change.** A bare brick wall already took the **`brick` substrate's 0.90**
  through `materials.resolve`, and still does. `CHIMNEY_BRICK`'s 0.85 is a coating's stated gloss
  and reaches no wall — the colour is shared, the gloss is not.
- **Not a claim about the Lake House's finish.** `lake_house_construction` is a 1835 shell under
  construction and repaints with the other two because its record says `construction: brick`.

### 9.4 THE BYTE CHANGE, MEASURED

`fort_structure.py` is in every one of its archetype's input hashes, so all **14** masters restaled
and all 14 were rebuilt. **Three moved:**

| master | bytes | what changed |
|---|---|---|
| `fort_dearborn_commandants_quarters__brick_1816.glb` | 14,680 → 14,684 | `brick` baseColorFactor |
| `fort_dearborn_magazine__brick_1816.glb` | 6,236 → 6,236 | `brick` baseColorFactor |
| `lake_house_construction__shell_1835.glb` | 5,620 → 5,620 | `brick` baseColorFactor |

The other eleven rebuilt **byte for byte identical** — a comment and a constant lookup moved, and
nothing that reaches a vertex did. That is the staleness rule working as designed rather than a
wave of churn: the hash restaled 14 because it hashes the module, and the bytes proved only three
of them had anything to change.

### 9.5 WHAT IS LEFT, AND IT IS FILED

The sheet's one brick is still called **`chimney_brick`**, and a wall now reads it. That name is
now wrong by one surface, and renaming it — or growing the sheet a `wall_finish`-style selector
that answers *"what colour is a bare brick wall"* the way §8.3 made the placeholder ask rather
than name — is a `common/materials.py` change, which is in **every** asset's input hash and
therefore costs a town-wide bake. It is not worth one on its own and it is filed as **T-0332**. **CLOSED by §10.**

---

## 10. WIRED IN — T-0332, 2026-09-13: the row is named for the fabric, and the surfaces ask

### 10.1 THE DEFECT, IN ONE LINE

`CHIMNEY_BRICK` was named in T-0008, when a stack was the only thing in this town made of brick.
By the end of §9 the row was read by **three** committed masters and a fourth surface, and only
one of those is a chimney:

| reader | surface | since |
|---|---|---|
| `fort_structure.WALL_RGBA["brick"]` | the fort commandant's quarters, the magazine, the Lake House shell — attested brick **WALLS** | T-0267, §9 |
| `frame_tavern.BRICK_RGBA` | the Sauganash's stacks — a chimney | T-0092 / T-0008 |
| `materials.chimney_finish("interior")` | every framed house's stack | T-0008 |

A sheet row is a statement about a FABRIC. Named for one of the surfaces that wears it, it
misdescribes the other two, and §9.5 filed exactly that.

### 10.2 WHAT CHANGED, AND IT IS BOTH HALVES OF THE TICKET

1. **The row is `BRICK`** (`key="brick"`), and its note now says out loud that it is the town's
   one brick on a chimney and on a wall alike, and that reading it at the fort is not a claim
   that 1816 brick matched 1833 brick — it is the only brick this project has argued.
   **No alias is kept.** Three call sites is not a compatibility surface, and a sheet carrying
   two names for one row is the drift the rename exists to end.
2. **The surfaces ASK.** §8.3's move, made for the wall: a new `materials.wall_colour(construction)`
   answers *"what colour is a bare wall of this fabric"*, `fort_structure` calls it instead of
   naming the row, and `frame_tavern` calls `chimney_finish("interior")` — the disposition it
   actually builds — instead of naming it either. Renaming the row a second time would now touch
   the sheet and nothing else.

`wall_colour` returns **`None`** where the sheet states no colour, and that is deliberate. A
selector that quietly dealt the nearest row would invent a colour under a reader that looks like
it is asking the sheet.

### 10.3 THE MEASUREMENT — A NAMING PARCEL, PROVED BY THE BYTES

`common/materials.py` is in every asset's input hash, so the whole town restaled and the whole
town was rebuilt in this commit:

| measurement, 2026-09-13, on this branch | reading |
|---|---|
| assets stale before the bake | **384 of 384** |
| masters rebuilt | 382 structures + 2 terrain |
| masters whose **bytes** moved | **0** |
| `assets/manifest.json` lines changed | 382, every one an `inputs_sha256` |
| `brick` `baseColorFactor` on all three brick masters | `0.45, 0.23, 0.17` — before and after |
| `tools/check.sh` | 369 steps, none red; stale check 384 match / 0 stale |

Zero moved bytes is the acceptance clause, not a happy accident: a rename that repaints a
building is the wrong change, and this is the reading that says it did not. Compare §9.4, where
the same shape moved three of fourteen — because that parcel changed a VALUE and this one
changes a NAME.

### 10.4 WHAT THE BAKE COST, BECAUSE THE FOLKLORE WAS WRONG

`generators/code_inputs.py` says a full-town rebake is "twenty minutes of Cycles and 349 GLBs
whose bytes change because Cycles is not bit-reproducible". **Measured here: 22 seconds for 382
structures and 10 for the terrain epoch, and no GLB's bytes changed at all.** The twenty minutes
and the churn are both properties of `--ao`, which is off by default and which nothing passes
(T-0015) — so the argument that a `common/` rename is too expensive to make was costing more
than the rename. `frame_tavern`'s own note had the right order of magnitude ("a two-and-a-half-
minute rebuild") and it is the one to believe.

### 10.5 WHAT IS LEFT, AND IT IS NOT FILED — WITH THE MEASUREMENT THAT SAYS WHY

`fort_structure.WALL_RGBA` still carries three archetype-local literals: `braced_frame`
(0.60/0.55/0.46), `stone` (0.58/0.56/0.51) and `earth` (0.34/0.30/0.22). Moving them onto the
sheet is the shape §2.3 argues for in general, and it is NOT filed, for reasons that are
measured rather than assumed:

* **`stone` and `earth` reach nothing.** No record in the dataset states either construction
  (counted for this ticket: zero of each), so both are unreached fallbacks. Putting an unreached
  value on the sheet would add two rows no source states and no building wears — §5's own
  complaint — and `wall_colour` saying `None` for them is the honest form of the same fact.
* **`braced_frame` would have to be a repaint or a new row.** The sheet's nearest finish is
  `unpainted` at 0.52/0.44/0.34, which is a different colour, so adopting it would move buildings
  — forbidden by this ticket's own acceptance. Carrying the fort's value onto the sheet instead
  is a fourth convergence parcel with its own evidence to argue, in the shape of T-0138 and
  T-0267, and it should arrive that way or not at all.

The naming defect §9.5 filed is closed. What is left is a palette question, and it is written
here rather than in a ticket because the owner asked for fewer tickets to work, not for fewer
things to be known.

## 11. WIRED IN — T-1487, 2026-09-20: the roof gets its covering, and §2.2 gets read properly

### 11.1 THE REFUSAL WAS THIS SHEET'S OWN SUMMARY, NOT THIS SHEET'S RESEARCH

`generators/common/materials.py` carried one roof row, `roof_plane`, with `tile_m = None`
and a note reading *"the roof plane, COVERING UNSTATED"*. Its module docstring said, under
a heading **WHAT IS NOT CLAIMED HERE**, that *no source in this repository states what any
Chicago roof of 1835 was covered with*, and three archetypes quote that sentence back in a
comment beside a roughness literal they declined to choose between.

**§2.2 above never said that.** It grades `shingle` **attested** on the North Side school of
1833 and **inferred** as the ordinary covering of a framed building here; it grades
`roof_board` **inferred, and well argued**, on `outbuilding.py`'s own sentence. What §2.2
says is unattested is the **exposure** — and it names the two ways out in the same cell:
*"Pick the exposure from a source or record a liberty."*

So the covering was never the open question. A summary written in the code overstated the
research it summarised, and then the code obeyed the summary for a year. That is worth
recording as a class of defect: **a docstring that restates a memo can be wrong in the
direction of caution and still be wrong**, and nothing catches it, because caution reads
as rigour.

### 11.2 WHAT IS ON THE SHEET NOW

| row | tile | module | texel | roughness | where the roughness came from |
|---|---|---|---|---|---|
| `shingle` | 4.48 m | 0.14 m (L263) | 228.6 px/m | 0.90 | the framed archetypes' committed literal |
| `roof_board` | 4.00 m | — | 256.0 px/m | 0.93 | `outbuilding.py`'s committed literal |
| `roof_plane` | — | — | — | 0.90 | unchanged; the fallback, carrying zero records |

**Not one roughness is new, and §2.2's table is the reason to say so out loud.** §2.2 quotes
0.94 for `roof_board`, which is `sawn_board`'s. The shipped value on all 130 outbuilding
roofs is **0.93**, and §3.1 says in terms that the deliverable is a roughness map rather than
better constants and that a round should not be spent re-tuning the eighteen numbers. So the
sheet took the archetype's value and not the memo's: adopting 0.94 would have moved 130 roofs
for the sake of agreeing with a table. §2.2's 0.94 is hereby corrected to the shipped 0.93.

`roof_plane` is **kept and carries no record**. `roof_substrate()` resolves every archetype in
this dataset to shingle or board, so the fallback is unreached — and it stays on the sheet so
that a reader can see the question was answered rather than removed, which is the opposite of
§10's `wall_colour` finding only because the case is the opposite: an unreached fallback for a
covering nothing can be said about is a *statement*, where an unreached fallback COLOUR would
have been an invention.

### 11.3 THE DEALING RULE, AND WHICH HALF OF IT IS A LIBERTY

`roof_substrate(archetype)` is one sentence — **an outbuilding takes boards, every other
roofed building takes a shingle field** — and it splits cleanly into what is graded and what
is claimed:

| population | phases | authority |
|---|---:|---|
| `outbuilding` → `roof_board` | 130 | §2.2, on `outbuilding.py`'s own argument |
| `frame_dwelling`, `frame_storefront`, `frame_tavern` → `shingle` | 182 | §2.2, *the ordinary covering of a framed building here* |
| `log_dwelling`, `fort_structure` → `shingle` | **63** | **L266** — a claim, because §2.2 grades shingle for a FRAMED building and neither of these is one |

L266's argument is that the two coverings split on **what a roof is for** and not on what the
walls beneath it are made of: the board roof is argued as the *shed's*, and a cabin is a
dwelling that carries a family through a winter. The liberty states which way it is wrong if
it is wrong — toward a town that reads slightly better built than it was — and what would
discharge it.

### 11.4 WHAT DID NOT MOVE

* **No float.** Every roof in the town comes out of the bake at the roughness it went in at,
  and at the colour `roof_finish()` already dealt it. What moved is that each roof is now
  drawn on a row that says what it is made of.
* **The condition grading.** Fresh, weathered, darkened, patched: 218 records state one, and
  a covering and a weathering are two different claims. `roof_finish()` keeps its half.
* **No confidence.** A covering dealt by rule does not make a roof better attested.
* **The renderer.** Nothing here is visible yet. The material slots are now NAMED for their
  covering (`roof_shingle`, `roof_board`), and `docs/GLB-CONTRACT.md` says in terms that
  material names are not pinned by that document and a renderer keyed on one would be reading
  a convention nobody promised to keep — so the name is a label for a person reading a GLB,
  and **T-1488** has to choose deliberately between proposing a pin and carrying the substrate
  in the material's `extras`. It also has to answer the question that split T-1465 in two:
  `build.py`'s `unwrap()` is `smart_project`, a per-object island pack in 0..1, and a tile
  rate expressed in metres cannot be read off it.
* **The brick half.** L264 committed a brick course on the same day L263 committed the
  shingle exposure, and `brick` still carries `tile_m = None`. That is T-1450's other half and
  it is still open; this parcel is the roof half and did not reach into it.

### 11.5 ONE NAME CORRECTED IN PASSING

`palisade.py` carried a material called `roof`. It draws the two **gate leaves** — the name
came along with `M_ROOF`, the index the shared mesh helpers use for a second material. It is
`gate` now, so that *"every material called roof states its covering"* is true of the town
rather than true with one exception. This is the same defect §9.5 filed against
`chimney_brick`: a slot named for the surface that happened to reach it first.
