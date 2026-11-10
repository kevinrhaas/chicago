# Early masonry surfaces — T-3341

The existing Chicago 1835 procedural brick and clay sheets now cover the early
scenes' remaining untextured materials. Actual desktop/default-phone visual,
whole-boot and phone-memory qualification pass on runtime `cab4514539`.
PR #1918 carries the remaining protected-check and dev-merge release gates.

The material and fabric argument is already recorded in [chimneys.md](chimneys.md).
The library's own `material.json` retains its evidence labels: brick fabric is
attested, its dimensions are reconstructed; the stick-and-clay face is reconstructed.
The procedural maps are project-permissive original output, covered by
`assets/LICENSES.md`; no held photograph or third-party image supplies their pixels.

## Surface selection

Only sidecars whose `scene` is `1812` or `1835` can bind this path. The `brick`,
`draft_brick`, `k13_brick` and interior `chimney` roles take brick; a `wall` role
takes it only where the record says brick construction. An exterior log stack
takes clay. A log building with the explicit `chimney_ridge_at` attribute takes
brick on that ridge, following the same standing fabric ruling as the fort.

The actual before census covers 447 scene/phase sidecars with these material roles.
Fourteen early brick/stack material instances already wear period sheets from
T-3387; those sheets, UVs, mean colours and existing K03 shuffle are preserved.
These include the first fort's magazine and the Lake House shell, so their before/after is a regression
control rather than a claim that this ticket first gave it a texture.

The seven recorded ridge cases are `kinzie_house_1812`,
`kinzie_lodging_house_1812`, `kinzie_bake_house_1812`, `wolf_point_tavern`,
`philo_carpenter_log_shop`, `jb_beaubien_homestead` and `hogan_store`.
`miller_house` records a ridge stack on its frame addition and an exterior stack
on its log core. Its one native chimney primitive is partitioned by the two
disconnected stack footprints: the ground-foot component and its overlapping
corbel stay clay; the roof-foot component takes brick. The actual native test
proves every triangle position and confidence value survives that partition.

## The shader and its limits

Face coordinates are projected in metres, as the existing wall relief does.
The brick sheet's generator states 20 columns and 48 courses across 4.2 metres,
with alternate half-brick offsets. Those reconstructed dimensions are used
directly, rather than borrowing the 1904 library's module. The clay sheet spans
2.04 metres. The existing brick-bond algorithm supplies the whole-brick
permutation, shade and mottle; normal, roughness, occlusion and luminance sample
the same permuted face with the original derivatives, preserving mip selection.
The native mean colour stays the mean. See L-early-masonry-surfaces-3341.

The new 48-course shader is a separate registration. The existing 1904 shader,
twelve-course uniforms and panel bindings are unchanged. A page with no early
scene fetches none of the new sheets. `?masonry=flat` provides the untextured
comparison; `?bricks=tiled` retains relief but disables the shuffle.

## Measured source cost, before budget changes

The canonical encoder produced these 1024-pixel KTX2 deliveries:

| Sheet | Normal bytes | Packed ORL bytes |
| --- | ---: | ---: |
| Clay brick and lime mortar | 315,054 | 126,350 |
| Stick-and-clay | 411,110 | 72,804 |
| Total | 726,164 | 199,154 |

That is 925,318 new compressed map bytes before material metadata and code.
The six lossless WebP fallbacks total 1,625,354 bytes. Existing device texture
policy drops the top mip on a phone, giving 512-pixel maps from these deliveries.
No native vertex, triangle, GLB or existing texture is replaced.

