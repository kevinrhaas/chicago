---
id: T-1053
title: The three over-declared South Water entries cannot be narrowed without re-lotting a yard building, because frontage.lots is also the block's declared business front
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0449
opened: 2026-09-12
closed: 2026-09-12
pr: 1181
claimed_by: run 9/12/2026, 2:29:20 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T08:29:21.843Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34680626097
---

The three over-declared South Water entries cannot be narrowed without re-lotting a yard building, because frontage.lots is also the block's declared business front.

Piece 2 of 2 of **T-0449 — Four South Water frontage entries declare lots their runs never reach, and each hides its block's headroom**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

MEASURED ON THIS BRANCH, 2026-09-12, by T-1054. The measurement is not in doubt on any
of the three; what this ticket owns is the decision the measurement runs into.

`frontage.lots` looked like one fact — the lots a party-line run stands across — and it
turns out to answer three different questions in three different files:

1. **the run's own strip.** `frontage_strip` in `tools/generate_block_infill.py` runs the
   strip from the west line of the westmost declared lot to the east line of the
   eastmost, and an east-anchored run takes its anchor off that eastmost line. On all
   three entries the eastmost declared lot IS the one the run stands on, so narrowing the
   list moves nothing.
2. **the block's lot classes.** `check_block` puts every declared lot in `built on by
   this parcel`, and that is also what makes an ancillary yard building on a declared lot
   stand behind a roof of the same parcel.
3. **the block's declared BUSINESS FRONT.** `shared_business_fronts` in
   `tools/plat_occupancy.py` applies the owner's 2026-08-27 clause — a documented store
   standing at the street does not exhaust a business-front lot — to exactly
   `int(index) for index in frontage["lots"]`.

So narrowing a declaration to the truth withdraws the owner's clause from the lots it
drops, and `generate_block_infill.py --check` refuses all three corrections for reasons
that are nothing to do with the declaration:

| entry | narrowed to | what refuses it |
|---|---|---|
| `..._south_water_franklin` | 4, 6 → **6** | the A3 yard building on lot 4 stands behind no roof of the parcel |
| `..._south_water_wells` | 0, 2, 4 → **2, 4** | the A3 on lot 0 reads as standing behind `h_jones_store`, which the parcel did not build |
| `..._south_water_dearborn` | 0, 2, 4 → **4** | the same, with `chicago_american_office` |

**The question, and it looks like the owner's.** His ruling is about a FACE — "a lot of
this block's own declared business front is not exhausted by a researched building
standing at the street on it" — and the field it is keyed to is about a RUN. Two
readings, and they are not the same size:

- **key the clause to the face** (every lot of the block that comes to the face a run
  fronts). Truthful to the ruling as it was worded, and it relaxes occupancy on lots
  across the town that no run was ever dealt — which is a change to what the schedule
  offers, and wants its own measurement before anybody spends it.
- **give the entry a second field** — the declared business front beside the declared
  run — so the two questions stop sharing an answer. Additive and local, but it is new
  schema on the recipe and somebody has to say which lots a block's front is.

Either way, the yard buildings on `franklin` lot 4, `wells` lot 0 and `dearborn` lot 0
still have to be answered for: on the first there is no roof behind them at all, and a
yard building serving nothing is the false statement the over-declaration was covering.
Re-lotting one moves geometry and re-bakes.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- One of the two readings above is chosen and written down with the reason, or the
  question is put to the owner with both costs measured.
- The three declarations name only the lots their runs measurably stand across, and
  `tools/measure_frontage_declaration.py --check` passes with `CONCEDED` empty.
- Every yard building the correction orphans is answered for — re-lotted onto the lot it
  actually serves, with its bake in the same commit, or refused in writing.
- `tools/generate_block_infill.py --check`, `tools/reconcile_665.py --check` and
  `bash tools/check.sh` all green; `validate.py --stale` is what catches a record that
  stopped matching its mesh, so a moved roof that skipped its bake cannot merge.

**Links:** T-0449 (the parent) · T-1054 (the measurement) · T-0429 · T-0432 ·
T-0199 / T-0213 (the owner's business-front clause) · `tools/plat_occupancy.py`.

