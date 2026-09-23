# The public-square pond — where one document argues both ways

**Parcel T-E5(a)** (ROADMAP · LANE 3 GROUND) · written 2026-08-16 · **a dating, not a change to the ground**

`AGENTS.md`: *where sources disagree, record the disagreement here and pick the best-attested
reading with reasoning — never silently choose.* This is that record. Nothing in this parcel
models, moves or removes any water; the four in-town water features are still deferred to the
hydrology parcel exactly as they were. What changes is that each of them now states where it
stands on **1835-07-01**, and this one states that it does not know.

---

## 0. Headline

`data/terrain/epochs/e1834_harbor_cut/terrain_spec.json` defers four in-town water features
under one shared phrase — **"existence documented, geometry conjectural"**. Existence is a claim
about a *place*; a scene is a *date*. Nobody had asked the second question, and the four do not
answer it alike:

| dossier zone | feature | at 1835-07-01 | what dates it |
|---|---|---|---|
| 14 | The slough | **present** (inferred) | a structure this project already stands in the scene |
| 15 | **The public-square pond** | **not established** (inferred) | nothing — and the same document argues both ways |
| 16 | The Frog Pond, Lake & LaSalle | present (inferred) | a newspaper, one year late to the day |
| 17 | The Wells Street marsh | present (inferred) | the sentence that gives the slough gives what it drains |

Three of the four survive the question. The pond is the one that does not, and it is the one
T-E5 was opened about.

---

## 1. The sharpest thing here is not the pond

**The scene draws a bridge over a watercourse the scene does not contain.**

`data/sidecars/1835/slough_log_bridge.json` — *The Slough Log Bridge, Water Street* — is a
committed structure standing on 1835-07-01, and its own `documented_range` note quotes the
source running the crossing *"until after 1840"*. Zone 14, the slough it crosses, is deferred
and undrawn. A visitor walks onto a timber crossing laid over open prairie.

That is **not** an argument for cutting a channel. The slough's depth and width are conjectural
and parcel (c) still owns them — the deferral's reasoning is intact. It is an argument that the
four features were never on one footing, which is what a single shared phrase implied.

---

## 2. The disagreement, stated in full

One document — `chicagology_prefire273`, rung 2 — carries **both** of the following.

**FOR a pond at the scene date.** The slough sentence, transcribed at
`docs/research/01-terrain-hydrology.md` § 2.2, describes the stream *"which drained **the pond**
and the marsh extending up Wells Street, and in a winding course passed over the site of the
Tremont House and entered the river at the end of State Street"* — and adds that where Water
Street crossed it, a log bridge was needed **until after 1840**. That is a drainage system
described as a working feature of the town, and the pond is named inside it as the thing being
drained. Nothing in that sentence is in a remembered past tense.

**AGAINST.** Three things, and the deferral weighed none of them.

1. **The pond quotation dates nothing.** `docs/research/08-fauna.md` line 44 gives it verbatim:
   *"Our public Square [where the Court House and City Hall now stand] **was then** a pond, where
   the Indians had trapped the muskrat, and where the first settlers hunted ducks."* A past tense
   set against an 1857 present, with no *then* the sentence fixes. And
   `data/sources/chicagology_prefire273.json` identifies the document it transcribes as built on
   **Gurdon Hubbard's description of Chicago as he found it in 1818** and on **George Davis's 1832
   drawing** — *"This is a picture of Chicago, and of all that then composed it, as described to
   us by Gurdon S. Hubbard, Esq."* The document's own *then* is a generation before the scene.
2. **The dossier's own row says the wrong season.** `docs/research/01-terrain-hydrology.md`
   row 15 reads *"~1 city block, **seasonal**; bed +1.0 to +2.0; **water 0.5–2 ft deep in
   spring**"*. The scene date is **1 July**. The row states a season and the deferral read it as
   a scene. The same dossier's modelling rule 2 says the ponding is *"worst in spring"* and that
   summer 1835 is *"drier than the spring 'impassable' condition"* — while noting that ponds 15
   and 16 *"were still wet in July 1836"*, which is a statement about zone 16's newspaper and not
   about zone 15.
