# 1608 Prairie refined from the district draft to a K01 brick house (T-2341)

Piece 1 of T-1859 (Refine 1600, 1604 and 1608 north-west frontage), split because 1600's
corner windows and curved bay and 1604's traced rear range are each a run of their own
(T-2342, T-2343). The draft T-2334 stood is refined **in place**: `house_1608_prairie` keeps its
id, its traced main-body rectangle and its placement, and its archetype changes from
`prairie_draft` to `k01_frontage`. The draft rules' `skip` names `s20-1608-f`, so the draft
builder stands no second building there.

## The builder change

K01 was cut for 1808 Prairie and refused every construction but `brick_with_stone_front`.
It now also builds `construction: brick`, keyed on the record naming no `stone_front`:

- the street front is laid in the side walls' K03 brick instead of the K02 stone;
- a brick **street front's** openings keep the front's stone dressings (K09 head, or K01's
  flat lintel) rather than the side walls' brick segmental heads;
- params refuse a mismatch (a stone front with no `stone_front`, or a brick one with one).

1808's resolved parameters are unchanged and `python3 generators/k01_emit.py --check` holds
every K01 asset to its bytes. The four kit assets that hash the K01 module (1808, the 1729
conservatory, the 1638 front, the 1812 coach house) were re-emitted for the code hash only;
their GLBs are byte-identical.

## What the house is

Read from sheet 20 (T-2328 trace, T-1840 census `s20-1608-f`): two storeys and a basement,
brick, a bay on the Prairie face (south half) and a small projection on the south wall. Built:
the K08 canted bay on the front (centred 0.76 m north of the traced bay so its eaves clear the
K10 corner bracket) and the K08 full-height projection on the south wall; the door, therefore,
on the north half (the draft had it south, where the bay stands). Everything else is the kits'
reconstruction: K03 brick, K06 two-over-two sash, K09 cornice-hood lintels, K07 door and stoop
(9.31 m to the walk), K10 bracketed cornice, a 30-degree K04/K05 hip in painted standing-seam
tin, two brick stacks, K04 gutters and pipes. Liberty `L-k01-1608-brick-front-2341`; 1608
is retired from `L-draft-prairie-16-18-west-2334`.

Not built: a strip about 0.85 m out along the north wall (u 6.2-13.0 m) that the trace draws
and the census does not mention.

## Captured and measured

`node tools/qa_k01_t2341.mjs` on the published `/1904/` app; *before* is `dev` at eeac199
(the draft), *after* this branch. Desktop 1280×800 at full, phone 390×780 at light. Stands:
front (across Prairie), oblique from the south and north walks, rear (1608's own yard), roof
(the air). 0 page errors and 0 failed requests on all eight runs. The first full run's rear
stand stood inside a neighbour's building; it was moved and the rear and roof stands re-taken
both sides (`*-b.json`), and those are the images here.

| | load to ready | JS heap | draw calls | triangles | frame (software GL) |
|---|---|---|---|---|---|
| desktop before → after | 25.0-38.5 → 25.2-25.3 s | 23.2 → 23.5 MB | 49-83 → 60-93 (+10 to +11) | 1.41-2.77 M → 1.44-2.80 M (+30 k) | +2 to +5 % |
| phone before → after | 13.4-13.6 → 13.7-13.8 s | 23.2 → 23.5 MB | 20-23 → 31-34 (+11) | 91-119 k → 121-149 k (+30 k) | +4 to +12 % |

The master is 2.69 MB, the web derivative 0.95 MB (the draft's was a small fraction of that);
1808's K01 derivative is 2.02 MB. Every stand stays within the scene budget. Desktop load
swings by seconds between runs on this runner and the fall is not a claim; frame time is a
relative reading on software GL, not a device claim.

## Limits

- No photograph, plate or description of 1608 has been read; every form is the kits'.
- K01 builds a hip roof only, and windows on the south wall only (the north is a blank wall);
  1600's windows to 16th Street need that lifted (T-2342).
