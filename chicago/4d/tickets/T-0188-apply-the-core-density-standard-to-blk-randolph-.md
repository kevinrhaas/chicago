---
id: T-0188
title: Apply the core density standard to blk_randolph_market, the last core block below the bar off the South Water reach (successor to T-0143)
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 373
claimed_by: null
blocked_on: null
needs_bake: true
---

Apply the core density standard to blk_randolph_market, the last core block below the bar off the South Water reach (successor to T-0143).

**Acceptance:** `blk_randolph_market` is dealt and built to the core density standard — its
one free corner lot built to the corner, its improved lots carrying their outbuildings — with a
before/after pair from the same stand, the 665-roof total unmoved, both gates green, and the
successor filed if any core block still stands below the bar.

**Where T-0143 left it.** T-0143 took `blk_randolph_dearborn`'s last four roofs of headroom on
lot 1, the Washington-and-Dearborn corner, and that block now has one free lot and no headroom.
Read `data/reconstruction/1835_665_roof_programme.json` at the time of the run rather than this
note, because the schedule is derived from what stands. What T-0143 measured on 2026-08-24, and
the constraints the next run will meet again:

* `blk_randolph_market` is dealt 4 roofs (A3, C4, D4, D5) against 2 free lots, **1 and 5, both
  on its Washington tier** — the same shape as the block T-0143 built, and lot 1 is again the
  block's free CORNER lot, at Market and Washington.
* The four `blk_south_water_*` blocks with headroom all front the reach whose committed street
  line is the open question in **T-0009** (`blocked-owner`), and T-0163 is measuring the same
  centreline. A new tightened row against a line that may move is the mistake T-0009 refused to
  make, and T-0143 refused it for the same reason.
* `blk_lake_franklin` has a free lot on Lake but is dealt **F3** (a large river warehouse, on a
  block that touches no water) and **I3** (which `REFUSED_FAMILIES` refuses by name). It cannot
  carry a three-unit run as dealt.
* A block already dealt takes its next deal as a further RECIPE ENTRY with its own `seq_start`;
  `blk_randolph_dearborn` now carries three and is the worked example. A lot a later deal builds
  on must LEAVE the earlier entries' `open_lots`, or the lot-accounting gate refuses it.
* **This needs a bake.** The four placeholder GLBs a Blender-free run writes are crude massings
  beside their canonically baked neighbours; T-0143 baked its four with
  `tools/bake.sh --only <id>` (about a minute each) and then regenerated the web derivatives per
  asset, because an uncompressed placeholder is refused as an undecided passthrough.
