import pathlib, sys

EDITS = {
  'tools/web_derivatives.sh': [
    ('''  local light="${1%.glb}.light.glb" source optimized output
  source="$(mktemp -t gltflight-source.XXXXXX.glb)"
  optimized="$(mktemp -t gltflight-opt.XXXXXX.glb)"
  output="$(mktemp -t gltflight-web.XXXXXX.glb)"
  if ! python3 tools/structure_versions.py build-light "$1" "$source" \\
    || ! "${GT_NPX[@]}" gltf-transform optimize "$source" "$optimized" --compress false --simplify false --palette false 2>&1 | tail -2 \\
    || ! "${GT_NPX[@]}" gltf-transform meshopt "$optimized" "$output" --quantize-position 16 2>&1 | tail -2; then
    rm -f "$source" "$optimized" "$output"''',
     '''  local light="${1%.glb}.light.glb" source optimized ktxed output
  source="$(mktemp -t gltflight-source.XXXXXX.glb)"
  optimized="$(mktemp -t gltflight-opt.XXXXXX.glb)"
  ktxed="$(mktemp -t gltflight-ktx2.XXXXXX.glb)"
  output="$(mktemp -t gltflight-web.XXXXXX.glb)"
  # T-2596: the light tier takes the same KTX2 recipe as the full derivative,
  # its textures capped at 1024 (a quarter of the 2048 tier's GPU residency).
  # --texture-compress false for the main loop's own reason: optimize's default
  # re-encodes every image, and the encode starts from the master's own pixels.
  # An image-free source (the producer fixture's) skips the encode; the encode
  # itself is FATAL-on-failure, so a light derivative that still carries a PNG
  # or JPEG never reaches the tree.
  if ! python3 tools/structure_versions.py build-light "$1" "$source" \\
    || ! "${GT_NPX[@]}" gltf-transform optimize "$source" "$optimized" --compress false --simplify false --palette false --texture-compress false 2>&1 | tail -2 \\
    || ! { [ "$(glb_images "$optimized" | cut -d' ' -f1)" = "0" ] || { encode_textures "$optimized" "$ktxed" 1024 && mv -f "$ktxed" "$optimized"; }; } \\
    || ! "${GT_NPX[@]}" gltf-transform meshopt "$optimized" "$output" --quantize-position 16 2>&1 | tail -2; then
    rm -f "$source" "$optimized" "$ktxed" "$output"'''),
    ('''  if [ "$stamp" != "glTF-Transform v$GT_CORE_VERSION" ]; then
    rm -f "$source" "$optimized" "$output"
    echo "   FATAL: v4 light derivative has an unpinned transform stamp." >&2
    return 1
  fi
  mv "$output" "$OUT/$light"
  rm -f "$source" "$optimized"''',
     '''  if [ "$stamp" != "glTF-Transform v$GT_CORE_VERSION" ]; then
    rm -f "$source" "$optimized" "$ktxed" "$output"
    echo "   FATAL: v4 light derivative has an unpinned transform stamp." >&2
    return 1
  fi
  mv "$output" "$OUT/$light"
  rm -f "$source" "$optimized" "$ktxed"'''),
    ('''  # The Glessner v4 set is not encoded here yet: its full and light files ship
  # inside a three-file recovery package with its own hashes and a baseline page
  # that reads them, and T-2596 owns that. measure_web_derivatives.py names it.''',
     '''  # The Glessner v4 master joined this path in T-2596: the full derivative
  # encodes at the same 2048 cap as every textured master, the light one at
  # 1024 (produce_light_version), and the three-file recovery package, the
  # manifest record and the baseline page's audit moved in the same run.'''),
    ('''    # and the encode runs between `optimize` and `meshopt`. Untextured masters and
    # the Glessner v4 set (T-2596) take exactly the path they always took.''',
     '''    # and the encode runs between `optimize` and `meshopt`. Untextured masters take
    # exactly the path they always took. The Glessner v4 master joined this path in
    # T-2596; the older Glessner versions (pre-v4, v2, v3) stay off it — their
    # derivatives are not part of that ticket's three-file package.'''),
    ('''    if [ "$rel" != "$GLESSNER_V4" ] && [ "$glessner" = "0" ] && [ "$(glb_images "$f" | cut -d' ' -f1)" != "0" ]; then''',
     '''    if { [ "$glessner" = "0" ] || [ "$rel" = "$GLESSNER_V4" ]; } && [ "$(glb_images "$f" | cut -d' ' -f1)" != "0" ]; then'''),
  ],
  'tools/measure_web_derivatives.py': [
    ('''    JPEGs between them until T-2595. The Glessner v4 set is exempt by name
    (`RASTER_EXEMPT`) until T-2596 re-encodes it.''',
     '''    JPEGs between them until T-2595. The Glessner v4 set was the last exemption, by name,
    until T-2596 re-encoded it; there is no exception now.'''),
    ('''# to a byte. The Glessner v4 set is the one exception, named here rather than by a size
# rule, and T-2596 is the ticket that re-encodes it and deletes this line.
RASTER_MIMES = ("image/png", "image/jpeg")
RASTER_EXEMPT = {"glessner_house__as_built_1887.glb": "T-2596",
                 "glessner_house__as_built_1887.light.glb": "T-2596"}''',
     '''# to a byte. The Glessner v4 set was the one exception, named here rather than by a size
# rule, until T-2596 re-encoded it and deleted the exemption.
RASTER_MIMES = ("image/png", "image/jpeg")'''),
    ('''        if n and row["name"] not in RASTER_EXEMPT:''',
     '''        if n:'''),
  ],
}
for name, pairs in EDITS.items():
    p = pathlib.Path(name)
    text = p.read_text(encoding='utf-8')
    applied = skipped = 0
    for old, new in pairs:
        n = text.count(old)
        if n == 1:
            text = text.replace(old, new)
            applied += 1
        elif n == 0 and text.count(new) >= 1:
            skipped += 1  # refire path: this edit already landed
        else:
            sys.exit(f'{name}: anchor matched {n} times (need exactly 1): {old[:80]!r}...')
    p.write_text(text, encoding='utf-8')
    print(f'{name}: {applied} edits applied, {skipped} already in place')
