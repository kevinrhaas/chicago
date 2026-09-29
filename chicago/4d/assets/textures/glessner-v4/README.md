# Glessner v4 material studies

Nine original deterministic PBR fabrics, generated with numeric noise:
granite grain, limestone grain, red-brown courtyard brick grain,
fine terracotta clay grain, muted weathered copper, dark oak and
dark olive painted joinery, short clipped turf and pale compacted gravel.

Run `python assets/textures/glessner-v4/generate.py` from `chicago/4d/` to regenerate.
`material-library.json` records metric repeat, seed, channel conventions and hashes.
Building albedo is 2048² sRGB JPEG; normal is 1024² OpenGL tangent-space PNG;
roughness is 1024² linear PNG. Ground albedo is 1024², with 512² normal/roughness.
Normals and roughness are filtered before reduction to avoid shimmer.
No ambient occlusion is baked into the colour, and no third-party pixels are used.

Every appearance is **reconstructed**. Stone and brick courses, joints, roof tiles,
the rock-faced silhouette,
openings, mouldings and copper standing seams are geometry, not flat photographs.
The copper's exact 1904 oxidation and every texture's microscopic arrangement are
artistic choices. The material library cannot establish a historical fact.

Export verification completed on 2026-09-29 with pinned Blender 4.5.3: all 25
material slots exported, 27 images deduplicated, albedo/normal/roughness all bound
to TEXCOORD_0, and metric SurfaceUV remained byte-for-byte unchanged through the
shared smart-unwrap step. Tint factors, copper metallicity and transmissive glass
with IOR 1.52 survived export.
The revised full material probe GLB was 15,284,056 bytes; the 27 source maps totalled
13,354,778 bytes, with no individual source map above 1.57 MB. This verifies the
material transport, not the finished building's visual quality.

The first close-view review exposed a stucco-like granite surface. The revised
granite normal has original domain-warped fracture fields at roughly 4–14 cm scale,
under its finer mineral grain; the warp breaks the conspicuous triangular pattern
seen in the second review. The glass now transmits through to the geometry's
separate dark backing and differently lowered blinds; it is not an opaque painted
window rectangle. Courtyard form and photographic likeness still require review
of the combined generated building.

The courtyard drive keeps the structure record's reconstructed pale gravel
interpretation for 1904; this library does not retroject the later concrete
paving into the model. The two ground fabrics add 1,586,424 source-map bytes.
Rough limestone headers use slot24, which pairs limestone albedo with the original
fracture normal at lower strength; smooth carved cornices retain slot2.
The brick slots distinguish main red-brown, dark-fired red, muted buff and smoky
gray-brown units. Buff and smoky variants reuse the neutral limestone colour
image with brick normal/roughness maps, adding no image payload. Their mixed
distribution is reconstructed kiln variability, not measured 1904 weathering.
