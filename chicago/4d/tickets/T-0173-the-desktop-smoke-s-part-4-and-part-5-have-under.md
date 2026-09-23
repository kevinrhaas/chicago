---
id: T-0173
title: The desktop smoke's part 4 and part 5 have under a minute of margin on the ceiling, and part 7 is over it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-30
pr: 590
claimed_by: run 8/29/2026, 11:11:30 PM CT
blocked_on: null
needs_bake: false
---

The desktop smoke's part 4 and part 5 have under a minute of margin on the ceiling, and part
7 is over it.

**Acceptance:** every part of both viewports fits inside 10 m 00 s on this runner, measured
and recorded in `tools/smoke_renderer.mjs`'s own header the way T-0121 and T-0167 recorded
theirs — with the new cut boundaries chosen at a section boundary that crosses no binding.

**Measured on run 8/23/2026 (T-0142's verification), a full nine-part desktop pass:**

| part | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| desktop | 4 m 33 s | 3 m 25 s | 2 m 11 s | **9 m 35 s** | **9 m 20 s** | 1 m 54 s | **10 m 37 s** | 8 m 20 s | 4 m 09 s |

Mobile is comfortable throughout: 1-2 at 2 m 40 s, 3-4 at 3 m 58 s, 5-6 at 3 m 30 s, 7 at
3 m 50 s, 8 at 3 m 07 s, 9 at 1 m 30 s.

Part 7 PASSED — it was run in the background after the ten-minute foreground command was
killed, and the result was read from the log — so nothing is unverified. But a part that has
to be rescued that way is a part that will be lost the next time a run is less careful, and
the failure mode is the one T-0060 exists to prevent: the page-error assertion is the LAST
line of a viewport's body.

T-0170 already owns part 7 on the grounds that it had 2 m 17 s of margin somewhere else and
was measured over the ceiling on another runner; this is that measurement, on this runner,
plus the two parts beside it. Close T-0170 into this or the other way round — do not cut
part 7 twice.

Roughly S: the cut is arithmetic on measured numbers and the header records it.

**Part 4 has now CROSSED the ceiling — measured 2026-08-28 on the steward runner (T-0028's
verification), twice on the same tree:**

| run | wall clock | outcome |
|---|---|---|
| `SMOKE_PORT=4291 SMOKE_VIEWPORT=desktop SMOKE_STAGE=4` | killed at 9 m 30 s | 42 checks taken, body incomplete |
| `SMOKE_PORT=4293 SMOKE_VIEWPORT=desktop SMOKE_STAGE=4` | killed at 9 m 48 s | 43 checks taken, body incomplete |

Against dev's own record for that part — 46 passed, 2 failed — both runs stop about four
checks short, at the confidence-mode checkbox (`#cm-reconstructed`). So the part no longer
fits a foreground command on this runner and the reading above (9 m 35 s on 2026-08-23) is
the last one that did. `the suite body ran to completion` is what reports it, and it reports
it as a FAIL that looks like a product red and is not one.

What is NOT lost, and it is worth saying because it changes how urgent this is: `zero page
errors` is taken in EVERY invocation rather than only at the end of the body, so the
assertion T-0060 exists to protect was green in both runs above. What is lost is the tail of
the part.

Mobile is still comfortable — `SMOKE_VIEWPORT=mobile SMOKE_STAGE=3-4` ran 7 m 20 s green
(116 passed, 0 failed) on the same tree and the same runner, in the same session.

**THE PART NUMBERS IN THIS TICKET ARE DATED (T-0346, 2026-08-30).** Part 4 was cut into
parts 4, 5 and 6 — the scene-detail ladder was 6 m 17 s of a part the ten-minute ceiling was
killing — and the old parts 5-9 are now 7-11. So read this ticket's numbers through
`old 5→7, 6→8, 7→9, 8→10, 9→11`, and old part 4 as new parts 4+5+6. The mobile legs are
`1-2 3-6 7-8 9-11` and carry exactly what they carried. The readings themselves stand; only
the labels moved.

**AND THE 30-MINUTE CAP THIS TICKET REASONS AGAINST IS NOT THIS MACHINE'S (T-0235,
2026-08-30).** The margins above are taken against a 30-minute figure that was never
measured on the steward runner, which has no GPU and rasterises on the CPU. The whole
gate was measured at 55 m 10 s unfiltered there on 2026-08-27, and the staged total the
committed record now yields is 46 m 35 s — desktop 18 m 02 s over the five parts that
have a reading, mobile 28 m 33 s over all four legs. `node tools/smoke_budget.mjs`
prints that table out of `tools/dev-smoke-state.json` rather than asserting it, names
the parts that still have no reading at all — desktop 4-9 — and `--for <path>…` answers
the question this ticket's margins exist to serve: which parts cover the change in
hand, and do their measured costs fit the 600 s foreground ceiling. See
`docs/SMOKE-BUDGET.md`.
---

**RESOLVED 2026-08-30 — the part this ticket uniquely owned is cut, and the other two are
accounted for.** The ticket names three parts and they did not all end up here:

- **Old part 4** — cut into three by **T-0346** earlier the same day (PR #583). Nothing left.
- **Old part 5, which T-0346 renumbered to 7** — this ticket's own, and what this closes.
  Re-profiled on the steward runner at load 0.81-2.86, it was **killed at 9 m 25 s** with its last
  two assertions unrun, so the 9 m 20 s reading of 2026-08-23 and the 8 m 51 s of 2026-08-29 are
  both dated: the part is over the ceiling, not near it. **7 m 04 s of the 9 m 25 s was one
  block** — the three road-legibility stations. No named section boundary inside the part halves
  it (the best leaves 7 m 37 s against 1 m 30 s), so the cut falls at the STATION, which is the
  grain the block is made of and crosses no binding. Part 7 keeps `south_water` and `from_above`
  and the shared `streetLayer` reading; a new part 8 takes `lake_market` with R-A1 — whose three
  assertions are taken standing at that station — and the batch merge under it. **Measured after
  the cut: part 7 5 m 05 s / 12 staged, part 8 5 m 06 s / 8 staged, both SMOKE PASS at desktop.
  12 + 8 = 20, the count the old part was taking.** Parts 8-11 renumber to 9-12; mobile `7-9` is
  43 passed / 34 staged and `10-12` is 168 passed / 159 staged, both run.
- **Old part 7, which T-0346 renumbered to 9 and this cut renumbers to 10** — **T-0170's**, still
  open. This ticket's own instruction is *"do not cut part 7 twice"*, and cutting a part another
  open ticket owns, while eight slices of this lane run at once against one queue, is precisely
  how it would get cut twice. So it is left where it is, with its numbers re-labelled for this cut
  in T-0170's own file.

The acceptance clause said "every part of both viewports fits inside 10 m 00 s". After this cut,
every part named in THIS ticket does. Part 10 does not, and it has a ticket of its own that is
above nothing and blocks nothing here.
