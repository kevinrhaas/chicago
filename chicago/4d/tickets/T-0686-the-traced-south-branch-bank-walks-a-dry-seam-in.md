---
id: T-0686
title: The traced South Branch bank walks a dry seam in Wright's wash for 30 m, and repairing it moves the waterline
state: done
epic: GROUND
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 882
claimed_by: run 9/5/2026, 6:38:19 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T12:48:53.818Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33963521943
---

The traced South Branch bank walks a dry seam in Wright's wash for 30 m, and repairing it moves the waterline.

Found by T-0684, and the measurement is already done — see
`docs/RESEARCH/south_branch_spike_1834.md`, which this ticket should be read
with rather than re-derived from.

**What is wrong.** `river.geojson`'s *South Division shore* vertices 8, 9 and 10
stand 11.9, 12.4 and 14.7 m west of the bank Wright inked, where the other 66
bank vertices in the epoch have a median of 0.70 m. Wright's wash is continuous
to the ink through the whole reach (median gap 0.70 m, worst 2.10 m over 221
rows), but at region rows 662-690 a dry seam three to six pixels wide runs
inside the wash parallel to the bank. The strip east of the seam is separated
from the channel body, `tools/trace_river.py`'s morphology does not recover it,
and the traced boundary walks the seam instead of the bank. Reproduce with
`python3 tools/measure_water_outliers.py --lobe-map`.

**Why it is not fixed in T-0684.** T-0453 acceptance 4: nothing moves there. The
repair is a change inside the trace, it re-derives the whole ring, and moving
the waterline re-derives `tools/generate_plat_lots.py`'s headroom check, the
wet-sample refusals and the frontage works. That count of changed records is
the work.

**Acceptance:**

1. The seam is bridged inside `tools/trace_river.py` — a parameter or a
   bank-side rule that reads the ink as well as the wash — and NOT by editing
   the GeoJSON. `--check` must reproduce whatever is committed.
2. The repair is shown not to have moved anything else: `measure_water_outliers.py
   --vs-ink` before and after, with the median and the p90 reported for both, and
   no bank vertex made worse.
3. Every downstream derivation the waterline feeds is re-run and its delta
   counted in the PR — records changed, refusals gained or lost.
4. The Clark Street bulge (`docs/RESEARCH/clark_reach_bulge_1834.md`) is the same
   family of fault in `tools/trace_shoreline.py`. Say whether the fix generalises
   or whether the two tools stay separate.
