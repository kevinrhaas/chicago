# T-3771 — 2140 Prairie's columned porch and stair, its dormers' crocketed gables, its tall stack's pots

Piece 2 of T-1928 (S17A). Piece 1 (T-3770, `docs/RESEARCH/k01-2140-tucker-3770/`) put the house on K01; piece 3
(T-3772) is the rear range's fittings and the before/after views and costs; T-1929 solves the cameras, works the
photo-match down and signs off the image gate. Liberty `L-k01-2140-tucker-3771`.

## What was read

The two Chicagology photographs (`chicagology_2140_photo_a`, `chicagology_2140_photo_b`, forms only,
`check_required`; their forms-only reading is banked in `tools/rights_derivation_baseline.json` by T-3770), opened
at full size and cropped; the 1898 quarter-century plate (not entered as a source) confirms the porch square-on.
Numbers are proportions read against the round tower's drum at about 86 px a metre in the second photograph, not
through a solved camera.

| what | where in the picture | read | built |
|---|---|---|---|
| porch | photo b x 1000-1290, y 940-1400 | before the door bay, about 3 m wide and 2 m out; a pair of turned shafts with Corinthian capitals at each front corner; plain entablature; stone balustrade on top as a balcony | K01 door hood on columns (`entrance_kit.hood`): `cluster` 2 shafts a side, `carved` 2 tiers, stone fabric and railing; soffit 4.9 m, frieze 0.5 m, cornice 0.2 m, balustrade 0.6 m |
| stair | photo b x 1050-1462, y 1270-1460; the plate | straight flight from the porch to the walk, toward the street, iron rails | K07 stoop 3.0 m wide (the porch's), landing 2.0 m, the street line 4.8 m out |
| dormer gables | photo b x 1080-1200, y 230-520 (and the 22nd Street dormer) | steep coped gables, crockets, a pinnacle at each edge of the face, a cross finial | `head: gable` at 60 degrees with `ornament` (coping, 3 crockets, pinnacles, finial) on both built dormers |
| tall stack | photo a x 590-720, y 210-460; photo b x 530-700, y 120-450 | four tall ribbed pots in a row along the 22nd Street flank (three seen in b), corbelled head with dentils, two narrow sunk slots a face, no bands | K15 `k15.stack.sherman` less its bands; `across: x`, 4 flues, `long` pots, plan 1.5 x 0.8 m; panels 2 x 0.08 m |

## The canopy

The ticket names "the southern entrance canopy" (the register's brief). That is the arched glass canopy over the
same door in the first photograph, which also shows the conical spires, and the 1911 sheet's one-storey `GLASS`
room before the door bay. The porch in the second photograph and the 1898 plate stands in the same place, with the
flat-topped towers. The register asks for one declared 1904 state; T-3770 kept the flat-topped towers, and the
canopy goes with the spires, so the porch is built and the canopy is not. A view dated by July 1904 showing the
spires and the canopy replaces both together (T-1929).

## The kit change

K15's head reads the roof under a stack (`k01_frontage_params.mansard_cover`), and it refused any mansard with a
mansard crown outright, because a mansard crown's covering is not read. 2140's crown stands over the square tower on
the Prairie front; both its stacks stand metres clear of it. The refusal now applies only to a stack standing under
the crown's plan (its overhang included); a stack clear of it reads the main mansard. No other record's bytes move:
the params module is not hashed into any mesh's inputs, and before this a K15 stack on a crowned mansard could not
build at all.

## Not built here

The polygonal tower's gabled faces, the round-arched heads and carved hoods (T-1929); the north street dormer the
square tower's crown displaces (T-3770's liberty); the rear range's fittings (T-3772); the corner fence (T-1945).

## Views

Rendered with `tools/render_structure_review.py` (Blender 4.5.3, AgX, -1.5 EV) from three ad-hoc cameras in the
building's frame (u east, v north, origin at the main body's south-west corner): south-east street oblique
(32, -16, 1.7 → 11, 6, 6.5, 30 mm), square-on the porch (24, 5.8, 1.7 → 13.38, 5.8, 4.0, 32 mm), and a raised
oblique over the roof (30, -14, 15 → 8, 7, 11, 34 mm). The solved photo-match views are T-1929's.
