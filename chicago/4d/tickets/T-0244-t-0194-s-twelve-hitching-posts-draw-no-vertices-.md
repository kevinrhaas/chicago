---
id: T-0244
title: T-0194's twelve hitching posts draw no vertices the gate can find, on dev
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-29
pr: 527
claimed_by: run 8/29/2026, 4:43:57 AM CT
blocked_on: null
needs_bake: false
---

T-0194's twelve hitching posts draw no vertices the gate can find, on dev.

Found on the T-0240 branch and **attributed to `dev`, empirically**: the same check, the
same smoke code, run against `dev`'s own published mirror with `SMOKE_ROOT`, fails there
too. It is not T-0240's, and it is not the merge of the two.

    desktop 1280x800: the Sauganash's two hitching posts stand on their own ground,
    carrying nothing —
      sauganash_hotel_hitching_post_1                  1.30/1.3 m, foot -0.000 m
      sauganash_hotel_hitching_post_2                  1.30/1.3 m, foot  0.000 m
      blk_lake_market_north_hitching_philo_carpenter_log_shop   -Infinity/1.3 m, foot Infinity
      blk_south_water_clark_north_hitching_madore_beaubien_house -Infinity/1.3 m, foot Infinity
      … and ten more, every one of them a street-edge post

**The two OLD posts measure correctly and all twelve NEW ones measure nothing.** `-Infinity`
for a height and `Infinity` for a foot are a max and a min taken over an EMPTY vertex set:
the check finds no geometry at all for those twelve. The Sauganash's pair, which come from
the older hand-authored frontage record rather than from the street edge, are fine.

So either the posts are not built, or they are built somewhere the check cannot resolve
them. T-0194's own changelog entry says *"a post is standing timber, so each one joins the
mesh its street already draws"* — which is the likely place to look first: a post folded
into a shared street chunk may not be findable by whatever key the check uses, in which
case the geometry is fine and the INSTRUMENT is wrong. That distinction is the first thing
to establish, because the two have opposite fixes and only one of them means a visitor is
missing twelve posts.

## Why it reached dev

`docs/PIPELINE.md`: **the dev gate is `check.sh` and nothing else.** The renderer smoke is
dispatch-plus-one-path on purpose, so a check that only the Playwright suite runs can go red
on `dev` without blocking a merge. `check.sh` passes here because it asks whether a record
re-derives from its own rule, never whether the renderer draws it — the same gap T-0242
records for the dooryard planter, found the same afternoon.

**Acceptance:** the twelve street-edge hitching posts each report a real height and foot to
the gate, or — if the geometry was always right and the check could not see it — the check
resolves posts by something that survives being folded into a shared chunk, with the reason
written down. Desktop part 2 green on an unmodified `dev`.

**Links:** T-0194 (the posts) · T-0240 (where it was found) · T-0242 (the same
generator/renderer gap, other layer) · `renderers/web/js/frontage.js` · docs/PIPELINE.md
§ dev's standing smoke result.