The prior actual published boot cost was 45,948,374 bytes against a 44.1 MiB
allowance, leaving 293,827 whole bytes. The added maps exceed that room, so no
whole-boot FITS claim is made here. The project permits a documented, measured
capacity change (AGENTS.md, the owner's frame-budget ruling); its new
44.9 MiB boot and 436 MiB storage allowances are explicitly priced in SITE-BUDGET
section 18. The actual whole boot is 46,888,266 gzip-wire bytes (44.716135 MiB)
against 44.9 MiB, with 192,796 whole bytes spare. Light geometry,
ordinary draw-call caps and inspection limits are not part of this change.

## Verification at this checkpoint

- Nine focused checks pass, including actual native mixed-stack conservation,
  explicit ridge-vs-gable selection, exclusion of mapped/1904 materials, shader
  composition and the original twelve-course K03 bindings.
- The new owner was instrumented and wrote nothing in-tree. Its measured row is
  enrolled in the complete source gate.
- The six WebPs and four KTX2 maps were derived by the existing canonical
  encoders. Their packed statements name the unchanged masters.
- Source syntax passes. All eight protected source parts and their aggregate pass
  on `cab4514539`, including the existing K03 and joint-floor owners. Their negative
  fixtures remain active; neither owner was weakened. Moving-frame and
  upload-release checks also pass on that runtime.
- Actual desktop 1280 by 800 and default-touch 390 by 780 before/after frames pass
  in both scenes: 28 directly reviewed surface images and two detail roundtrips,
  with no page, console, failed-request or bad-response errors.
- Official normal boot and both unchanged-ceiling default-phone memory gates pass;
  the measurements and limits are below.

## Actual published qualification, 2026-11-10

[Public qualification packet](https://github.com/kevinrhaas/chicago-evidence/tree/be72d55f6e5609efb2a712fcb8e342f9e5de6eea/evidence/t3341-early-masonry-20261110) contains exact source,
published-asset and grade pins, all real screenshots, camera matrices, raw gate
outputs and rejected fixtures. The 1835 visual build is `39df38072a`; 1812 and both
resource tools run on `cab4514539`. That final runtime only splits the same material
clone predicate into the existing joint-floor guard's required initializer and an
explicit early-material clone. The actual 33-house check and all three negative
fixtures pass without changing that owner. No shader, native asset or map changed
between those two visual builds.

| Gate | Actual | Ceiling |
| --- | ---: | ---: |
| First 1835 visit, gzip wire, ready plus 3 seconds |46,888,266 bytes /44.716135 MiB |44.9 MiB |
| Default 1812 phone resident estimate |320,512,587 bytes /305.664622 MiB |350 MiB, unchanged |
| Default 1835 phone resident estimate |533,963,944 bytes /509.227699 MiB |550 MiB, unchanged |

The official boot tool counts 1,207 real responses with zero failures. Its nine
new masonry requests total 927,833 gzip-wire bytes; no new albedo URL is requested
in the normal after boot. The 939,892-byte difference from the earlier 45,948,374-byte
post-B publication includes concurrent code integrated through PR #1910, such as
horse and shared-asset publication modules; it is not all attributed to this ticket.
The packet includes exact before/after URL entries. The entire current boot is
gated regardless of cause.

The unmodified official memory meter enters each published year door at spawn,
waits for uploads, draws real frames and performs two GCs. Both rows use default
Light, report no page errors and keep the normal geometry-release policy. Source
and published-build identity remain fixed before/after both resource tools. These
are measured resident estimates, not driver-overhead guarantees or frame timings.
The standalone full WebP view remains development fallback coverage; it does not
claim a measured fallback-phone memory result.

Actual bindings are 1812 brick 4/clay 11 and 1835 brick 357/clay 63. Full sheets are
1024 pixels; default phone sheets are 512. Both 1835 Full/Light detail roundtrips
retain all bindings. The magazine, north-range ridge and LakeHouse shell are
already mapped regression controls. Newly bound close views show GreenTree's
brick stacks, Kinzie bake-house ridge masonry, Miller's exterior clay and its
separate addition-ridge brick. Existing declared review annotations are classified
individually (26 in 1812, 14 in 1835); none is relabelled a new load failure.

These are reconstructed diagnostic camera stations, not historical photograph
stations. All 28 accepted surface frames were directly opened and reviewed. Six
original phone fixtures are retained as rejected because the People navigator
covered their stacks. Corrected views dock the real app navigator and fully expose
the stack faces. On the accepted before-magazine phone view, the navigator's closing
transition covers the lower door, while the full upper brick wall remains clear;
that frame qualifies the brick control only. Desktop People cards sit beside the
stack faces. No screenshot pixels or CSS are replaced. Final GitHub checks and
the dev merge are recorded by PR #1918 rather than inferred from this runtime packet.
