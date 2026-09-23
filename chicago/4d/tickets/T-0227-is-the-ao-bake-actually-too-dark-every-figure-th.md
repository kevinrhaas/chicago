---
id: T-0227
title: Is the AO bake actually too dark? Every figure that said so was wrong twice over
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 463
claimed_by: run 8/28/2026, 6:47:09 AM CT
blocked_on: null
needs_bake: false
---

Is the AO bake actually too dark? Every figure that said so was wrong twice over.

`bake_ao()` has said since it was written that AO on these archetypes is a geometry
problem, not a tuning problem, and quoted **"mean 0.265 with 69 % of texels below half"**
plus **"shortening the AO distance to 0.25 m only reaches 0.38"**. ROADMAP R-W3a is written
around those numbers. T-0158 measured them and both are unsound:

- they were read off an **sRGB-tagged buffer**, so they are the sRGB-ENCODED occlusion, not
  the occlusion (`Image.pixels` on an 8-bit buffer is raw in both directions, so the tag
  decides what the bake writes);
- they were taken over the **whole 512x512 atlas, 68.9 % of which is empty UV space** — the
  "69 % below half" is very nearly the empty fraction itself. Most of what that figure
  counted was blank, not dark.

Re-measured on `sauganash_hotel` from the exported file (T-0158, 2026-08-27): atlas-wide raw
mean **0.1665**; over the **81,458** texels the unwrap actually writes, mean **0.5358** with
**58.7 %** below half. The 0.38 figure carries both faults and has not been re-measured at all.

**And no judgement about AO here has ever been made on a file that carried it.** Until
T-0158 the export shipped a uniformly black texture, so "the Sauganash renders brown" was
never a reading of a rendered GLB — every AO opinion this project holds predates a working
export. That is now fixable: `--ao` produces a correct file, and `tools/critic_shots.mjs
--metrics` exists precisely so "did this change how it looks" stops being an adjective.

**Do this before R-W3a, not after.** R-W3a's acceptance is "the cage brings the number up",
and it is currently pointed at a number that is wrong in two directions. Building a cage to
improve a figure nobody has measured correctly is the expensive way to find that out.

Also open, and cheap to answer in the same run: an atlas that is 68.9 % empty is an unwrap
problem in its own right — `smart_project(angle_limit=1.15, island_margin=0.02)` is leaving
two thirds of every texture unused, which is two thirds of the ~107 KB each occlusion map
costs. See T-0158's cost figures: a 512-squared map on each of 348 masters is ~+37 MB against
1.5 MB of site-budget headroom.

**Acceptance:** one asset baked with `--ao` and shot through `critic_shots.mjs --metrics`
against the same asset without it, both tables quoted, and a stated answer to *is AO on this
geometry too dark* that rests on the rendered frame rather than on an atlas mean. Whichever
way it falls, correct `bake_ao()`'s docstring and R-W3a to match, and record the mean over
WRITTEN texels rather than over the atlas — an atlas mean is not a statement about the walls.
Refuting the premise ("it is fine, ship it") is a legitimate outcome and would retire R-W3a.
