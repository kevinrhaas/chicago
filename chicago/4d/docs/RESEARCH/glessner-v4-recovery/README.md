# Exact Glessner v4 packaged assets

The GitHub connector rejects request bodies over 16 MiB, smaller than the full
v4 GLBs. These 6 MiB archive parts retain the exact baked bytes, without reducing
geometry, textures or image quality. The renderer still consumes ordinary GLBs.

`tools/publish.sh` materializes only these three ignored outputs before the normal
asset validation and mirror copy:

- `assets/gltf/versions/glessner_house/v4/glessner_house__as_built_1887.glb`
- `assets/web/versions/glessner_house/v4/glessner_house__as_built_1887.glb`
- `assets/web/versions/glessner_house/v4/glessner_house__as_built_1887.light.glb`

Every part, archive and member hash is verified. Existing output must match;
a new bake is never silently replaced by the archive. Automatic materialization
never restores manifests, sidecars, default meshes or older versions. The initial
checkpoint archive contains those additional recovery snapshots; they are used
only by the explicit manual `--restore` command, which overwrites archived files.

From `chicago/4d`:

```sh
python3 tools/recover_glessner_v4.py --materialize  # fresh checkout, three GLBs only
python3 tools/recover_glessner_v4.py --check        # exact package/output gate
```

The normal canonical web-derivative step repacks the three outputs immediately after
recording the v4 derivative. Commit the changed archive parts and manifest with the
bake's data/manifests. `--out` measurements and derivatives for any other asset do
not repack. On a fresh checkout the producer first materializes the set only when
all three are absent; it never replaces a rebuilt master or a stale existing derivative.

For deliberate manual repacking/recovery, the same command remains available:

```sh
python3 tools/recover_glessner_v4.py --pack
python3 tools/recover_glessner_v4.py --check
bash tools/check.sh
```

Packing uses deterministic ZIP metadata and 6 MiB chunks. It includes exactly the
three GLBs; future repacks discard the initial archive's auxiliary snapshots. The
archive is storage, not evidence of a passing bake, visual review or release gate.
See `../glessner_v4_work.md` for validation and visual-review status.

The full master and full web derivative retain their detailed geometry. The light
web derivative is generated from the same v4 record for the existing balanced and
light settings. Its manifest separately pins the full master, rendering recipe,
and reduced output hashes. A failed reduction stops before recording or packing;
it never falls back to the default house, an earlier version, or a full-detail copy.
