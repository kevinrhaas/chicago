# What a Chicago chimney of 1835 was built of

**Opened by T-0008, which is R-W2a finding 1's other half.** The material sheet
(`docs/RESEARCH/materials.md`, wired as `generators/common/materials.py`) measured that
`frame_dwelling`, `frame_storefront` and `log_dwelling` built every chimney stack with the
**roof** material, so a stack came out painted whatever weathering condition its own roof
was dealt. R-W2c refused to fix that by picking a colour: *"it is not a palette fix, and
picking the placeholder's brick would be the wrong half of it"* — because the two stacks
this town has are two different objects, and the archetypes had already said so.

This file is the fabric question, answered at the tier the evidence carries. It does not
touch a stack's POSITION: `docs/LIBERTIES.md` **L26** has owned that since the archetypes
were written, and nothing here disturbs it.

## 1 · What this repository actually holds

**One coloured witness to any Chicago chimney, and it is retrospective.** Image 8 of the
owner's brief of 2026-08-18 (`data/sources/assets/owner_brief_2026_08_18/README.md`) is
the C. E. Petford watercolour of the Sauganash Hotel, and the brief's own reading of it
records **"brick chimneys"** on a two-storey clapboard block. The set's README says a
tier-5 retrospective view *may drive materials as `inferred` and may never drive a
coordinate*, which is exactly the weight taken here. T-0092 had already read that plate
onto the Sauganash's own stacks (`chimney_material: brick`); what was missing was any rule
for the other 142 buildings standing round it.

**Brick was being made in this town, and the date is documented.** `brickyard_north_side`
— Blodgett's brick-yard, Andreas vol. 1 p. 1161 — was established *"in the spring of 1833,
on the North Side, not far from the river bank, between Dearborn and Clark streets"*, and
the same sentence traces the town's first brick building to it. The record's own note adds
the corroboration: the Lake House, begun on the north bank in **1835**, is three storeys
and a basement of brick. So a brick stack in July 1835 needs no import and no invention: it
needs a mason and the yard two blocks away.

**Nothing states the fabric of any other stack, and three attributes could have.** Across
`data/structures/`, `chimneys` is a COUNT on every record that carries it; `chimney_material`
is stated on exactly one building; `construction` says what the walls are and never what
the flue is. There is no source in this repository describing a Chicago chimney catching
fire, being pulled down, or being built — the fire ordinances the town legislated
(`chicago_democrat_1833_11_26`, Ordinance 9 and its neighbours) are about goods in the
street, not about flues.

## 2 · The framed house: brick, INFERRED

A stack on a framed building in this dataset **rises inside the wall and breaks the roof at
the ridge**. That is not a new claim — `frame_dwelling._chimneys` has said it in as many
words since the archetype was written: *"the first stands at a GABLE END, rising inside the
wall and breaking the roof at the ridge. That is the eastern habit these settlers brought
with them, and it is the difference between a framed house and the log cabins next door."*
`frame_storefront` puts its stacks on the ridge line; `frame_tavern` puts them across the
frontage at the depth midline. All three are interior stacks.

An interior stack carries a fire up through a timber roof. It has to be masonry to do that,
and the masonry Chicago had in July 1835 was brick. Together with the one coloured witness
in §1, that is an **inferred** claim: reasoned from evidence about this town — a working
brick-yard, a brick hotel under construction, and a watercolour of one of these very
buildings — rather than stated of any particular house.

**The tone is not a new number.** It is `frame_tavern`'s committed `BRICK_RGBA`
(0.45/0.23/0.17 linear, roughness 0.85), wired to the Sauganash by T-0092 off the Petford
view, moved into the sheet so the town has ONE brick instead of an archetype-local copy per
archetype — the same move T-0007 made for the hewn log, and the complaint materials.md §2.3
files against exactly this shape of duplication. The Sauganash's own masters are byte-for-byte
unchanged by T-0008 as a result, which is the check that the value really did not move.

## 3 · The log cabin: stick-and-clay, RECONSTRUCTED

A stack on a log dwelling in this dataset stands **outside the gable**, and
`log_dwelling._stack` has always argued why: *"a stick-and-clay or fieldstone stack built
against the gable can be pulled away from the building when it catches fire, and it does
not eat floor space."* That sentence was committed years of parcels before this one, and it
is a claim about FABRIC that the renderer then ignored, painting the thing it describes in
the roof's colour.

