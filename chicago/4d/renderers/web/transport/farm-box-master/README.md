# Reconstructed farm-box wagon

This is one reusable optical/engineering specimen, separate from the eighty
placed static wagons and three selected fine-wood stands. It does not establish
an actual 1835 Chicago wagon, maker, owner, material species, paint or working
harness. Its named seat/boarding/hitch nodes are empty proposed interfaces.

Old Cart by Lyskilde/longtail is the licensed geometry/UV/PBR basis (CC BY4.0).
The unchanged 9,809,548-byte original and all six embedded PNGs remain in
`assets/authored/transport/farm_box_master_v1/old-cart-original.glb`.
`ATTRIBUTION.md` and `SOURCE.json` there identify the exact original, derivative
changes and rights. The authored metric master retains original PNG payloads;
web near/mid/far use explicitly measured WebP derivatives and meshopt compression.
The generator's GPL code license does not replace the source asset's CC BY4.0.

The body targets 3.05 by 1.07 by .55 metres, bed .95 metres, wheel radii
.535/.685 metres, track 1.21 metres and axle stations +/-1.175 metres. These
reuse earlier reconstructed W01 values, not recovered historic measurements.
The source's eight-spoke wheels and surface details are retained. The original
front axle pose is neutralized, wheel radial planes calibrated independently,
and one shaft becomes a central pole with a real bearing connection. Paired
shafts, exact original proportions, original steering pose and modern source
construction consequently differ deliberately. Unseen joinery, colors, wear
and small hardware remain reconstruction; ground contacts follow a lightly
irregular artist rim, not a perfect analytical wheel or suspension simulation.

Use the real detail/finish/steer/travel/pole controls. A grid square is one metre.
The optional warm material finish reuses all texture maps with a modest material
factor; neither finish is historically attested. Near frames the complete
specimen; middle/far use the rear wheel at 96/24 projected pixels. “Keep view”
allows direct comparison at one camera. Technical counters stay in Model details.
CPU submission/frame intervals are diagnostics from the current browser, not
physical-phone/GPU performance certification. The fixture has no actor routing,
boarding, load/force model or production scene-selection side effect.

Regenerate the authored master with the repository Python environment:

```sh
python3 tools/transport/farm_box/adapt_old_cart.py \
  --parameters data/transport/studies/farm-box-master.json \
  --output-dir /tmp/fresh-farm-box-master
```

Export using the explicitly pinned, separately installed tools directory (no
downloads occur in the producer):

```sh
node tools/transport/farm_box/export_lods.mjs \
  --input /tmp/fresh-farm-box-master/farm-box-source.glb \
  --output-dir /tmp/fresh-farm-box-web \
  --parameters data/transport/studies/farm-box-master.json \
  --tools-root /path/to/pinned/node_modules
```

Pins are glTF Transform core/functions/extensions4.5.0, meshoptimizer1.2.0 and
sharp0.35.5. `EXPORT-RECEIPT.json` binds exact source, recipe, exporter, output
bytes, oriented paired shader-attribute triangle preservation and explicit
negative controls. Near geometry/UVs/normals/tangents are exact to the metric
master. Mid respects .001 simplification error; far preserves structural timber
and the mid wheel geometry, avoiding the rejected board/rim damage. Near/mid/far
are distinct geometry and texture representations; none is a duplicate raw trial.
Normal/ORM maps have independent channel and normal-angle error checks. Smaller
normal maps are lossless because a measured near-lossless trial exceeded1degree.
All three deliveries declare required EXT_meshopt_compression/EXT_texture_webp.
The authored original/master are outside the copied renderer subtree.

`python3 tools/check_farm_box_master.py` regenerates the actual authored bytes,
checks frames, compact bounds, finite geometry, exact protected old selections,
current codec receipt hashes, conservative continuous front wheel/body clearance
and actual indexed pole/bearing/axle surface connection. Its deliberately moved
body and detached pole controls must be rejected. Clearance proof excludes
intended axle/hub interfaces; joinery contact is not load/strength certification.
A separate actual indexed 108-pose wheel/body diagnostic is retained in evidence.

Actual matched dated-reference review, current published app/budget/desktop/mobile
release coverage and ticket acceptance are separate from these construction
checks. Later1893 Studebaker Farm Wagon No4 is a period analogy only, never proof
of an1835 Studebaker or this particular specimen's presence. No photographic
completion or whole T-2793 closure follows from a generator/schema/preview PASS.

Measured source fit limits: the retained artist kingbolt is4.994mm eccentric
from the reconstructed yaw pivot, moving0.697mm over8degrees. Original rims
retain up to2.617mm all-roll ground irregularity, within the declared3mm mesh
tolerance. These are disclosed reconstructed/artist fit limits, not exact
coaxial joint, ideal-circle, suspension or load certification.

The final portable contract separately owns the actual source kingbolt in
vehicle_kingbolt and adds an actual central coupling in vehicle_reach. The
90x55mm reach reuses the licensed shaft geometry/UVs; its reconstructed endpoint
heights .6675/.73m meet the actual fixed front bolster and rear axle. It is not
an empty interface or a body stringer renamed as reach. Actual indexed-surface
connection and detached-reach negative controls are required. This adds44
triangles and two material batches; current webset is8,465,076bytes. Earlier
pre-reach pictures remain historical and do not qualify this added member.

Reviewed family-form analogues now include the held1835 Wild Cincinnati painting
and the explicitly retrospective Buffalo open-box print. See
`docs/RESEARCH/farm-box-master-2793/REFERENCE-COMPARISON.md` and
`data/sources/wild_1835_third_vine.json`. These do not replace the licensed
modern construction source or attest this individual model in Chicago.
