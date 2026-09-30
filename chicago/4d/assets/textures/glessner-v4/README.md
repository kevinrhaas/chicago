# Glessner v4 material studies

Nine original deterministic PBR fabrics made with numeric noise, plus separately
preserved original generated granite and turf albedos. The procedural fabrics are granite,
limestone, grey-tan common brick, terracotta, weathered copper, oak, green painted wood,
short turf and pale compacted gravel. Every appearance is **reconstructed**.

## Reproduction and provenance

Run `python assets/textures/glessner-v4/generate.py` from `chicago/4d/` to regenerate
the nine numeric fabrics. The recipe never overwrites
`granite_photographic_basecolor.png` or `turf_photographic_basecolor.png`. Both 1254²
RGB PNGs are unchanged original outputs of text-to-image generation without
reference images. Their exact prompts, methods, SHA256 and limitations are in
`granite_photographic_provenance.json` and `turf_photographic_provenance.json`.
No historical, supplied, Google, aerial or other photographic pixels were sampled,
traced or embedded. This generated material study is not a photograph or measured
reflectance scan of Glessner House and cannot establish historical appearance.

`material-library.json` records metric repeat, seed, channel conventions and hashes.
The 29 source maps total 20,387,130 bytes, including the 3,850,146-byte generated
granite PNG and 3,881,389-byte generated turf PNG. The active building uses them
for granite and lawn colour only; both numeric albedos remain reproducible source.
Building numeric albedo is 2048² sRGB JPEG; normal is 1024² OpenGL tangent-space PNG;
roughness is 1024² linear PNG. Ground albedo is 1024², with 512² normal/roughness.
Granite numeric albedo uses JPEG quality 89; other numeric albedos use quality 92.
Normals and roughness are filtered before reduction to avoid shimmer. The numeric
maps contain no baked ambient occlusion. The generated albedo prompt targets even
diffuse illumination and seamless edges; these are targets, not measurements.

## Material transport

Export verified on 2026-09-29 with pinned Blender 4.5.3: 28 material slots, 27 images
deduplicated, and metric SurfaceUV unchanged through the shared smart-unwrap step.
All texture references use TEXCOORD_0. Granite albedo repeats at 0.22 m through
KHR_texture_transform (scale 7.2727273); its procedural normal and roughness repeat
at 1.6 m. Turf albedo repeats at 0.4 m (scale 6), with numeric normal/roughness at
2.4 m. Granite normal strength is 1.0, rough court trim 0.8 and turf 0.25.
Three appended double-sided blade materials (slots25–27) use plain muted greens
and roughness0.92. The full material probe GLB is 20,808,216 bytes. Tint factors, copper metallicity and clear glass with
transmission 0.94 / IOR 1.52 survive export. This verifies transport, not completed
photographic likeness of the whole building.

## Reconstruction choices

Stone courses, joints, block outlines, openings, mouldings, roof tiles and copper
standing seams are geometry. The earlier crumpled procedural stone appearance led
to replacing active granite albedo with the original generated crystal study.
The 0.6 m initial repeat made crystals look pebbly; 0.22 m makes them finer. Cool
material multipliers counter excess pink feldspar. Numeric normal domain warp was
reduced from0.015 to0.004 to retain more angular fractures, and controlled neutral/directional studies selected normal strength1.0 with
5x3 physical split facets. Strength1.25 was too busy; the earlier0.4 was too flat.
The denser facets preserve the course boundary and use a4–70mm peak-offset cap
around the existing nominal8–46mm extrusion. This is reconstructed microgeometry. Numeric maps remain available;
none is presented as a measured historic surface. Rough court heads and sills use
granite grain; smooth carved cornices retain the separate limestone study. These
are reconstructed visual choices, not petrographic identification.

The brick body is grey-tan common clay, with intermittent warm red-fired, neutral
buff and smoky units, rather than predominantly saturated orange-red. Existing
60/20/14/6 unit distribution is retained. Slightly lighter, more neutral lime mortar
keeps joints legible; no soot or modern age staining is added. Buff and smoky units reuse limestone colour with
brick normal/roughness maps. This is reconstructed kiln variability, not measured
1904 weathering. Copper uses subdued brown/green patina; its exact oxidation after
17 years is an artistic choice. Its low-contrast maps let standing seams carry the
sheet construction. Pale linen blinds and muted green joinery are separate from
clear glass; no scene reflections are painted into windows. Oak midtones are warm
brown with restrained grain and varnish roughness bounded0.40–0.61, replacing the
earlier nearly black door appearance.

The drive retains the structure record's reconstructed pale gravel interpretation
for 1904. No later concrete paving is retrojected. The original numeric turf and gravel maps add 1,586,424
source-map bytes; the separate generated turf albedo is retained unchanged. Whole-building materials, geometry, lighting and historical
confidence still require review together.

The tower lantern belts use a v4-local curved block helper, supported by HABS
courtyard photo05 and the supplied courtyard close views. One stone course with
reconstructed joints replaces each smooth drum. Both rings keep their prior
outer radius and vertical endpoints; rough faces fit inside that envelope and
a narrow15mm top seating edge uses the same granite fabric. No new cornice or
height is added. Exact joints and microrelief are reconstructed, not measured.
