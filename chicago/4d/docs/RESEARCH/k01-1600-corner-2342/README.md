# 1600 Prairie refined from the district draft to a K01 brick corner house (T-2342)

Piece 2 of T-1859 (Refine 1600, 1604 and 1608 north-west frontage). The draft T-2334 stood is
refined **in place**: `house_1600_prairie` keeps its id, its traced main-body rectangle and its
placement, and its archetype changes from `prairie_draft` to `k01_frontage`. The draft rules'
`skip` names `s20-1600-f`, so the draft builder stands no second building there.

Built on the brick street front T-2341 taught K01 (PR #684). That change is carried here
unaltered, line for line, so this branch builds on `dev` whichever of the two lands first.

## The builder changes

1. **Windows on the north wall** — `north_bays`, window centres along the north wall, east to
   west. K01 was cut for 1808, whose north wall stands 0.02 m off the Glessner court, so it
   left that wall blank. 1600's north wall is its 16th Street side. A record that names
   `north_bays` gets sash on that wall at every storey, and the K03 string course at the
   second-floor line, run out past the north-west corner to meet the rear wall's. A record
   that names none builds exactly as before. Downpipes stay off the north wall.
2. **A bow sized to its sheet** — `bays[].plan`. A K08 bow (`k08.bay.bowed`) may take the
   record's chord and rise, never past a half-round. Any other plan is refused.

Every other K01 asset is unchanged: `python3 generators/k01_emit.py --check` holds them all to
their bytes.

## What the house is

Read from sheet 20 (T-2328 trace, T-1840 census `s20-1600-f`, '2B brick dwelling (D); curved bay
on the Prairie face; no rear building'): two storeys and a basement, brick, and a curved bay on
the north half of the front. In the footprint frame the trace draws it as a half-round, 3.06 m
at the wall and about 1.6 m out, with its north end on the 16th Street corner.

Built:
- the bow, 3.1 m on its chord and rising 1.55 m, centred 4.7 m from the south corner. Its north
  junction stands 0.75 m inside the corner, where the trace has it flush. K01 leaves at least
  0.3 m of pier at a corner, and the bow's eaves must also clear the K10 corner bracket (1608's
  bay moved 0.76 m for the same reason). Its cone is laid at 0.3, not the kit's 0.45, over a
  2.2 m upper storey, so a half-round's cone (whose apex is on the wall) meets the wall below the
  cornice's bed moulding.
- the door on the south half, with a K07 stoop running 8.84 m to the walk.
- five windows a storey on the 16th Street side, four on the south side and two at the rear.

Everything else comes from the kits: K03 brick on all four walls, K06 two-over-two sash, K01's
flat stone lintel over the door and over the chamber window, a K10 bracketed cornice, and a
31-degree K04/K05 hip in painted standing-seam tin. On the roof stand two brick stacks; K04
gutters and pipes run to splash stones. The K09 restrained surround is named for the principal
storey but stands over no window on this front, because the door and the bow take both bays.
Liberty `L-k01-1600-corner-2342`; 1600 is retired from `L-draft-prairie-16-18-west-2334`.

Not built: a shallow projection about 0.85 m out on the south wall (u 8.4-12.0 m). The trace
draws it but the census does not mention it. The draft's rectangle also stands about 0.45 m
inside the traced south wall, because a spike in the trace bounds the fit; that rectangle is
kept.

## Captured and measured

Captured with `node tools/qa_k01_t2342.mjs` on the published `/1904/` app. *Before* is `dev` at
99027c2 (the draft); *after* is this branch. Desktop is 1280×800 at full detail; phone is
390×780 at light. The stands are: front (across Prairie), oblique from the 16th Street corner,
the 16th Street side, rear (from the north-west), and roof (from the air). All four runs had
0 page errors and 0 failed requests, and every stand stayed within the scene budget.

| | load to ready | JS heap | draw calls | triangles | frame (software GL) |
|---|---|---|---|---|---|
| desktop before → after | 26.1 → 39.8 s | 25.0 → 25.2 MB | 65-106 → 77-116 (+10 to +12) | 1.50-3.00 M → 1.56-3.06 M (+61 k) | +3 to +7 % |
| phone before → after | 14.1 → 14.2 s | 25.0 → 25.3 MB | 36-70 → 48-81 (+11 to +12) | 179-617 k → 241-678 k (+61 k) | +5 to +15 % |

The bow's upper sashes were then lowered 0.1 m (sill 0.5 m above the bay's upper floor) to fit
inside its 2.2 m storey, as `tools/check_bay_kit.py` requires; the captures predate that change.
The master is 3.94 MB and the web derivative 1.13 MB. Desktop load time swings by seconds
between runs on this runner (1608's two readings spanned 25-38 s on the same tree), so the rise
is not a claim. Frame time is a relative reading on software GL, not a device claim.

## Limits

- No photograph, plate or description of 1600 has been read; every form comes from the kits.
- The sheet draws no openings, so the 16th Street side's windows are reconstructed, like every
  other window here.
