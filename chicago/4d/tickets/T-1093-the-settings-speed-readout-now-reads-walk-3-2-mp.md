---
id: T-1093
title: The Settings speed readout now reads 'walk · 3.2 mph' and the mobile part-7 assertion wants '3.2 mph', so dev is red on a prefix nobody meant to assert against
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-13
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T12:03:46.195Z
claimed_run: null
---

The Settings speed readout now reads 'walk · 3.2 mph' and the mobile part-7 assertion wants '3.2 mph', so dev is red on a prefix nobody meant to assert against.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0878's gate run, which is why it is filed rather than fixed: it is nothing to do
with that unit's diff.

`tools/smoke_renderer.mjs:8315` asserts `/^\d+(?:\.\d)? mph$/` against the Settings speed
readout. The readout now reads **`walk · 3.2 mph`** — the mph is there, the units are right,
and the assertion fails on a prefix it was never written to police. Measured at mobile
390x780 on 2026-09-12, part 7.

A second red came up in the same leg and is a different animal, so it is noted here and not
claimed: part 8's `raising the road-legibility aid reaches the render` read `worst 3` against
a `worst >= 4` threshold on a loaded runner (`mean 0.24` passed its own `>= 0.15`). That is
the image-delta threshold going marginal under starvation, the T-0215 shape, and it wants a
reading on a quiet box before anyone touches the constant.

**Acceptance:** the assertion says what it means — the readout presents miles per hour —
whatever else the label carries, and it is re-read green at mobile part 7. If the `walk ·`
prefix is itself the fault, fix the readout instead and say which.
