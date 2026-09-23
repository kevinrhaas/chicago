---
id: T-1081
title: The smoke's walking-speed assertion still expects a bare '3.2 mph' and the HUD has read 'walk · 3.2 mph' since T-0823, so mobile part 3 has been red on dev for a week
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-13
pr: 1247
claimed_by: run 9/13/2026, 6:43:44 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T12:10:34.386Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34754956831
---

The smoke's walking-speed assertion still expects a bare '3.2 mph' and the HUD has read 'walk · 3.2 mph' since T-0823, so mobile part 3 has been red on dev for a week.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-1079's smoke leg, 2026-09-12. `tools/smoke_renderer.mjs` line 8315 asserts
`/^\d+(?:\.\d)? mph$/` on `#v-speed`. Since T-0823 landed the per-pace sliders on
2026-09-05 (167cdc176), `hud.js` paints that element through `gaitReadout('walk')` and it
reads **`walk · 3.2 mph`** — which is the shipped, intended UI. So the UNIT is right and
the ASSERTION is stale: mobile part 3 has been failing on dev for a week for a reason that
is not a defect in the product.

**Acceptance:** the assertion accepts the gait prefix and still refuses `m/s`, the gait
word itself is asserted rather than dropped (the readout naming the gait is the whole of
T-0823), and the same staleness is checked for on the wagon and horse readouts before this
closes — three sliders landed together and only one of them is asserted on.

REPRODUCED BY T-1070, 2026-09-12, on both viewports, running the smoke legs that cover a
street diff:

    mobile 390x780:   FAIL  walking speed is presented in miles per hour — speed label walk · 3.2 mph
    desktop 1280x800: FAIL  walking speed is presented in miles per hour — speed label walk · 3.2 mph

So it is not mobile-only. Every other check in every leg that run passed, which is worth
saying because it makes this one assertion and not a broken part.

And one consequence beyond the count of red parts: this assertion sits on the group that
covers `data/streets/1835.json`, so EVERY run that touches a street line draws a red leg
it must read, attribute and argue past before it can merge. T-1070 spent a leg doing that.
A gate that is red for a reason unrelated to the diff in front of it stops being a gate.

SHIPPED, 2026-09-13. `tools/smoke_renderer.mjs` § the navigation reading now tests
`/^[a-z][a-z ]*[a-z] · \d+(?:\.\d)? mph$/` against `#v-speed` and still refuses `m/s`, so
the gait word T-0823 put there is COVERED rather than contradicted: a readout that loses
its unit fires, and so does one that loses its name. The acceptance's third clause is met
by a second assertion taken on all three pace readouts at once — `v-speed`,
`v-wagon-speed`, `v-horse-speed` — because `hud.js` paints them through one
`gaitReadout`, so a fault in it reaches the wagon and the horse and only one of them was
ever asserted on.

MEASURED HERE, each leg in the foreground against the published mirror:

    mobile  stage 7   PASS  24 passed, 0 failed, 3 m 23 s
    desktop stage 7   PASS  24 passed, 0 failed, 5 m 13 s
    mobile  stage 8   FAIL  16 passed, 1 failed, 3 m 12 s — the road-legibility aid, T-0690

Part 7 is green at BOTH viewports for the first time since 2026-09-05. The dev record had
this failure filed under mobile part 8 as well; that is where the leg that measured it was
cut (`stage 2,7-8`), not where the assertion lives — part 8's own red is T-0690's and is
untouched by this. All three readings filed with `dev-smoke-state.mjs record`.

T-1093 asked the same question five days later and is withdrawn to this ticket.
