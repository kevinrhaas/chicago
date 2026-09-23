# Fort Dearborn's gates and its corner works, against `p4_0` — T-0095

> Companion to `docs/RESEARCH/fort_dearborn.md` (the plan source, the scale, the wrong-fort
> guards) and `docs/RESEARCH/fort_dearborn_palisade.md` (what is evidence about the stockade).
> This memo is about one plate and three claims made off it.

**Run 2026-08-24.** T-0095 came off row 4 of `docs/RESEARCH/fort_dearborn_image_accuracy.md`
and read, in its own words:

> `p4_0` draws the corner works RISING ABOVE the curtain with their own pyramidal roofs and
> small lanterns, and a log-faced work over the gate in the middle of the wall. The model
> builds the bastions as shallow projections at curtain height and draws no gate at all.

Three claims. **Measured: the first is wrong, the second is right, the third is wrong.**
And a fourth thing nobody had claimed turned out to be true and was the only defect in the
scene: both gates stood a quarter open.

`tools/measure_fort_works_plate.py` holds the plate half and `tools/measure_fort_gates.py`
holds the mesh half; both run in `tools/check.sh` and both carry `--self-test`.

---

## 1. Where `p4_0` actually puts its raised works

The plate is read on a Gaussian-blurred luminance, each column against **its own** sky
sampled from a band well above the fort — a single global threshold walks the skyline down
a slope that is in the paper, not in the drawing. The ink mask is then eroded by a
horizontal window twelve pixels wide, so that a mark narrower than three drawn pickets is a
LINE and not a mass: that removes the flagstaff, the finials and the engraver's hatching,
and once the mast is gone the flag is no longer connected to anything and drops out with the
ink blemish floating in the sky at (970, 250). What is left, reduced to the one component
touching the wall, is the fort's silhouette.

| reading | value |
|---|---|
| the stockade's east angle | column **319** |
| the picket crest | y **376.6**, and **42.4 px** high |
| the last legible crest, west | column **1181** |
| the drawn wall run | **862 px** |
| rise at the east angle, over its first 20 px | **0.04 curtain heights** |

The crest is found, not assumed. It is the skyline in exactly two places — the wall inboard
of the east angle before the first range begins, and the wall past the last range at the
west end — and the pair is identified by the property that separates it from the bank
horizons either side of the fort, which are also flat runs at a similar level: **the fort
stands between them.** 95 % of the silhouette between the pair is above it.

The six tallest separated peaks of that silhouette, in curtain heights above the crest, with
0.000 the east angle and 1.000 the west:

| rise | width | along the wall | what it is |
|---|---|---|---|
| **2.96** | 3 px | **0.521** | the right-hand work's lantern |
| **2.25** | 93 px | **0.435** | the left-hand work's lantern |
| 1.97 | 224 px | 0.633 | the west range's ridge |
| 1.97 | 202 px | 0.680 | the west range's ridge |
| 1.80 | 7 px | 0.137 | a chimney on the east range |
| 1.80 | 304 px | 0.748 | the west range |

**The two roofed, lanterned, log-faced works stand at 0.435 and 0.521 of the wall. A corner
work stands at 0.000 or 1.000.** The nearer of the two is a quarter of the run — some 23 m,
three of this record's own bastion lengths — from the nearest angle. They are over the gate,
which is where the ticket's own second clause put one of them; there are only two works on
the sheet and both of them are that one.

**The one angle the plate draws unoccluded is drawn PLAIN.** The picket crest is the skyline
from column 319, rising 0.04 curtain heights over its first twenty columns. That angle is
the north-east, and the record leaves the north-east plain — Andreas and Hubbard both give
the works as north-west and south-east, and the 1830 plan draws works at exactly three
angles with the north-east bare. The plate and the record agree, and what they agree on is
that there is nothing there.

**The other angle is not evidence, because the plate does not show it.** The crest is last
legible at column 1181. Past it the silhouette stands 25 px higher again and that material
is green by 12.1 against 8.0 over the fort itself — the tree outside the walls. The
north-west bastion, the one angle on this face the record actually puts a work at, is behind
it. No height is read out of leaves.

### How the misreading happened

The same shape as T-0094, one day apart. The reading that produced this ticket saw two
roofed lanterned works on the plate, knew the record puts works at two angles, and joined
them. Nothing checked where on the wall they stood.

---

## 2. Why the plate could not have settled it in any case

`data/exclusions.json` already pins a feature of this very plate to the **first** fort: the
flagstaff, which the T-0044 pass refused for exactly this reason — the passage it comes from
ends *"Such was the old Fort previous to 1812"*, and `fort_dearborn_first_1803` closes *"none
of it may be borrowed for the second fort's records"*.

