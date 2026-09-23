---
id: T-1029
title: Three derived artefacts are stale on dev and nothing re-derives them: civic/crosswalk.json, civic/voter_crosswalk.json and layer_reads_baseline.json's record counts
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-14
pr: 1332
claimed_by: run 9/14/2026, 10:36:00 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T16:23:40.568Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34862757162
---

Three derived artefacts are stale on dev and nothing re-derives them: civic/crosswalk.json, civic/voter_crosswalk.json and layer_reads_baseline.json's record counts.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**FOUND BY T-1026**, which needed to re-derive the crosswalks its card fold moved and
checked, before committing any of them, which of the rebuilds were actually its own. Three
were not. Rebuilt on a CLEAN `dev` checkout with no ticket's change in the tree, these files
still move:

- `data/research/civic/crosswalk.json` — 104 lines in, 920 out. Its declared `refusals` for
  the T-0493 pass reads 82 and the tool derives 27.
- `data/research/civic/voter_crosswalk.json` — 1,183 in, 1,600 out.
- `tools/layer_reads_baseline.json` — the record COUNTS only: `households[].head` is banked at
  1,338 and measures 1,349, `merged[]` at 42 and measures 54. The path SET is right, which is
  why the gate is green: `measure_layer_reads.py` holds membership exactly in both directions
  and does not compare counts.

**WHY IT SURVIVED.** `check.sh` does not run these three against their writers, so `dev` is
green over all of it — and a ticket that re-derives them sweeps hundreds of lines of other
tickets' drift into its own PR, which is the one thing the one-revertible-unit rule forbids.
T-1002's fold hit the same wall and left `data/research/civic/` untouched for the same reason.
So the drift is nobody's to clear as a side effect, and it compounds.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The three files re-derived and committed, in a PR that does NOTHING else, so the diff is
  legible as what it is: a catch-up, not a finding.
- Each one's delta ACCOUNTED FOR before it lands — name the passes whose landed work moved it.
  A catch-up commit that cannot say what it is catching up to is a laundering of unread change,
  and `refusals` falling 82 → 27 is a big enough move to owe an explanation.
- `check.sh` gains a step per file, so the next drift fails on the commit that causes it. This
  is the load-bearing clause: without it this ticket is filed again in a month.
- For `layer_reads_baseline.json`, decide and write down whether counts should be gated at all.
  They are a measurement, and a gate on them would fire on every ticket that adds or folds a
  card — which may be right, or may be why they were left ungated. Either answer is a result.
- `bash tools/check.sh` green. No bake: nothing here moves geometry.