**It is now true of every log stack in the town, which it was not when this section was
written.** Until T-0435 (2026-09-13) the code built the stack at a fixed compass face
while the roof ran its ridge along the longer plan axis, so 31 of 49 stacks stood against
an EAVE — the fabric argument above was being made from a disposition two-thirds of the
town did not have. §7 records the repair and the before/after; the argument here is
unchanged, because it was the geometry that was wrong and not the reasoning.

So the fabric follows the disposition that was already argued: a **cat-and-clay** stack —
split sticks laid up in courses like a miniature crib and daubed inside and out with the
same clay the wall below it is chinked with. Fieldstone is the other half of the archetype's
own sentence and is **not** built: a stone stack is a different silhouette as well as a
different colour, and choosing between the two per building would need evidence this
project does not have. One treatment, declared.

**Nothing attests any Chicago log house's stack, so this is `reconstructed`** — the tier
AGENTS.md exists to license: *invented within bounds, because the scene needs it and nothing
states it.* The bounds are two values this repository already ships:

| bound | value | why it binds |
|---|---|---|
| not as pale as the CHINKING | 0.700 / 0.670 / 0.590 | the same clay, sitting sheltered under an eave, while a stack takes weather and smoke on every face |
| not as dark as the palest ROOF CONDITION | 0.424 / 0.384 / 0.345 (`weathered`) | below that it stops reading as masonry against the roof beside it, which is the whole defect T-0008 fixes |

Nothing states where between the two it sits, so it sits at the **midpoint**, to three
decimals: **0.562 / 0.527 / 0.468**. Roughness is the sheet's `earth` substrate (0.95),
because the surface is daub. `docs/LIBERTIES.md` **L168** records the invention.

## 4 · What is deliberately left alone

- ~~**The fort.**~~ — **ANSWERED 2026-08-28, T-0137, in §6 below.** `fort_structure` built its
  stacks with `M_ROOF` when this file was written, because its buildings are the second Fort
  Dearborn of **1816** — seventeen years before Blodgett dug his first clay — on federal
  ground, with `construction` running log, brick, earth and stone across ten records, and
  neither §2 nor §3 reached them without inventing a third answer. T-0137 asked the evidence
  question the way this section says to, and no third answer is needed: **brick is attested
  inside this fort, twice, in 1816.** §6 is the argument, and the fort's ten stacks now take
  §2's row. This bullet is kept rather than deleted because tickets cite it.
- ~~**The 90 inferred placeholders**~~ — **CONVERGED 2026-08-28, T-0138.** They shipped a
  `placeholder_chimney_brick` at `#89503F`, a different brick from the archetypes' and 20 %
  apart in linear red; R-W2a finding 4 is right that a town painted by two generators with no
  shared palette splits visibly in half. `inferred_placeholder.py` now asks
  `materials.chimney_finish("interior")` for its stack, so the placeholders and the archetypes
  read the same row — §2's brick, at `0.45 / 0.23 / 0.17`, roughness 0.85. **The literal lost
  because it had no witness**: nothing in this repository argues for `#89503F`, and §2's value
  is the Petford watercolour's, so this converges on the evidenced side rather than splitting
  the difference. **The byte change did not happen, because there is nothing left to change**:
  `generators/inferred_placeholder.py --check` reports *0 flagged placeholder GLBs; 230
  superseded by a canonical bake*, and no committed GLB carries the material name at all. K38's
  passthrough re-bank was not needed and no building repaints. What the parcel buys is that the
  split cannot walk back in the day a record outruns the bake and a placeholder is emitted again.
- **A log dwelling's placeholder stack is still brick, and that is the massing's fault, not the
  palette's.** `chimney_finish` is asked for `interior` unconditionally because the placeholder
  builds one kind of stack — a box inside the footprint depth, rising through the roof. §3's
  daub belongs to a stack standing OUTSIDE the gable, and painting it onto a stack drawn inside
  the roof would put the right fabric on the wrong silhouette. Left alone deliberately.
