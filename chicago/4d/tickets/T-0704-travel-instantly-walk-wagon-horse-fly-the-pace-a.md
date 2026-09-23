---
id: T-0704
title: Travel: instantly, walk, wagon, horse, fly — the pace and seated eye height apply to free movement
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 829
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:52:46.080Z
claimed_run: null
---

The owner, 2026-09-04: go "instantly, by walking (at walking speed), by wagon (fast), by horse (faster)" — and those paces must also serve free movement: "go as fast as a horse through the city".

**Decision.** `PACES` in `js/travel.js`: `instantly` · `walk` (Settings slider; sprint ×2.28; eye offset 0) · `wagon` (3.6 m/s, no sprint, +0.5 m seat) · `horse` (canter 6.5, Shift gallop 11, +0.75 m seat) · `fly`. `applyPace()` writes `WALK.speed/sprintSpeed/eyeHeight` and resettles the walker; the Travel tab is a `role=radiogroup` of five `.seg-btn[data-mode]`, the top-bar `#btn-pace` chip and key `P` cycle the pace. Default mode **instantly**, which keeps first-run behaviour and every existing arrival assertion. The paces are interface choices, not claims about 1835 — the Travel note says so, and there is no LIBERTIES entry.

**Acceptance:** smoke PART 12 — Travel offers five modes and the choice persists across a reload; horse → `WALK.speed` 6.5 and sprint 11 with eye height = slider + 0.75; wagon → 3.6 and + 0.5; walk → back to the slider and offset 0; the existing eye-height assertion still holds (eyeY stays honest). Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
