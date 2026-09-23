---
id: T-0153
title: Twelve of the sixteen Playwright instruments cannot be pointed at a browser
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-08-23
pr: 318
claimed_by: run 8/22/2026, 11:51:14 PM CT
blocked_on: null
needs_bake: false
---

`tools/smoke_renderer.mjs` launches with `executablePath: process.env.PW_EXECUTABLE
|| undefined`, which is why the release gate runs on any machine that has a Chromium
somewhere. Twelve of the other fifteen Playwright tools call a bare
`chromium.launch()`, so they can only ever use the browser Playwright installed for
itself — and when that is absent they die before their first frame:

```
browserType.launch: Executable doesn't exist at
  /opt/pw-browsers/chromium_headless_shell-1234/chrome-headless-shell-linux64/...
```

Found while trying to run `measure_tie_class.mjs`, which is the instrument T-0013's
acceptance is written against — so T-0013 cannot be measured, let alone finished,
until this is fixed. It is not one ticket's problem: the same line is missing from

    light_probe · measure_facade_variety · measure_furniture_reach · measure_head_reach
    measure_head_support · measure_river_edge · measure_shadow_reach
    measure_shipped_batches · measure_sward_draw · measure_tie_class
    measure_timber_detail · shoot

Four already have it (`critic_shots`, `measure_drawn_placement`, `measure_east_band`,
`smoke_renderer`), which is what makes this an oversight rather than a decision — the
pattern was established and then not carried to the tools written after it.

This matters more than a convenience flag. Nearly every one of these is a MEASURING
instrument, and this repo's whole discipline is that a change is measured before it is
claimed. An instrument that cannot start on the machine doing the work quietly turns
"measured" into "asserted".

**Acceptance:** every Playwright tool under `tools/` honours `PW_EXECUTABLE`, by the
same one-line form `smoke_renderer.mjs` already uses; `measure_tie_class.mjs` runs to
completion on this runner with `PW_EXECUTABLE` set and prints its partition; and a
check refuses a future tool that calls `chromium.launch()` without it, so the pattern
cannot lapse a third time.