3. **This project already stands two county buildings on that block, before the scene date.**
   `data/sidecars/1835/estray_pen.json` — Chicago's **first public building** — on the square's
   south-west corner from **March 1832**, and `data/sidecars/1835/log_jail.json` on its
   north-west corner from the **fall of 1833**. A pound is not built in a pond.

---

## 3. The reading picked, and why it is not "the pond was not there"

**Not established.** Graded `inferred`, in `data/terrain/1835_intown_water_dating.json` zone 15.

The temptation is to read §2's three points as a refutation and strike the pond. That would be
wrong twice. It would discard the slough sentence, which is the same document and better placed
in time than the quotation is. And it would answer a question about *extent* with a claim about
*existence*.

Because the buildings do not refute a pond — **they bound one**. A pond covering the whole block
is refused by this project's own committed records. A pond covering *part* of the block is
untouched by them, and is exactly what T-E5's third question asked for: *"a wet part of the square
with the three public buildings clear of it — which is a claim about extent that no source
reached supports."*

So the date and the extent are **one question**, and neither is settled. That is the finding:
`existence documented, geometry conjectural` was true of a *place* and was being read as though
it were true of the *scene*, and the geometry it called conjectural is not a detail to be filled
in later — it is the thing that decides whether water stands under Chicago's first public
building.

**What T-E5 asked for, discharged.** Its fallback was *"if it cannot be made honestly, the honest
answer is a `docs/LIBERTIES.md` entry saying the square is drawn dry and why."* No liberty is owed
and none is taken: nothing was invented, no confidence moved up, and the square was **already**
drawn dry and already recorded as such in the deferral a visitor can read. What was missing was
the reason, and the reason is now in that same visitor-facing text.

---

## 4. What it cost downstream, which is the part nobody would have looked for

`data/fauna/zones/f04_marsh.json` rested **three claims** on the pond quotation as though it were
in-scene evidence, and one of them said so in as many words.

| claim | before | after |
|---|---|---|
| `ondatra_zibethicus.presence` | `attested`, sourced **only** to the pond quotation, noted as *"direct evidence of animals present in numbers at a named location inside the scene box"* | `attested`, carried by Andreas — *"ducks and muskrats in the marshes"* — with the limit stated |
| `anas_platyrhynchos.presence` | `attested`, sourced **only** to the pond quotation | `attested`, carried by Andreas, same limit |
| the zone note | *"the two documented anchors are both inside the platted grid"* | the two anchors are named as unequally dated, and both as unmodelled |

**No grade moved**, and that is deliberate rather than convenient. What carries `attested` is
Andreas's marshes, and the marshes he names *are* the habitat this zone plants — `z04_marsh`'s
extent is a **buffer of the mapped water**, the river-shore strip, and has never reached the
square. The animal is attested in the habitat the scene draws. It is no longer attested at a
named block the scene draws dry, and the notes now say which of those two things they mean.

---

## 5. What this parcel did NOT do

- It did not model, move or size any water. All four features remain deferred to parcel (c).
- It did not touch `docs/research/01-terrain-hydrology.md`, `08-fauna.md` or `02-flora.md`.
  Research dossiers are committed **verbatim** as citable inputs; disagreements with them belong
  here, which is why this file exists.
- It did not resolve the disagreement in §2. It recorded it and graded the result
  `not_established`, which is a different and more honest thing.
- It did not answer **how much** of the block was wet, and nothing here should be read as
  licensing a guess at it. That is `T-E5(b)`, and its first question is whether any source states
  an extent at all.

---

## 6. How much of the square was wet — the reading, 2026-08-24 (T-0027)

**Parcel T-0027**, the ticket §5 above opened. `tools/measure_public_square.py` takes it on every
commit; nothing below is asserted, and no number here is authored by this project.

### 6.1 The reading

Sampled at 0.5 m over the committed platted block `blk_randolph_lasalle` — **43,885 samples, one
per 0.25 m², over 10,976 m²** — against `data/terrain/epochs/e1834_harbor_cut/heightfield.json`:

| | |
|---|---|
| ground | **+2.84 to +2.96 ft** above the summer-1835 water surface (mean +2.90) |
| relief across the whole block | **1.49 in** |
| samples at or below the water surface | **0 of 43,885** |
| **wet fraction** | **0.0 %** |
| the dossier's own bed for zone 15 | +1.0 to +2.0 ft — the ground stands **0.84 to 1.96 ft above it** |
| the square's drain (`state_slough_course`) | heads **34.4 m** off the block's east kerb, outside it |

