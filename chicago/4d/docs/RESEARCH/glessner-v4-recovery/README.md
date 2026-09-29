# Exact Glessner v4 packaged assets

The GitHub connector rejects request bodies over 16 MiB, smaller than either
v4 GLB. These 6 MiB archive parts retain the exact baked bytes, without reducing
geometry, textures or image quality. The renderer still consumes ordinary GLBs.

`tools/publish.sh` materializes only these two ignored outputs before the normal
asset validation and mirror copy:

- `assets/gltf/versions/glessner_house/v4/glessner_house__as_built_1887.glb`
- `assets/web/versions/glessner_house/v4/glessner_house__as_built_1887.glb`

Every part, archive and member hash is verified. Existing output must match;
a new bake is never silently replaced by the archive. Automatic materialization
never restores manifests, sidecars, default meshes or older versions. The initial
checkpoint archive contains those additional recovery snapshots; they are used
only by the explicit manual `--restore` command, which overwrites archived files.

From `chicago/4d`:

```sh
python3 tools/recover_glessner_v4.py --materialize  # fresh checkout, two GLBs only
python3 tools/recover_glessner_v4.py --check        # exact package/output gate
```

The normal canonical web-derivative step repacks the two outputs immediately after
recording the v4 derivative. Commit the changed archive parts and manifest with the
bake's data/manifests. `--out` measurements and derivatives for any other asset do
not repack. On a fresh checkout the producer first materializes the pair only when
both are absent; it never replaces a rebuilt master or a stale existing derivative.

For deliberate manual repacking/recovery, the same command remains available:

```sh
python3 tools/recover_glessner_v4.py --pack
python3 tools/recover_glessner_v4.py --check
bash tools/check.sh
```

Packing uses deterministic ZIP metadata and 6 MiB chunks. It includes exactly the
two GLBs; future repacks discard the initial archive's auxiliary snapshots. The
archive is storage, not evidence of a passing bake, visual review or release gate.
See `../glessner_v4_work.md` for validation and visual-review status.
