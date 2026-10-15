# 1619 Prairie refined from the district draft to a four-storey K01 stone-front house, bounded by the 1911 sheet (T-2434)

Piece 3 of T-1869. Its premise moved under it: T-2439 ruled that the Building Budget drawing is John
H. Hamline's house at **1621**, and T-2440 moved that build there and stood 1619 back as its draft.
So the house in this group without a picture is **1619**, and this ticket builds it, bounded by the
sheet, its own and not a copy of a neighbour. The draft is refined **in place**: `house_1619_prairie`
keeps its id, its archetype changes from `prairie_draft` to `k01_frontage`, the draft rules' `skip`
names `s20-1619-f`, and the frontage row already names the house.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1619-b1`, T-1840 census `s20-1619-f`, '4-storey brick
dwelling (D), stone (blue) front with a curved bay', and `s20-1619-a1`, 'brick rear block and a
2-storey frame half-round piece at its east end'):

- the main body, 13.3 m deep and 8.46 m along the front, 3.8 m back from the street line (the plan
  T-2420 first read off this trace, kept);
- four storeys, brick, a stone street front;
- the curved bay: the stone part bulges 1.02 m from the front over v 3.79-7.55, a 3.76 m chord, on
  K08's bow at the sheet's own chord and rise;
- the brick rear block, 6.0 m behind the south 5.69 m of the rear wall, one part with the house and
  so four storeys;
- the frame piece at its east end: 2.97 m deep, 4.77 m across, two storeys, frame;
- '12 12 12 8' against the south wall, so the walls are laid 12 inches (0.30 m) thick.

Built (all reconstructed, liberty `L-k01-1619-stone-front-2434`): a K02 front in **rock-faced Lemont
limestone**, dressed smooth at the openings, over two rusticated base courses, on K03 brick sides and
rear; the bow rising the **full four storeys** with three lights a storey, K10's moulded stone cornice
carried round its top and along the front under K01's flat roof; the door in the north strip on a K07
stoop; three windows a storey over the passage to 1615; the south wall, on the lot line to 1621,
blank; two stacks against it.

**Why that stone and that date.** The lot was sold as a building lot to J. Foster Rhodes in July 1891,
who "contemplates improving" it (`cgn-1619-text`, read in `docs/RESEARCH/hamline-1621-2436`). That
is the likeliest origin of the four-storey stone front, so it is built as a front of about 1891-92
would most likely be faced. The date is not itself a reading, and the liberty says so.

**Its own.** 1615 to the north is plain brick under a bracketed timber cornice. 1621 to the south is
smooth white Bedford limestone, two storeys under a wall gable and a crow-stepped parapet. 1625 is
rock-faced brownstone, Tudor. 1619 is grey-buff rough stone, four storeys, flat-topped, with the
broad bow running the full height to the cornice.

## Built otherwise than read

- **The frame piece is half-round on the sheet and is built as a rectangle** on its chord and depth,
  because K01's rear wings are rectangles. A curved K01 wing is the kit's to learn.
- **The trace's north wall steps 0.6 m out over its rear half**, across the narrow passage where the
  sheet prints 1615's wall figures. Like T-2420, this build does not build the step.

## Before and after, the same stands (`tools/qa_k01_t2434.mjs`)

Actual published `/1904/` app, *before* is `dev` at 89f71ee7c (the draft), *after* is this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (from the street), oblique
from the north and south walks, rear (the yard) and roof (the air). **0 page errors and 0 failed
requests on every run.** Desktop was run in two parts (`QA_PART=a|b`), because one pass of five stands
does not fit a 600 s call on this runner. *Before* was read on the phone only.

| phone, light | front | oblique N | oblique S | rear | roof |
|---|---|---|---|---|---|
| draws before → after | 191 → 208 | 252 → 270 | 214 → 232 | 243 → 261 | 223 → 241 |
| triangles before → after | 808 k → 885 k | **1.329 M → 1.407 M** | 949 k → 1.027 M | 1.079 M → 1.156 M | 1.016 M → 1.093 M |

| desktop, full (after) | front | oblique N | oblique S | rear | roof |
|---|---|---|---|---|---|
| draws / triangles | 262 / 2.78 M | 337 / 3.49 M | 305 / 3.02 M | 346 / 4.29 M | 290 / 2.99 M |

Every desktop stand is inside full's ceiling (360 draws, 4.6 M triangles).

**The phone's oblique-north stand is over light's 1.27 M-triangle ceiling, and it was over before
this change: 1.329 M on `dev` with the draft standing.** The stand looks down the row from 1613 past
1621, and nobody had read the light tier there before. This house adds 38.6 k triangles (the web
GLB: 39,450 against the draft's 804), drawn twice for the sun's shadow pass, so +77 k at the stand.
That is in line with its neighbours (1621 is 17 k, 1625 19 k, 1615 14 k for half the height), and K01
still has no light derivative, so the phone draws the full assembly. The breach is filed as its own
ticket rather than fixed here. Trimming this house could not clear a 59 k overrun that was already
there before it.

The master is 5.67 MB and the web derivative 1.92 MB.

Screens: `before-mobile-*.jpg`, `after-{desktop,mobile}-*.jpg`. Readings:
`browser-validation-before-mobile.json`, `browser-validation-after-mobile.json`,
`browser-validation-after-desktop-{a,b}.json`.

## Limits

- No photograph, plate or description of 1619 as it stood after 1891 has been read. Every form but
  the plan, the storeys, the bay's place and size and the rear pieces' places is the kits'.
- No image gate applies: there is no picture. One found later puts the house under it
  (AGENTS.md rule 11).
