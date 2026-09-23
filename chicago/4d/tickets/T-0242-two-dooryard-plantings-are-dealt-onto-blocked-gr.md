---
id: T-0242
title: Two dooryard plantings are dealt onto blocked ground and refused at load, on dev
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: 416
claimed_by: null
blocked_on: null
needs_bake: false
---

The dooryard planter did not know a plank walk is a floor, and T-0240's walk found it.

**Filed mid-run on a wrong premise, and corrected before it closed — the correction is the
useful part, so it is kept rather than tidied away.** It was first written as a defect
*inherited from `dev`*, on two readings that were each true and together wrong:
`data/flora/plantings/town_dooryard_plantings.json` is byte-identical to `dev` on the
T-0240 branch, and `blocked()` in `renderers/web/js/trees.js` does not read the frontage
layer. **What that missed is `main.js` line 902**, where the array `blocked()` walks is not
`footprints` but `planting` — `footprints.concat(wharves.keepOut, boats.keepOut,
frontage.keepOut, decks)`. The walk is in there. It was T-0240's.

The attribution was settled by running the same smoke stage against `dev`'s own published
mirror with `SMOKE_ROOT`, which is what that variable is for: the two problems do not
appear there and do appear on the branch.

    trees: planting town_dooryard_plantings/recon_1835_blk_randolph_clinton_d4_02_bush_1
           stands inside a committed footprint or on the travelled track — not drawn
    trees: planting town_dooryard_plantings/recon_1835_blk_randolph_dearborn_d1_12_bush_2
           stands inside a committed footprint or on the travelled track — not drawn

## The real fault, which is a generator/renderer disagreement

`tools/generate_dooryard_plantings.py` says in its own docstring that a stem stands "where
the renderer's own refusals allow", and lists them: footprint clearance, the street
shoulder, the dry floor, committed fence lines, neighbours. **The frontage keep-out was not
on that list**, because when the tool was written the street edge reached no block a
dooryard stands on. `tools/generate_yard_goods.py` — the other generator that has to know
where a walk lies — has read `data/frontage/` all along.

So `tools/check.sh` passed: it asks "does this record re-derive from its own rule", never
"would the renderer draw it". The record claimed 128 stems and the town grew 126, and the
gap was visible only in the smoke's problem list.

Neither bush was ON the boards — they stood 0.99 m and 2.63 m clear of a walk edge. The
refusal is `trees.js` CLEAR_MARGIN, which refuses a stem within **4.5 m of any polygon edge
in `planting`**, and a keep-out rectangle sits in that array beside the footprints.

## What was done

`world()` now reads the walks and crossings out of `data/frontage/` — the same records
`frontage.js` builds its `keepOut` rectangles from, derived the same way
`generate_yard_goods.py` derives them — and `clear()` refuses a point within
`WALK_MARGIN_M` (5.0 m, `CLEAR_MARGIN` plus this tool's usual half metre, the same pair as
`FOOTPRINT_MARGIN_M`) of a walk's own half-width.

**128 stems before and after, none dropped and none added.** Four bushes re-dealt to legal
ground, all of them on Randolph blocks: the two refused, and two neighbours whose deal
shifted behind them. The two agree by construction now instead of by luck.

**Closed in T-0240's PR** — it was that PR's own consequence, the same way the walk refused
two wagon stands in `data/yard/town_trade_goods.json`, and the gate could not go green
without it.

**Links:** T-0240 · `renderers/web/js/main.js` line 902 (`planting`) ·
`renderers/web/js/trees.js` `blocked()` · `tools/generate_dooryard_plantings.py` ·
`tools/generate_yard_goods.py` · docs/PIPELINE.md § dev's standing smoke result.
