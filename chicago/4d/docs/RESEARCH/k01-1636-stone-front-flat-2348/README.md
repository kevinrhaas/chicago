# 1636 Prairie refined from the district draft to a K01 stone-front house under a flat roof, with its rear wing (T-2348)

Piece 3 of T-1863 (the 1634/1636 stone-front pair). 1634 is T-2350, which taught K01 the flat roof
(`k01.roof.flat`) and a bay laid in the front's own stone; this piece stands 1636 on those, and its
narrow back building on K01's rear wings (T-2343). No kit changed here.

The draft T-2334 stood is refined **in place**: `house_1636_prairie` keeps its id and its archetype
changes from `prairie_draft` to `k01_frontage`. The draft rules' `skip` names `s20-1636-f`, and the
frontage row names the house (`house_id`). 1636 has no stable on the sheet.

## The plan, re-cut

The draft fitted two rectangles inside the traced main part: r1, a strip 22.0 m deep and 4.75 m wide
along the north (party) side, and r2, 14.25 m by 2.75 m beside its front half. Read as a building,
that is a **wide front body and a narrow back building behind its north side**, so the K01 record
takes them that way:

- **Main body**: 13.75 m deep, 7.5 m along the front (r2 joined to r1's front part), its origin moved
  8.25 m toward the street and 2.75 m south (lot frame u 30.75, v -3.75, the same u as 1634's).
- **Rear wing** (`rear_wings`): u -8.25..0, v 2.75..7.5, three storeys, flush with the party wall.

Read back through the sheet's fit in the record's frame, the trace's south wall is at v -0.1..0.0,
its party line at v 7.45..7.7 and the back building at u -8.2..0, v 2.45..7.65: the fit holds to the
0.25 m cell.

## What the house is

Sheet 20 (T-2328 trace `s20fp-1636-b1`, T-1840 census `s20-1636-f`): three storeys over a basement
('3B'), brick with a stone front, attached to 1634. Built on 1634's kits, so the pair matches:

- K02 brownstone front over two rusticated base courses, on K03 brick side and rear walls; 1634's
  stone (its brown rests on cgn-1634-text's 1890 "brown stone mansion", carried to the partner).
- K06 two-over-two sash under K09 cornice-hood lintels (two lower storeys) and flat stone lintels.
- **The sheet's canted stone bay** (p1: 3.76 m at the front, a 1.8 m face, 0.8 m out, centred 1.82
  m from the south corner) as K08's canted bay (3.7 m, 1.5 m face, 1.1 m out), three storeys in the
  front's brownstone, centred 0.38 m north of the sheet's to keep K01's corner pier.
- **The door at the north end, beside the party wall.** The draft rules mirrored the pair's doors to
  their outer ends, but the bay fills the south half of 1636's front, exactly as 1634's bay fills the
  south end of its own: the pair repeats rather than mirrors. The rules' row is corrected.
- The flat tin deck, coped side parapets and stone blocking course, the K10 bracketed cornice along
  the street; 1634's storey heights, so floors, cornice and parapets run level across the pair.
- Three windows a storey in the south wall over 1638's side yard; one in the rear wall beside the
  wing; two stacks against the party wall. The north wall is blank.
- **The rear wing**: three storeys from a 1.4 m floor (3.6, 3.3, 3.0 m: back-building storeys, its
  deck under the main wall head), two sash a storey to the south, one to the rear, a flat tin deck.

Liberty `L-k01-1636-stone-front-flat-2348`; 1636 is retired from `L-draft-prairie-16-18-west-2334`.

## The image gate

The Prairie library was searched for 1636 on 2026-10-11: it holds the Robinson 1886 crop
(`cgn-1636-robinson-1886`, a site plan with no elevation) and nothing else by address. The 1638
photograph (`a16-cgy-1638-gothic-photo`) shows at its right edge a sliver of a dark coursed brick
wall, plausibly 1636's south side, with no opening, corner or front to fit a camera to. There is no
picture of 1636's appearance, so no camera is solved and the ticket carries no `## Image gate`.

## Found on the way (written into T-2347, which revisits 1634)

- **1634 stands 0.6-0.7 m inside the party line.** In its own frame the shared line the trace draws is
  at v -0.4..-0.7, and the K01 south wall at 0. With 1636's north wall on the line, the pair shows a
  ~0.75 m slot between the two blank party walls. It is 1634's fit, and it is also why 1634's wing
  seemed to "run 0.5 m past" its south side: the wing is right and the main body is short.
- **Both fronts stand 1.6 m behind the traced outline.** The trace's front edge is at u 15.3-15.4 in
  both houses (the outer side of the blue band the sheet draws along the pair); the draft fit and both
  K01 bodies stop at u 13.75, inside the band. 1636 is kept flush with 1634; which line is the wall
  face is a question for the pair together.

## After, the same stands (`tools/qa_k01_t2348.mjs`)

Actual published `/1904/` app. Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front
(across Prairie), oblique from the south and north walks, rear (over the yards), rear-south (the
wing from 1638's yard), roof (the air). Both runs: 0 page errors, 0 failed requests, every stand
`withinBudget`.

| | load to ready | JS heap | draw calls | triangles |
|---|---|---|---|---|
| desktop | 28.5 s | 31.6 MB | 131-166 | 1.83-3.22 M |
| phone | 17.4 s | 31.4 MB | 99-160 | 439-907 k |

The master is 3.72 MB and the web derivative 1.57 MB (the draft's were 66 kB and its web copy). No
*before* reading was taken. Frame times and load are software GL on the runner, a relative reading.

## Limits

- No photograph, plate or description of 1636 has been read; every form but the plan, the storeys,
  the stone front and the bay's place is the kits'.
- No gutter or downpipe, as 1634: K01's gutter runs round a hip's eaves only.
