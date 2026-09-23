---
id: T-0317
title: Build out the NEXT anonymous block: after blk_lake_franklin the last ungenerated block is owner-blocked, and the roofs left stand on blocks that already stand
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 521
claimed_by: run 8/29/2026, 2:54:41 AM CT
blocked_on: null
needs_bake: false
---

Build out the NEXT anonymous block: after blk_lake_franklin the last ungenerated block is owner-blocked, and the roofs left stand on blocks that already stand.

**Acceptance:** one named block built to the adoption rules as they stand, its gates green, its
STATUS row written, AND the successor ticket filed. That is T-0028's acceptance verbatim, and this
is its successor under T-0028's own programme rule: *one run, one demonstration, one successor —
never a ticket whose scope is "keep going".*

**Where T-0028 left it, 2026-08-28.** It opened `blk_lake_franklin` (Lake, Wells, Randolph,
Franklin), built 3 of its 4 dealt roofs and deferred the fourth. That block is now `at_capacity`.
Re-derive `data/reconstruction/1835_665_roof_programme.json` with `tools/reconcile_665.py` at the
time of the run rather than trusting this note — but as it stood on 2026-08-28:

* **No ungenerated platted block is left to open but one.** `blk_south_water_market` carries 27
  roofs of headroom on measured dry ground (`tools/measure_block_gating.py`: South Water is 25 m
  away, 0 of 5 samples wet) and is **blocked on the owner** at **T-0183** — Market x South Water is
  a bend in Wacker Drive, not a crossing, and the node rule cannot derive the control point. Do not
  reopen that question; it is answered and the fork is his.
* `blk_south_water_clinton` is `not_a_block` and no trace will ever join it (T-0163).
* **The five blocks still `open` all ALREADY STAND.** `blk_south_water_franklin` (head 4),
  `blk_south_water_lasalle` (8), `blk_south_water_clark` (4), `blk_south_water_dearborn` (4) and
  `blk_randolph_market` (4). Densifying those is the CORE DENSITY standard — T-0079's clause, the
  T-0105 -> T-0143 -> T-0188 line — not this programme's "next anonymous block".
* The four `blk_south_water_*` blocks front the reach whose committed street line is the open
  question in **T-0009** (`blocked-owner`). T-0143 and T-0188 both refused to tighten a row against
  a line that may move, and that refusal still stands.
* **So the workable ground is `blk_randolph_market`'s SECOND DEAL** — 4 roofs, 2 free lots, dealt
  A1, D3, D4, D5, all of them buildable, on a block one street back from the business front. A
  block already dealt takes its next deal as a further recipe entry with its own `seq_start`;
  `blk_randolph_dearborn` carries three and is the worked example.

**Watch for the F3 refusal.** `blk_south_water_dearborn` is dealt **F3**, the large river warehouse,
which `tools/generate_block_infill.py` now refuses by name (T-0028, L203). Defer it in the recipe
with its reason rather than reaching for a shape — and read **T-0316**, which asks the deal to stop
sending warehouses onto inland blocks in the first place.

**This needs a bake.** Placeholder GLBs a Blender-free run writes are crude massings beside their
canonically baked neighbours. Bake per structure with `tools/bake.sh --only <id>` — the Blender
half is seconds, and `tools/web_derivatives.sh --only <name>.glb` afterwards avoids the ~11 minute
full derivative pass that `bake.sh` runs unconditionally.

Related: **T-0028** (parent), **T-0183**, **T-0009** (both `blocked-owner`), **T-0143**, **T-0188**
(the core density line), **T-0316**, **L203**.