- **The covering of any roof**, which R-W2a finding 2 says nobody states and this parcel
  does not pretend to know. A stack that is no longer roof-coloured makes no claim about
  the roof it passes through.

## 5 · What would replace this

A source describing a Chicago chimney — an insurance survey, a builder's account, a
recollection naming brick or clay at a named house — turns §2 from `inferred` into
`attested` for that building and §3 from `reconstructed` into something better. Failing
that, an inventory of Blodgett's output would bound how much of the town could have been
brick at all; the record already says the yard's first working season was 1833 and says
nothing about how many thousand it burned.

## 6 · The fort: brick, INFERRED — and no third row (T-0137)

**The premise that made the fort an exception is the one thing about it that is wrong.**
§4 excluded the garrison because 1816 is seventeen years before Blodgett's brick-yard, so
§2's warrant — *a working yard two blocks away* — cannot reach it. True, and beside the
point: the fort did not need a yard in town, because **brick is attested inside the fort
itself**, twice, independently, and both statements are already committed on the records.

| the statement | the source | the record it is committed on |
|---|---|---|
| "the brick building, just within the north stockade" | Hubbard, standing in the fort in 1827 (Andreas vol. 1) | `fort_dearborn_commandants_quarters`, `construction: brick`, **attested** |
| "(brick, about 25x50 ft.)" | the 1855 key (Wentworth, 1881) | the same record — two independent statements twenty-eight years apart |
| "the magazine, of brick" | Hubbard, same walk | `fort_dearborn_magazine`, `construction: brick`, **attested** |

Two of the fort's eleven built structures are attested masonry. That is a garrison with
brick on the ground and men who could lay it, and it settles the only question §4 could not:
whether a masonry flue at this post in 1816 needs anything invented. It does not.

### The disposition decides which row, and it was already committed

`common/materials.py::chimney_finish` selects on **where the stack stands**, not on the
record, "because no record in this dataset states a chimney fabric except the Sauganash's".
The fort's geometry has always answered that question, in `fort_structure._chimneys`: each
stack stands on the **depth midline**, rises from the ground **inside the building**, and
breaks the roof at the ridge. That is §2's interior stack exactly — the same thing
`frame_dwelling` builds and for the same reason, a flue carried up through a timber roof
has to be masonry.

It is emphatically **not** §3's. The cat-and-clay row is argued from a stack built *outside*
the gable so that it "can be pulled away from the building when it catches fire", and no
building in this fort has one. Painting a cat-and-clay flue up the middle of a barracks
would contradict the geometry the archetype has built since it was written.

So the fort takes **§2's brick row, unchanged** — `BRICK` (named `CHIMNEY_BRICK` until
T-0332 renamed it for the fabric rather than one of its surfaces), 0.45/0.23/0.17 linear at
roughness 0.85, the town's one brick. No third row, no new number, and no new liberty:
`docs/LIBERTIES.md` **L26** already owns where a fort stack stands, and the fabric here is
reasoned from attested evidence rather than invented, so it is **inferred** and L168's own
"not covered here" paragraph is corrected rather than extended.

### What is NOT claimed

- **Not that the tone is read off the fort.** Nothing in this repository shows the colour of
  any fort chimney. The tone is §2's, which is read off the Petford watercolour of a town
  building of the 1830s, and using one brick for the town is the convergence
  `docs/RESEARCH/materials.md` §2.3 asks for rather than a claim that the two bricks matched.
  The fort's own WALL brick is a third value — `fort_structure.WALL_RGBA["brick"]`,
  0.47/0.26/0.20 — and converging it is **T-0267**, not this parcel: it moves two committed
  masters and is a separate argument.
  **CLOSED 2026-08-29 (T-0267).** It converged onto this same row, on this same argument, and
  the walls make no more of a claim about 1816 clay than the stacks did. Three masters moved,
  not two — `lake_house_construction` carries `construction: brick` as well.
  `docs/RESEARCH/materials.md` §9 is the whole of it.
- **Not that every fort building had a chimney.** The COUNT is the record's, as everywhere
  else. Six of the thirteen `fort_structure` masters count one; the magazine's record says
  in terms that a magazine has none, and the tool below reads the records, not the geometry.
