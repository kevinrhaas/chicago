# Glessner v4 refined-04 actual-model review

Actual GLB SHA-256: `5992aed6d90d6c5787ac18568f58a6e65a6952a204bfc160e9b4ead6aba73cdc`. Review harness imports the GLB without changing its meshes, UVs, textures or materials. Lighting, cameras and neutral ground are recorded in each review.json.

## Completed renders

- `refined-04-neutral/prairie-entry-detail.png`: 800 px, 48 samples, mathematical overcast.
- `refined-04-clear-entry/prairie-entry-detail.png`: 800 px, 48 samples, clear sky32/45 degrees.
- `refined-04-clear-court128/courtyard-bow-detail.png`: 800 px,128 samples, clear sky50/225 degrees. The preceding64-sample job was interrupted before saving any image and does not count as a result.
- `refined-04-geometry/`: fixed stable-south, alley-west, courtyard-west, overhead and overhead-west views,600 px/32 samples, mathematical overcast. These are geometry checks, not photographic hero images.

## Visual findings

The dense fracture geometry with selective corner normals is a meaningful stone improvement. The broad triangular wedges are less conspicuous, chipped borders survive, and the entrance arch's outer stones now share the rough finish. The carved entry and window band remain separate readable features.

The east courtyard dormers now have clearly projecting flared pyramidal caps, hip covers and finials. Ridge crest repetition is visible. The overheads show the intersecting roofs, small western dormer, copper return and distinct hollow chimney stacks. The rear views show stable/courtyard/garden windows and the raised north-court service access.

**New blocking visual defect:** the two curved lantern stone bands render as jagged high-contrast black/white cavities. The geometry parcel identified the custom-normal basis as planar at the origin despite a cylindrical position mapping. A local Jacobian normal transformation is required; this is not acceptable final stone shading.

At128 samples the direct-sun courtyard door glass is less speckled than at48 but still very dark. A separate controlled pane study identified open-backed/single-quad transmissive glass as the cause of much of the remaining noise and darkening. Closed4 mm panes and the Prairie door's opaque backing cutout are source repairs being prepared, not review-only shader changes.

The brick palette, lime mortar and broad lawn variation are being evaluated in a separate material-only trial on a verified unchanged copy of this geometry. The current lawn remains an even, clean green field; the brick reads more uniformly tiled than the supplied recent photographs.

## Gate

**Photographic quality has not passed.** Refined-04 advances the masonry and roof detailing but requires curved-band normal and glazing topology repairs before a final high-resolution assessment. Keep fixed QA views; the two additive oblique cameras are available for presentation without inventing context beyond the open passage.
