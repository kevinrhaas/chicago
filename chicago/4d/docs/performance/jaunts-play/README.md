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
recovered implementation. Full gate and shared smoke validation remain pending.
