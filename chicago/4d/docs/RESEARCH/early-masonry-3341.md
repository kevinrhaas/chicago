# Early masonry surfaces — T-3341

This source checkpoint binds the existing Chicago 1835 procedural brick and clay
sheets to the early scenes' remaining untextured materials. Published visual and
resource qualification is pending; this document does not claim a completed ticket.

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
Fourteen fort brick/stack material instances already wear period sheets from
T-3387; those sheets, UVs, mean colours and existing K03 shuffle are preserved.
These include the first fort's magazine, so its before/after is a regression
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
capacity change (AGENTS.md, the owner's frame-budget ruling); its precise new
boot/site allowance and actual post-change measurements remain pending until the
current picture-group merge supplies the integration baseline. Light geometry,
ordinary draw-call caps and inspection limits are not part of this change.

## Verification at this checkpoint

- Nine focused checks pass, including actual native mixed-stack conservation,
  explicit ridge-vs-gable selection, exclusion of mapped/1904 materials, shader
  composition and the original twelve-course K03 bindings.
- The new owner was instrumented and wrote nothing in-tree. Its measured row is
  enrolled in the complete source gate.
- The six WebPs and four KTX2 maps were derived by the existing canonical
  encoders. Their packed statements name the unchanged masters.
- Source syntax passes. Full source CI, published desktop/phone before-and-after
  frames, actual boot, and 1812/1835 phone memory remain pending.

The final visual packet must include the already textured magazine as a control,
a first-fort ridge stack, an 1835 brick building and a cabin's exterior stack at
desktop and 390 by 780. No completed sign-off is inferred from the unit checks.
