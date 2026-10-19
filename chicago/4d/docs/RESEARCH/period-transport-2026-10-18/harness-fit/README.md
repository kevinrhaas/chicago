# Breastcollar route clearance measurement

Measured 2026-10-18 against the actual loaded skinned horse GLB in neutral idle, phase 0. `measure.py` uses installed Python Playwright/Chromium and the local server at port 8774; it changes no generator or model. Run from any working directory with that server active.

`torso-clearance.json` records all nine currently authored breastcollar centerline points, closest torso-surface point, triangle normal, signed triangle-plane separation, source triangle indices, and a **candidate** point 10 mm along the outward triangle normal. Only the `continuous_body_neck` source vertex range in the exported horse manifest is eligible. Including all coat geometry would accidentally select the nearby upper foreleg for certain side points and understate the gap to the chest.

The original route had torso gaps ranging from 61 to 171 mm, considerably beyond the original 8 mm strap thickness. These are distances to the nearest torso triangles, not evidence of correct anatomical breastcollar placement. The candidate centerline follows the existing model's chest; it does not establish historical form or load suitability.

The nearest-triangle mesh is faceted and produces small left/right asymmetries and a nonzero center X. For a symmetric original reconstruction, average each mirrored pair and enforce X=0 at the center before constructing a smooth strap. Recompute clearance along the entire strap, including its width and thickness, not just the nine route points: a 65 mm tall strap can intersect a sloping chest even if its centerline is 10 mm out. Nearby joints and the animated forelegs also need a separate sweep. A full normal offset is a modeling candidate, not collision certification.

Earlier all-coat measurement found a 2.3 mm separation at `[.30,1.17,.43]`; that was to a foreleg. The torso-only separation at that point is 82.9 mm. This report corrects that reading.

## Revised route: width-aware result

After adopting symmetric torso-fitted route points, centerline gaps are approximately 9.66–11.74 mm. `torso-clearance-before.json` preserves the original loose route. The updated `measure.py` reads `breastcollar_route_m` from the source JSON and measures actual breastcollar mesh vertices over neutral idle phase 0 and 21 walk phases.

The first centerline correction with a vertical 65 mm-wide, 8 mm-thick strap still had an upper-edge intersection indication: signed nearest torso distance ranges **−9.538 to +29.512 mm**. Each pose has 36 duplicated flat-mesh vertices below −1 mm, out of 204 vertices. Worst measured vertex is `[0,1.204504,.589993]`; nearest surface `[.001643,1.199842,.598151]`. The centerline is close, but the vertical width axis keeps upper/lower edge Z fixed while the chest slopes forward. A torso-tangent width direction can address this without moving the entire band far outward. Inspect after changing orientation and rerun measurement.

This is a vertex proximity/sign test against the continuous torso only. It does not certify watertight inside/outside status, triangle intersections, foreleg clearance, force transfer, or historical fit.

## Width orientation correction: current result

After setting the reconstructed strap-width direction to `[0,.869,.495]` and regenerating, the same actual-vertex test reports **+1.482 to +20.554 mm** signed nearest torso separation over idle 0 and all 21 walk phases. No sampled vertex is below −1 mm in any pose. This supersedes the negative-clearance result above; the current `torso-clearance.json` contains this corrected export's receipt.

The smallest sampled gap occurs at walk phase .15, vertex `[−.231031,1.144690,.384849]`. This targeted correction removes the earlier sampled upper-edge penetration indication. Full triangle/foreleg collision and historical load suitability remain outside the measurement.

## Final raised 50 mm band

The latest `torso-clearance.json` supersedes earlier route/width receipts: actual breastcollar vertices have **+4.167 to +16.774 mm** nearest-face signed torso separation over neutral idle plus 21 walk phases, with the narrow executable criterion passing. Source width is a reconstructed 50 mm, not a historical measurement. See `FORELIMBS.md` for the separately qualified 101-phase upper-limb triangle result and its small sampled clearance. These measurements do not complete the harness ticket.
