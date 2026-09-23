---
id: T-0705
title: Horse gait moves the rider's eye; off under reduced motion and by a setting
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: XS
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 829
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:52:46.224Z
claimed_run: null
---

The owner, on horseback: "maybe a gallop up-and-down view".

**Decision.** `walker.state.bob` — canter 2.0 Hz ± 6 cm, gallop 1.6 Hz ± 9 cm — is added in `apply()` only, so `eyeY` stays honest for the eye-height smoke. It is zero under `prefers-reduced-motion`, when `settings.headBob` is off (`#s-head-bob` in Travel), and on any pace without a gait.

**Acceptance:** smoke PART 12 — on horse, the bob amplitude sampled over `travelSimulate` is between 0.03 and 0.10 m; it is exactly zero with `#s-head-bob` off and under reduced-motion emulation. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
