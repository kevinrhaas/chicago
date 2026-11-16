# T-3162 (piece 1 of T-1894) — 1823 Prairie onto K01 from its engraving and the 1883 album vignette

It refines the district draft (T-2330) in place under `dent_house_1823_prairie`.
T-3163 (piece 2 of T-1894) owns what the pictures show that is not built yet, the vignette's camera,
and the match records' `matches`.

## The pictures

- **The Chicagology engraving** (`chicagology_1823_dent_engraving`; Prairie library
  `a18-cgy-1823-dent-engraving`, "link only"). A halftone after a photograph, the house from the
  north-west across Prairie Avenue, printed beside an engraved portrait of Thomas Dent. Undated. Its
  verticals are vertical, so it was taken with a level camera and a rising front. It is the picture
  the camera is solved for. It is committed as the image store's copy, with its attribution, at
  `data/sources/assets/dent_1823_engraving_t1894/` (rights `check_required`: forms and proportions
  only).
- **The 1883 New Chicago Album vignette** (`newberry_new_chicago_album_1883_residences`; Prairie
  library `a19-nby-newchicagoalbum-1883-residences`, no known restrictions). The same view, drawn
  small and dated. It shows the stone front against the brick flank, and the pavilion's pedimented
  attic. It is cited, not committed. Its camera is T-3163's.

Both draw one state of the house, two years after it was built (1881) and later. Nothing read so far
records an alteration before 1904.

## The plan, from the 1911 sheet (trace s28fp-1823-b1, in the lot's frame: u toward the street, v south)

| part | u (m) | v (m) | built as |
|---|---|---|---|
| front block | 20.8 – 32.85 | -7.71 – 6.17 | K01's main body, 12.05 x 13.88 m; the frame's origin is its rear north corner |
| south pavilion | 32.85 – 33.97 | 0.43 – 6.15 | a K08 projection 5.74 m wide and 1.12 m forward, flush with the south wall, under K01's hipped crown |
| rear range ('rear2B') | 14.1 – 20.8 | -7.71 – 4.4 | K01 rear wing, two storeys under a flat tin deck; the north wall runs on unbroken, the south side narrows |

## The camera

