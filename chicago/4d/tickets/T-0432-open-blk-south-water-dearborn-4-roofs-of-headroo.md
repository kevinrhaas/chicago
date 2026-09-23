---
id: T-0432
title: Open blk_south_water_dearborn: 4 roofs of headroom on two free lots
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0420
opened: 2026-08-29
closed: 2026-09-11
pr: 1135
claimed_by: run 9/11/2026, 9:27:42 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-11T15:55:16.019Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34609865983
---

Open `blk_south_water_dearborn` — 4 roof(s) of headroom, 2 free lot(s) — under the anonymous-block
programme (T-0028). Piece 4 of 4 of **T-0420**, which held all four South Water blocks in one
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
| bounded by | south_water (N), lake (S), dearborn (W), state (E) |
| lots | 8 |
| standing roofs | 10 |
| free lots | 2 |
| headroom | **4** — 3 principal, 1 ancillary |
| families dealt | A5, D4, D5, H3 — one roof each |
| frontage weight | 0.4886 |
| trade roofs in the deal (T-0213) | 0 |

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The 4 roof(s) stand on `blk_south_water_dearborn`'s own committed lots, and the row stands ON THE BLOCK FACE
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

**Prior attempt: PR [#599](https://github.com/kevinrhaas/custom/pull/599), closed unmerged 2026-09-05 under T-0803.**
Opened 2026-08-30; **515 commits behind `dev`** with 73 changed files and a bake when it
was read. **Read its PR body before starting**, and read this part first, because it is a
finding about the whole programme rather than about this block:

> the `balanced` scene-detail tier's triangle ceiling, measured on the same runner, same
> command, both trees: `dev` **1,208,434** of 1,210,000 — PASS by 1,566. That branch
> **1,210,608** — FAIL by 608. Four roofs cost **2,174** triangles at the worst stand and
> `dev` had 1,566 to give.

That is T-0098's sentence returning word for word: the bar had not been reached by a parcel
that overspent it, it had been reached, full stop, and the next VISIBLE parcel of any size
was going to fail it whatever it was. The block comment at the definition in
`renderers/web/js/main.js` records five raises and one return and twice declined a sixth.
The PR filed **T-0441** with the measurement and three shapes an answer could take (raise
with stated headroom and a named retirement · trim first and name the trim · hold the
buildings). **T-0441 never reached `dev`** — it lives only in that closed PR, so whoever
takes this ticket next re-files it or settles it. It also filed T-0438, T-0439, T-0440.

Its branch could NOT be deleted from the session that closed it — this environment's proxy refuses a ref delete over both git and the REST API (HTTP 403) — so `ticket.mjs claim` **will see it as a rival branch and refuse**. That refusal is a false stop: the PR is closed and the branch is abandoned. `claim T-0432 --force` is correct here. `ticket.mjs inflight` reads it as COLD, which is the honest signal.
