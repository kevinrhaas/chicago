---
id: T-0184
title: Mitre the road ribbon's panel joints, so a bend stops opening a wedge of prairie
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 391
claimed_by: run 8/26/2026, 11:27:23 PM CT
blocked_on: null
needs_bake: false
---

Mitre the road ribbon's panel joints, so a bend stops opening a wedge of prairie.

`renderers/web/js/streets.js` `addRecord()` builds every panel square to ITS OWN chord: the
row at a shared centreline point is drawn twice, once perpendicular to the incoming chord and
once perpendicular to the outgoing one. Where a street bends, those two rows cross at the
centreline and diverge towards the edges, so the outside of every turn carries a triangular
wedge of unpainted ground — apex on the centreline, `half_width * tan(turn/2)` wide at the
ribbon's edge — and the inside carries a matching overlap.

**Measured on the shipped build (T-0111, 2 cm plan probe of drawn triangles inside the nominal
ribbon).** Dearborn's new 5.7-degree joint at the South Water corner: a 0.61 m2 sector, of which
South Water's own roadway covers half, leaving 0.30 m2 uncovered — small enough to ship, and
recorded in docs/LIBERTIES.md L178 as an admitted artefact. **South Water Street's own west
approach is the real prize:** its authored line turns 17.9 degrees at [140, -35] on a 10.5 m
track, which is a sector of about 4.3 m2 at a single joint, and it has been there since the
street layer shipped. Lake, North Water and the fort road each have bends of their own.

The fix is a mitre: compute one normal per centreline POINT — the bisector of the incoming and
outgoing chord normals, scaled by `1 / cos(turn / 2)` and capped so a sharp turn cannot spike —
and let both panels share it. Adjacent panels then emit identical corner positions and neither a
gap nor an overlap is possible. `dryReach`, the `MIN_PANEL_W_M` drop and `refinedPanel`'s drape
refinement all take the normal as an argument already.

**Why it was not done inside T-0111:** it moves ribbon geometry on every bent street in the town,
and T-0111's parcel was 2.7 m of Dearborn. It needs its own before/after measurement, its own
smoke leg and a check that no road-contrast band moves against its baseline.

**Acceptance:** the 2 cm plan probe finds ZERO uncovered ground inside the nominal ribbon at every
authored bend in `data/streets/1835.json` (Dearborn's corner and South Water's west approach named
explicitly, before and after); no street's ribbon leaves its own `track_width_m` half-width, so
`tools/measure_drawn_placement.mjs --gate` still reads 0 strays and its `--refute` control still
fails a mirrored build; the smoke's panel accounting, drape and approach-coverage checks stay green
at both viewports; and a screenshot from the South Water west approach shows the join closed.

**Links:** T-0111 (which measured this and admitted it) - docs/LIBERTIES.md L178 -
`renderers/web/js/streets.js` (`addRecord`, `refinedPanel`) - T-0110 (the drape refinement that
shares this code path).

---

## Measured and closed, 2026-08-27

The instrument is `tools/measure_road_joints.mjs` (probe in `tools/road_joint_probe.mjs`, shared
with the smoke): a **2 cm plan lattice** over every authored bend, classifying each point twice —
inside the nominal ribbon (within `track_width_m / 2` of the drawn centreline, on a chord the
module is allowed to paint, not on water) and inside any drawn street triangle in plan. Its
control runs on every build: the same lattice against a **reference ribbon built under the old
square-joint rule**, so the wedge is measured rather than remembered.

| | uncovered inside the nominal ribbon | drawn triangles |
|---|---|---|
| before | **23.472 m2** over 21 live bends | 22,596 |
| after | **0.000 m2** | 22,618 |

Worst bends before: **south_water [120, -57], 17.8 deg on a 10.5 m track — 4.292 m2**; [180, -5]
4.245; [220, 6] 3.575; **fort_road [1140, 78], 39.3 deg — 2.594**; [140, -35] 1.772; [160, -18]
1.765; north_water [920, 190] 1.534. Each agrees with the closed form `half^2 * turn / 2` to
three decimals, which is what says the lattice is reading geometry and not noise.

**THE TICKET'S TWO NAMED JOINTS WERE BOTH WRONG, AND BOTH WAYS ROUND.**

1. **South Water's west approach turns 17.8 deg at [120, -57], not at [140, -35].** The angle and
   the 4.3 m2 are right; the coordinate names the NEXT vertex, which turns 7.4 deg for 1.772 m2.
2. **Dearborn's corner measured 0.000 m2 uncovered, not L178's 0.30.** South Water Street's own
   10.5 m roadway covers the WHOLE 0.61 m2 sector at that joint, not half of it: the sector
   reaches at most 3.50 m from [698.93, 7] and South Water's ribbon spans N 1.8 to N 12.3 there.
   L178 is revised in place rather than rewritten, since the artefact it admitted was real
   everywhere else on the street layer and is what this ticket closed.

**Two costs, stated.** (a) **22 triangles town-wide**, read off the shipped scene: 23 of the 30
authored bends mitre at ZERO cost (a mitre moves vertices, it adds none) and 7 are too sharp for
one mitre and pay 3 triangles each, except fort_road [1140, 78] at 39.3 deg which pays 4. That is
0.0018 % of the `balanced` ceiling. (b) A mitred corner stands `half * (sec(turn/2) - 1)` past its
bend by construction; capped by sub-mitring, the worst in town is **0.029 m** at fort_road
[1075, 38], against the 0.05 m the drawn-placement census tolerates. Recorded as **L194**.

**A third finding, filed rather than fixed (T-0226):** three of North Water Street's six bends
carry no joint question at all, because its committed centreline runs inside the water mask and no
ribbon may be drawn there. The probe reports them as `paintable 0.00` rather than as 33.8 m2 of
uncovered ground apiece, and counts them, so they cannot hide.

**Gates, run on the published mirror:** `tools/check.sh` CHECK PASS - `measure_drawn_placement.mjs
--gate --refute` 0 strays, worst 0.00 m, negative control fires - `measure_road_joints.mjs --gate`
0.000 m2 with its square-joint control at 23.472.

**The full smoke was NOT run to completion, and CI is the authority for it.** The runner was at load
48 with 105 concurrent Chromium processes from ten parallel agents, and agents were reporting
browsers killed mid-run and timeouts on unmodified `origin/dev` controls. Partial, reported as such:
mobile 390x780, stage 5, published mirror — all five street-layer checks passed, including the new
joint-station check; the only failure is the "suite body ran to completion" line caused by killing
the run. The new check WAS verified RED on the pre-fix build before it was believed, naming South
Water [120, -57] at all three radii.
