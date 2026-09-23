---
id: T-0431
title: Open blk_south_water_clark: 4 roofs of headroom on two free lots
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0420
opened: 2026-08-29
closed: 2026-09-05
pr: 916
claimed_by: run 9/5/2026, 2:27:53 PM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-05T20:33:26.622Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33987077283
---

Open `blk_south_water_clark` — 4 roof(s) of headroom, 2 free lot(s) — under the anonymous-block
programme (T-0028). Piece 3 of 4 of **T-0420**, which held all four South Water blocks in one
ticket: four blocks is four demonstrations, and T-0028's programme rule is one run, one
demonstration, one successor. This ticket owns ONE block, which is one run.

**Why this ground is workable now, and it is the whole reason the parent exists.** T-0143 and
T-0188 each refused to tighten a party-line row against a street line that might move, and T-0317
inherited the refusal. T-0009 closed it on 2026-08-29 under the owner's ruling: the drawn South
Water line does NOT move — the corridor was re-derived from committed control (`recentred`, +8.58 m)
and `data/streets/1835.json` was not touched. The refusal is discharged for the four blocks that
front this reach. `blk_south_water_market` is NOT one of them and is not in this family of
tickets: T-0183 measured it out as a wedge the South Branch pinches to 2.8 m of depth at Market,
and what to do with that wedge is with the owner.

**The block, re-derived on 2026-08-30 by `tools/reconcile_665.py`** (not typed — every figure here
is read back out of `data/reconstruction/1835_665_roof_programme.json`, and a run that finds them
changed should trust the tool and correct this table):

| field | value |
|---|---|
| bounded by | south_water (N), lake (S), clark (W), dearborn (E) |
| lots | 8 |
| standing roofs | 10 |
| free lots | 2 |
| headroom | **4** — 3 principal, 1 ancillary |
| families dealt | A3, C2, D3, D4 — one roof each (**corrected 2026-09-05**: the table
  above was written on 2026-08-30 and the schedule has re-dealt since; trust the tool) |
| frontage weight | 0.6066 (**corrected 2026-09-05**, was 0.6023) |
| trade roofs in the deal (T-0213) | 1 |

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The 4 roof(s) stand on `blk_south_water_clark`'s own committed lots, and the row stands ON THE BLOCK FACE
  rather than on a re-derived line — that is the distinction T-0143 and T-0188 were protecting and
  it survives the ruling unchanged.
- `tools/reconcile_665.py` re-derives and the census reconciles: this block moves to
  `at_capacity`, or its remaining headroom is stated and why.
- The roofs are BAKED in the same commit (`./tools/bake.sh --only <structure-id>` per structure —
  `validate.py --stale` hard-fails a record that no longer matches its committed mesh), and
  `tools/publish.sh` mirrors the result.
- A screenshot from the same spot shows roofs that were not there. This is a VISIBLE ticket and it
  is the payoff the whole programme was for; it does not need the invisible-run exemption.
- One successor is handed on, per T-0028: the next block in this family, or — for whichever of the
  four runs last — the statement of where the programme's committed ground runs out.

**Links:** T-0420 (the parent) · T-0365 (the succession this discharges) · T-0009 (the ruling) ·
T-0028 (the programme) · T-0143 · T-0188 · T-0317 · T-0183 (the market wedge, not this ground) ·
`tools/reconcile_665.py` · `tools/measure_block_gating.py`.

**Prior attempt: PR [#601](https://github.com/kevinrhaas/custom/pull/601), closed unmerged 2026-09-05 under T-0803.**
Opened 2026-08-30; **541 commits behind `dev`** with 73 changed files and a bake when it
was read. **Read its PR body before starting** — it carries two things this ticket will hit
again. First, the finding that **the schedule dealt 4 roofs and the ground holds 2**:
`reconcile_665.py` sizes principal room as `ROW_UNITS_PER_LOT * (free_lots - 1)`, which
counts LOTS, and lot 2 is free only under the owner's 2026-08-27 business-front clause, so
it is by construction not a whole lot — measured, 12.97 m free to the west of the drug
store and 1.42 m to the east. Filed as **T-0439**. Second, the correction that made the
parcel possible at all: the first deal (2026-08-15) was declared on frontage lots `[2, 4]`
but stands entirely on lot 4, so `reconcile_665.py` counted lot 2 free while
`generate_block_infill.py`'s T-0105 lot accounting counted it built on. Narrowing the
declaration to `[4]` moves no coordinate and both units re-derive byte-identical.

Its branch could NOT be deleted from the session that closed it — this environment's proxy refuses a ref delete over both git and the REST API (HTTP 403) — so `ticket.mjs claim` **will see it as a rival branch and refuse**. That refusal is a false stop: the PR is closed and the branch is abandoned. `claim T-0431 --force` is correct here. `ticket.mjs inflight` reads it as COLD, which is the honest signal.
