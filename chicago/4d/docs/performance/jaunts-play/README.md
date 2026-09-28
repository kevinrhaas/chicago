# T-1279 playable jaunt acceptance

`node tools/test_jaunts_reducer.mjs` checks immutable history, once-only effects,
stale session/leg callbacks, rapid Next, Previous mid-ride, pause/resume, replacement,
End and late content loads. Timer and EventTarget listener registrations are counted;
the controller owns none. Travel owns two per-ride callbacks, released on stop.

`PW_EXECUTABLE=<chromium> node tools/test_jaunts_play.mjs` exercises the published
mirror at 390×780 and 1280×800. It plays the real five-stop pilot and a two-stop
fixture through the same runtime. Fixture injection is confined to the harness.
The travel simulator advances the existing ride clock; it does not replace travel.
The harness writes per-viewport JSON state dumps and screenshots beside this file.
Each viewport has its own receipt, so retrying one cannot overwrite the other.

Assertions cover navigation, effect history, rapid Next, End under 200 ms,
position-preserving Resume, identical initial framing from near/far anchors,
completion, Explore clearing the session, no boot jaunt requests, zero page errors,
no pointer lock and 44 px controls clear of popup and drawer. Mobile also checks
320×568 and short landscape. No daybook storage, mode switching or ETA ships here.

Recovery note: the earlier unpushed draft and browser receipts were lost in a
workspace reset. Only newly generated receipts in this directory describe this
recovered implementation.

Recovered checkpoint `2d08f71`: preflight PASS, 680 steps (284 intentional
fault-injection self-tests), eight reducer cases PASS. Published mobile play PASS:
End 123.6 ms, zero page errors, five pilot stops and the second fixture. Published
mobile shared parts 3–4 PASS: 116 assertions and zero page errors.

Desktop 1280×800 play also PASS: pilot and fixture, End 197.3 ms, zero page errors.
The desktop stills were inspected for popup/drawer clearance and readable outcome.
Mobile shared parts 1–2 PASS as well: 158 assertions, zero failures.

Boot payload: 9.815 MB / 12 MB, 1,020 requests; runtime/panel/catalog are absent
until Jaunts opens. Remaining shared smoke is still pending.
An extra parallel smoke attempt was interrupted when three browser processes
filled the 8 GB workspace memory budget; it is not a pass or a failure reading.
The desktop play harness uses real trusted mouse input after explicit enabled,
visible and hit-target checks, avoiding multi-frame actionability waits on the
software renderer. The assertions and navigation semantics are unchanged.

All thirteen mobile shared smoke parts now pass, as do desktop parts 1–11 and 13.
The final focused mobile repeat measured End at 200.3 ms against the unchanged
200 ms limit. Returning directly to Jaunts had first focused the welcome heading,
before focusing the catalog. That intermediate focus is now skipped only on the
direct Jaunts return; ordinary welcome entry still focuses its heading. The same
End assertion then passed at 1.1 ms on mobile and 0.8 ms on desktop, with both
near/far anchors explicitly entered and identical first-stop framing.

`JAUNT_FRAMING_ONLY=1` repeats only the changed End/framing path and initial
layout. It writes a separate `*-framing.json` and preserves the full play receipts.
Both focused repeats pass with zero page errors. Desktop part 11 first timed out
on a completed click under overlapping browser load; the unchanged isolated retry
passed all 23 assertions. Desktop part 12 first timed out on scene reload; its
isolated retry was interrupted when the session ended and has no final verdict.
Part 12 remains pending on the integrated tree. Parts through mobile 13 and desktop
7 were run before the focus optimization; subsequent readings name their tree hash.
The branch includes dev through 2a199d9, including the separately completed PR #137.

Integrated preflight PASS: 680 steps, changelog-entry and ticket-ID checks.

The integrated desktop part-12 retry passed 93 assertions and reported zero page
errors, then timed out on the second scene reload. Its first reload had passed.
The harness sets a 90-second default action/readiness budget, but these two reload
calls overrode it with 30 seconds. They now use the existing 90-second budget,
matching initial readiness. No readiness predicate, pixel, input, route or saved-
state assertion changes. The failed readings remain recorded; the revised-harness
repeat is pending. The per-command ten-minute budget remains unchanged.
