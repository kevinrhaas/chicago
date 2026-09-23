# data/residents/reconstructed_trades/

DERIVED. Written by `tools/reconstruct_trade_households.py --build` (T-1347, of T-1173),
the `trade_households` stage of the 1835 resident reconstruction programme. Do not
hand-edit a card here: `--check` re-derives the whole directory and refuses a differing
byte, and `tools/check.sh` runs it.

Every person here is `grade: reconstructed` and **nobody in this directory is named by any
source**. They exist because the order book counts the town of 1 July 1835 as short of
that many adults at a trade in that division, and each card says on its face which bucket
ordered it, which seed drew every value and what evidence would retire the person.

The directory is deliberately OUTSIDE `data/residents/households/`, for the reason
`readmitted/` is: that directory is re-derived by the research mints and
`data/residents/index.json` is derived from it, so a reconstruction that is not a reading
lives here and is overlaid onto the scene by `tools/compile_scene.py`.
