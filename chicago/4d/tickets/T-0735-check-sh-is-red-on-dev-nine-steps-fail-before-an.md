---
id: T-0735
title: check.sh is red on dev: nine steps fail before any branch touches them, five because finishing a research cohort is what makes its own gate fire
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 867
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T10:27:17.209Z
claimed_run: null
---

check.sh is red on dev: nine steps fail before any branch touches them, five because finishing a research cohort is what makes its own gate fire.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured 2026-09-05** on a clean `origin/dev` worktree, before any branch touched it —
`./tools/check.sh` exits 1 with nine failing steps:

```
sidecars derived from data/
the 75-person real-resident research cohort is fixed
the second non-overlapping 75-person research cohort is fixed
the third non-overlapping 75-person research cohort is fixed
the thirteenth research cohort is fixed
the fourteenth research cohort is fixed
the fifteenth research cohort is fixed
the civic, church, press and book residents re-derive from the ladder
the regraded residents re-derive from the ladder too
```

The dev gate IS `check.sh` and nothing else (`docs/PIPELINE.md`), so every steward branch
now merges at parity with a red gate instead of on a green one, and the question "is this
red mine?" costs a worktree and ten minutes on every run. T-0510 paid it.

**Five of the nine are one bug.** `select_resident_research_*.py --gate` refuses a cohort
whose members "already carry a research row" — and researching the cohort is precisely what
gives every member one. The check is meaningful at SELECTION time and self-refuting after
the pass runs. The fix is narrow: `researched_ids()` should ignore a row whose
`resident_research.ticket` is the cohort's own ticket, so a row from ANOTHER pass still
fails and completion does not. Four files carry the same shape: `select_resident_research_
pilot.py`, `_pass_2.py`, `_pass_3.py` and `_pass_13.py` (which pass 14 and 15 share).

The other four want a `--build` and a look at what moved: `tools/build_sidecars*`, and the
two ladder re-derivations under `tools/`.

**Acceptance:** `./tools/check.sh` exits 0 on `origin/dev`, and the cohort gate still fails
when a manifest claims somebody another pass has already ruled on.

---

**CLOSED 2026-09-05 by PR #863 (T-0739).** `./tools/check.sh` exits 0 on `f3dfcc28f`, on
both acceptance clauses: the nine steps are repaired, and the cohort gate's novelty refusal
still fires — #863 scopes it to the first write, when no manifest exists, so a cohort that
completes its own research no longer trips the check that selected it.

**One correction worth keeping, because it explains why the narrow fix was not the one
taken.** This ticket proposed that `researched_ids()` ignore a row whose
`resident_research.ticket` is the cohort's own. Measured against the tree at `cfda02f34`,
that fixes cohort 15 alone: its 76 colliding rows all carry `T-0510`, its own ticket, but
cohorts 13 and 14's 152 carry T-0442, T-0462, T-0463 and T-0493 — written by PR #844 when
the pilot, pass 2 and pass 3 sweeps' findings were finally spent onto the people those
passes reserved in June. Under the narrow fix both cohorts stay red for ever, on other
passes' honest work. The scoping #863 chose has no such hole.

Two of the nine were the ladder re-derivations, and what they were hiding is worth
recording: four cards carried `sources` a merge had left unsorted, 450 `index.json` rows
were missing `projected_resident`, and the regrade had never been run against the land
sales, the parish register, the 1843 directory or the death notices that landed after it —
17 people were standing at `inferred` where the owner's ratified ladder says `attested`.
