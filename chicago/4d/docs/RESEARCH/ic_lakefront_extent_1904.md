# Outer Illinois Central corridor and coast, 1904 (T-2495)

The detailed district stopped at local N -2900 and -3800. The context map continues
about 2645 m beyond both edges. Rails stopped at the district boundary while the
old terrain apron extruded each boundary's shoreline due north or south.

## Map read

E. H. Talbot, *Talbot's industry and railroad map of Chicago* (1904), University
of Chicago Library, Map Collection:

- [North sheet](https://www.lib.uchicago.edu/e/collections/maps/chi1900/G4104-C6P3-1904-T3-N.html)
- [Southeast sheet](https://www.lib.uchicago.edu/e/collections/maps/chi1900/G4104-C6P3-1904-T3-SE.html)

The Zoomify raster tiles were read at full resolution on 2026-10-14. The north
sheet's crop [13400,12100,14600,16456] shows the railway west of the Grant Park
fill, Central Station and the railway lands near Twelfth and Sixteenth Streets,
the southeast bearing past Twenty-second, and the wider railroad land at
Twenty-sixth to Twenty-eighth. The southeast crop [4400,0,6100,2000] carries the
corridor past Thirty-third through the southern end of the context map. Offshore
water hachures and detached breakwaters are not mainland shore.

`data/terrain/epochs/e1871_postfire/context_spec.json` preserves the pixel picks.
Six surviving Prairie/Indiana crossings at Sixteenth, Eighteenth and Twenty-second
fit the north raster to the existing project control. The generated context file
records all residuals. This is a small-scale map and the outer reach is beyond the
control: **40 m is a working uncertainty, not the much smaller fitted residual**.
The southeast sheet is tied at the north sheet's southern rail continuation and
carries its scale and axes; this registration is reconstructed, not surveyed.

## What the scene does with it

`python3 tools/extend_ic_lakefront_1904.py` emits the context coast sidecar, its
indexed apron GLB, and `data/railway/1904_context.json`. The railway file contains
the existing detailed tracks verbatim and a connected continuation for each track
that meets a district boundary (nine north, eleven south). The map depicts a
corridor symbol, not a track census: those outer counts, the 4.3 m spacing and the
intermediate curves are reconstructed. They are not claimed as traced rail pairs.

The detailed district remains on its prior Sanborn-derived reconstruction. The
first 160 m outside each edge joins that reading to Talbot's outline. The terrain
carries each boundary cross section along the resulting coast. Its grades are
reconstructed; no period level survey has been located. The ground GLB and the
runtime sampler use that same section, so track beds, context roofs, streets and
walking heights agree. The old straight apron triangles are removed, not covered
with a second conflicting coastline. The original district mesh is retained.

The rail corridor and coastline are independent north of Twelfth: the intervening
Grant Park fill is not covered wholesale in railway ballast. Talbot labels it
“Being filled up”; the map's drawn mainland boundary bounds this reconstruction,
not a claim that every part of the fill was complete on 1 July. Detached
breakwaters, station buildings, switch details and individual piers are not
reconstructed as structures in this change.

The extension ends at the context map's actual north/south reach, derived from the
same haze distance as `build_context_1904.py`. Beyond the map, the far terrain apron
holds its last coast section to its existing outer edge. This is a rendering
continuation, not another historical observation.

## Validation

The generator's `--check` re-derives all three outputs. It checks that the original
tracks are unchanged, every extension meets its named parent endpoint exactly,
both directions reach the context boundary, all rail centres remain on dry flat
ground, source ids resolve, and the terrain sampler is continuous at both joins.
Browser results and remaining gate limitations are recorded in STATUS.md.

Published Chromium/SwiftShader views at 1280x800, 120 m above the core joins:
[north](ic-lakefront-2495/north.png), [south](ic-lakefront-2495/south.png).
Both were captured after entering the scene, with real rendering active. The
1904 boot reported no problems and no page errors. These views document the
implementation, not additional historical evidence.

Phone-sized 390x780 Light views also load without errors:
[north](ic-lakefront-2495/mobile-north.png),
[south](ic-lakefront-2495/mobile-south.png). Published mobile smoke parts 3/14:
221 passed, zero failed (15m34s on this SwiftShader runner).

Final preflight passes, including all 876 code/data gate steps. Full desktop
aerial views use 260 / 104 draw calls and 2,741,643 / 1,000,839 triangles (north /
south), within 330 calls and 4,600,000 triangles. These are draw-count readings,
not a hardware frame-rate claim. The broader desktop smoke twice timed out
booting 1835 before the requested sections, with zero page errors; that gate is
unresolved, so this change is not merged or promoted to production.
