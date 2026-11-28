# Scalable period hair — T-3792

Hair has three separate responsibilities: `human-hair-styles.js` describes period cuts,
`human-hair.js` builds and shades them, and `human-hair-dynamics.js` controls crowd
admission and secondary motion. The existing Graphics detail setting selects the tier.

| Tier | Near heads | Drawn near hair-card triangles | Distance | Tip limit |
| --- | ---: | ---: | ---: | ---: |
| Light | 0 | 0 | — | 0 |
| Balanced | 12 | 72,000 | 20 m | 2 mm |
| Full | 16 | 220,000 | 24 m | 8 mm |

These bounds cover **all optional near scalp and facial cards**, including existing
styles. Nearest heads receive detail first, with a small preference for an admitted
head to avoid swapping detail at equal distances. A denied head keeps its body cap and
photographic face. Body caps, full photographic skins and the existing Light tails
remain under body LOD rules. Rendered triangles and total resident/parked geometry
are different quantities; the table is a draw bound, not a whole-app memory bound.
Newly added triangles are reported separately in `humans.hairStats.addedTriangles`.

Each body owns its material uniforms, while compatible bodies share the compiled
shader program. A critically damped spring follows bounded inertial movement and a
small seeded reconstructed breeze. Tied hair uses one quarter of the tip limit and
settles faster. GPU deformation pins roots and facial cards, removes the inward
component at the scalp and observes the hat band's clipping plane. Vehicle parents
contribute their world movement. LOD swaps preserve the spring pose; disposal removes
the controller and owned materials. Geometry buffers are not rewritten each frame.

Close photographic buns gain fine overlapping cards over the existing cap. Strand
edges use the renderer's existing MSAA; computers with MSAA off retain the original
deterministic alpha cutoff. No temporal accumulation, new atlas or additional
multisampling pass is introduced. The original Grey fitted heads and full skins keep
their existing hair and beard shapes.

The child review found native caps intersecting their own skulls by up to 1.15 mm.
Cap fitting now runs in build slices, using the child's own skin to provide 2.5 mm of
clearance. It retains the cap's triangle/vertex count and UVs, and leaves the child's
head, eyes and proportions intact. Normals accumulate in float precision. Its static
geometry variant follows the source cap's disposal; it adds no texture or draw call.

Focused tests cover the spring's independent closed-form solution, frame subdivision,
teleports, motion limits, crowded tier budgets, optional-card admission, per-body
uniform ownership, driver transfer, LOD parking and child-cap clearance against an
independent sphere. Native tier comparisons, the complete project gate and published
desktop/mobile checks qualify delivery. Node controller timings and SwiftShader
stills do not establish physical-GPU frame rates; those remain unmeasured.