### 6.2 Why the zero is not a measurement of a pond

**It is a measurement of the model, and the second row is what says so.** An inch and a half of
relief across a city block is *inside* the terrain spec's own declared micro-relief — two octaves
of value noise at ±0.10 ft, seed 18350701, which `micro_relief.note` calls **"a texture, not a
claim"**. So the square carries no landform at all: it is the South Division's plain profile plus
noise, exactly as `not_modelled_in_this_box` says zone 15 is. **Reading a wet fraction off this
ground would be reading the noise seed**, which is why the tool asserts the relief as well as the
water — assertion 1 is only a statement about the model for as long as assertion 2 holds.

### 6.3 So the honest answer to "how much" is a DEPTH, and it is the thing §3 could not reach

`docs/research/01-terrain-hydrology.md` row 15 puts the pond's bed at **+1.0 to +2.0 ft**. The
committed ground stands **0.84 ft above the top of that band and 1.96 ft above its floor**. The pond
the dossier describes therefore cannot be laid on this block — **it has to be dug**, over the whole
of it, out of the one land elevation in this box that rests on a documentary sentence: *"to the west
of State Street, it sloped down to the river in a level plain elevated only two to three feet above
the river"*.

That reframes §3. The parcel had the extent and the date as one question; they are one question
inside a THIRD, which nobody had asked. Modelling zone 15 is not choosing a boundary — it is
choosing an excavation, roughly one to two feet deep over 10,976 m², under the block carrying
Chicago's first public building, on no source that states a depth. **`geometry conjectural` was
carrying that, and it does not survive being read out loud.** The date stays `not_established`, the
geometry stays deferred, and the reason both stay is now a number.

### 6.4 And the drain is already in the scene

`state_slough_course` — dossier zone 14, carved by T-0005 and amended by T-0118 — is committed with
its head, in the spec's own words, *"just east of Clark between Washington and Randolph (the
square's drain)"*. Its head vertex stands **34.4 m** off the block's east kerb and feathers to zero
depth, so **the scene contains the pond's drain and not the pond**. §1 found a bridge over a
watercourse the scene did not contain; this is the same shape one feature upstream, and it is the
one piece of positive, committed evidence that this block collected water. The tool asserts the head
stays within 60 m of the block, because nothing else joins that file to this reading.

### 6.5 What was actually wrong, and what T-0027 changed

Not the terrain — **the sward**. `docs/research/02-flora.md` heads its ZONE 3 **"SLOUGH & SEDGE
MEADOW (Public Square → Tremont House site → river at State St; river-shore strip)"** and its § 1.2
calls the slough from *"the Public Square area (Randolph/Clark/LaSalle/Washington)"* the single most
important vegetation feature **inside** the platted grid. `z03_sedge_meadow`'s extent is an
**elevation band** of +0.6 to +2.2 ft — and it could never reach a block the terrain draws at
+2.9 ft, *because zone 15 is deferred*. The block three sources describe as water was being planted
by the same rule as anonymous prairie 800 m west, and the pond quotation reached the flora layer
nowhere at all. §4 records the mirror of this: the fauna zone had rested three claims on that
quotation and had to withdraw them, because `z04_marsh` is a buffer of the mapped water and **"has
never reached the square"**.

So the zone now also holds the square **by polygon** — `include_polygons`, the exact mirror of the
`exclude_polygons` the matcher already had — and the ring is the committed plat's block boundary,
vertex for vertex, held there by the same tool. **Nothing is fitted**, in particular not fitted
around the estray pen, the log jail and the court-house: they stand *on* the sward, which is what a
seasonally ponded bed carries and open water does not. **No water is drawn**, and the zone's own
`cover.standing_water_fraction` of 0.10 is explicitly not claimed here. `docs/LIBERTIES.md` **L188**
records the one invention: that the wet ground stopped at the surveyor's line.

**What this parcel did NOT do.** It moved no ground, cut no basin, dated no water and promoted no
confidence. Zone 15 is still deferred, still `not_established`, and still needs a bake and a source
before it can be anything else.