`data/reference_views/dent_house_1823_prairie/chicagology_engraving.json`, level, from the far walk of
Prairie Avenue north-west of the house. Eleven points (corners at grade, the base course and the
cornice; plan places from the sheet's trace) fitted by least squares, 9.4 px RMS. Its `solve` says
how it was fitted and how far it holds.

## Before and after, from the engraving's camera

- before: `before-draft-chicagology_engraving.jpg` (dev's draft, rendered from the same camera in the
  draft's frame, eye u 46.64, v -17.56)
- after: `../photo-match/dent_house_1823_prairie/chicagology_engraving-side-by-side.jpg`

## What K01 could not carry, and so is open

- The pavilion's pediment of paired lights in front of its steep roof. K05's steepest hipped crown
  (65 degrees at its end) peaks about 2 m under the engraving's roof.
- The mansard's cresting. The broad carved pediment over the triple group: K05's gable head stands
  over one sash. The north flank's paired lights under one pediment.
- The north flank's one-storey box bay under a hood. The stack over the rear range, where K01 stands
  no stack.
- The stoop that climbs from the north. The narrow light beside the door. The grilled arched basement
  doorway under the landing. The moulded window heads.

No generator rule was changed: every part is the K01, K02, K05 and K08 kits as they stand. The front
is K02's Bedford limestone because the Lemont profile cannot course a base under a 2.35 m principal
floor.

## T-3163 (piece 2 of T-1894) — the pictures worked down

**The engraving's camera, re-solved.** Read again with a pixel ruler, the pavilion's front corners
stand at x 1035 and 1232 px, not the 990 and 1155 px T-3162 fitted to, so its camera put the pavilion
about 60 px left of the print and its cornice about 65 px low, and every front opening read through
it came out 0.5-1.4 m north of its place. The new fit (eleven readings, 11 px RMS; its `solve` says
which) moves the eye back across the avenue to u 55.5, v -24.8 and lands the mansard's curb, which
it was not fitted to, on the print's. Through it:

| what | T-3162 | T-3163 |
|---|---|---|
| the triple group's lights (v) | 0.88, 1.9, 2.92 m | 1.6, 2.75, 3.9 m |
| the door (v) | 4.85 m | 6.2 m |
| the north flank's columns (u) | 2.1, 4.3, 8.4, 10.9 m | 0.25, 2.15, 5.0 (chamber storey), 7.35, 11.0 m |
| the rear range's columns on the flank | three | one (the wall from x 140 to 225 px is blank) |
| the north stack (u, top) | 7.6 m, 18.3 m | 7.8 m, 17.5 m, on the cornice |

**The vignette's camera, solved.** `album_1883.json`, on a cut of the plate committed with its
attribution at `data/sources/assets/dent_1823_album_1883_t3163/`: ten readings, 5.5 px RMS at
about 13 px a metre, so a cross-check rather than a measurement. It agrees with the engraving's
places within about 5 px, and with the curb's height where the engraving draws it higher.

**Built from the pictures:** the north flank's box bay under its hood (K08's rectangular bay; its foot
carried to grade 0.5 m proud, since K08's corbelled oriel stands only on an upper floor: open); the
pavilion carried up an attic with paired lights under a coped stone gable and finial (K08's gable,
1801's), replacing the hipped crown, which is what lets the deck carry its iron cresting (K10's);
paired-light gabled dormers on the street face and the north flank; K09 cornice hoods over the front's
windows and surrounds on the pavilion's; the stoop climbing from the north along the front (K01's side
stoop, 1621's). One generator fix, in the parameter module only: the side stoop's check against a
street-front bay read a bow's `chord_m` and failed on a projection sized by `width_m`.

**Still open** (the match records): the triple group's broad dormer, whose pediment rises over the
curb in both pictures; the stack over the rear range; the grilled arched doorway under the landing;
the narrow light beside the door on the principal storey; the box bay's corbelled foot; and, on the vignette, the slated cheeks
either side of the pavilion's pedimented attic. Each needs K01 to do something it does not, so the
ticket is released with the records saying so (T-3153: no photo follow-up tickets from a run).

- before: `before-t3162-chicagology_engraving.jpg` (T-3162's build through T-3162's camera)
- after: `../photo-match/dent_house_1823_prairie/chicagology_engraving-side-by-side.jpg` and
  `album_1883-side-by-side.jpg`

## T-1894 (reopened) — the rear stack and the door's narrow light

Two of the six open differences, each a small addition to K01:

- **The stack over the rear range.** A flat-decked wing may now carry `rear_wings[].stacks`
  (until now only a slated wing could, T-1890): T-2302's plain prism under its cap, standing on
  the tin deck 0.3 m or more inside the wing's walls. Read through the engraving's camera at
  x 170-235 px with its top at y 188 px: u -4.8 m, v 0.7 m, 0.9 x 0.75 m (the main stack's plan,
  which the same camera puts within 10 px of its own reading), 16.6 m high. The vignette draws it
  at the flank's rear corner, in the same place. Its band about two-thirds up and its corbelled
  cap are not modelled.
- **The narrow light beside the door on the principal storey** (x 960-980 px). `front_bays_by_storey`
  may now name the principal storey, provided the door's bay stays among its centres; the light is
  laid at v 7.4 m on the storey's sash, as the chamber storey's above it.

Still open, each needing K01 to do something it does not: the triple group's broad dormer whose
pediment rises over the curb, the grilled arched doorway under the landing, the box bay's
corbelled foot, and (on the vignette) the slated cheeks either side of the pavilion's attic.

## T-1894, 2026-11-15 — the grilled arched doorway under the landing

K01's side stoop (`entrance_kit.side_stoop`) takes an optional `arch` — `v_m`, `span_m`, `spring_m`,
`depth_m`, and an optional `grille` of `bars`, `set_back_m` and `ring_radius_m` — and K07 cuts a
round-headed basement arch in the landing's street face (`Entrance._arch_face`, T-2500's terrace arch,
now taking the face's role) with iron in its void (`Entrance._arch_grille`, after K08's basement
grille, T-2525). The Dent house carries one: 1.05 m across under the door at v 6.2 m, jambs 0.6 m over
grade under a half-round head, a 0.4 m void, five uprights and a ring in the head.

Read through the engraving's camera against the render: the print's arch at x 925-980 px, its crown at
y 938 px. A first bake with the jambs at 0.8 m put the crown 15 px (about 0.27 m) high; at 0.6 m it
lands at y 935 px. The 1883 vignette draws the arch a little larger, which its half-metre scale does
not resolve. Both pictures draw the landing's face about 1 m longer to the north than the build's
1.8 m, the flight shorter and the landing's top lower: recorded open on both match records, not built
here (it would move the stoop that both records mark fixed).

The other open items (the broad dormer through the curb, the box bay's corbelled foot, the pavilion
attic's slated cheeks) are unchanged.

## T-1894, 2026-11-15 (second piece) — the box bay on its corbels, and the flank's basement lights

Both pictures stand the north flank's box bay on a corbelled block under its broad light, with a
basement light in the flank's wall beneath it; the build had carried the bay to grade 0.5 m proud
with that light in its own foot, because K08's corbelled oriel stood only on an upper floor.

- **K01** (`k01_frontage_params.resolve_bays`) now lets an oriel stand on the principal floor too,
  when its corbel courses (or its apron's foot) still clear grade by a metre. Nothing else changes:
  every other K01 house's resolved parameters are as they were, and `validate.py --stale` reads 0
  stale.
- **The Dent house**: the bay is `k08.oriel.canted_corbelled` on the principal floor at 2.35 m, its
  plan the bay's own 2.4 m by 0.5 m, its one storey the principal one with its paired light, on three
  0.2 m courses, so its foot stands at 1.75 m. Through the engraving's camera the build's block is at
  y 865-900 px against the print's 857-895 px.
- **The flank's basement lights**, read off the engraving at y 915-965 px (0.45-1.45 m over grade),
  square-headed in the brick: under the bay (x 404-438 px, laid at u 6.05 m where the print puts it
  under the bay's front, 1.15 m across), under the 2.15 m column (x 310-332 px) and under the 11.0 m
  column (x 530-565 px). The render's land within about 8 px of each. The print draws two more,
  under the 0.25 m column (x 265-285 px) and under the rear range's column (x 230-250 px); K01 lays
  a read window no nearer than 0.45 m to a wall's end, and a rear wing's basement lights only
  round-headed, so those two are recorded open.

Still open, as before: the triple group's broad pedimented dormer over the curb, the pavilion attic's
slated cheeks, and the landing's length.

## T-1894, 2026-11-15 (third piece) — the flank's last two basement lights

The engraving draws five basement lights along the north flank's foot, all square-headed in the
brick. The second piece laid three; the other two needed K01 to do two things it would not.

- **K01, a flush wing's end** (`k01_frontage_params._flush_wing_end`). A light read off a picture
  keeps 0.45 m off its wall's ends, so that a corner keeps its pier. At 1823 the main body's north
  flank (K01's `side.south`) does not end at its rear: the rear range carries it on flush, past the
  light's head, as the 1911 sheet's unbroken north wall gives it. Where a rear wing carries a flank
  on flush like that, past the light's head plus 0.45 m, that end is no corner, and a read light may
  stand 0.1 m inside it, still in the main body's own wall. Every other end still keeps 0.45 m.
- **K01, a wing's square basement lights** (`rear_wings[].basement_lights.<side>.head: "plain"`).
  A wing's basement lights were only round-headed (1811's, T-3133). They may now be square, a plain
  hole as the main body's read lights are, at least 0.3 m high.
- **The Dent house**: the light under the 0.25 m column (x 265-285 px) at s 0.48 m, its south edge
  0.1 m inside the main body's rear (the print centres it about 0.2 m further south, within the
  bar); the light under the rear range's flank column (x 230-250 px) at the range's s 5.25 m. Both
  are 0.75 m across and 0.45-1.45 m over grade, the size of the other three. Through the engraving's
  camera the render's land at about x 275-288 and 232-245 px. The reconstructed north downpipe,
  which the first would have crossed, moves from s 0.6 m to the blank pier at 1.2 m.

Both match records mark the flank's basement lights fixed. Still open: the triple group's broad
pedimented dormer over the curb, the pavilion attic's slated cheeks, and the landing's length.

## T-1894, 2026-11-15 (fourth piece) — the landing a few risers under the door, drawn to its length

Both pictures draw the stoop's landing about 1 m longer to the north than the build's 1.8 m, and
the engraving draws three more things that go with it: its flight is shorter (its foot about
x 760 px against the build's 743), the landing's top edge stands lower (y 905 px against 865), and
the iron rail turns level along the landing at y 870 px, about 0.9 m over it. Read along the
flight's line at about 51 px a metre, the print's flight runs from x 760 to x 897-907 px: nine
treads of 0.3 m. So the landing does not stand at the 2.35 m hall floor; the door opens a few
risers under it, on a vestibule, as 1612's does (T-2369).

No new generator capability was needed: K01 already takes `entrance_floor_m`, the door's floor
between 1.0 m and the hall less 0.5 m, read from a source.

- **`entrance_floor_m` 1.7** — ten risers of 0.17 m, the print's nine treads. The landing drops
  0.65 m.
- **`side_stoop.landing_v_m` [4.4, 7.1]** — 2.7 m, from the flight's head to the pavilion. The
  flight's foot falls at v 1.7 m.
- **The arch re-read** — with the face at the print's length, the 1.05 m arch under the door
  rendered at x 952-995 px against the print's 925-980: about 0.45 m south and 0.25 m narrow. It is
  now 1.25 m across, centred at v 5.8 m (the face's middle is 5.75 m, and the vignette draws it a
  little south of the middle), on 0.5 m jambs, so its crown stays at about 1.13 m.
- **`door_clear_height_m` 3.2** — the print's doorway is the leaves (y 757-887 px) under a
  transom light to y 697 px and a cornice hood. A 2.70 m door on the lowered floor put its head at
  4.4 m, 0.65 m under T-3163's. 3.2 m is K01's tallest principal door (head 4.9 m, y 730 px).

Through the engraving's camera the render's landing top edge lands at y 905 px, its face's north
end at about x 900 px, the flight's foot at about x 763 px, the door's foot at about y 900 px, and
the arch's jambs at x 927-978 px. Through the vignette's camera the landing's top, its length to the
pavilion and the arch's place land within 1-2 px. The vignette draws the arch broader (about 22 px
against 13), where the engraving is after a photograph at four times the scale: recorded on the
vignette's arch line, which the two pictures do not agree on.

Both match records mark the landing's length fixed, and the engraving's record marks the arch's
width fixed. Newly recorded open on the engraving's record: the doorway's height. The print's hole,
with its transom, is about 3.8 m from the landing against the build's 3.2 m, and has no transom
glazing and no hood. The door stood about as far under the print's transom before this change
(its head at about y 721 px), and nothing recorded it. Still open, as before: the triple group's
broad pedimented dormer over the curb and the pavilion attic's slated cheeks.
