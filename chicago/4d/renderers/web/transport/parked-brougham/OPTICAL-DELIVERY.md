# Optical-only Brougham delivery

The parked runtime selects `brougham-near-delivery-v1.glb` and
`brougham-mid-delivery-v1.glb`. Their entire BIN chunks, geometry/layout/scene
JSON, node hierarchy and materials 0–6 are byte-identical to the retained physical
indexed near/mid masters. They retain 45,338/23,062 triangles and eight batches.
There is no geometric simplification or normal interpolation change.

Only cabin material 7 becomes a reconstructed thin-sheet alpha approximation:
BLEND, opacity 0.14, transmission 0, IOR 1.5. This avoids the renderer's additional
whole-scene transmission pass. The original four raw/indexed physical masters,
including their transmission 0.98 material, remain exact and separately checked.
The 1893 catalogue supports a design and colour family; neither optical coefficient
is a measured historic-glass property. Source attribution and GPL-3.0-or-later
licensing remain those of the original project-authored model.

Regenerate into a fresh directory with Node 22:

```
node tools/transport/brougham/generate_optical_delivery.mjs \
  --source-dir renderers/web/transport/parked-brougham --output /tmp/brougham-optical-fresh
```

Copy only the two generated `*-delivery-v1.glb` files into this directory and its
`CANDIDATE.json` as `OPTICAL-DELIVERY-RECEIPT.json`. The receipt preserves the
generator's fresh-output scope and false photographic/world-acceptance flags;
copying the derivative into the runtime does not turn those flags into acceptance.
`python3 tools/check_brougham_near.py` checks the unchanged physical masters,
independent full-BIN/JSON identity, genuine corruptions and byte-exact regeneration.
The native LOD test reads the actual files through vendored GLTFLoader.

The 24-view source-bound optical diagnostic on e97 completed with no runtime
errors but was NONPASS: one Full carriage view exceeded the old 4.6M ceiling and
both Light aerial stands exceeded their unchanged 1.27M ceiling. The measured
selected-inspection Full allowance is now explicitly 4.7M; this does not resolve
the Light floor or the separately recorded memory failures. The actual readings
and their original limits are in
`docs/measurements/brougham-optical-delivery-3084.json`. Final shipping-source
publication, required app checks, photographic acceptance and T-3085 remain open.
