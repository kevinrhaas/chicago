---
id: T-0092
title: The Sauganash's fabric corrected to the three views: log wing, frontispiece, chimneys and shutters
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: K2
parent: T-0043
opened: 2026-08-18
closed: 2026-08-20
pr: 286
claimed_by: run 8/20/2026, 7:37:27 PM CT
blocked_on: null
needs_bake: true
---

The Sauganash's fabric corrected to the three views: log wing, frontispiece, chimneys and shutters.

Piece 3 of 3 of **T-0043 — Image-accuracy pass: the Sauganash**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

The BUILDING itself, against images 8, 9 and 10 of
`data/sources/assets/owner_brief_2026_08_18/README.md`: the log wing at the left with its own
door direct to grade and a shed-roofed porch hood over it; the small flat-hooded **entrance
frontispiece** on the main block's front door; **brick chimneys** and the Petford view's dark
green/moss shingle roof; **louvred shutters** on the sash (image 10 only — the weakest of the
three claims, and the card must say so). `data/structures/sauganash_hotel.json` already carries
`log_wing: true` as inferred; none of the rest is on the record and none of it is in the mesh.

**NEEDS THE BAKE**, measured rather than assumed: every item here is a field of the
`frame_1831` phase that `generators/mesh_inputs.py` hashes into
`assets/manifest.json`'s `inputs_sha256` for `sauganash_hotel__frame_1831.glb`, so
`tools/check.sh` reports the mesh stale and refuses the commit until Blender rebuilds it. The
improve runner has no Blender; this closes on the nightly `chicago-4d-bake.yml` or on a runner
that has one.

**Acceptance:** a before/after pair from a stand matching the engraving's quarter, the fabric
corrected to the views, every claim carded at its honest tier.

**Links:** owner_brief_2026_08_18 README (images 8, 9, 10) · T-0043 (parent) · T-0083 (the same
work at the Green Tree).
