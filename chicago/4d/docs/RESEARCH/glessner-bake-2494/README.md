# T-2494 — Glessner full-bake reproducibility

A canonical CI rebuild of dev `0b233706c` produced a different Glessner package from the committed, measured package. The K01 guard correctly refused the rebuilt bytes. This investigation keeps that guard and its self-test unchanged.

## Established evidence

- [Original dev failure](https://github.com/kevinrhaas/chicago/actions/runs/38498564271) and [independent branch failure](https://github.com/kevinrhaas/chicago/actions/runs/38497642120) rebuilt the same differing package. Their Full atlas key began `5ad97a909111`; the committed atlas key was `6e0d3cbb7660`.
- The original revision reproduces `6e0d3cbb7660` locally in an isolated build, a full-town build and a build with the exact canonical launch flags. Geometry, topology, UV, material and mask arrays agree byte for byte between the local cases.
- The newer T-2218 revision reproduces its committed key `447b6297e787` locally both alone and after the preceding town buildings. Two- and four-thread builds also agree byte for byte.
- Those initial observations ruled out local build order and the tested thread/launch variations. [The measured input fingerprints](local-inputs.json) preserve them; the direct CI comparison below establishes the cause.

## Cause and repair

[The math-library comparison](math-library-comparison.json) isolates the mismatch.
The same pinned Blender binary and source, with Ubuntu's glibc 2.39 `libm.so.6`
preloaded instead of the host's glibc 2.41 math library, reproduce the latest dev
failure's atlas key prefix `19bd4a00e6ee4967`. All coordinates, loop indices, polygon
starts/counts, materials and masks remain byte-identical; 3,601,263 of 6,045,728 UV
scalar coordinates change. Disabling the tested CPU math optimizations and restricting
the process to one CPU both reproduce the original local key. The responsible producer
is `_welded_unwrap`: its Blender smart projection / island packing depends on the
host math library. The T-2431 AO cache rejected the resulting new UV key and ran Cycles
afresh. Pinning Blender alone did not pin this host dependency.

[The instrumented full CI bake](ci-inputs.json), revision `439d42f9f`, confirms the
complete key `19bd4a00e6ee4967347cdf85833ec2bd68458805f88539bcfc2f40ae4f942408`.
Its recipe and every component except UV match the local producer fingerprint.
The two original K01 checks fail as expected, with the other 875 steps passing.

The repair retains each validated UV layout in its existing atlas NPZ. Its independent
`unwrap_key` hashes the exact pre-unwrap mesh and granite mask, pinned Blender and
unwrap settings/recipe. No geometry rounding or key exemption is introduced. A cache
hit must also validate the coordinates' shape, dtype, finite values and checksum.
The complete original atlas key is then computed from the actual mesh and restored
UVs before AO can be reused. Changed geometry or unwrap settings regenerate UVs;
changed AO settings rebake AO. Both Full and Light use this producer.

Regression checks exercise changed geometry/topology/mask, Blender and unwrap settings,
legacy caches, wrong checksums, modified coordinates, wrong shape/dtype and NaNs. They
also require both committed atlas sizes to retain valid UV layouts. The K01 stale
package guard and its self-test are unchanged.

## Repaired package

[The complete-file comparison](repaired-package.json) reproduces all three files
byte for byte under both math libraries. Full remains `ca2ccfb8684a` and web Full
`974b878f7780`, identical to the approved T-2218 package. Light is `4a7fd95a03a3`:
its binary geometry/texture payload remains `789b50599439`, and its only JSON change
from T-2218 is the producer recipe stamp (`124412d15940`). K01 measures that intentional
stamp change; it does not accept the unexplained CI output. Both committed UV caches
and the stale/corrupt-cache regression checks pass. Cache writes are atomic, with a
regression check that a failed write preserves the previous cache.

Final full preflight, canonical CI bake and published desktop/mobile results are
recorded on the PR against the tested commit. These package comparisons are not a
new claim of photographic acceptance or physical-GPU performance.

## Diagnostic evidence before the repair

The atlas-key producer now logs each hashed input separately: coordinates, loop vertex indices, polygon starts/counts, UVs, packed material mask, and the complete recipe. It hashes precisely the same bytes in the same order as before. It changes no geometry, texture, confidence, cache key or stale-package assertion.

The diagnostic producer rebuilds the Full master byte for byte: `ca2ccfb8684ad046c4217182ac1b3d93f49addf9b2812bdd2b0e7f66cec09743`. [Its actual producer fingerprints](local-producer-inputs.json) hash the packed mask exactly as the key does; the earlier controlled experiments record the raw Boolean mask array. Use the producer receipt for the like-for-like CI comparison.

The Light GLB binary payload is also unchanged (`789b50599439c0f54fc52f1a719cf27bdd78d1f907745140e2eb93cb496c2748`). Its only JSON change is the embedded `glessner_light.recipe_sha256`, which correctly records this producer-code revision. That expected stamp change updates the Light asset hash and is measured by K01; the stale-package guard remains intact. It is distinct from the unexplained canonical CI rebuild on unchanged source.

The instrumented full CI bake and the repaired package's validation are recorded on
the PR. Whole-house image acceptance remains T-2228.

This is an invisible infrastructure pass blocking the visible copper-corner repair in T-2220. That ticket waits on T-2494 so two workers cannot rebuild the house concurrently.
