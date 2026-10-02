# T-1830 — Glessner west wing and north entry

Owner follow-up, 2026-10-01, after T-1805/PR #230. Ten supplied views:

| Supplied image time | What was read |
|---|---|
| 210139 | Reported projecting gable/roof artifact in dev |
| 210331 | Stable north gable and ordinary eave return |
| 210748 | Historical northwest view: full northern west gable, lower rear roof, dormer |
| 211223 | West elevation and lower rear eave |
| 211421, 211547 | Open north arch, landing, low left cheek and left-turn stair |
| 211804, 211849 | HABS sheets 2 and 3; reread from full-resolution repository scans |
| 212425, 212524 | West dormer hood/tile cheeks and complete west elevation |

No third-party image pixels are copied or redistributed. The existing cleared owner
brief records the request and qualitative comparisons. HABS sheets 2–3 provide the
161.25 × 74 ft overall envelope, 35.5 × 59.75 ft stable and 12 ft north arch.
The sheets do not supply a roof plan or west elevation. Modern fabric is not dated
1904 merely because it survives. Heights and hidden joins below are reconstructed.
The c.1955 wooden stairs behind the service wing are explicitly excluded.

## Geometry decision

T-1805's sampled interpolation left warped planes and retained too much of the old
high rear roof. Replace it with a union of planar roof solids, clipped at their true
intersections. The full west-facing northern gable returns to the lower west eave
at S32 ft. Keep the north gable's W141 door/loft/pigeon axis and its W125.75–156.25
feet. Retain the north-range measured section at its east-side join.

The rear roof is reconstructed with ridge 31 ft ng, west eave 15.5 ft, east/south
eaves 23.1 ft and a south hip commencing at S50 ft. The east/south upper windows
remain visible. The west dormer is timber with tile cheeks and a projecting hipped
hood, nine feet wide about S46; hood eave 26 ft, apex 30 ft. These unprinted heights
are proportional estimates, approximately ±1.5 ft, not survey measurements.

The north arch becomes an actual open porch. HABS sheet 2 locates the left-turn
flight and side-facing door. Reconstructed depth 6 ft; three front risers reach a
1.5 ft landing, eight further risers turn east to the 6 ft door threshold. A small
back-wall window is kept above the landing; sheet 3 is checked against the upper
floor so it is not mistaken for the wide window over the outer arch.

## Geometry review and recovery checkpoint

Claim: T-1830 in chicago-tickets/main. Branch: steward/t-1830-glessner-west-wing-alcove.
The planar roof union and the shared full/light entrance are implemented and visually
reviewed. The first source checkpoint is ece92a8. The roof helper belongs to the
`masonry_house_v4*` family so both master freshness and light receipts hash its code.
The outer arch has a short masonry return opening into the taller porch room; a
full-depth low spring line would obstruct the ascending turn. The inset west sash
stands above a tiled apron, beneath a flared hipped hood. L331 records estimates.

Six generated review views are in `renders/`: northwest roof, west alley, south,
courtyard-facing east, north alcove and the turn to its side door. They show no
projecting gable strip, the lower rear eave, upper south/courtyard windows, and an
open route up the left stair. The 1,800-ray envelope check and aperture/glazing
regressions pass. The exact shipped light derivative was decoded and rendered at
the same northwest and entrance-turn cameras; both retain the repaired geometry.
It contains 188,675 triangles, below the 200,000 ceiling. The three-file recovery
package verifies, and all canonical/older-version meshes report fresh. After
integrating dev through cffaef54 (including the publishing, terrain, roadway and prairie changes), source
preflight passes: 727 steps, none red; changelog and ticket-id checks pass.
The new geometry test has a measured no-write isolation row. Full published-mirror
browser checks on repair checkpoint a8fac67 pass: mobile 1–6, 297/0; mobile 7–13,
290/0; desktop 1–6, 294/0; desktop 7–13, 290/0. Both screen sizes finish with zero
page errors. After the later dev terrain change, stage 5 was repeated on 6f53477:
26/0 on each viewport. The repair changes no 1835 meshes or renderer logic, so
those budget results cover the integrated 1835 geometry. Its desktop worst stands
are 1,442,860 full triangles and 817,290 light triangles, within their ceilings.
The independent roadway change retains its recorded mobile/desktop stages 7–8 passes
and does not change the 1904 scene. The later prairie change carries its own mobile/desktop
parts 3/10/11 checks and keeps triangle/draw/texture counts unchanged. The Glessner meshes remain byte-identical to the visually reviewed repair. All six
workflow receipts are filed in tools/dev-smoke-state.json, with their actual commits
and unknown CI load/tree digests stated, and linked from PR #243.

Commands from chicago/4d:
- Pinned Blender 4.5.3: generators/build.py -- --only glessner_house --no-bake.
- tools/web_derivatives.sh --only glessner_house__as_built_1887.glb.
- tools/render_structure_review.py: northwest, alley, south, courtyard west, north entry.
- Regenerate sidecars/source use, run check.sh/preflight.sh and smoke_budget.mjs --for-diff.
- Push all recoverable checkpoints; merge only the validated repair to dev.
