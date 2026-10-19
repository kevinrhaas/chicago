# Upper-forelimb proximity follow-up

Measured 2026-10-18 without modifying existing model/source/test files. Run `measure_forelimbs.py` with the local 4D server running on port 8774. It loads the actual horse GLB, chooses idle phase 0, then 21 walk phases, and compares every actual breastcollar mesh vertex with the deformed `fore_l_upper_mesh` and `fore_r_upper_mesh` triangle ranges declared by the horse export manifest.

`forelimb-clearance.json` records a signed nearest-surface distance range of **−64.57 to +156.54 mm**. Negative values use the normal of the nearest upper-leg triangle. Each sampled pose has 72–96 duplicated flat-mesh collar vertices below −1 mm, out of 204 vertices. Neutral idle minimum is approximately −30.0 mm; strongest negative readings occur around walk .4/.9.

Worst sample: walk phase .9, collar vertex `[−.231031,1.144690,.384849]`; nearest upper-right-leg surface `[−.282256,1.152354,.346290]`; face normal `[−.793299,.118694,−.597150]`; signed nearest distance −64.572 mm. The corrected torso-only route therefore does not establish upper-leg clearance.

This test reports a concrete interference indication, not a collision certificate. It samples vertices rather than triangle/edge intersections; signed nearest-face distance is not a watertight inside test. It excludes lower limbs, fittings, straps other than breastcollar, forces and pressure. Negative readings need visual inspection and route/anatomy reconciliation before a fitted harness claim. Do not simply offset the band 65 mm from the chest: that would discard the torso-fit improvement and can conceal the unresolved shoulder/upperleg geometry relationship.

## Current raised, 50 mm band result

The preceding negative-distance report describes the earlier low route and is preserved as `forelimb-clearance-before.json`. Raising the band removed most interference, but a 65 mm-wide band still had actual triangle intersections at four sampled walk phases; that failed receipt is preserved as `raised-65mm-forelimb-intersections.json`.

The current original reconstruction uses a raised chest route, per-point surface-tangent width orientation, **50 mm reconstructed width** and 8 mm thickness. The final sweep uses neutral idle plus **101 walk phases**. Across all 102 poses:

- Actual upper-forelimb maximum Y reaches 1.306008 m; actual breastcollar minimum Y is 1.306597 m.
- Minimum global vertical AABB separation is **+0.589 mm**.
- No breastcollar/upper-forelimb triangle-pair AABB overlaps occur, hence no selected triangle intersections at any sampled pose.
- The executable assertion checks actual selected triangle intersection count is zero. It deliberately does not assert nearest-face signed distance globally: points outside a finite triangle near its cap can lie behind the face plane while remaining outside the limb.

`measure_forelimbs.py` contains a triangle-pair AABB broad phase and separating-axis triangle test for candidates, including coplanar edge axes. The current geometry needs no narrow-phase tests because every pair is already disjoint at the AABB stage. This proves separation of the selected loaded triangle surfaces **at sampled poses**, not continuous-time clearance, other gear/limbs, forces, pressure or historical suitability. The 0.589 mm sampled gap is small and should not be described as a physical safety margin.
