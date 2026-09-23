---
id: T-0959
title: The School Section's tier lines are level and 4th on dev and skewed and 5th on the rival reading: settle the ordinal and the skew against Wright's sheet
state: done
epic: GROUND
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-12
pr: 1213
claimed_by: run 9/12/2026, 4:42:58 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T22:35:44.594Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34720581758
---

`#977` and `#978` are two reconstructions of the same thing — the School Section's grid
south of Madison, off Wright's 1834 survey — and both find **142 blocks** and **8 east-west
tier lines**. They disagree on what to call those lines and on whether they run level.

| | on `dev` (#977, T-0797/T-0876) | on `#978`'s branch |
|---|---|---|
| tier ids | `school_section_tier_4` … `_11` | `school_section_tier_05` … `_12` |
| the first line, west end | `[-773.77, -1100.06]` | `[-763.1, -1148.4]` |
| the first line, east end | `[835.57, -1100.06]` | `[824.9, -1122.7]` |
| the line's run | **level** — one northing end to end | **skewed**, 25.7 m of rise over 1,588 m |
| `geometry_confidence` | `inferred` | `attested` |
| the artefact | `data/traces/vectors/school_section_blocks_1834.json`, with `registration`, `residuals`, `sale_test` and `numbering_cross_check` | `data/reconstruction/1835_school_section_blocks.json`, off `traces/school_section_module_1834.json` |

**Two questions, and the first is cheap.** Is the first ruled tier south of Jackson the
FOURTH line of the grid or the FIFTH? The two files are a whole tier apart in their indexing
while drawing the same eight lines, so at most one is right, and the sheet letters none of
them — the branch's own note says *"THE SHEET RULES IT AND LETTERS IT NOTHING. South of
Jackson the tiers carry no lettering."* The ordinal is therefore a claim about counting from
a named line, and it should be stated as one.

**The second is the one that moves ground.** `dev`'s tiers are level; the branch's carry the
survey's skew, and at the west end the two put the same line **48 metres apart**. `dev`'s is
`inferred` and registered against the raster with residuals published; the branch calls its
own `attested` off the registered NARA scan. A line that is `attested` and a line that is
`inferred` cannot both be the same line, and the confidence is the part that has to be
earned — `attested` on a skew of 0.93° needs the residuals to show the skew is in the sheet
and not in the registration.

**`dev` is the record in force.** #978 is closed under T-0930 and nothing here amends the
committed grid; this ticket is the disagreement, kept so it outlives the branch.

**Acceptance**

1. The ordinal is settled by counting from a line the sheet does name, and the tier ids
   state what they are counted from.
2. The skew is resolved against `registration`/`residuals`: either the tiers carry it and
   `dev`'s level lines are corrected, or the skew is registration error and the branch's
   `attested` was not earned.
3. `geometry_confidence` on the tier lines ends up matching the evidence actually cited,
   whichever way (2) falls.
4. If the tiers move, the blocks and `1835_reserved_ground.json` move with them in the same
   commit, and the bake follows.
