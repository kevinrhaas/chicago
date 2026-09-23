---
id: T-1092
title: Re-seat the four grids the NA sheet places — the School Section, Kinzie's Addition, the Michigan St tract and Wabansia's streets — on the adopted registration, and re-bake what stands on the ground that moves
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1090
opened: 2026-09-12
closed: 2026-09-12
pr: 1223
claimed_by: run 9/12/2026, 8:31:47 PM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-13T02:38:49.018Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34730623338
---

Re-seat the four grids the NA sheet places — the School Section, Kinzie's Addition, the Michigan St tract and Wabansia's streets — on the adopted registration, and re-bake what stands on the ground that moves.

Piece 2 of 2 of **T-1090 — Adopt the eleven-point registration of the NA Wright sheet: regenerate the nine NA-keyed traces, re-seat the School Section grid on a G1 that moves 16.2 m, and re-bake what stands on it**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance:** the four grids are re-seated by re-running their own generators (never by
hand), `validate.py --stale` is green because the meshes standing on the moved ground were
regenerated in the same commit, and `tools/rederive_datum.py` is green because the datum is
fitted from the BPL master and this sheet is not it. The School Section grid carries no raw
pixel of its own — it is rescaled onto the section's exact mile square and anchored on G1,
which M1 moves 16.21 m, so it moves rigidly by that and by nothing else. Takes T-1091 first:
this ticket seats on the registration that one adopts.

Measured medians under M1, from `data/traces/gcp/wright_1834_nara_hup_fit_adjudication.json`:
Wabansia streets 22.80 m, Michigan St tract grid 9.98 m, Kinzie addition street grid 7.84 m.
