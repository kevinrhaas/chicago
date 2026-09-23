---
id: T-1056
title: The woody stratum scatters evenly over the sand bar, because nothing keys it to the sandy HILLS Andreas excepts
state: done
epic: GROUND
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0940
opened: 2026-09-12
closed: 2026-09-12
pr: 1190
claimed_by: run 9/12/2026, 5:53:09 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T11:55:25.207Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34689484029
---

The woody stratum scatters evenly over the sand bar, because nothing keys it to the sandy HILLS Andreas excepts.

Piece 2 of 2 of **T-0940 — The sand bar renders as mesic-prairie green with scrub on it, though z08_lakeshore and z09_sand_prairie cover it and declare sand at 55 and 18 per cent bare soil**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

## What the split run already established, so the next one does not pay for it again

The scrub is NOT the trees. `renderers/web/js/trees.js` already handles the sand correctly:
`communityAt()` asks the sward `if (zoneAt?.(e, n) === DUNE_ZONE) return 'dune'` BEFORE the
divisions, and its comment carries Andreas verbatim — the North Division timber is
"continuous except for the sandy hills near the lake", and "the sandy hills are not an
absence of vegetation; they are the lakeshore's own community". The poplars z08 records are
placed from that rule.

The even scatter is `renderers/web/js/flora.js`'s SHRUB PASS (ROADMAP K54, ~line 1348). It
deals from `zone.shrubShare`, and `shrubShare = shareOf(dry.shrubs.density)` — the sum of the
zone's recorded clump densities, evaluated on a uniform lattice over the whole extent. Two
things follow:

- **`cover.bare_soil_fraction` gates nothing.** It is read into `zone.bareSoil` (flora.js
  ~2058) and from there reaches only the census summary. The matrix layer is thinned by
  `cover.matrix_fraction` (z08: 0.35) and the forb and shrub layers are thinned by neither, so
  a zone declaring 55 per cent bare soil still carries its full recorded shrub density over
  100 per cent of its area.
- **The bar inherits a mainland community.** z08 and z09 are `kind: "everywhere"` rectangles
  whose own notes say "The north-south bounds are the scene's own, not the belt's". Their
  species lists were written for the beach, the foredune and the relict ridges — sand cherry,
  `salix_cordata`, `cornus_sericea`, juniper, `salix_interior`, and z09's black-oak grubs. No
  source places any of them on a wave-washed bar; the bar simply falls inside two boxes.

## The question this ticket has to answer, and the trap in it

Andreas's exception is to the sandy HILLS. z09's own note puts its belt at **+7.6 to +9.5 ft
above the water** (2.32–2.90 m); the bar's crest is **+1.21 m**. So height plausibly separates
the stable dune and ridges, which carry woody growth, from the active strand and the bar,
which do not.

**Do not put that number in a shader.** It exists today only as prose inside a zone note.
Turning prose into a renderer constant is the silent invention this project refuses. Either
the bound becomes a recorded, `inferred` attribute on the sand zones with a note stating the
reasoning, or the bar gets its own community record. Decide which, and say why.

## Acceptance

1. The bar's vegetation is beach grass and low scrub in pockets — no even scatter of woody
   growth — and the rule that does it is read from a RECORD, not written into a renderer.
2. The "sandy hills near the lake" exception is carried onto the bar's planting explicitly,
   not by a hand-placed exclusion polygon.
3. Whatever happens to `cover.bare_soil_fraction` is decided once and written where the next
   zone will read it: either it gates the herb and woody strata as it gates the matrix, or it
   is documented as a record-only claim.
4. Report what moved outside the bar's footprint. The active beach face inside z08 is expected
   to lose woody growth by the same rule; the mainland prairie must not move at all.
5. `tools/check.sh` green.
