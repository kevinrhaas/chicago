# T-2494 — Glessner full-bake reproducibility

A canonical CI rebuild of dev `0b233706c` produced a different Glessner package from the committed, measured package. The K01 guard correctly refused the rebuilt bytes. This investigation keeps that guard and its self-test unchanged.

## Established evidence

- [Original dev failure](https://github.com/kevinrhaas/chicago/actions/runs/38498564271) and [independent branch failure](https://github.com/kevinrhaas/chicago/actions/runs/38497642120) rebuilt the same differing package. Their Full atlas key began `5ad97a909111`; the committed atlas key was `6e0d3cbb7660`.
- The original revision reproduces `6e0d3cbb7660` locally in an isolated build, a full-town build and a build with the exact canonical launch flags. Geometry, topology, UV, material and mask arrays agree byte for byte between the local cases.
- The newer T-2218 revision reproduces its committed key `447b6297e787` locally both alone and after the preceding town buildings. Two- and four-thread builds also agree byte for byte.
- These observations do not establish the cause of the CI mismatch. They rule out local build order and the tested thread/launch variations. [The measured input fingerprints](local-inputs.json) preserve the results; they are not measurements of the CI runner.

## Producer diagnostic

The atlas-key producer now logs each hashed input separately: coordinates, loop vertex indices, polygon starts/counts, UVs, packed material mask, and the complete recipe. It hashes precisely the same bytes in the same order as before. It changes no geometry, texture, confidence, cache key or stale-package assertion.

The diagnostic producer rebuilds the Full master byte for byte: `ca2ccfb8684ad046c4217182ac1b3d93f49addf9b2812bdd2b0e7f66cec09743`. [Its actual producer fingerprints](local-producer-inputs.json) hash the packed mask exactly as the key does; the earlier controlled experiments record the raw Boolean mask array. Use the producer receipt for the like-for-like CI comparison.

The Light GLB binary payload is also unchanged (`789b50599439c0f54fc52f1a719cf27bdd78d1f907745140e2eb93cb496c2748`). Its only JSON change is the embedded `glessner_light.recipe_sha256`, which correctly records this producer-code revision. That expected stamp change updates the Light asset hash and is measured by K01; the stale-package guard remains intact. It is distinct from the unexplained canonical CI rebuild on unchanged source.

The next canonical CI bake must identify which input differs before a repair is chosen. Local package checks and exact-head CI results are recorded on the PR. Whole-house image acceptance remains T-2228.

This is an invisible infrastructure pass blocking the visible copper-corner repair in T-2220. That ticket waits on T-2494 so two workers cannot rebuild the house concurrently.