- **Not anything about the roofs.** A stack that is no longer roof-coloured makes no claim
  about the roof it passes through. R-W2a finding 2 still stands.

### The gate

`tools/measure_stack_fabric.py` reads the committed masters and asks, of every building whose
record counts a chimney, whether **anything stands above its roof material**. A stack has to
clear the roof to draw at all, so if the highest thing over the roof is the roof, the stack is
inside the roof's own primitive and is painted with it. That is the fault R-W2a found, stated
as a property of the bytes rather than of a generator, and `tools/check.sh` now fails on it.
Before this parcel: **6 buildings, 10 stacks**, all of them the fort's. After: none.

## 7 · How HIGH a stack had to stand: the by-law of 5 August 1835 (T-0333)

Sections 1 to 6 above are about what a stack is made of. This section is about a number,
and it is the first documented **dimensional** constraint this project holds on anything
above a roof line.

The Trustees of the Town of Chicago passed their by-laws on **5 August 1835**, over
Hugunin's and Alex. N. Fullerton's names. The Democrat printed them three times that
month, and `chicago_democrat_1835_08_19` — page 1, column 2, lines 106-123, claim
**`c005`** — is the printing that sets them line by line where 12 August weaves the two
halves of the sentence into one column. Section 18:

> *"…and every stove pipe or chimney passing through the roof of any building shall
> extend and be carried at least eighteen inches above the roof, and no stove pipe shall
> be passed through the side or end of any building, under the penalty of five dollars
> for each and every offence."*

It was enforced, not merely printed: section 21 sends a fire warden into every house,
store and shop in his district once a month from September to May. Sections 15 to 17 are
the same fear from the other side — shavings swept out weekly, nothing burnt in a street
or on a lot without a trustee's leave.

**The date is after the scene date and the constraint is not applied retrospectively.**
1 July 1835 is five weeks before the sitting, so nothing in this reconstruction is
conformed to a rule the town had not yet passed. What the by-law is used for here is the
opposite direction: as a **bound** the drawn town is measured against, and it turns out
the town was already inside it.

### It brackets a figure this project had only one side of

`docs/ROADMAP.md`'s flagstaff work quotes Andreas describing a Chicago with *"not a
single steeple nor a chimney four feet above any roof."* That is a maximum a memoirist
noticed, twenty years later, with no instrument. Eighteen inches is a minimum the town
wrote down and fined people for breaking. Both can be true, and together they bracket
every stack in the scene between **0.457 m and 1.219 m** above its own roof. Every stack
this project draws stands inside that bracket.

### The census, measured on the committed masters

`tools/measure_stack_ordinance.py`, read off the glTF accessor bounds rather than off any
generator — the same discipline §6's fabric gate uses, for the same reason. Clearance is
measured to the top of the `roof` material, which is the ridge, so a stack standing off
the ridge clears its own roof plane by MORE than the figure below.

| archetype | buildings | stacks | above its own roof |
|---|---|---|---|
| `frame_dwelling` | 116 | | 0.780 m — **30.7 in** |
| `log_dwelling` | 44 | | 0.720 m — **28.3 in** |
| `frame_storefront` | 36 | | 0.710 m — **28.0 in** |
| `frame_tavern` | 11 | | 0.550 m — **21.7 in** |
| `fort_structure` | 6 | | 0.780 m — **30.7 in** |
| **town** | **213** | **234** | **least 0.550 m — 21.7 in** |

**Every stack in the town already complies, and the tightest has 3.7 inches to spare** —
the eleven `frame_tavern` stacks, which are the only ones the archetypes finish without a
corbelled head. So this ticket closes as a gate and this section, and **no geometry
moves**: nothing was raised, no master was rebuilt, and `docs/LIBERTIES.md` is untouched,
because a documented constraint the model already satisfies is not an invention.

### Two questions the ticket asked, answered

**Is a stove pipe the same object as a chimney here?** The by-law names both and treats
them alike. This model has only one of them: **there is no stove pipe anywhere in it.**
Every stack drawn is masonry — brick on §2's and §6's argument — and no archetype carries
a pipe object at all. So section 18's second clause, *"no stove pipe shall be passed
through the side or end of any building"*, binds nothing that is drawn. `log_dwelling`'s
stack does stand OUTSIDE its gable, which §3 argues is the frontier pattern, but it is a
chimney and it is carried above the roof like every other; it is not a pipe out through
an end wall.

