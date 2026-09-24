# data/residents/staffing_hands/

DERIVED. Written by `tools/mint_staffing_hands_1835.py --build` (T-1448, of T-1434), the
`staffing_hands` stage of the 1835 resident reconstruction programme. Do not hand-edit a
card here: `--check` re-derives the whole directory and refuses a differing byte, and
`tools/check.sh` runs it.

Every person here is `grade: reconstructed` and **nobody in this directory is named by any
source**. They exist because a business record this project holds is short of a hand its
class is staffed with AND the reconstruction order book had an outstanding `lodging/trade`
slot to count that hand in. Both halves had to be true, which is why there are 36 of them
and not the 130 the shops want.

A card here is a CONTAINER for one house's hands in one division — not a family. Each
person carries the house he worked at, the role the staffing model wants, the bucket that
ordered him, and a `slept` block saying whether he lived at his work or boarded out. It
names no roof: T-1199 seats a reconstructed household on the lot grid.

The directory is deliberately OUTSIDE `data/residents/households/`, for the reason
`reconstructed_trades/` is: that directory is re-derived by the research mints and
`data/residents/index.json` is derived from it, so a reconstruction that is not a reading
lives here and is overlaid onto the scene by `tools/compile_scene.py`.
