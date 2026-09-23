---
id: T-0429
title: Open blk_south_water_lasalle: 8 roofs of headroom on three free lots
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0420
opened: 2026-08-29
closed: 2026-09-05
pr: 597
claimed_by: run 8/30/2026, 1:51:13 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-05T15:43:21.242Z
claimed_run: null
---

Open `blk_south_water_lasalle` — 8 roof(s) of headroom, 3 free lot(s) — under the anonymous-block
programme (T-0028). Piece 1 of 4 of **T-0420**, which held all four South Water blocks in one
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
| bounded by | south_water (N), lake (S), lasalle (W), clark (E) |
| lots | 8 |
| standing roofs | 9 |
| free lots | 3 |
| headroom | **8** — 6 principal, 2 ancillary |
| families dealt | A1, A2, C3, D1, D2, D3, D6, D7 — one roof each |
| frontage weight | 0.6023 |
| trade roofs in the deal (T-0213) | 1 |

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The 8 roof(s) stand on `blk_south_water_lasalle`'s own committed lots, and the row stands ON THE BLOCK FACE
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

---

## 2026-08-30 — built, gated green on `check.sh`, and PARKED on the balanced tier's ceiling

PR **#597**, branch `steward/t-0429-south-water-lasalle`, left OPEN with the `hold` label.

**Built as the acceptance asks.** Six principal roofs shoulder to shoulder on lots 0 and 2 —
this block's own committed lots, the row standing ON THE BLOCK FACE and not on a re-derived
line — and the two yard buildings behind them. `reconcile_665.py` re-derives and the block moves
to `at_capacity`; lot 1 stays open. Every mesh baked in the same commit, `validate.py --stale`
clean, `publish.sh` run. `./tools/check.sh` PASS, 0 errors, 28 warnings, the same 28 dev carries.

**Two things had to be found before it could be dealt.** The ruling (T-0009) was only half of it.
The first deal on this block DECLARED its frontage as lots 0, 2 and 4 and its run stands, measured,
on lot 4 alone — so `plat_occupancy.py` scored the lots free off footprints while `check_block`
scored them built on off the recipe, and the eight roofs of headroom could not be spent by anybody.
Corrected to `[4]`; no roof moved and no record changed. **T-0449 filed**: four MORE entries do the
same thing, and they are precisely T-0430, T-0431 and T-0432's blocks.

**The corner clause met a watercourse, and that is the parcel's one new reading.** Lot 0 is the free
corner at South Water and LaSalle, so the density standard says build to the corner and T-0022's
fabric rule independently sends the log dwelling to the west end — the two agree here, unlike
T-0317. `lasalle_slough_lower`, the slough Wright 1834 draws dropping south off the main stem just
east of La Salle Street, crosses this frontage at 4.86 m on its committed alignment. The westmost
point that carries a roof at all is 9.81 m; the run stands at 10.11 m. The corner clause is recorded
as REFUSED BY THE GROUND rather than dropped.

**WHY IT IS NOT MERGED, and it is the owner's call rather than a failure of the parcel.** The
renderer smoke is green everywhere except `desktop part 5`: `balanced` reads **1,216,632 triangles
of 1,210,000** at the forks from Wolf Point — over by 6,632, 0.55 %. That is a triangle count, not a
timing, and desktop part 5 read PASS on dev on 2026-08-28, so it is this parcel's eight roofs.
`full` and `light` are untouched.

The remedy would ordinarily be the conscious re-budget AGENTS.md sanctions. **It is refused here
because the record already refused it**, at the definition in `renderers/web/js/main.js`: *"the
number stays at 1,210,000 and the budget question lives entirely in T-0223, which orders the trim
first and the ceiling after."* T-0223 has 180,100 triangles — 27x this overshoot — cast by
kilometre-wide quadrant meshes submitted whole to a shadow box that cannot hold them. Two routes,
both his: land T-0223's trim and this fits inside the existing ceiling, or re-budget `balanced`
alone with a measured figure written at the definition.

A second red, `mobile part 9`, is two pixel-difference checks moving 2 cells against thresholds of
3 and 4. Part 9 last read PASS on dev on 2026-08-29. It was NOT attributed — no re-run on a quiet
box and none against a clean `origin/dev` — and this record says so rather than guessing. All seven
readings are filed in `tools/dev-smoke-state.json` with their conditions; mobile part 12 had no
reading at all before this branch.

**The successor T-0028's programme rule owes is already in the queue**: T-0430, the next block in
this family. The ticket stays `open` because its PR has not merged.

---

## Outcome — closed 2026-09-05 against PR #597, which had already delivered it

**This ticket was finished on 2026-09-01 and never closed.** PR #597
(*"blk_south_water_lasalle's second deal builds the west half of the river row"*) merged
into `dev` at 2026-09-01T00:40:50Z carrying all eight roofs. The run that opened it did not
reach `ticket.mjs done`, so the ticket stayed `state: claimed` — the only ticket in the repo
in that state — and sat in `list --workable` for five days, where it read as available work.

It was not free. A later branch, `steward/t-0429-south-water-lasalle`, rebuilt the block from
scratch: 116 files, 5,827 insertions, baked and gated, and then parked on the 32 MB published
ceiling without ever opening a PR. Every one of the eight records it "adds" already existed on
`dev` under the same ids — the merge of that branch into current `dev` is eight add/add
conflicts on the ticket's own payload. That branch is litter and is deleted with this close.

**Acceptance, re-measured on `dev` at this commit — not taken on trust:**

| clause | measured |
|---|---|
| 8 roofs stand on the block's own committed lots | `standing_roofs` **9 → 17** on `blk_south_water_lasalle` |
| `reconcile_665.py` re-derives; block moves to `at_capacity` or states its headroom | `state: at_capacity`, `headroom: 0`, `free_lots: 1` in `data/reconstruction/1835_665_roof_programme.json` |
| the roofs are baked in the same commit, `publish.sh` mirrors the result | shipped by #597; `check.sh`'s `validate.py --stale` re-asserts every record against its committed mesh here |
| one successor handed on per T-0028 | **T-0431** (`blk_south_water_clark`) and **T-0432** (`blk_south_water_dearborn`), both in QUEUE — the two South Water blocks still `open`, 4 roofs of headroom each |

The one clause this close does NOT re-demonstrate is the screenshot. #597 took it; nothing has
moved since, and re-taking it would be re-proving a merged PR rather than this one.

**Nothing about the town changes here.** No record, mesh, street, lot or heightfield is touched.
This is the bookkeeping #597 owed, and the queue is what it repairs. The gap that let a merged
ticket sit `claimed` for five days is filed as its own ticket rather than fixed in passing.