That same entry lists the first fort's own most distinctive features: **two blockhouses** at
the south-east and north-west angles, a **double row of pickets**, a **covered way** to the
river, a **flagstaff in the parade**, two-storey barracks with galleries. `p4_0` draws two
roofed lanterned log towers, a flagstaff, a way climbing the bank from the water to the gate,
and two-storey ranges. It also draws a **single** row of pickets, and it puts its two towers
amidships rather than at the angles.

**So the sheet matches neither fort's documented arrangement.** It is a retrospective
artist's impression carrying features of both, which is precisely why the courthouse plate in
the same directory is filed as a negative reference. It may drive massing "as inferred" under
that directory's README, and this project has taken setting and materials from it happily —
but a tier-5 view that already carries one certified first-fort feature is not the evidence
that adds a roofed lanterned tower to the second fort, at an angle **or** over a gate.
Nothing new is massed at this fort on its authority.

---

## 3. What the model already had, and the number for each

The ticket's other two claims are about the model rather than the plate, and both are
answered by measurement rather than by argument.

**"Draws no gate at all" — false, and it was false when the row was written.**
`palisade.py::_gate` has built a gateway in every documented wall since the archetype was
written: two heavy jamb posts, a lintel over the head, and two leaves. The committed master
carries them as their own primitives on their own materials, at glTF z ≈ 0 and z ≈ −53 —
both walls. From `p4_0`'s own stand the north gate reads as a framed opening with dark
leaves in it.

**"The corner works read above the curtain" — they do not, and nothing asks them to.**
A bastion here is a re-entrant of the picket line at curtain height, which is what the 1830
plan draws ("shallow rectangular projections") and what Andreas's own sentence implies by
naming bastions and a block-house as different things at different angles. The plate raises
nothing at either angle it draws. **This half of the acceptance rests on the refuted premise
and is not built.** It is recorded here rather than quietly dropped.

**"The south-west blockhouse reads above the curtain" — true, by 5.6 m.** It is a separate
record on the `fort_structure` archetype: two storeys, 5.2 m to the eave, a 30° pyramid roof
on a 14.52 × 9.80 m footprint. Measured in the scene, its instance bounds are
**15.98 × 9.48 × 11.26 m** against the palisade's **3.80 m**. It stands two and a half
curtain heights over the wall.

---

## 4. The defect nobody had claimed: both gates stood a quarter open

`palisade.py` says of the gate it builds, in terms:

> The leaves are hung shut. A fort with its gates standing open makes a claim about the hour
> of the day; a fort with them shut makes a claim about a garrison that is there.

The garrison is attested and the leaves were not shut. Each leaf was placed by computing a
midpoint from two endpoints and then spanning half a gate width either side of it. For the
left leaf the first endpoint is the gate CENTRE and it comes out right. For the right leaf
the selector made both endpoints the same jamb, so the midpoint landed **on** the jamb and
the leaf was built centred there:

| | placed | belongs |
|---|---|---|
| opening | 24.70 – 28.30 m | |
| left leaf | 24.70 – 26.50 | 24.70 – 26.50 ✓ |
| right leaf | **27.40 – 29.20** | 26.50 – 28.30 |

**0.90 m of a 3.6 m gateway standing open — a quarter of the gate, daylight straight through
the wall — and 0.90 m of leaf lying out past the opening across the pickets. In both
documented gates, and in the committed GLB.** From the north bank you could see the grass of
the parade and a building beyond it through a gate the record says is shut.

It survived because the two halves failed differently: one good leaf makes a gate look like a
gate until you are close enough to see ground through it.

**Fixed** by writing what was meant — each leaf runs from the meeting stile at the centre of
the gateway to its own jamb — and rebaked. `tools/measure_fort_gates.py` holds it, and holds
it by reading the shipped mesh rather than by re-deriving the placement, because the
derivation was the fault. Before and after from `p4_0`'s stand at `docs/evidence/t-0095-{before,after}.png`,
and the gate itself at 5x in `t-0095-close-{before,after}.png` — the gateway is 60 px
tall in a 1280x800 frame, so the wide pair alone does not show the fault.

---

## 5. The acceptance, clause by clause

| clause | outcome |
|---|---|
| the gates in both documented walls are drawn | **met** — and they were already drawn; they are now also SHUT, which they were not |
| the corner works read above the curtain | **not built — the premise is refuted.** `p4_0` raises no work at either angle it draws, the angle it draws clearly it draws plain, and the angle the record puts a work at is behind a tree |
| the south-west blockhouse reads above the curtain | **already met** — 9.48 m of building over a 3.80 m curtain, measured in the scene |
| every new form value carries its own confidence and note | **no form value was added.** Nothing measured here supports one, and the plate is not evidence that could |
| a before/after from `p4_0`'s stand is committed | **met** — `docs/evidence/t-0095-{before,after}.png`, plus `t-0095-close-{before,after}.png` at 5x on the gate itself |
| geometry — needs the nightly bake | **baked in this unit.** One asset: `fort_dearborn_palisade__picket_1816` |
