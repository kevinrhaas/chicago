# Exact Glessner v4 recovery assets

The GitHub connector rejects request bodies over 16 MiB, smaller than either
the v4 master or web GLB. These archive parts preserve the exact baked files,
their comparison versions, manifests and v4 sidecar in a recoverable branch
checkpoint. No mesh, texture or image quality was reduced for the transfer.

From `chicago/4d`:

```sh
python3 tools/recover_glessner_v4.py            # verify all part/member hashes
python3 tools/recover_glessner_v4.py --restore  # restore generated files
```

Then use authenticated git to add the ordinary `assets/gltf/`, `assets/web/`
and sidecar files, run the normal preflight and published smoke, and push the
branch. The archive is a recovery measure, not a replacement for the normal
asset layout or evidence that the release gates passed. See
`../glessner_v4_work.md` for validation and visual-review status.
