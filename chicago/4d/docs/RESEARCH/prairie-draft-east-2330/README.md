# The district draft's east side, 18th to 20th Prairie (T-2330)

Piece 2 of T-2159. The builder T-2329 wrote (`tools/draft_prairie_1904.py`) is run on the block's east side, and the result is read in the actual published `/1904/` app.

## What stands

There are ten houses: 1801 Kimball, 1811 Coleman/Ames, 1815 Sears/Meeker, 1823 Dent, 1827 Doane, 1901 Ream, 1905 Field Sr., 1919 Field Jr., 1923 Kellogg and 1945 Armour/Corwith. There are also seven alley buildings, behind 1811, 1815, 1827, 1901, 1905, 1923 and 1945, which are the barns, garages and stable that sheet 28 draws. That is every east-side row of the census (frontage-28-049 to -058) and every detached rear polygon the trace owns there. 1801, 1823 and 1919 have no detached rear polygon on the sheet. Their rear ranges are attached and stand as wings.

Each house is placed by the data in `data/components/prairie_1904/draft_prairie_1904.json`:
- block 28's `sides` gains `"east"`;
- one frontage row per address carries the register's silhouette;
- `by_side.east` names the pass (T-2330) and the side's own liberty (`L-draft-prairie-18-20-east-2330`).

The west side's 18 records and GLBs are byte-identical.

| | roof | silhouette the register names |
|---|---|---|
| 1801 Kimball | steep hip, dormers | conical corner tower at the 18th Street corner, pale (Bedford) stone |
| 1811 Coleman/Ames | Romanesque hip | brownstone front on brick sides and rear |
| 1815 Sears/Meeker | mansard | stone, 'mansard with gabled dormers' |
| 1823 Dent | mansard, 3 stacks | 'high attic/mansard profile, tall chimneys', brick |
| 1827 Doane | mansard | square tower under a pyramid plus a lower round bay under a cone |
| 1901 Ream | mansard | post-1887 Second Empire stone front, central entrance |
| 1905 Field Sr. | mansard | Second Empire, central portico |
| 1919 Field Jr. | hip, dormers (2½S.B.) | the street body, with the rear range behind |
| 1923 Kellogg | low hip | restrained, no tower (the register says not to invent one) |
| 1945 Armour/Corwith | hip, dormers | corner mansion over its rear2B range |

## Three small builder changes (west output unchanged)

1. **The door was facing the wrong way.** The archetype put a `"north"` entrance at the high-v end of the front, and v points north only on the west side. On the east side v points south, so every `"north"` door would have stood at the south end. The builder now writes `v_toward: "south"` on records whose lots face that way, and the archetype reads it. West records do not carry the key, so their bytes do not move.
2. **A square tower.** `corner_tower` takes `sides: 4` for a square shaft under a pyramid, which Doane needs. The register's rule is "preserve both different tower geometries". The default 8-sided path is float-identical.
3. **The street body of a one-part trace.** Sheet 28 traces 1919 and its rear range as one 606 m² part. The largest rectangle inside it is a 47 × 7 m strip down the lot, which would have stood as the house. The frontage row's `front_body_from_u_m: 21.3` fits the main body in front of the part's own break, where it narrows to the street front. The result is a 25.8 × 9 m body with the 21 × 11 m rear range behind it.

The builder also stops writing "the sheet marks it 'D' (dwelling)" for 1919, whose 1911 label is *The Gatlin Institute*. The record now says the 1911 use is not carried back, and that the 1904 residence is inferred from the register's family row.

## Captured and measured

Captured with `node tools/qa_draft_t2330.mjs` on the published `/1904/` app. *Before* is dev e55bc287e (the west draft merged). *After* is this branch. Desktop is 1280×800 at full detail; phone is 390×780 at light. There are six stands: the landing (the spawn, looking down the avenue), across (from Glessner's corner at 1801 and 1811), the west walk, the east walk, the east alley and the air. All four runs had **0 page errors and 0 failed requests**.

| | load to ready | JS heap (after GC) | draw calls | triangles at the stands |
|---|---|---|---|---|
| desktop before → after | 24.9 → 24.9 s | 19.5 → 20.8 MB | 54-87 → 56-87 | 1.38-2.67 M → 1.48-2.77 M |
| phone before → after | 13.0 → 12.9 s | 19.5 → 20.8 MB | 49-71 → 51-71 | 314-534 k → 391-612 k |

The 17 east GLBs add 665 KB of web derivatives (4.15 MB of masters). The renderer batches by material key, so flat colours add at most two draw calls. Frame time is read on this runner's software GL (`frame_ms_median` in the JSON). It rose about 15-35 % with the added triangles, which is a relative reading, not a device claim.

## Limits

- None of the three tower corners (1801, and 1827's two) is read off the sheet.
- 1919's projecting tower/bay is T-1906's to draw. 1905's conservatory bay and fence are T-1904's and T-1905's.
- Rounded bays stay square-cornered projections, and no K02-K16 kit part is laid, as on the west side.
