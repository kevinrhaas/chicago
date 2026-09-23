---
id: T-1090
title: Adopt the eleven-point registration of the NA Wright sheet: regenerate the nine NA-keyed traces, re-seat the School Section grid on a G1 that moves 16.2 m, and re-bake what stands on it
state: split
epic: META
requested_by: loop
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: null
claimed_by: null
blocked_on: null
needs_bake: true
closed_at: 2026-09-12T22:02:20.994Z
claimed_run: null
---
Adopt the eleven-point registration of the NA Wright sheet: regenerate the nine NA-keyed traces, re-seat the School Section grid on a G1 that moves 16.2 m, and re-bake what stands on it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

T-0878 adjudicated the fit and did not adopt its own answer, because the ticket's own
acceptance said to measure the cost of adoption first and the measurement says the cost is
more than one run. The adjudication is
`data/traces/gcp/wright_1834_nara_hup_fit_adjudication.json`, recomputed on every commit by
`tools/adjudicate_wright_na_fit.py --check`; read its `verdict` block before touching
anything here. In short: M1, an eleven-point affine adding the School Section's north-west,
south-west and south-east corners to the eight, is the only candidate that improves the
out-of-sample number (leave-one-out 23.29 → 20.17 m) and it cuts the section's mile error
from 3.06 to 1.03 per cent, which is the control's own 0.79 per cent and not the model's.

WHAT ADOPTION IS, and it is why this is an L:

1. `fit` in `data/traces/gcp/wright_1834_nara_hup_gcps.json` becomes M1's coefficients,
   with the eight-point fit retained beside it as what it was — the published
   registration of T-0787, still the transform the scan-to-scan block is comparable
   through. Do not silently overwrite a published number.
2. Nine committed traces are keyed to this pixel space and every one of them moves.
   Measured medians under M1: School Section numbering 27.11 m (max 84.37), Wabansia
   numbering 25.22, Wabansia streets 22.80, Kinzie block name 21.29, Wabansia water lots
   17.98, Michigan St tract grid 9.98, Kinzie addition numbering 8.19, Kinzie addition
   street grid 7.84. Each has a generator; re-run it, do not hand-edit the output.
3. The School Section grid carries no raw pixel of its own — it is rescaled onto the
   section's exact mile square and anchored on G1, which moves 16.21 m. So it moves
   rigidly by that, and `tools/generate_school_section_grid.py` is the thing to re-run.
4. `needs_bake`. Ground moves under structures, so `validate.py --stale` will refuse the
   data change until the meshes are regenerated. Budget a `--only` bake per touched
   structure, or a town bake if the count is large — and that alone is most of a run.
5. The datum does NOT move: `tools/rederive_datum.py` fits from the BPL master and never
   reads this sheet. Assert that rather than assume it — a green `rederive_datum.py` in the
   PR is the evidence.

If the four pieces will not fit one run — and the measurement says they will not —
`ticket.mjs split` this before claiming rather than shipping a self-invented part 1 of 2.

**Where the reasoning is:** `docs/RESEARCH/wright_1834_nara_hup_fit.md`.
