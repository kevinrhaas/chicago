# T-1881 — 1729 Prairie's photographic sign-off

The owner's 2026-10-28 reopening of 1729 Prairie (Pullman) asked for every reference view
worked to `matches` under the T-3153 bar. Forty-odd runs since then rebuilt the stepped front,
the 18th Street face, the porte-cochère, the rear step, the roof, the ivy, the trees and the
boundary walls. On 2026-11-08 three of the six match records still read `differs`, on six
items. This page is the house's sign-off (AGENTS.md rule 11: one sign-off, never split).

**Acceptance, stated before the work:** every record reads `matches` with nothing `open`; an
item that rests on a gap two pictures or two camera fits disagree about is ruled `within
tolerance` with what was read (T-3153); anything over the bar that the pictures agree on is
fixed in this PR. All four crops below are picture over (or beside) render, from the committed
side-by-sides, which were made from the GLB in the tree (sha256 `968ac3f1…`).

## Ruled within tolerance

| record | item | why |
|---|---|---|
| det 4a08066 | the mansard and cresting ~0.8 m higher in the print | three pictures, three readings. Through det 4a08066 the deck edge is ~11 px high; through det 4a08065 the mansard's face is 50 px against the render's 63, ~0.8 m **lower** than the build; through Taylor 16554 cornice-to-grade is 175 px against 178 and the face 63 against 60. The build sits between the two Detroit prints and agrees with 16554. Taylor 1445's "8-10 % over" was scaled on the GLB's own cornice, so it is not a fourth reading |
| det 4a08066 | the porte-cochère's east arch ~0.6 m wider | Taylor 1445 2.86 m, det 4a08065 2.37 m, this print 3.3-3.5 m, crown read off the ivy. The build's 2.8 m, balanced at both ends as the owner asked, is inside the spread |
| det 4a08066 | 18th Street's parkway trunks up to ~5 m off | planted at Taylor 1445's trunks (18 px/m, square on); this print (5-6 px/m, grazing, ~10 years later) puts them elsewhere |
| det 4a08065 | the door's leaves read at v 5.0, the build's at v 6.875 | the leaves are glimpsed behind an elm trunk, twigs and ivy at ~13 px/m; v 5.0 is the joint between the north block and the entry part. The 1890 Albertype plate, unobscured at ~22 px/m, puts the columns either side of the door within 3-7 px of the build's, and governs (as it does for the lantern) |
| Taylor 1445 | the north block and portico forward of the wall | built, and fixed in the Albertype, det 4a08065 and Clark 1905 records. What remains is this camera's fit along the Prairie front (its solve: no level pinhole fits the front's ends and its piers, 10.8 px rms) |

The det 4a08065 record's umbrella item (the owner's 2026-10-28 report) closes as `fixed` with
the rest: what it names was rebuilt as its own items in that record.

## What was looked at again

All six side-by-sides were looked at whole, not only their open rows. Taylor 16554 renders
~25 px high and shifted along the flank against the photograph, which is its camera's
principal point, not the house: heights between the same features agree within ~3 px
(`heights-taylor-16554.jpg`). Nothing new over the bar that the pictures agree on was found
on the house. The stable, the glasshouses and the ground south of 18th Street are T-1934's
and are not judged here.

## Crops

- `mansard-det-4a08065.jpg` — det 4a08065 (left) and render (right), y gridded: the print's
  mansard face ~50 px, the render's ~63.
- `mansard-det-4a08066.jpg` — det 4a08066 and render: the print's roof stands higher.
- `heights-taylor-16554.jpg` — Taylor 16554 (top) and render (bottom), same heights, offset.
- `door-det-4a08065.jpg` — det 4a08065 and render at the portico: the door behind the elm.
