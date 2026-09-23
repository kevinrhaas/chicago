---
id: T-0878
title: Wright's 1834 registration is three per cent long in y: the School Section's mile measures 1658.65 m north-south and 1603.04 m east-west on the same fit
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-12
pr: 1214
claimed_by: run 9/12/2026, 4:54:00 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T22:41:25.243Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34721016295
---

Wright's 1834 registration is three per cent long in y: the School Section's mile measures 1658.65 m north-south and 1603.04 m east-west on the same fit.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while working T-0797, and it is a fact about the FIT rather than about the sheet.

Section 16 is a statute mile square — 1609.344 m — and its north-east corner, State and
Madison, is GCP G1 of `data/traces/gcp/wright_1834_nara_hup_gcps.json`. Measuring the
section's own outer lines on the registered scan, through that fit:

| | measured | mile | departure |
|---|---|---|---|
| east-west | 1603.04 m | 1609.344 m | -6.30 m (-0.39 %) |
| north-south | 1658.65 m | 1609.344 m | **+49.31 m (+3.06 %)** |

The x scale is right to four tenths of one per cent over a mile. The y scale is three per
cent long — **more than the width of any block in the grid**, and eight times the fit's own
16.19 m RMS.

The registration already predicted the direction of this: it measured 5.2 per cent x/y
anisotropy on this scan against 3.7 per cent on the BPL copy and wrote that "the extra
stretch is in the long axis, along which the manuscript was torn and backed". What is new
is the SIZE of it at the bottom of the sheet, measured against a length that is known
exactly rather than against control points.

T-0797 anchored its grid on the section rather than on the paper, so nothing it committed
is wrong. But every OTHER trace off this sheet is placed by the fit alone.

**Acceptance:** state whether the eight-point global affine should stand, and if not what
replaces it — a y-scale correction, a second-order term, or control at the sheet's foot,
which the section's south-west corner and the two reserved corners now supply. Measure the
change on the committed traces before adopting it; a datum that moves is a bigger event
than a fit that is known to be long, and `tools/rederive_datum.py` is the gate that will
say so.

---

## ANSWERED, 2026-09-12

**`data/traces/gcp/wright_1834_nara_hup_fit_adjudication.json`** is the answer and
**`docs/RESEARCH/wright_1834_nara_hup_fit.md`** is the reasoning. Both are recomputed from
committed data by `tools/adjudicate_wright_na_fit.py --check`, which is now a step of
`tools/check.sh`, so the verdict cannot outlive its inputs.

**The eight-point global affine stands where it was fitted and nowhere else.** All eight
control points lie between y=1631 and y=3225 px of a 6628 px sheet; the School Section
occupies y=3169–5495, entirely below every one of them. The three per cent is an
EXTRAPOLATION error, not a scale error, and the section's own square proves the distinction
without any model: the sheet is 0.70055 m/px in x and 0.71397 m/px in y, a real 1.92 per cent
anisotropy, against the fit's 5.2.

**What replaces it is control at the sheet's foot, in the same affine form.** The section's
other three corners — PLSS corners of sections 8/9/16/17, 16/17/20/21 and 15/16/21/22, all
still street crossings — are committed as
`data/traces/gcp/wright_1834_nara_hup_section_corners.json`, with their own ±13 m systematic
uncertainty measured rather than assumed. Both alternatives the ticket named were tested and
both are worse:

| model | RMS/8 | RMS/3 | RMS/11 | leave-one-out | mile N–S |
|---|---|---|---|---|---|
| M0 committed affine, 8 pt | 16.19 | 42.71 | 26.23 | 23.29 | +3.06 % |
| M1 affine, 11 pt, foot control | 18.39 | 6.22 | 16.02 | **20.17** | +1.03 % |
| M2 y rescaled ×0.970273 | 27.89 | 16.88 | 25.36 | n/a | 0.00 % |
| M3 second-order poly, 11 pt | 16.33 | 0.74 | 13.94 | **51.28** | +0.23 % |

M1 is the only candidate that improves the out-of-sample number. M2 buys the mile and pays
11.7 m of RMS on the control the project already had. M3 is an overfit and the leave-one-out
says so rather than a prior about polynomials. M1's residual +1.03 per cent is the modern
control square's own +0.79 per cent, so the remaining error belongs to the control, not the
model — which is why driving the mile to zero (M2) is the wrong target.

**The datum does not move.** `tools/rederive_datum.py` fits from `wright_1834_gcps.json`, the
BPL master, and never reads this sheet. That was the ticket's stated fear and it is not there.

**Adoption is not done here, because the ticket said to measure its cost first and the cost is
more than one run**: M1 moves the committed NA-keyed readings by a median 7.8–27.1 m and up to
84.4 m, and four traces are seated through a G1 that moves 16.21 m. Filed as **T-1091** (adopt
the fit, regenerate the five pure readings) and **T-1092** (re-seat the four grids, re-bake the
ground that moves), split from T-1090 because the queue check refuses an L.

Until T-1091 lands, a reading taken south of Madison Street off this sheet carries about three
per cent of y error, and the `fit` block in the registration now says so in place.
