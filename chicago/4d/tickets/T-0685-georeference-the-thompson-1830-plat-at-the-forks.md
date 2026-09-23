---
id: T-0685
title: Georeference the Thompson 1830 plat at the forks and measure its bank against the Wright 1834 line for the owner's ruling
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0453
opened: 2026-09-04
closed: 2026-09-05
pr: 905
claimed_by: run 9/5/2026, 8:30:01 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T18:01:37.015Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33968826436
---

Georeference the Thompson 1830 plat at the forks and measure its bank against the Wright 1834 line for the owner's ruling.

Piece 2 of 2 of **T-0453 — The river banks are traced from Wright 1834 and the owner reads the Thompson plat differently at Wolf Point**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

This piece carries T-0453's acceptance 1, 2 and 3.

**Why it is its own run.** `data/sources/thompson_plat_1830.json` records the
sheet as a PARAMETER SOURCE — "no open high-resolution archival scan located",
the surviving artifact a Canal Commissioners' working copy, and the standing
instruction "read for its stated figures, never traced for geometry". There are
no Thompson GCPs in `data/traces/gcp/` (only Wright 1834 and Hathaway 1834), so
the plat cannot be measured against the Wright line until it has been fitted to
the same frame the datum was fitted in — which is a run's work by itself, of the
same shape as `tools/rederive_datum.py`'s fit, with its own residuals to report.

**Acceptance:**

1. The Thompson plat is georeferenced into EPSG:26916 through committed ground
   control of the same form as `data/traces/gcp/wright_1834_gcps.json`, with the
   fit's residuals reported. If the sheet will not carry a fit at a useful
   residual, that is the finding and it is recorded rather than forced.
2. Its bank at the forks is traced and committed **beside** the Wright 1834
   line, not over it — both readable, each with its source.
3. The disagreement is measured in metres at named eastings, the way T-0444
   measures the West Division's spacings, and reported rather than characterised.
4. The owner rules which is the planform of record, and the ruling is written
   into the ticket with the measurement in front of it. If they differ by less
   than the ±20 m the file already declares, that is a pass and the finding is
   that there was nothing to fix.
5. Nothing moves. Moving the bank re-derives every waterline test in the project
   and that is its own unit of work.

---

## What this measured, 2026-09-05 — the number acceptance 4 asked to have in front of it

Acceptances 1, 2, 3 and 5 are done. **4 is the owner's and is why this is blocked, not closed.**

**The fit (acceptance 1).** The plat DOES carry a fit, and a good one. Twenty-two street-corridor
crossings on the repository copy, matched to modern OpenStreetMap intersections in EPSG:26916 —
the same control method and the same projection as `wright_1834_gcps.json`, on purpose, four of
the points shared with it — fitted conformally at **RMS 4.9 m, max 7.8 m** against Wright 1834's
17.5 m and Hathaway 1834's 17.7 m. Committed as `data/traces/gcp/thompson_1830_gcps.json`. The
sheet's own boundary lines are excluded from the control because a boundary drawn as one stroke
does not say whether it is the street's centre or the block face.

**The trace (acceptance 2).** Both banks at the forks, extracted as connected ink components —
no vertex placed by hand — and committed BESIDE the Wright planform as
`data/traces/vectors/thompson_1830_forks_banks.json`. Nothing overwrites `river.geojson`.

**The disagreement (acceptance 3), in metres, at named northings and eastings.**

| where | Thompson vs Wright |
|---|---|
| main stem, north bank, E +200 … +350 | agree to **2.7 – 13.5 m** |
| main stem, north bank, point … E +125 | agree to **6.5 – 17.9 m** |
| **North Branch, east bank, N 0 … +240** | Thompson **27 – 43 m WEST** |
| **North Branch, west bank (Wolf Point), N 0 … +240** | Thompson **35 – 60 m WEST** |
| channel width at the same northings | Thompson **88 – 93 m**, Wright **66 – 83 m** |

Perpendicular distance from each committed vertex to the Thompson line: North Division shore
median 9.7 m, max 42.7 m; West Division shore median 49.2 m, max 60.4 m.

**It is not the fit.** RMS 4.9 m over a 1,900 px baseline bounds the fitted rotation to ~0.28°,
which carried 434 px north of the northernmost control point is 1.1 m of lateral error;
translation contributes ~1.0 m. The Thompson georeference can account for about **3 m** of a
27–60 m disagreement, and Wright's declared 17.5 m for at most another 17.5 m. The rest is
between the two draughtsmen. It is also structured, not noise: both banks displaced west
together, over 240 m of reach, with the channel consistently ~20 m wider.

**So acceptance 4 does NOT reach its pass condition.** They do not differ by less than the
±20 m the file declares — they differ by twice it, and only on the branch. The full argument,
including what each answer would cost, is `docs/RESEARCH/thompson_forks_georeference.md` § 6.
In short: Wright is a survey OF the river at a date four years nearer the scene; Thompson's
river is a freehand boundary on a plat of lots, on a working copy dated to at least 1836, but it
is the legal definition of the town and it georeferences four times tighter. A third answer is
open — that the two need not be reconciled, and the honest statement is that the North Branch at
Wolf Point is uncertain by ~40 m, twice what `thompson_plat_1830.json` currently declares.

**Nothing moved** (acceptance 5). **T-0451 waits on this ruling** — the North Division's
north–south streets stand on ground this bank bounds.

---

## THE OWNER'S RULING, 2026-09-05 — acceptance 4, answered

**WRIGHT 1834 REMAINS THE PLANFORM OF RECORD. NOTHING MOVES.**

Put to the owner with the measurement in front of it — the fit at RMS 4.9 m against Wright
1834's own 17.5 m, the North Branch's east bank 27–43 m west and its west bank 35–60 m
west, the channel 88–93 m against 66–83, both banks displaced together over 240 m of reach,
and the georeference able to account for about 3 m of it. He took the case
`docs/RESEARCH/thompson_forks_georeference.md` § 6 makes for the status quo: **Wright is a
survey OF the river, at a date four years nearer the scene, and the river is its subject.**
Thompson's river is a boundary on a plat of lots, drawn freehand — the stroke visibly
wavers where a surveyed line would not — surviving as a Canal Commissioners' working copy
dated to at least 1836.

**What that settles, and what it deliberately does not.** It settles which line the project
builds on: no waterline, landing, heightfield, plant layer or frontage rule is re-derived,
and `thompson_plat_1830.json`'s standing instruction — read the sheet for its figures, never
trace it for geometry — stands unchanged. It does **not** make the two sheets agree. The
27–60 m is measured and it stays measured; it is the honest uncertainty at Wolf Point, and
`thompson_plat_1830.json` now says so in place of the open question.

The Thompson GCPs and the forks trace stay committed BESIDE the Wright planform, each with
its source, which is what acceptances 1 and 2 asked for and what makes the disagreement
re-checkable rather than an anecdote.

**A correction to how this ticket described the remedy.** The session that carried the
ruling first said `thompson_plat_1830.json` "declares ±20 m" and that the figure needed
replacing. It does not: that record has no tolerance field, and the ±20 m is the project's
own georeference uncertainty, cited in the note rather than declared by it. The note now
names it as such. Nothing else about the ruling changes.
