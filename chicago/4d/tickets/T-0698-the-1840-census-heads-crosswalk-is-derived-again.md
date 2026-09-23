---
id: T-0698
title: The 1840 census heads crosswalk is derived against 849 residents and 17 sheets, and the town now holds 1,404 and 25
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-07
pr: 992
claimed_by: run 9/7/2026, 6:39:52 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T11:40:44.401Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34113002137
---

The 1840 census heads crosswalk is derived against 849 residents and 17 sheets, and the town now holds 1,404 and 25.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`data/research/census_1840/resident_crosswalk.json` declares its own inputs, and the declaration is
stale: `residents layer, persons: 849` where the town now holds **1,404**, `1840 left sheets read in
this repo: 17` where **25** are committed, and `Fergus 1843 and Norris 1844 directory adjudications
— the independent discriminator: 79` where there are now **134**. Nothing gates it —
`tools/check.sh` never runs `tools/crosswalk_census_1840_heads.py --check` — so it went stale
silently across T-0514's mint and the sheet reads after it.

**Why T-0670 did not just rebuild it.** It tried. `--build` re-derives to 733 named heads, 8
matched, 17 candidate, 708 refused (from 498/5/5/488) and that is one more ruling than the
`census_1840` domain's spend ceiling allows: `tools/measure_research_spend.py` then reports
"25 reached, 24 written, ceiling 0 (+1)" and the gate fails. The extra ruling has to be RULED onto
the person's card or the ceiling raised with a reason, and neither is a decision a run doing
something else should take.

**The ask.** Re-derive it, spend or refuse the ruling that overruns the ceiling, and then GATE it —
add `python3 tools/crosswalk_census_1840_heads.py --check` to `tools/check.sh` beside the other
crosswalks, so the next mint cannot leave it behind in silence.

**Links:** T-0670 (which found it and reverted rather than rule) · T-0514 (the mint) ·
`tools/crosswalk_census_1840_heads.py` · `tools/measure_research_spend.py`.
