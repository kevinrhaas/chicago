---
id: T-0053
title: A patched lit material silently inherits another layer's shader program
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

A patched lit material silently inherits another layer's shader program.

**Found by walking into it, T-0050, 2026-08-18.** The first build of the enclosure layer drew a
perfectly correct fence in SOLID BLACK, at both viewports, in full sun, with no page error, no
console error and no shader warning. Unpatching the material lit it perfectly, which is what made
the cause so hard to see.

**The mechanism.** three caches a compiled program under a key that ends in
`material.customProgramCacheKey()`, whose default (`three.core.js`, `Material`) is
`this.onBeforeCompile.toString()` — the hook's SOURCE TEXT, not the closure. Every material
`renderers/web/js/confidence.js` `patch()` touches installs the same arrow function, so every
patched material in the app reports the SAME key text. Two patched materials that agree on every
other program parameter therefore share one compiled program, and whichever compiles first wins.
A plain patched `MeshStandardMaterial` — no map, opaque — is parameter-for-parameter the twin of a
mapless building material out of `buildings.js`, which chains a second hook reading the per-vertex
`_roughness` and facade-tone attributes. Handed that program, geometry that never bound those
attributes renders black.

**Who is exposed today.** Nobody, and that is luck rather than design: `streets.js` has a map,
`trees.js` has vertex colours, `flora.js` is Lambert, `terrain.js` has maps — every existing
patched material differs from the buildings' in some other program parameter. The next layer that
patches a plain lit material walks into it. T-0050 fixed only its own call site, with a
`customProgramCacheKey` of its own.

**Acceptance:** a patched plain `MeshStandardMaterial` cannot be handed another patched material's
program, demonstrated by an assertion that FAILS on today's `confidence.js` and passes after. The
obvious fix — give every patched material a unique key — is the one to argue against in writing
before taking, because it would give each of the 334 building materials its own program; the
question this ticket has to answer is what belongs in the key, not whether to widen it blindly.

**Links:** `renderers/web/js/confidence.js` `patch()` · `renderers/web/js/enclosures.js` (the
worked example and its comment) · `docs/STATUS.md` 2026-08-18.
