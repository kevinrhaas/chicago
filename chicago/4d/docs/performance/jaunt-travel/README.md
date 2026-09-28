# T-1280 travel modes and estimates

`node tools/test_travel_estimate.mjs` tests the pure estimator against the real
router on a reduced water-and-bridge fixture with the named scene endpoints.
The fixture is a routing test, not a new river reconstruction. It checks route
length, a forced bridge detour, live pace settings, altitude-dependent flight,
instant framing, approximate fallback and missing positions.

`node tools/test_jaunts_reducer.mjs` covers mode replanning, retired callbacks,
preserved choices/inventory, manual pause, resume and one-leg instant arrival.
The estimate and movement controller share their pace and flight definitions.

`PW_EXECUTABLE=<chromium> node tools/test_jaunt_travel.mjs` exercises the published
mirror at 390×780 and 1280×800, including the dev URL base. It switches horse to
fly while moving, reads the changed banner and estimate, measures ascent and
grounded arrival, pauses with actual movement intent, resumes and jumps to the
next stop. It compares localStorage before and after the outing.

The primary-path measurement combines declared reading/action seconds with the
travel controller's simulated elapsed seconds. This isolates travel from the
software renderer's frame rate; it does not measure a human reader's pace.
Display estimates round to half-minutes and say “about”. Flight is a viewing
convenience; neither its speed nor the interface's ground paces are historical
transport claims.

Estimator and nine reducer cases pass. Published travel acceptance passes at
both viewports: mode selection, rising flight and grounded arrival, lower live
ETA, movement pause/resume, direct arrival, unchanged localStorage, 44 px controls,
320×568 and short landscape layouts, popup/drawer clearance and zero page errors.
The control row's measured height is reserved for overlays, including wrapped
labels. Mobile flight and desktop arrival stills were visually inspected.

| Viewport | Recommended-mode estimate | Measured path + declared reading | Difference |
|---|---:|---:|---:|
| 390×780 | 236.5 s | 243.3 s | +2.9% |
| 1280×800 | 227.8 s | 230.6 s | +1.2% |

The pilot recommends Horse in content version 2, fitting the 4–6 minute target.
Its mobile card estimates Walk 10.5, Wagon 5.5, Horse 4, Fly 3 and Instantly 2
minutes. Desktop reads 9.5, 5, 4, 3 and 2; each prices the travel controller's
viewport-specific framing positions. Horse → Fly lowered the remaining estimate
from 202.0 to 142.9 seconds on mobile and 191.0 to 140.5 on desktop.

Full preflight passes all 681 steps, plus changelog-entry and ticket-ID checks.
Scoped shared travel/chrome smoke is still pending.