**What about the limits of the Corporation?** Section 18 binds *"within the limits of the
Corporation"*, and section 22 of the same sitting walks those limits street by street —
the only documented statement in this corpus of where the built town was held to end in
1835. **This project does not draw that boundary yet: T-0334 owns it.** The gate therefore
does not decide which buildings the by-law reaches, and it conforms nothing, because
nothing has to move: every stack clears eighteen inches on both sides of a line nobody has
drawn. What it holds is that none may drop back under. The day a record legitimately
stands a shorter stack outside the limits, T-0334's boundary is what will scope this gate
— and the gate's own failure message says so, rather than tempting the next run to weaken
a documented figure.

### The same by-law read one stack at a time (T-0333's other half)

The gate above reads accessor bounds, and says plainly what that costs: *"a building
carrying stacks on two roofs reports its TALLEST stack. That the lower one clears its own
ridge by the same margin is the archetype's guarantee, not this measurement's."* A glTF
POSITION accessor carries one bound per primitive, so an ell's low stack and the main
block's high one collapse into a single number and "the roof" collapses to the tallest
ridge on the building. That is the right conservatism for a floor and it cannot answer a
question about a particular stack.

`tools/measure_stack_projection.py` answers those, and **it is not a second gate — it is
not wired into `tools/check.sh`, and the by-law has one gate.** It runs the archetypes
outside Blender (`common/mesh.MeshBuilder` needs bpy only at `to_object`), builds each
building twice — once as its record counts, once with the count forced to zero — and takes
the boxes that appear only in the first as the stacks, so it trusts no archetype's private
helper and no material name. The roof under each stack is then sampled over that stack's
own plan footprint.

**The guarantee holds, and is now a reading.** All 234 stacks clear eighteen inches stack
by stack, not only building by building; the minimum is the same 0.550 m and nothing else
is within eight inches of the floor. `miller_house` is the case that shows the two
measurements are genuinely different: its second stack stands on the frame addition and
its head is **2.271 m BELOW the log core's ridge**, exactly as `log_dwelling._chimneys`
argues it should be — a figure a bounds reading would have to report as a stack sunk into
its roof.

**And it found one thing the bounds cannot see.** Classified against each roof's own ridge
frame, `log_dwelling`'s 47 stacks split **17 at a gable end** (0.720 m clear, every one)
and **30 against an EAVE wall** (2.344 to 3.197 m clear, because an eave stack runs up
past a roof that is at eave height beside it and keeps going to the ridge). `_stack` builds
at the −x face unconditionally while `_roof` runs the ridge along the longer plan axis, so
a cabin deeper than it is wide gets an eave stack. That contradicts the archetype's own
docstring — *"one exterior stack against a gable end"* — and it is the disposition **§3
argues the cat-and-clay fabric from**: *"built against the gable so it can be pulled away
from the building when it catches fire."* Two-thirds of the town's log stacks are not in
it. **T-0435** owns that; it moves geometry on 29 masters and needs a bake.

### T-0435: the stacks now stand where the argument says (2026-09-13)

The eave figure is **zero**. On the tree this was fixed against the split had grown to 49
stacks, **31 of them against an eave**, and the same instrument now reads **49 at a gable
end and 0 at an eave** — the only reading in the census that moved, stack for stack, is
those 31.

The repair is one sentence of code: `_stack` no longer builds at the −x face
unconditionally. It takes a `gable_axis`, and `_gable_axis` answers it from the roof the
building actually has — the ridge's own axis, so the gables are the ends the ridge runs
to. A SHED roof is answered `x` unconditionally rather than from the plan, because
`_shed_roof` always falls from the −y wall to the facade whatever the proportions are, so
its sloping ends are always the ±x faces; no record in the 1835 scene asks for a
shed-roofed log dwelling today, and the branch is a rule stated before it is needed. The
block itself is written once, in a (gable, cross) frame, and swapped into world axes at
the last step, so the two orientations cannot drift apart by hand.

**Two things a gable-fronted cabin made the archetype say out loud.** On a cabin deeper
than it is wide the ±y faces are the gables, which means the FACADE is a gable, and two
pieces of the elevation had quietly assumed it was not:

