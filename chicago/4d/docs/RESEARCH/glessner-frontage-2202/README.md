# T-2202 — Prairie frontage ground contact

Target: 1 July 1904, exterior/courtyard only. The previous model left the
main door approach unpaved and its 6-mm passage floor below parts of the
rendered ground. This pass adds three bounded house-side lawn strips with
stone edging, rounded return corners and true joints; two access gaps;
stone entry paving and two low risers to the retained door sill; a stone
porte threshold; and continuous carriage surfacing to the existing drive.

## Evidence and uncertainties

- Taylor photograph 2135, Art Institute mqc 28805, c.1887–1889: visually
  reviewed early stone boundary, entry access and temporary ground disturbance.
  Library audit 008; 101/109 are the same exposure. Public domain by age.
- HABS IL-1015 sheet 2 (1963): visually reviewed grass-strip plan/returns,
  entry and passage positions; 74-ft Prairie frontage and 26-ft-6 east wing.
- HABS sheet 6 (1965): visually reviewed curb elevations/access gaps;
  door sill at 0.00 and sidewalk before doorway at -0.74 ft.
- Existing Sanborn-aligned placement: retain the 14.7-ft east setback,
  +/-1.5 ft. T-1728's street, public curb and sidewalk remain unchanged.
  The approach crosses the one-foot public margin to meet the walk.

The early photograph and later survey bracket visible fabric, not a 1904
survey. Curb width/height/radius, stone joint positions, paving recipe and
the two low risers are explicitly **reconstructed** in `prairie_frontage`
and L-glessner-frontage-2202. The one-foot-deep porte threshold is likewise
reconstructed. No restricted image supplies new assets or texture pixels.
No temporary construction rubble or post-1904 street treatment is copied.
T-1745 is split; its legal-lot work supplies no new vertical datum here.

## Coordinates and ownership

Use the existing building frame: W west/S south in feet, converted once by
`masonry_house_params.py`; metric x east/y north/z up. The door sill remains
0.2256 m above the model datum. Entry paving is 0.064 m; the two rises are
0.0808 m each. Carriage paving falls from 0.064 m to the existing courtyard
0.0366 m. These low surface lifts are rendering clearances over the
lowest-footprint terrain anchor, not newly surveyed historic grades.

The frontage is generated in both canonical detail levels. Full keeps
35-mm dressed bevels and hidden stone ends; light omits those microdetails
and uses three segments per quarter-round (under 9 mm centreline sag),
retaining the same curb height/width, joint spacing and access geometry.
The existing house/roof/light recipe geometry is otherwise retained. No
triangle limit is raised. Solid sides reach below grade and paving joints
have a mineral bed 3 mm below the surface, so joints cannot expose grass.

## Validation

`tools/test_glessner_block_clipping.py --self-test` now samples 1,108 points
across both access routes and both detail levels, including joints; checks
that neither lawn nor curb closes the access, and checks sill/drive datums.
Its existing glazing, aperture and concave-polygon fixtures remain in force.
Before/after published browser captures use identical street-eye cameras,
normal terrain, lighting, neighbors and dark glass at 1280×800/full and
390×780/light. Browser and asset receipts are recorded below; repository and
merge receipts follow after the final checks. This ticket does not certify whole-house photographic
acceptance; T-2200's frozen camera/reference records remain unchanged.

## Published visual and contact review

Desktop/full (1280×800) and mobile/light (390×780) pass the dedicated browser
review with zero page errors or HTTP errors, dark glass retained and all
four street-eye stands inside the existing draw/triangle budgets. Nine
rendered-model ground rays per detail level reach the intended surfaces;
maximum height disagreement with the design is 0.311 mm after compression.
Passage clearance above the terrain is at least 21 mm at the sampled exit.
The main-door upper tread meets the existing bottom reveal at +16 mm from
the facade; it does not overlay that coplanar face.

| View | Before | After |
| --- | --- | --- |
| Desktop entry | [before](before/desktop-entry.png) | [after](after/desktop-entry.png) |
| Desktop carriage passage | [before](before/desktop-porte.png) | [after](after/desktop-porte.png) |
| Mobile entry | [before](before/mobile-entry.png) | [after](after/mobile-entry.png) |
| Mobile carriage passage | [before](before/mobile-porte.png) | [after](after/mobile-porte.png) |

The remaining frontage/inside-passage captures and machine receipts are in
`before/` and `after/`. Ground rays target the building batches, which retain
CPU picking geometry, and compare against the terrain sampler. Other light
scene batches deliberately release CPU buffers after upload. Published
palette materials are named `merged`, so the assertion uses the actual
Glessner instance identity plus height agreement, rather than a material label.

Light contains 199,880 triangles against the unchanged 200,000 ceiling.
Draw calls are unchanged at all four stands in each viewport (desktop 54–58,
mobile 52–53). The drawn triangle delta, including the shadow pass, is +2,964
full and +920 light; every stand remains inside its existing budget.
These are rendered draw/triangle counts, not an FPS or whole-town performance
claim. Older comparison versions were verified to have unchanged input
hashes and retained byte-for-byte; only the canonical v4 assets are rebuilt.
`asset-hashes.json` pins the three resulting files and the recovery package
verifies them. `camera-candidate.json` retains T-2200's fixed cameras: all
87 landmark residuals remain unchanged to 0.001 px. Existing photographic
exceptions and the missing whole-west reference are not resolved by this work.

The generic smoke path map conservatively assigns all structure records to
all stages. This change affects only the 1904 Glessner asset/sidecar: part 13
covers that scene, part 12 covers the new release notes, and the dedicated
page test above covers the exact new access geometry in both detail levels.
The remaining 1835/1812 render paths are unchanged. Smoke receipts below
state the actual parts run; they do not claim the full fourteen-stage gate.

## Repository integration and affected smoke

The first repository gate passed 801 of 802 steps. Its sole failure was an
inherited order-book pointer to withdrawn T-2242; the separately claimed
T-2248 owns that repair. No assertion is weakened to work around it.

Published mobile stages 12–13 pass: 216 checks, zero failures (205 staged
and 11 always-on). The run took 13 m 53 s on this software-rendered host,
exceeding the steward command-duration target; this is not a speed claim.
Published desktop stages 12–13 also pass: 216 checks, zero failures and zero
page errors (205 staged, 11 always-on), in 45 m 39 s. The unusually slow
software-rendered run is retained as measured, not a performance pass.
Both transcripts are beside this report. These are stages 12–13, not all 14.

The desktop run began over 09199675. Dev's unrelated T-2245/T-2248 changes
were integrated while it ran, and the published mirror was refreshed before
its 1904 tail. All assertions passed, including the final Glessner spawn and
budget checks. Its ledger tree hash is deliberately unset rather than
claiming one exact tree for the complete run. The dedicated deployed 1904
review checks the final build separately. Final local preflight passes on dev ef75326f plus this change: all 802
repository checks, the preflight changelog question and ticket-ID check.
The committed-diff changelog check is also run after the commit; CI and
deployment receipts are recorded on T-2202.
