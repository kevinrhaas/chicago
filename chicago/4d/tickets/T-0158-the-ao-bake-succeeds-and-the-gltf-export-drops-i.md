---
id: T-0158
title: The AO bake succeeds and the glTF export drops it: the shipped occlusion texture is uniformly black
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-27
pr: 389
claimed_by: run 8/26/2026, 11:27:17 PM CT
blocked_on: null
needs_bake: false
---

Split out of T-0015, which measured it. `generators/build.py --ao` bakes ambient
occlusion correctly and then ships nothing:

| | measured 2026-08-23, `sauganash_hotel`, 512×512, 48 samples |
|---|---|
| in memory, straight after `bpy.ops.object.bake(type="AO")` | min **0.000**, max **1.000**, mean **0.2158** over 262,144 texels |
| in the exported GLB's `occlusionTexture` | min **0**, max **0** — every texel |

So the bake is fine and the export loses it. Confirmed with two independent PNG
decoders (a hand-rolled one and the repo's own `critic_metrics.decodePng`), and
the exported PNG is byte-identical at 3,620 bytes whether or not the object is
explicitly selected and activated before the bake — so selection is **not** the
cause and does not need re-testing.

What makes it worth a ticket rather than a footnote: it fails silently in the
worst direction. The run exits 0, the texture is wired into all six materials,
the GLB grows 4 KB, and `assets/manifest.json` records `baked_ao: true`. Under
glTF an occlusion value of 0 means FULLY occluded, so every asset built this way
would render with its ambient light extinguished — while the manifest asserted
it carried good AO.

`assert_ao_survived_export()` in build.py now refuses this at build time (T-0015),
so the failure is loud. This ticket is the mechanism behind it.

Worth checking first, in rough order of likelihood: whether the image needs
`img.pack()` or a `filepath` before the exporter will read its pixels; whether
the exporter re-reads the image from disk rather than from the in-memory buffer;
whether `colorspace_settings.name = "Non-Color"` being set AFTER the bake
invalidates the buffer; and whether the `ShaderNodeSeparateColor` → `Occlusion`
wiring path exports the node's input rather than the texture.

Note this is the SECOND fault of this exact shape here — the comment above the
wiring block records that the exporter once dropped AO entirely, "the bake
silently produces nothing, which is exactly what happened before this was
added". A fix should leave behind something that fails when it recurs, not just
a working export.

**Acceptance:** `--ao` on one asset produces a GLB whose occlusion texture holds
real variation — `assert_ao_survived_export` passes on merit rather than being
relaxed — and the in-memory mean and the exported mean agree to within a few
per cent, demonstrated by printing both. If the export path turns out to be
unfixable within Blender's exporter, that is a legitimate outcome recorded with
the evidence, and `--ao` should then be retired rather than left as a flag that
cannot work.

---

## FIXED 2026-08-27 — the third hypothesis was right, and it hid a second fault

**The mechanism.** `colorspace_settings.name = "Non-Color"` was set AFTER the bake. Setting a
colorspace on a GENERATED image with no file behind it and no packed data **frees the image
buffer**, which regenerates from `generated_color` — black — and **clears `is_dirty`**, the flag
Blender's exporter tests in `make_temp_image_copy()` before it will carry unsaved pixels. One
statement destroyed the data and switched off the exporter's rescue path. The fix is to tag the
image before the bake.

The ticket's other three suspects are eliminated with it: no `pack()` and no `filepath` are
needed, the exporter reads the in-memory buffer perfectly well, and the
`ShaderNodeSeparateColor` → `Occlusion` wiring exports the texture correctly. Two of them
(`pack()`, and leaving the colorspace alone) also *survive* the export — they are simply the
wrong number, see below.

**Measured** — `sauganash_hotel`, 512×512, 48 samples, Blender 4.5.3, four bakes of the same
asset; occlusion PNG lifted out of the GLB and decoded by a stdlib reader self-tested against all
five PNG filter types:

| when the image is tagged `Non-Color` | in memory after the bake | in the exported GLB | drift |
|---|---|---|---|
| **after the bake — as shipped** | min 0.000 max 1.000 mean **0.2158** | min **0** max **0** mean **0.0000** over 262,144 texels | **100 %** |
| **before the bake — the fix** | min 0.000 max 1.000 mean **0.1665** | min 0.0000 max 1.0000 mean **0.1665** | **0.0 %** |
| bake, `pack()`, then Non-Color | mean 0.2158 | mean 0.2158 | 0.0 % |
| no colorspace change at all | mean 0.2158 | mean 0.2158 | 0.0 % |

**The second fault: 0.2158 was never the occlusion.** `Image.pixels` on an 8-bit buffer is RAW in
both directions — set 0.1665, read back 0.1647, saved PNG byte 42, identically under `sRGB` and
`Non-Color` (an sRGB encode would be byte 113). So the tag decides what the **bake writes**, not
how the buffer is read: under `sRGB` the bake stores the sRGB-ENCODED occlusion. glTF samples an
occlusion texture as `byte / 255` with no transfer decode, so the old path was ~30 % too bright
before it went black.

**The third fault, and it is the one that matters most: the population.** `bake_ao()`'s
"mean 0.265, **69 % of texels below half**" and R-W3a's copy of it are taken over the whole
512x512 atlas — and **68.9 % of that atlas is empty UV space**. The famous 69 % is very nearly
the empty fraction itself; most of what it counted was blank, not dark. Over the **81,458**
texels the unwrap actually writes, the corrected reading is **mean 0.5358 with 58.7 % below
half** — not 0.1665 and not 0.265. The 0.38 has not been re-measured at all.

So every number the AO parcel is written around is void, in two independent directions, and
**none of them was ever read off a file that carried the occlusion** — the export was shipping
black. The concern's shape survives (over half the written surface below half occlusion, on a
documented-white building) but nothing quantitative does. Corrected in place in `bake_ao()` and
R-W3a, and **T-0227** filed to settle it from a rendered frame before a cage is built to improve
a figure nobody has measured correctly.

