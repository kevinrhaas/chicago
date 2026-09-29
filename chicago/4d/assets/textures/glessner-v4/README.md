# Glessner v4 material studies

Seven original deterministic PBR fabrics, generated with numeric noise:
granite grain, limestone grain, red-brown courtyard brick grain,
fine terracotta clay grain, muted weathered copper, dark oak and
dark olive painted joinery.

Run `python assets/textures/glessner-v4/generate.py` from `chicago/4d/` to regenerate.
`material-library.json` records metric repeat, seed, channel conventions and hashes.
Albedo is 2048² sRGB JPEG; normal is 1024² OpenGL tangent-space PNG; roughness is
1024² linear PNG. Normals and roughness are filtered before reduction to avoid shimmer.
No ambient occlusion is baked into the colour, and no third-party pixels are used.

Every appearance is **reconstructed**. Stone and brick courses, joints, roof tiles,
the rock-faced silhouette,
openings, mouldings and copper standing seams are geometry, not flat photographs.
The copper's exact 1904 oxidation and every texture's microscopic arrangement are
artistic choices. The material library cannot establish a historical fact.

Export verification completed on 2026-09-29 with pinned Blender 4.5.3: all 24
material slots exported, 21 images deduplicated, albedo/normal/roughness all bound
to TEXCOORD_0, and metric SurfaceUV remained byte-for-byte unchanged through the
shared smart-unwrap step. Tint factors and copper metallicity survived export.
The full material probe GLB was 13,969,088 bytes; the 21 source maps totalled
12,158,443 bytes, with no individual source map above 1.69 MB. This verifies the
material transport, not the finished building's visual quality.
