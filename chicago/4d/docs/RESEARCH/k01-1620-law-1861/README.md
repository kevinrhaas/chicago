# 1620 Prairie, the Robert Law house, refined from the district draft to a K01 brick house (T-1861)

Package N03 of the T-1837 Prairie programme. The draft T-2334 stood is refined **in place**:
`law_house_1620_prairie` keeps its id and its placement frame, and its archetype changes from
`prairie_draft` to `k01_frontage`. The draft rules' `skip` names `r1886-1620-f`, so the draft
builder stands no second building there. Its stable on the alley
(`law_house_1620_prairie_coach_house`) is still the draft's (R-series work).

1620 is the one house on the block the 1911 sheet does not draw: the T-1840 census stands it for
1904 on Robinson 1886 plate 10 and the 1904 Blue Book. Its plan, place and brick are read off
that plate through its T-1250 fit (4.54 m RMS, the weakest of the four).

## The kit changes

1. **Brick arches on a brick street front** — `street_front_trim.brick_heads: "segmental"`. A
   brick street front kept the stone lintel or K09 head on every window (T-2341). A record that
   names `brick_heads` lays them in the brick instead: two rowlock rings on a segmental arch,
   the head the side and rear walls already wear (T-2291). The hole stays the K01 rectangle, so
   the sash under each arch stays flat. Refused on a stone front.
2. **The scroll-band fence on the front-yard boundary** — `boundary.fence` may name
   `k11.fence.scroll_band` as well as `k11.fence.spear_on_curb`. The kit's `fence_run` already
   built both styles; the frontage builder had only ever asked it for the spear.

Every other kit asset keeps its bytes: `python3 generators/k01_emit.py --check` and the K12, K13
and K16 emitters rebuild 1600, 1608, 1612, 1808, 1729's conservatory, 1638's front and 1812's
coach house to the committed bytes. Their manifest input hashes move because the builder module
is hashed.

## What the house is

The register's brief (frontage-20-006, not a source record): "irregular earlier brick envelope
across lots 13-14, projecting bay, arched windows, stoop, bounded roof and lattice/iron
boundary; rear stable remains separate".

Built:
- **The plate's L under one rectangle**, 16.75 m from the rear wall to the front by 11.25 m
  across it: the 16.75 x 7.5 m main body and the shallower 10.75 x 3.75 m south part. The
  origin moves 3.75 m south of the draft's so that the rectangle starts at its own (0, 0).
- two storeys over a raised basement (1.4 m principal floor, 3.9 m and 3.6 m storeys; the
  draft's 3.5 m upper storey left the arch no room under the cornice's bed moulding).
- three bays across the front: the door on the south bay with a K07 stoop, a window, and a K08
  canted bay on the north half, its eaves clear of the K10 corner bracket.
- windows on all four walls (4 a storey on the south, 3 on the north, which faces 1616 across
  a 4.7 m side yard, and 3 at the rear), every one under a segmental brick arch.
- K03 common brick, K06 two-over-two sash, a K10 bracketed timber cornice, a 30-degree K04/K05
  hip in painted standing-seam tin, two brick stacks, K04 gutters and pipes.
- **The boundary**: the K11 scroll-band fence on a stone curb along the street line (5.93 m in
  front of the house), a pair of walk-gate leaves on the stoop's walk, a single walk gate across
  the south side yard's mouth, and a 1.2 m brick wall with piers on the south lot line from the
  street back to u 12.0.

Liberty `L-k01-1620-law-1861`; 1620 is retired from `L-draft-prairie-16-18-west-2334`.

Not built:
- the plate's **notch**: the rectangle closes the 6.0 x 3.75 m rear corner the L leaves at the
  south-west, 22.5 m2 over the traced 168 m2, as 1612's closes its court. K01's traced rear
  wing (T-2347) is what would reopen it.
- **arched sash**: the arches stand over flat-headed sash.
- the **1898 Tribune drawing** the register says "supports bay/arches" has not been read.
  Nothing about this house's own trim is built.

## Captured and measured

Captured with `node tools/qa_k01_t1861.mjs` on the published `/1904/` app. *Before* is `dev` at
b625bb6 (the draft); *after* is this branch. Desktop is 1280×800 at full detail and phone is
390×780 at light. The stands: front (across Prairie), oblique from the south-east, the north side,
rear (from the south-west) and roof (from the air). All four runs had 0 page errors and 0 failed
requests, and every stand stayed within the scene budget.

| | load to ready | JS heap | draw calls | triangles | frame (software GL) |
|---|---|---|---|---|---|
| desktop before → after | 20.0 → 29.0 s | 25.6 → 25.8 MB | 80-109 → 90-119 (+10) | 1.59-2.86 M → 1.68-2.96 M (+93 k) | +3 to +9 % |
| phone before → after | 12.1 → 11.8 s | 25.5 → 25.8 MB | 41-63 → 52-73 (+10 to +11) | 217-337 k → 309-430 k (+93 k) | +10 to +19 % |

The master is 4.91 MB and the web derivative 1.29 MB; the scroll-band fence is about a third of
the master. Desktop load time swings by seconds between runs on this runner (1608's two readings
spanned 25-38 s on the same tree), so the rise is not a claim. Frame time is a relative reading
on software GL, not a device claim.

## Limits

- No photograph, plate or description of 1620 has been read. Except for the plan, place and
  brick, every form comes from the kits.
- The plate prints no storey count and draws no openings, bay or boundary. The two storeys, the
  bay's place and every window are reconstructed.