**Acceptance, met.** `--ao` on one asset:

```
AO baked mean 0.1665 -> exported mean 0.1665 (min 0.0000 max 1.0000) over 262,144 texels, 0.0 % drift
built sauganash_hotel__frame_1831.glb  202,292 bytes  ~1124 tris
```

`assert_ao_survived_export()` passes on merit, and was shown **refusing the real broken GLB**
(uniform 0.0000 over 262,144 texels) rather than only a synthetic one. `--ao` is NOT switched on:
at mean 0.1665 it is still the geometry problem R-W3a describes.

**What fails when it recurs.** `generators/ao_export.py` — a stdlib PNG decoder and GLB reader
(no Blender, no numpy, no Pillow; CI installs `jsonschema` and `pyproj` only). `build.py` asserts
on the exported bytes and writes the manifest entry **only if it passes**, so `baked_ao: true`
cannot outlive the occlusion. `--gate` runs in `check.sh` over all 348 masters in 0.27 s and
cross-checks the manifest in both directions; `--self-test` breaks all 17 assertions in memory.
A uniformly WHITE texture is refused too — a guard that only knows the failure it has seen is
the guard that lets the next one through.

**Cost, for whoever takes R-W3a.** With the export working, the master goes 94,420 → 202,292
bytes (+114 %) — so T-0015's "+4.4 % file size" was measuring the size of the bug and is void.
A 512² map on each of 348 masters is ~+37 MB, textures do not meshopt, and the published tree is
23.53 MB against a 25 MB budget.

**The rebake.** `mesh_inputs.py` hashes `build.py`'s bytes, so this reorder restaled all 346
structure masters. The rebake took 1 m 23 s and all 346 GLBs came back byte-identical; the only
change under `assets/` is 346 hash strings in `manifest.json`. The route T-0015 could not use
(T-0139) now works and is cheap.
