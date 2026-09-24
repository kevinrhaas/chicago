# Chicago 1835 PBR Texture Library

Version 1.0.0 provides **25 seamless, 1024 × 1024, physically scaled materials** for the
1835 Chicago reconstruction. The library is engine-neutral and includes both Blender/OpenGL
and Unreal/DirectX normal maps.

## What is included

Each material folder contains:

- `*_basecolor.png` — 8-bit RGB, sRGB; no directional lighting or cast shadows
- `*_normal_gl.png` — 8-bit RGB, linear; OpenGL/Blender (+Y)
- `*_normal_dx.png` — 8-bit RGB, linear; DirectX/Unreal (-Y)
- `*_roughness.png` — 8-bit grayscale, linear
- `*_height16.png` — 16-bit grayscale, linear
- `*_ao.png` — 8-bit grayscale, linear
- `*_metallic.png` — 8-bit grayscale, linear
- `*_orm.png` — 8-bit RGB, linear; R=AO, G=Roughness, B=Metallic
- `material.json` — physical span, texel density, confidence, notes, and color-space contract

The root also contains `manifest.json`, this guide, research notes, a contact sheet, and the
deterministic generator used to build the library.

## Material coverage

| Group | Materials |
|---|---|
| Walls | weathered clapboard; whitewashed clapboard; white lead-painted clapboard; red-oxide clapboard; board-and-batten; vertical sawn boards; hewn oak logs with chinking |
| Timber | weathered sawn boards; fresh framing; weathered heavy timber |
| Roofs | weathered wood shingles; weathered board roof |
| Masonry | local clay brick with lime mortar; rubble limestone with lime mortar; cat-and-clay chimney daub |
| Ground | packed black loam; muddy rutted street; wet prairie muck; Lake Michigan dune sand; river-stone/gravel fill |
| Waterfront | weathered plank walk; water/tar-darkened dock timber |
| Props | forged iron; plain weathered signboard; Sauganash blue-painted shutter |

## Historical-use rule

These files distinguish three evidence levels:

- **Attested**: a committed project source identifies the material or finish.
- **Inferred**: the material is reasoned from a named structure, regional building practice,
  or an already committed dimensional rule.
- **Reconstructed**: a bounded visual invention used where a scene needs a surface and no
  source settles its exact appearance.

Read each `material.json` before assigning a texture. A historically plausible texture is not
permission to apply it to every building. In particular:

- white lead paint and bright-blue shutters are exceptional, not town-wide defaults;
- red oxide is period-plausible but not attested on a named 1835 Chicago building in the
  current evidence set;
- the North Side school is the one directly attested shingled roof; applying shingles to
  other roofs is an inference or reconstruction;
- board-and-batten, the brick module, rubble-stone pattern, and exact shingle exposure remain
  reconstructed;
- no human or Indigenous depiction is contained in this library.

## Physical scale

Use the `span_m` field in each `material.json` as the width and height represented by one tile.
Examples:

| Material | One tile represents | Density |
|---|---:|---:|
| Clapboard | 4.48 × 4.48 m | 228.57 px/m |
| Hewn log | 4.08 × 4.08 m | 250.98 px/m |
| Board surfaces | 4.00 × 4.00 m | 256 px/m |
| Mud street | 8.00 × 8.00 m | 128 px/m |

Do not resize individual maps independently. Every map in a set aligns pixel-for-pixel.

## Blender setup

1. Connect Base Color as **sRGB**.
2. Set Normal, Roughness, Height, AO, Metallic, and ORM to **Non-Color**.
3. Feed `normal_gl` through a Normal Map node.
4. Feed Roughness and Metallic directly to Principled BSDF.
5. Use Height through a Bump node for real-time work, or Displacement with adequate subdivision.
6. Multiply AO into Base Color only if the target renderer lacks a dedicated AO input.
7. Set UV scale from `span_m`; do not tune until it “looks right.”

## Unreal setup

1. Import Base Color with **sRGB enabled**.
2. Import `normal_dx` as a Normal Map; it already uses DirectX green-channel orientation.
3. Import ORM with **sRGB disabled** and compression set for Masks.
4. Connect ORM R→Ambient Occlusion, G→Roughness, B→Metallic.
5. Import Height with sRGB disabled for parallax, virtual heightfield mesh, or displacement.
6. Set world-aligned or UV scale using `span_m`. Unreal units are centimeters, so a 4.48 m tile
   spans 448 cm.

## Generation and licensing

The production maps are original procedural output built from the reconstruction's dimensional
constants and declared color/roughness ranges. No third-party photograph is embedded or sampled.
The separate AI-generated mud study visible in the working conversation informed art direction,
but it is not copied into these production maps. See `RESEARCH_NOTES.md` for the evidence route.