- *The back window.* `_core_openings` has always put one window on the −y elevation under
  the rule *"none on the gable ends: the gables carry the chimney at one end and the
  notching at both, and a log gable was rarely pierced."* That rule was written when the
  back wall was assumed to be an eave. On a gable-fronted cabin −y is a gable and now
  carries the stack, so the window goes to the −x eave instead — the same rule applied to
  the roof the building has. The facade stays the one gable that is pierced, because a
  cabin has to have a door.
- *The second stack.* `brown_boarding_house` is the only record in the scene that asks for
  it — two stacks, no frame addition, 7.32 m wide and 12.19 m deep — and "the other end of
  the one element there is" is its street front. Centred, the shaft would have stood
  through the doorway. It slides along the gable into the clear band the facade leaves
  between the door reveal and the nearer flanking window and stands in the middle of it,
  which is where an end-wall flue serving the front pen would rise anyway. The figures it
  is placed from are `_core_openings`' own, hoisted into module constants so a second copy
  cannot drift.

**Before and after, on the extreme case.** `brown_boarding_house` carried the deepest fault
in the town: both its stacks stood against an eave with **3.197 m** of flue above the roof
beside them — a chimney standing over ten feet proud of the surface it is built against.
They now clear **0.720 m** (the rear gable) and **1.118 m** (the facade gable, measured
through the eave overhang it passes at its offset). Every other moved stack lands on the
same **0.720 m** the seventeen correct ones always had, which is what the geometry
predicts: a gable stack is the same block on either axis.

**The by-law is not touched.** All 249 stacks on 227 buildings still clear eighteen inches;
the floor is still the eleven frame taverns' 0.550 m. A stack that follows the ridge to a
gable gets SHORTER — 3.197 m to 0.720 m at the extreme — and 0.720 m is 28.3 inches, so
nothing approaches the gate. `tools/check.sh` is green, including `validate.py --stale`,
which is what forced all 49 log masters to be regenerated rather than the 30 that visibly
moved: the archetype's own sha is in every log building's input hash. 30 masters changed
bytes; the other 19 rebuilt byte-for-byte identical, which is the evidence the change
reaches exactly the cabins it should.

### A correction: section 22 is not the corporation limits

The paragraph above says section 22 of this sitting *"walks those limits street by
street"*. It does not, and the distinction matters because two different lines are being
run together. **Section 22 is the hay-stacking boundary** — *"it shall not be lawful for
any person to stack hay within the following limits in the town of Chicago, to wit:
commencing on Washington street at the United States Reservation, and running thence West
to the intersection of Canal Street, thence North to the intersection of Kinzie Street,
thence East to the intersection of Wolcott street, thence to Illinois Street, and thence
to Lake Michigan"* — a six-vertex line drawn round the built core, INSIDE the corporation
and narrower than it, under a twenty-five dollar penalty. It is a use restriction with its
own limits, not a statement of the town's boundary. That line is **T-0334**.

**The corporation's own limits are not in this repository at all**, as geometry or as a
sourced claim. The one description held is the note on `chicagology_prefire278` — fixed
6 November 1833 at Jackson south, Jefferson and Cook west, Ohio north, "barely
seven-eighths of a square mile", extended 11 February 1835 east to the lake shore and out
to Chicago Avenue and Twelfth Street — and that record's own note grades the incorporation
half of the page **rung 3, not 2**, and says in terms that no value in the dataset rests on
it. Nothing here changes that: no boundary is committed and no confidence is graded off it.
**T-0436** owns finding it in something better.

What can be measured meanwhile is the drawn town's extent, and it is why the gate is safe
without the line. The 213 chimneyed buildings stand between local **E −273.2** (on Clinton
Street, the westernmost street this project commits) and **E +1287.3** in the North
Division, and between **N −619.6** (`heacock_house_monroe`, on Monroe) and **N +386.7**.
Every limit street named above lies whole platted tiers beyond that box on its own side.
So the gate covers the whole drawn town soundly today, and the outside-the-limits column of
any census of it is empty **by extent rather than by a boundary** — which is a different
and weaker thing to be able to say, and is worth saying in those words.
